#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 로봇 데이터 MongoDB 시뮬레이터 v2.0
실시간 로봇 센서 데이터를 생성하고 MongoDB에 저장합니다.
개선사항: Date 타입 저장, 멱등성 보장, 성능 최적화, 인덱스 자동 관리, MongoDB 응답 처리 강화
"""

import json
import random
import logging
import schedule
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from logging.handlers import RotatingFileHandler
import os


class MongoDBResponse:
    """MongoDB 저장 응답 클래스 - 상세한 결과 및 성능 지표"""
    def __init__(self, success: bool, inserted_id=None, 
                 modified_count=0, matched_count=0, upserted_id=None,
                 error_message=None, execution_time=0.0, 
                 operation_type="unknown"):
        self.success = success
        self.inserted_id = inserted_id
        self.modified_count = modified_count
        self.matched_count = matched_count
        self.upserted_id = upserted_id
        self.error_message = error_message
        self.execution_time = execution_time
        self.operation_type = operation_type  # "insert", "update", "upsert"
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "inserted_id": str(self.inserted_id) if self.inserted_id else None,
            "modified_count": self.modified_count,
            "matched_count": self.matched_count,
            "upserted_id": str(self.upserted_id) if self.upserted_id else None,
            "error_message": self.error_message,
            "execution_time": round(self.execution_time, 3),
            "operation_type": self.operation_type,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        if self.success:
            return f"MongoDB {self.operation_type} 성공 ({self.execution_time:.3f}초)"
        else:
            return f"MongoDB {self.operation_type} 실패: {self.error_message}"


class ProcessFlowTracker:
    """프로세스 플로우 추적 클래스"""
    def __init__(self):
        self.current_step = None
        self.step_start_time = None
        self.processed_robots = 0
        self.generated_data_points = 0
        self.errors = []
        self.steps_completed = []
        
    def start_step(self, step_name: str):
        """단계 시작"""
        self.current_step = step_name
        self.step_start_time = datetime.now()
        logging.info(f"🔄 단계 시작: {step_name}")
    
    def complete_step(self, step_name: str, success: bool = True):
        """단계 완료"""
        if self.current_step == step_name and self.step_start_time:
            duration = (datetime.now() - self.step_start_time).total_seconds()
            status = "완료" if success else "실패"
            logging.info(f"✅ 단계 {status}: {step_name} ({duration:.2f}초)")
            
            self.steps_completed.append({
                "step": step_name,
                "success": success,
                "duration": duration,
                "timestamp": datetime.now()
            })
    
    def add_error(self, error_message: str):
        """오류 추가"""
        self.errors.append({
            "message": error_message,
            "timestamp": datetime.now(),
            "step": self.current_step
        })
    
    def increment_robot(self, data_points_count: int = 0):
        """처리된 로봇 수 증가"""
        self.processed_robots += 1
        self.generated_data_points += data_points_count
    
    def get_current_status(self) -> Dict[str, Any]:
        """현재 진행 상황 반환"""
        return {
            "current_step": self.current_step,
            "processed_robots": self.processed_robots,
            "generated_data_points": self.generated_data_points,
            "step_duration": (datetime.now() - self.step_start_time).total_seconds() if self.step_start_time else 0,
            "errors": self.errors[-5:],  # 최근 5개 오류만
            "steps_completed": self.steps_completed,
            "success_rate": (self.processed_robots / 30 * 100) if self.processed_robots > 0 else 0
        }
    
    def reset(self):
        """상태 초기화"""
        self.current_step = None
        self.step_start_time = None
        self.processed_robots = 0
        self.generated_data_points = 0
        self.errors = []
        self.steps_completed = []

class RobotDataSimulator:
    def __init__(self, config_file: str = "simulator_config.json", target_robot_ids: List[str] = None):
        """시뮬레이터 초기화"""
        self.config = self._load_config(config_file)
        self.client = None
        self.db = None
        self.collection = None
        self.stop_requested = False  # 정지 신호 플래그 추가
        self.process_tracker = ProcessFlowTracker()  # 프로세스 추적기 추가
        
        self._setup_logging()
        self._setup_database()
        self._ensure_indexes()
        
        # 로봇 ID 생성 (개별 로봇 모드 지원)
        if target_robot_ids:
            self.robot_ids = target_robot_ids  # 특정 로봇만 처리
            logging.info(f"🎯 개별 로봇 모드: {target_robot_ids}")
        else:
            self.robot_ids = [f"AGV-{i:03d}" for i in range(1, self.config['simulation']['robot_count'] + 1)]  # 전체 로봇 처리
            logging.info(f"🏭 전체 로봇 모드: {len(self.robot_ids)}대")
        
        self.route_names = [f"ROUTE{i}" for i in range(1, 21)]
        
        # 랜덤 시드 설정
        if self.config['simulation'].get('random_seed') is not None:
            random.seed(self.config['simulation']['random_seed'])
        
        logging.info(f"🚀 로봇 데이터 시뮬레이터 v2.0 초기화 완료")
        logging.info(f"   로봇 수: {len(self.robot_ids)}")
        logging.info(f"   엄격 모드: {self.config['simulation']['strict_mode']}")
        logging.info(f"   정규화 저장: {self.config['simulation']['normalized_storage']}")
        logging.info(f"   랜덤 시드: {self.config['simulation'].get('random_seed', 'None')}")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"설정 파일을 찾을 수 없습니다: {config_file}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"설정 파일 JSON 파싱 오류: {e}")
            raise
    
    def _setup_logging(self):
        """로깅 설정 (로테이션 포함)"""
        log_config = self.config['logging']
        
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_config['file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # RotatingFileHandler 설정
        rotating_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config.get('max_size_mb', 10) * 1024 * 1024,  # MB to bytes
            backupCount=log_config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        # 콘솔 핸들러 (Windows 인코딩 문제 해결)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(log_config['format'])
        rotating_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 로거 설정
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            handlers=[rotating_handler, console_handler],
            force=True
        )
    
    def _setup_database(self):
        """MongoDB 연결 설정"""
        try:
            db_config = self.config['database']
            self.client = MongoClient(db_config['connection_string'])
            
            # 연결 테스트
            self.client.admin.command('ping')
            
            self.db = self.client[db_config['database_name']]
            self.collection = self.db[db_config['collection_name']]
            
            logging.info(f"✅ MongoDB 연결 성공: {db_config['database_name']}.{db_config['collection_name']}")
            
        except ConnectionFailure as e:
            logging.error(f"❌ MongoDB 연결 실패: {e}")
            raise
    
    def _ensure_indexes(self):
        """인덱스 자동 생성 및 보장"""
        try:
            if self.config['simulation']['normalized_storage']:
                # 정규화 모드 인덱스
                self._ensure_normalized_indexes()
            else:
                # 단일 컬렉션 모드 인덱스
                self._ensure_single_collection_indexes()
            
            logging.info("✅ 인덱스 생성/검증 완료")
            
        except Exception as e:
            logging.error(f"❌ 인덱스 생성 실패: {e}")
            # 인덱스 오류는 치명적이지 않으므로 경고만 출력하고 계속 진행
            logging.warning("⚠️ 인덱스 생성 실패했지만 시뮬레이터는 계속 실행됩니다.")
    
    def _ensure_single_collection_indexes(self):
        """단일 컬렉션 모드 인덱스 생성"""
        try:
            # 기존 인덱스 확인
            existing_indexes = list(self.collection.list_indexes())
            index_names = [idx['name'] for idx in existing_indexes]
            
            # 유니크 인덱스 (robot_id + mission_start_date)
            unique_index_name = "robot_id_1_mission_start_date_1"
            if unique_index_name not in index_names:
                self.collection.create_index(
                    [("robot_id", 1), ("mission_start_date", 1)],
                    unique=True,
                    background=True
                )
                logging.info("✅ 유니크 인덱스 생성: robot_id + mission_start_date")
            
            # 일반 인덱스들
            indexes_to_create = [
                ("mission_start_date_1", [("mission_start_date", 1)]),
                ("location_site_1_location_line_1", [("location.site", 1), ("location.line", 1)]),
                ("data_points_timestamp_1", [("data_points.timestamp", 1)]),
                ("robot_id_1", [("robot_id", 1)])
            ]
            
            for index_name, index_spec in indexes_to_create:
                if index_name not in index_names:
                    self.collection.create_index(index_spec, background=True)
                    logging.info(f"✅ 인덱스 생성: {index_name}")
                    
        except Exception as e:
            logging.error(f"❌ 단일 컬렉션 인덱스 생성 실패: {e}")
            raise
    
    def _ensure_normalized_indexes(self):
        """정규화 모드 인덱스 생성"""
        try:
            missions_collection = self.db['robot_missions']
            datapoints_collection = self.db['robot_data_points']
            
            # robot_missions 인덱스
            missions_indexes = list(missions_collection.list_indexes())
            missions_index_names = [idx['name'] for idx in missions_indexes]
            
            # 유니크 인덱스
            unique_index_name = "robot_id_1_mission_start_date_1"
            if unique_index_name not in missions_index_names:
                missions_collection.create_index(
                    [("robot_id", 1), ("mission_start_date", 1)],
                    unique=True,
                    background=True
                )
                logging.info("✅ robot_missions 유니크 인덱스 생성")
            
            # 일반 인덱스들
            missions_indexes_to_create = [
                ("mission_start_date_1", [("mission_start_date", 1)]),
                ("location_site_1_location_line_1", [("location.site", 1), ("location.line", 1)])
            ]
            
            for index_name, index_spec in missions_indexes_to_create:
                if index_name not in missions_index_names:
                    missions_collection.create_index(index_spec, background=True)
                    logging.info(f"✅ robot_missions 인덱스 생성: {index_name}")
            
            # robot_data_points 인덱스
            datapoints_indexes = list(datapoints_collection.list_indexes())
            datapoints_index_names = [idx['name'] for idx in datapoints_indexes]
            
            # 유니크 인덱스
            datapoints_unique_index_name = "mission_id_1_timestamp_1"
            if datapoints_unique_index_name not in datapoints_index_names:
                datapoints_collection.create_index(
                    [("mission_id", 1), ("timestamp", 1)],
                    unique=True,
                    background=True
                )
                logging.info("✅ robot_data_points 유니크 인덱스 생성")
            
            # 일반 인덱스들
            datapoints_indexes_to_create = [
                ("robot_id_1_timestamp_1", [("robot_id", 1), ("timestamp", 1)]),
                ("timestamp_1", [("timestamp", 1)])
            ]
            
            for index_name, index_spec in datapoints_indexes_to_create:
                if index_name not in datapoints_index_names:
                    datapoints_collection.create_index(index_spec, background=True)
                    logging.info(f"✅ robot_data_points 인덱스 생성: {index_name}")
                    
        except Exception as e:
            logging.error(f"❌ 정규화 모드 인덱스 생성 실패: {e}")
            raise
    
    def generate_random_location(self) -> Dict[str, str]:
        """랜덤 위치 생성"""
        locations = self.config['locations']
        
        if self.config['simulation']['strict_mode']:
            # 엄격 모드: 권장 값만 사용
            return {
                'site': random.choice(locations['sites']),
                'line': random.choice(locations['lines']),
                'floor': random.choice(locations['floors']),
                'area': locations['area']
            }
        else:
            # 자유 모드: 원문 값도 허용
            sites = locations['sites'] + ['P']  # 원문 값 추가
            lines = locations['lines'] + ['P1L']  # 원문 값 추가
            floors = locations['floors'] + ['3F', '5F']  # 원문 값 추가
            areas = [locations['area'], 'FSF']  # 원문 값 추가
            
            return {
                'site': random.choice(sites),
                'line': random.choice(lines),
                'floor': random.choice(floors),
                'area': random.choice(areas)
            }
    
    def generate_sensor_data(self, timestamp: datetime) -> Dict[str, Any]:
        """센서 데이터 생성 (Date 타입 사용)"""
        sensor_ranges = self.config['sensor_ranges']
        
        # 기본 센서 데이터 (Date 타입으로 저장)
        data = {
            'timestamp': timestamp,  # datetime 객체 직접 저장
            'unix_time': timestamp.timestamp(),
            'pos_x': random.randint(sensor_ranges['pos_x'][0], sensor_ranges['pos_x'][1]),
            'pos_y': random.randint(sensor_ranges['pos_y'][0], sensor_ranges['pos_y'][1]),
            'theta': random.randint(sensor_ranges['theta'][0], sensor_ranges['theta'][1]),
            'localization_score': round(random.uniform(sensor_ranges['localization_score'][0], sensor_ranges['localization_score'][1]), 2),
            'tilt_x': round(random.uniform(sensor_ranges['tilt_x'][0], sensor_ranges['tilt_x'][1]), 2),
            'tilt_y': round(random.uniform(sensor_ranges['tilt_y'][0], sensor_ranges['tilt_y'][1]), 2),
            'spm_flex_1': 0,
            'spm_flex_2': 0,
            'gtd_5000': 0,
            'NH3': round(random.uniform(sensor_ranges['NH3'][0], sensor_ranges['NH3'][1]), 2),
            'H2S': round(random.uniform(sensor_ranges['H2S'][0], sensor_ranges['H2S'][1]), 2),
            'VOCs': round(random.uniform(sensor_ranges['VOCs'][0], sensor_ranges['VOCs'][1]), 2),
            'F2': round(random.uniform(sensor_ranges['F2'][0], sensor_ranges['F2'][1]), 3),
            'HF': round(random.uniform(sensor_ranges['HF'][0], sensor_ranges['HF'][1]), 2),
            'temperature': round(random.uniform(sensor_ranges['temperature'][0], sensor_ranges['temperature'][1]), 1),
            'humidity': round(random.uniform(sensor_ranges['humidity'][0], sensor_ranges['humidity'][1]), 1),
            'illuminance': round(random.uniform(sensor_ranges['illuminance'][0], sensor_ranges['illuminance'][1]), 2),
            'noise': round(random.uniform(sensor_ranges['noise'][0], sensor_ranges['noise'][1]), 2),
            'thermal_cam_Pan': 0,
            'thermal_cam_tilt': 0,
            'thermal_cam_zoom': 0,
            'sonic_cam_pan': 0,
            'sonic_cam_Tilt': 0,  # 원문 대소문자 유지
            'sonic_cam_zoom': 0,
            'normal_Pan': 0,
            'normal_Tilt': 0,
            'normal_Zoom': 0,
            'PTZ_Pan': 0,
            'PT7_Tilt': 0,  # 원문 필드명 유지
            'PTZ_Zoom': 0,
            'pillar_number': f"G{random.randint(10, 25)} D-{random.randint(1, 5)}",
            'bay_number': f"P{random.randint(0, 10):02d}",
            'shot_number': str(random.randint(1, 10)),
            'vr_image': {'$oid': f"689ad5a5869bfe5d99d68ccf"},
            'ptz_image': {'$oid': f"689ad5fdf1d60ed343922e4e"},
            'thermal_image': {'$oid': f"689ad6089fec0031f514f5e1"},
            'thermal_rawdata': {'$oid': f"689ad61606ac3c5ece7086c3"},
            'thermal_real_image': {'$oid': f"689ad62e3d11dabdfa4b881e"},
            'sonic_original_image': {'$oid': f"689ad625abeb55500dde1efd"},
            'sonic_rawdata': {'$oid': f"689ad625abeb55500dde1efd"}
        }
        
        return data
    
    def generate_data_points(self, mission_start: datetime, mission_end: datetime) -> List[Dict[str, Any]]:
        """미션 기간 동안의 데이터 포인트 생성"""
        data_points_count = random.randint(
            self.config['simulation']['data_points_min'],
            self.config['simulation']['data_points_max']
        )
        
        data_points = []
        mission_duration = (mission_end - mission_start).total_seconds()
        
        for i in range(data_points_count):
            # 미션 기간 내 균등 분포
            time_offset = (mission_duration / (data_points_count - 1)) * i if data_points_count > 1 else 0
            timestamp = mission_start + timedelta(seconds=time_offset)
            
            data_point = self.generate_sensor_data(timestamp)
            data_points.append(data_point)
        
        return data_points
    
    def generate_mission_data(self, robot_id: str, start_time: datetime) -> Dict[str, Any]:
        """단일 미션 데이터 생성 (Date 타입 사용)"""
        # 미션 지속시간 (4~10분)
        duration_minutes = random.randint(
            self.config['simulation']['mission_duration_min'],
            self.config['simulation']['mission_duration_max']
        )
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # 배터리 상태
        battery_start = random.randint(
            self.config['battery']['start_min'],
            self.config['battery']['start_max']
        )
        battery_drain = random.randint(
            self.config['battery']['drain_min'],
            self.config['battery']['drain_max']
        )
        battery_end = max(0, battery_start - battery_drain)
        
        # 미션 데이터 생성 (Date 타입으로 저장)
        mission_data = {
            'robot_id': robot_id,
            'mission_start_date': start_time,  # datetime 객체 직접 저장
            'mission_end_date': end_time,
            'mission_start_battery_state': battery_start,
            'mission_end_battery_state': battery_end,
            'route_name': random.choice(self.route_names),
            'location': self.generate_random_location(),
            'data_points': self.generate_data_points(start_time, end_time),
            'simulated_at': datetime.now()  # datetime 객체 직접 저장
        }
        
        return mission_data
    
    def generate_time_based_missions(self, base_time: datetime) -> List[Dict[str, Any]]:
        """10분 단위 기준으로 미션 생성 (정확한 그리드 스냅)"""
        missions = []
        time_grid = self.config['simulation']['time_grid_minutes']
        
        # 10분 그리드로 스냅
        base = base_time - timedelta(
            minutes=base_time.minute % time_grid,
            seconds=base_time.second,
            microseconds=base_time.microsecond
        )
        
        for robot_id in self.robot_ids:
            # 10분 그리드 내 랜덤 오프셋 (동시 출발 방지)
            offset_minutes = random.randint(0, time_grid - 1)
            start_time = base + timedelta(minutes=offset_minutes)
            
            mission_data = self.generate_mission_data(robot_id, start_time)
            missions.append(mission_data)
        
        return missions
    
    def save_to_mongodb(self, mission_data: Dict[str, Any]) -> MongoDBResponse:
        """MongoDB에 미션 데이터 저장 (멱등성 보장) - 강화된 응답 처리"""
        start_time = time.time()
        
        try:
            if self.config['simulation']['normalized_storage']:
                result = self._save_normalized_enhanced(mission_data)
            else:
                result = self._save_single_collection_enhanced(mission_data)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"데이터 저장 실패: {str(e)}"
            logging.error(f"❌ {error_msg}")
            self.process_tracker.add_error(error_msg)
            
            return MongoDBResponse(
                success=False,
                error_message=error_msg,
                execution_time=execution_time,
                operation_type="save_failed"
            )
    
    def _save_single_collection_enhanced(self, mission_data: Dict[str, Any]) -> MongoDBResponse:
        """단일 컬렉션에 저장 (멱등성 보장) - 강화된 응답 처리"""
        try:
            # 중복 체크 및 업서트
            filter_criteria = {
                "robot_id": mission_data['robot_id'],
                "mission_start_date": mission_data['mission_start_date']
            }
            
            result = self.collection.replace_one(filter_criteria, mission_data, upsert=True)
            
            # 결과 분석
            if result.upserted_id:
                operation_type = "insert"
                logging.info(f"✅ {mission_data['robot_id']} 새 미션 삽입")
            elif result.modified_count > 0:
                operation_type = "update"
                logging.info(f"✅ {mission_data['robot_id']} 기존 미션 업데이트")
            else:
                operation_type = "no_change"
                logging.info(f"ℹ️ {mission_data['robot_id']} 미션 변경 없음")
            
            return MongoDBResponse(
                success=True,
                inserted_id=result.upserted_id,
                modified_count=result.modified_count,
                matched_count=result.matched_count,
                upserted_id=result.upserted_id,
                operation_type=operation_type
            )
            
        except Exception as e:
            error_msg = f"단일 컬렉션 저장 실패: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return MongoDBResponse(
                success=False,
                error_message=error_msg,
                operation_type="single_collection_error"
            )
    
    def _save_normalized_enhanced(self, mission_data: Dict[str, Any]) -> MongoDBResponse:
        """정규화된 구조로 저장 (멱등성 보장 + insert_many 최적화) - 강화된 응답 처리"""
        try:
            missions_collection = self.db['robot_missions']
            datapoints_collection = self.db['robot_data_points']
            
            # 미션 메타데이터 저장 (멱등성 보장)
            mission_meta = {k: v for k, v in mission_data.items() if k != 'data_points'}
            
            # 업서트로 중복 방지
            filter_criteria = {
                "robot_id": mission_meta['robot_id'],
                "mission_start_date": mission_meta['mission_start_date']
            }
            
            mission_result = missions_collection.replace_one(filter_criteria, mission_meta, upsert=True)
            
            # 미션 ID 결정
            if mission_result.upserted_id:
                mission_id = mission_result.upserted_id
                operation_type = "insert_normalized"
                logging.info(f"✅ {mission_data['robot_id']} 새 정규화 미션 삽입")
            else:
                # 기존 미션 찾기
                existing_mission = missions_collection.find_one(filter_criteria)
                mission_id = existing_mission['_id']
                operation_type = "update_normalized"
                logging.info(f"✅ {mission_data['robot_id']} 기존 정규화 미션 업데이트")
                
                # 기존 데이터 포인트 삭제
                delete_result = datapoints_collection.delete_many({"mission_id": mission_id})
                logging.info(f"🗑️ {delete_result.deleted_count}개 기존 데이터 포인트 삭제")
            
            # 데이터 포인트 일괄 삽입 (insert_many 최적화)
            datapoints_inserted = 0
            if mission_data['data_points']:
                data_points_batch = []
                for dp in mission_data['data_points']:
                    dp_copy = dp.copy()
                    dp_copy['mission_id'] = mission_id
                    dp_copy['robot_id'] = mission_data['robot_id']
                    data_points_batch.append(dp_copy)
                
                if data_points_batch:
                    dp_result = datapoints_collection.insert_many(data_points_batch, ordered=False)
                    datapoints_inserted = len(dp_result.inserted_ids)
                    logging.info(f"📊 {datapoints_inserted}개 데이터 포인트 삽입")
            
            return MongoDBResponse(
                success=True,
                inserted_id=mission_result.upserted_id,
                modified_count=mission_result.modified_count + datapoints_inserted,
                matched_count=mission_result.matched_count,
                upserted_id=mission_result.upserted_id,
                operation_type=operation_type
            )
            
        except Exception as e:
            error_msg = f"정규화 저장 실패: {str(e)}"
            logging.error(f"❌ {error_msg}")
            return MongoDBResponse(
                success=False,
                error_message=error_msg,
                operation_type="normalized_error"
            )
    
    def generate_and_save_missions(self):
        """미션 생성 및 저장 (프로세스 추적 포함)"""
        current_time = datetime.now()
        logging.info(f"🔄 미션 생성 시작: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 프로세스 추적 초기화
        self.process_tracker.reset()
        
        # 1단계: 미션 생성
        self.process_tracker.start_step("mission_generation")
        missions = self.generate_time_based_missions(current_time)
        self.process_tracker.complete_step("mission_generation", True)
        
        # 2단계: 데이터 저장
        self.process_tracker.start_step("data_saving")
        success_count = 0
        total_execution_time = 0.0
        operation_stats = {"insert": 0, "update": 0, "error": 0}
        
        for i, mission in enumerate(missions):
            robot_id = mission['robot_id']
            data_points_count = len(mission.get('data_points', []))
            
            # MongoDB 저장 (강화된 응답 처리)
            result = self.save_to_mongodb(mission)
            
            if result.success:
                success_count += 1
                total_execution_time += result.execution_time
                operation_stats[result.operation_type.split("_")[0]] = operation_stats.get(result.operation_type.split("_")[0], 0) + 1
                
                logging.info(f"✅ {robot_id} {result}")
                self.process_tracker.increment_robot(data_points_count)
            else:
                operation_stats["error"] += 1
                logging.error(f"❌ {robot_id} {result}")
                self.process_tracker.add_error(f"{robot_id}: {result.error_message}")
        
        self.process_tracker.complete_step("data_saving", success_count == len(missions))
        
        # 결과 통계
        avg_execution_time = total_execution_time / len(missions) if missions else 0
        logging.info(f"📊 미션 생성 완료: {success_count}/{len(missions)} 성공")
        logging.info(f"⏱️ 평균 저장 시간: {avg_execution_time:.3f}초")
        logging.info(f"📈 작업 통계: {operation_stats}")
        
        return {
            "success_count": success_count,
            "total_missions": len(missions),
            "avg_execution_time": avg_execution_time,
            "operation_stats": operation_stats,
            "process_status": self.process_tracker.get_current_status()
        }
    
    def get_statistics(self):
        """현재 데이터 통계 조회"""
        try:
            if self.config['simulation']['normalized_storage']:
                return self._get_normalized_statistics()
            else:
                return self._get_single_collection_statistics()
        except Exception as e:
            logging.error(f"❌ 통계 조회 실패: {e}")
            return 0
    
    def _get_single_collection_statistics(self):
        """단일 컬렉션 통계"""
        total_docs = self.collection.count_documents({})
        logging.info(f"📊 현재 총 문서 수: {total_docs}")
        
        # 로봇별 통계
        pipeline = [
            {"$group": {
                "_id": "$robot_id",
                "count": {"$sum": 1},
                "avg_battery_start": {"$avg": "$mission_start_battery_state"},
                "avg_battery_end": {"$avg": "$mission_end_battery_state"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        robot_stats = list(self.collection.aggregate(pipeline))
        logging.info(f"🤖 로봇별 통계:")
        for stat in robot_stats:
            logging.info(f"   {stat['_id']}: {stat['count']}개 미션")
        
        return total_docs
    
    def _get_normalized_statistics(self):
        """정규화 모드 통계"""
        missions_collection = self.db['robot_missions']
        datapoints_collection = self.db['robot_data_points']
        
        total_missions = missions_collection.count_documents({})
        total_datapoints = datapoints_collection.count_documents({})
        
        logging.info(f"📊 정규화 모드 통계:")
        logging.info(f"   총 미션 수: {total_missions}")
        logging.info(f"   총 데이터 포인트 수: {total_datapoints}")
        
        # 로봇별 통계
        pipeline = [
            {"$lookup": {
                "from": "robot_data_points",
                "localField": "_id",
                "foreignField": "mission_id",
                "as": "data_points"
            }},
            {"$project": {
                "robot_id": 1,
                "data_point_count": {"$size": "$data_points"}
            }},
            {"$group": {
                "_id": "$robot_id",
                "mission_count": {"$sum": 1},
                "total_data_points": {"$sum": "$data_point_count"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        robot_stats = list(missions_collection.aggregate(pipeline))
        logging.info(f"🤖 로봇별 통계:")
        for stat in robot_stats:
            logging.info(f"   {stat['_id']}: {stat['mission_count']}개 미션, {stat['total_data_points']}개 데이터 포인트")
        
        return total_missions
    
    def run_simulator(self):
        """시뮬레이터 실행"""
        logging.info("🚀 로봇 데이터 시뮬레이터 v2.0 시작")
        
        # 초기 통계
        self.get_statistics()
        
        # 스케줄링 설정
        mission_interval = self.config['scheduling']['mission_interval_minutes']
        schedule.every(mission_interval).minutes.do(self.generate_and_save_missions)
        
        logging.info(f"⏰ 스케줄 설정: {mission_interval}분마다 미션 생성")
        
        try:
            while not self.stop_requested:  # 정지 신호 확인
                schedule.run_pending()
                time.sleep(1)
                
                # 정지 신호가 있으면 루프 종료
                if self.stop_requested:
                    logging.info("🛑 정지 신호를 받았습니다.")
                    break
                    
        except KeyboardInterrupt:
            logging.info("🛑 시뮬레이터 중지됨 (KeyboardInterrupt)")
        finally:
            self.client.close()
            logging.info("🔌 MongoDB 연결 종료")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='로봇 데이터 MongoDB 시뮬레이터 v2.0')
    parser.add_argument('--config', default='simulator_config.json', help='설정 파일 경로')
    parser.add_argument('--strict', action='store_true', help='엄격 모드 (권장 값만 사용)')
    parser.add_argument('--normalized', action='store_true', help='정규화 저장 모드')
    parser.add_argument('--interval', type=int, help='미션 생성 간격 (분)')
    parser.add_argument('--test', action='store_true', help='테스트 모드 (1회 실행)')
    parser.add_argument('--seed', type=int, help='랜덤 시드 설정 (재현 가능성)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 (상세 로그)')
    
    args = parser.parse_args()
    
    try:
        # 시뮬레이터 초기화
        simulator = RobotDataSimulator(args.config)
        
        # 명령행 옵션 적용
        if args.strict:
            simulator.config['simulation']['strict_mode'] = True
            logging.info("🔒 엄격 모드 활성화")
        
        if args.normalized:
            simulator.config['simulation']['normalized_storage'] = True
            logging.info("📊 정규화 저장 모드 활성화")
        
        if args.interval:
            simulator.config['scheduling']['mission_interval_minutes'] = args.interval
            logging.info(f"⏰ 미션 간격 변경: {args.interval}분")
        
        if args.seed is not None:
            simulator.config['simulation']['random_seed'] = args.seed
            random.seed(args.seed)
            logging.info(f"🎲 랜덤 시드 설정: {args.seed}")
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.info("🔍 디버그 모드 활성화")
        
        if args.test:
            # 테스트 모드: 1회 실행
            logging.info("🧪 테스트 모드 실행")
            simulator.generate_and_save_missions()
            simulator.get_statistics()
        else:
            # 정상 모드: 지속 실행
            simulator.run_simulator()
            
    except Exception as e:
        logging.error(f"❌ 시뮬레이터 실행 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
