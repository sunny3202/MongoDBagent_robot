#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개별 로봇 관리 시스템
각 로봇의 상태를 개별적으로 제어하고 모니터링
"""

import json
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from robot_data_simulator import RobotDataSimulator, ProcessFlowTracker


class RobotStatus(Enum):
    """로봇 상태"""
    RUNNING = "running"      # 🟢 작업중
    IDLE = "idle"           # 🟡 대기중  
    STOPPED = "stopped"     # 🔴 정지됨
    ERROR = "error"         # ⚠️ 오류
    MAINTENANCE = "maintenance"  # 🔧 점검중


class RobotState:
    """개별 로봇 상태 정보"""
    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.status = RobotStatus.STOPPED
        self.last_seen = None
        self.battery_level = 0
        self.last_mission_time = None
        self.error_message = None
        self.missions_today = 0
        self.data_points_today = 0
        self.start_time = None
        self.total_runtime = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "robot_id": self.robot_id,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "battery_level": self.battery_level,
            "last_mission_time": self.last_mission_time.isoformat() if self.last_mission_time else None,
            "error_message": self.error_message,
            "missions_today": self.missions_today,
            "data_points_today": self.data_points_today,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "total_runtime": self.total_runtime,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }


class IndividualRobotManager:
    """개별 로봇 관리자"""
    
    def __init__(self, config_file: str = "simulator_config.json"):
        self.config_file = config_file
        self.robot_states: Dict[str, RobotState] = {}
        self.robot_threads: Dict[str, threading.Thread] = {}
        self.robot_simulators: Dict[str, RobotDataSimulator] = {}
        self.process_flows: Dict[str, ProcessFlowTracker] = {}
        
        # 로봇 ID 목록 생성 (설정에서 가져오기)
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        robot_count = config.get('simulation', {}).get('robot_count', 30)
        self.robot_ids = [f"AGV-{i:03d}" for i in range(1, robot_count + 1)]
        
        # 모든 로봇 상태 초기화
        for robot_id in self.robot_ids:
            self.robot_states[robot_id] = RobotState(robot_id)
            self.process_flows[robot_id] = ProcessFlowTracker()
        
        logging.info(f"🤖 개별 로봇 관리자 초기화 완료: {len(self.robot_ids)}대")
    
    def start_robot(self, robot_id: str) -> Dict[str, Any]:
        """개별 로봇 시작"""
        try:
            if robot_id not in self.robot_states:
                return {"success": False, "error": f"로봇 {robot_id}를 찾을 수 없습니다"}
            
            robot_state = self.robot_states[robot_id]
            
            if robot_state.status == RobotStatus.RUNNING:
                return {"success": False, "error": f"로봇 {robot_id}가 이미 실행 중입니다"}
            
            # 개별 로봇 전용 시뮬레이터 생성 (특정 로봇만 처리)
            simulator = RobotDataSimulator(self.config_file, target_robot_ids=[robot_id])
            
            # 스레드에서 실행
            thread = threading.Thread(
                target=self._run_robot_simulator,
                args=(robot_id, simulator),
                daemon=True
            )
            thread.start()
            
            # 상태 업데이트
            robot_state.status = RobotStatus.RUNNING
            robot_state.start_time = datetime.now()
            robot_state.last_seen = datetime.now()
            robot_state.error_message = None
            
            self.robot_threads[robot_id] = thread
            self.robot_simulators[robot_id] = simulator
            
            logging.info(f"✅ 로봇 {robot_id} 시작됨")
            
            return {
                "success": True,
                "message": f"로봇 {robot_id}가 시작되었습니다",
                "robot_state": robot_state.to_dict()
            }
            
        except Exception as e:
            logging.error(f"❌ 로봇 {robot_id} 시작 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_robot(self, robot_id: str) -> Dict[str, Any]:
        """개별 로봇 정지"""
        try:
            if robot_id not in self.robot_states:
                return {"success": False, "error": f"로봇 {robot_id}를 찾을 수 없습니다"}
            
            robot_state = self.robot_states[robot_id]
            
            if robot_state.status != RobotStatus.RUNNING:
                return {"success": False, "error": f"로봇 {robot_id}가 실행 중이 아닙니다"}
            
            # 시뮬레이터 정지
            if robot_id in self.robot_simulators:
                simulator = self.robot_simulators[robot_id]
                simulator.stop_requested = True
                
                # 스레드 종료 대기
                if robot_id in self.robot_threads:
                    thread = self.robot_threads[robot_id]
                    thread.join(timeout=5)
                
                # 정리
                del self.robot_simulators[robot_id]
                del self.robot_threads[robot_id]
            
            # 상태 업데이트
            if robot_state.start_time:
                robot_state.total_runtime += (datetime.now() - robot_state.start_time).total_seconds()
            
            robot_state.status = RobotStatus.STOPPED
            robot_state.start_time = None
            robot_state.last_seen = datetime.now()
            
            logging.info(f"🛑 로봇 {robot_id} 정지됨")
            
            return {
                "success": True,
                "message": f"로봇 {robot_id}가 정지되었습니다",
                "robot_state": robot_state.to_dict()
            }
            
        except Exception as e:
            logging.error(f"❌ 로봇 {robot_id} 정지 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def reset_robot(self, robot_id: str) -> Dict[str, Any]:
        """개별 로봇 리셋"""
        try:
            if robot_id not in self.robot_states:
                return {"success": False, "error": f"로봇 {robot_id}를 찾을 수 없습니다"}
            
            # 실행 중이면 먼저 정지
            if self.robot_states[robot_id].status == RobotStatus.RUNNING:
                stop_result = self.stop_robot(robot_id)
                if not stop_result["success"]:
                    return stop_result
                time.sleep(1)  # 정지 대기
            
            # 상태 초기화
            robot_state = self.robot_states[robot_id]
            robot_state.status = RobotStatus.STOPPED
            robot_state.last_seen = datetime.now()
            robot_state.error_message = None
            robot_state.missions_today = 0
            robot_state.data_points_today = 0
            robot_state.total_runtime = 0
            robot_state.start_time = None
            
            # 프로세스 플로우 리셋
            self.process_flows[robot_id].reset()
            
            logging.info(f"🔄 로봇 {robot_id} 리셋 완료")
            
            return {
                "success": True,
                "message": f"로봇 {robot_id}가 리셋되었습니다",
                "robot_state": robot_state.to_dict()
            }
            
        except Exception as e:
            logging.error(f"❌ 로봇 {robot_id} 리셋 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def get_robot_status(self, robot_id: str) -> Dict[str, Any]:
        """개별 로봇 상태 조회"""
        if robot_id not in self.robot_states:
            return {"success": False, "error": f"로봇 {robot_id}를 찾을 수 없습니다"}
        
        robot_state = self.robot_states[robot_id]
        process_status = self.process_flows[robot_id].get_current_status()
        
        return {
            "success": True,
            "robot_state": robot_state.to_dict(),
            "process_status": process_status
        }
    
    def get_all_robots_status(self) -> Dict[str, Any]:
        """모든 로봇 상태 조회"""
        robots = []
        summary = {
            "running": 0,
            "idle": 0, 
            "stopped": 0,
            "error": 0,
            "maintenance": 0
        }
        
        for robot_id, robot_state in self.robot_states.items():
            robots.append(robot_state.to_dict())
            summary[robot_state.status.value] += 1
        
        return {
            "success": True,
            "robots": robots,
            "summary": summary,
            "total_robots": len(self.robot_ids)
        }
    
    def get_operational_stats(self) -> Dict[str, Any]:
        """운영 중심 통계 - 대시보드 호환 형식"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_missions_today = sum(state.missions_today for state in self.robot_states.values())
        total_data_points_today = sum(state.data_points_today for state in self.robot_states.values())
        
        # 상태별 집계
        status_count = {
            "working": 0,    # 대시보드가 기대하는 필드명
            "moving": 0,     # 대시보드가 기대하는 필드명
            "idle": 0,
            "error": 0
        }
        
        # 배터리 통계
        battery_levels = [state.battery_level for state in self.robot_states.values() if state.battery_level > 0]
        avg_battery = sum(battery_levels) / len(battery_levels) if battery_levels else 0
        
        low_battery_robots = []
        critical_battery_robots = []
        error_robots = []
        
        for robot_id, state in self.robot_states.items():
            # 상태 매핑 (대시보드 호환)
            if state.status == RobotStatus.RUNNING:
                status_count["working"] += 1
            elif state.status == RobotStatus.IDLE:
                status_count["idle"] += 1
            elif state.status == RobotStatus.ERROR:
                status_count["error"] += 1
            else:
                status_count["idle"] += 1  # 기본값
            
            # 배터리 알림
            if state.battery_level < 20 and state.battery_level > 0:
                critical_battery_robots.append({
                    "robot_id": robot_id,
                    "battery_level": state.battery_level
                })
            elif state.battery_level < 30 and state.battery_level > 0:
                low_battery_robots.append({
                    "robot_id": robot_id,
                    "battery_level": state.battery_level
                })
            
            if state.status == RobotStatus.ERROR:
                error_robots.append({
                    "robot_id": robot_id,
                    "error_message": state.error_message
                })
        
        # 🎯 대시보드가 기대하는 형식으로 반환
        return {
            "success": True,  # 🔥 대시보드가 필수로 확인하는 필드
            "daily_stats": {
                "completed_missions": total_missions_today,
                "total_data_points": total_data_points_today,
                "success_rate": 98.5,
                "avg_process_time": 6.8,  # 대시보드가 기대하는 필드
                "date": today_start.isoformat()
            },
            "robot_status": status_count,  # 🔥 대시보드가 기대하는 필드명
            "battery_stats": {  # 🔥 대시보드가 기대하는 필드
                "average": round(avg_battery, 1),
                "low_count": len(low_battery_robots),
                "critical_count": len(critical_battery_robots)
            },
            "alerts": {
                "low_battery": low_battery_robots,
                "errors": error_robots,
                "critical_count": len(critical_battery_robots) + len(error_robots)
            },
            "timestamp": now.isoformat()
        }
    
    def _run_robot_simulator(self, robot_id: str, simulator: RobotDataSimulator):
        """개별 로봇 시뮬레이터 실행"""
        try:
            robot_state = self.robot_states[robot_id]
            process_tracker = self.process_flows[robot_id]
            
            logging.info(f"🚀 로봇 {robot_id} 시뮬레이터 시작")
            
            while not simulator.stop_requested:
                try:
                    # 미션 생성 및 실행
                    process_tracker.reset()
                    result = simulator.generate_and_save_missions()
                    
                    if result and isinstance(result, dict):
                        robot_state.missions_today += result.get('success_count', 0)
                        robot_state.data_points_today += result.get('process_status', {}).get('generated_data_points', 0)
                        robot_state.battery_level = 85 - (robot_state.missions_today * 2)  # 간단한 배터리 시뮬레이션
                    
                    robot_state.last_seen = datetime.now()
                    robot_state.last_mission_time = datetime.now()
                    
                    # 10분 대기 (설정에서 가져와야 함)
                    for _ in range(600):  # 10분 = 600초
                        if simulator.stop_requested:
                            break
                        time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"❌ 로봇 {robot_id} 실행 오류: {e}")
                    robot_state.status = RobotStatus.ERROR
                    robot_state.error_message = str(e)
                    break
            
            logging.info(f"🛑 로봇 {robot_id} 시뮬레이터 종료")
            
        except Exception as e:
            logging.error(f"❌ 로봇 {robot_id} 시뮬레이터 치명적 오류: {e}")
            self.robot_states[robot_id].status = RobotStatus.ERROR
            self.robot_states[robot_id].error_message = str(e)
    
    def start_all_robots(self) -> Dict[str, Any]:
        """모든 로봇 시작"""
        results = []
        started_count = 0
        
        for robot_id in self.robot_ids:
            if self.robot_states[robot_id].status != RobotStatus.RUNNING:
                result = self.start_robot(robot_id)
                results.append({"robot_id": robot_id, "result": result})
                if result["success"]:
                    started_count += 1
        
        return {
            "success": True,
            "message": f"{started_count}대 로봇 시작 완료",
            "results": results,
            "started_count": started_count,
            "total_robots": len(self.robot_ids)
        }

    def stop_all_robots(self) -> Dict[str, Any]:
        """모든 로봇 정지"""
        results = []
        stopped_count = 0
        
        for robot_id in self.robot_ids:
            if self.robot_states[robot_id].status == RobotStatus.RUNNING:
                result = self.stop_robot(robot_id)
                results.append({"robot_id": robot_id, "result": result})
                if result["success"]:
                    stopped_count += 1
        
        return {
            "success": True,
            "message": f"{stopped_count}대 로봇 정지 완료",
            "results": results,
            "stopped_count": stopped_count,
            "total_robots": len(self.robot_ids)
        }
    
    def reset_all_robots(self) -> Dict[str, Any]:
        """모든 로봇 리셋"""
        results = []
        for robot_id in self.robot_ids:
            result = self.reset_robot(robot_id)
            results.append({"robot_id": robot_id, "result": result})
        
        return {
            "success": True,
            "message": f"{len(results)}대 로봇 리셋 완료", 
            "results": results
        }
