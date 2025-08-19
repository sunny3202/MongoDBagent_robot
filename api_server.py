#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 로봇 데이터 시뮬레이터 REST API 서버
모니터링 앱과 연동하여 시뮬레이터를 원격 제어합니다.
"""

import json
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from robot_data_simulator import RobotDataSimulator
from mongodb_stats import MongoDBStatsInterface
from robot_manager import IndividualRobotManager
from config_manager import ConfigManager, create_config_blueprint
from pymongo import MongoClient
import logging

class SimulatorAPI:
    def __init__(self, config_file: str = "simulator_config.json"):
        """API 서버 초기화"""
        self.config_file = config_file
        self.simulator = None
        self.simulator_thread = None
        self.is_running = False
        self.start_time = None
        self.last_status = "stopped"
        self.error_message = None
        
        # MongoDB 직접 연결 설정
        self.config = self._load_config()
        self.mongo_client = None
        self.mongo_stats = None
        self._setup_mongodb_connection()
        
        # 개별 로봇 관리자 초기화
        self.robot_manager = IndividualRobotManager(config_file)
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager(config_file)
        
        # Flask 앱 설정
        self.app = Flask(__name__)
        CORS(self.app)  # CORS 허용
        
        # 설정 관리 Blueprint 등록
        config_bp = create_config_blueprint(self.config_manager)
        self.app.register_blueprint(config_bp)
        
        # API 라우트 등록
        self._register_routes()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('api_server.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logging.info("시뮬레이터 API 서버 v2.0 초기화 완료")
        
    def _load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    def _setup_mongodb_connection(self):
        """MongoDB 연결 설정 (API 서버 전용)"""
        try:
            if not self.config:
                logging.warning("설정이 없어 MongoDB 연결을 건너뜁니다")
                return
                
            connection_string = self.config.get('database', {}).get('connection_string', 'mongodb://localhost:27017/')
            database_name = self.config.get('database', {}).get('database_name', 'robot_data')
            
            self.mongo_client = MongoClient(connection_string)
            db = self.mongo_client[database_name]
            
            # 연결 테스트
            db.client.admin.command('ping')
            
            # MongoDB 통계 인터페이스 초기화
            self.mongo_stats = MongoDBStatsInterface(db, self.config)
            
            logging.info(f"✅ MongoDB 연결 성공: {database_name}")
            
        except Exception as e:
            logging.error(f"❌ MongoDB 연결 실패: {e}")
            self.mongo_client = None
            self.mongo_stats = None
    
    def _register_routes(self):
        """API 라우트 등록"""
        
        @self.app.route('/')
        def dashboard():
            """메인 대시보드 페이지"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """시뮬레이터 상태 조회"""
            try:
                status_info = {
                    'status': self.last_status,
                    'is_running': self.is_running,
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                    'error_message': self.error_message,
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(status_info), 200
            except Exception as e:
                logging.error(f"상태 조회 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/start', methods=['POST'])
        def start_simulator():
            """시뮬레이터 시작"""
            try:
                if self.is_running:
                    return jsonify({'message': '시뮬레이터가 이미 실행 중입니다.', 'status': 'running'}), 400
                
                # 요청 데이터 파싱
                data = request.get_json() or {}
                seed = data.get('seed')
                strict_mode = data.get('strict_mode', False)
                normalized_mode = data.get('normalized_mode', False)
                interval = data.get('interval', 10)
                
                # 시뮬레이터 시작
                self._start_simulator_thread(seed, strict_mode, normalized_mode, interval)
                
                response = {
                    'message': '시뮬레이터가 시작되었습니다.',
                    'status': 'started',
                    'config': {
                        'seed': seed,
                        'strict_mode': strict_mode,
                        'normalized_mode': normalized_mode,
                        'interval': interval
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"시뮬레이터 시작: {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"시뮬레이터 시작 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_simulator():
            """시뮬레이터 정지"""
            try:
                if not self.is_running:
                    return jsonify({'message': '시뮬레이터가 실행 중이 아닙니다.', 'status': 'stopped'}), 400
                
                self._stop_simulator_thread()
                
                response = {
                    'message': '시뮬레이터가 정지되었습니다.',
                    'status': 'stopped',
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"시뮬레이터 정지: {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"시뮬레이터 정지 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/restart', methods=['POST'])
        def restart_simulator():
            """시뮬레이터 재시작"""
            try:
                # 현재 설정 저장
                current_config = {}
                if self.simulator:
                    current_config = {
                        'seed': self.simulator.config['simulation'].get('random_seed'),
                        'strict_mode': self.simulator.config['simulation'].get('strict_mode', False),
                        'normalized_mode': self.simulator.config['simulation'].get('normalized_storage', False),
                        'interval': self.simulator.config['scheduling'].get('mission_interval_minutes', 10)
                    }
                
                # 정지 후 시작
                if self.is_running:
                    self._stop_simulator_thread()
                    time.sleep(2)  # 정지 대기
                
                # 저장된 설정으로 재시작
                self._start_simulator_thread(
                    current_config.get('seed'),
                    current_config.get('strict_mode', False),
                    current_config.get('normalized_mode', False),
                    current_config.get('interval', 10)
                )
                
                response = {
                    'message': '시뮬레이터가 재시작되었습니다.',
                    'status': 'restarted',
                    'config': current_config,
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"시뮬레이터 재시작: {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"시뮬레이터 재시작 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/test', methods=['POST'])
        def test_simulator():
            """시뮬레이터 테스트 실행 (1회)"""
            try:
                # 요청 데이터 파싱
                data = request.get_json() or {}
                seed = data.get('seed')
                strict_mode = data.get('strict_mode', False)
                normalized_mode = data.get('normalized_mode', False)
                
                # 테스트 실행
                result = self._run_test(seed, strict_mode, normalized_mode)
                
                response = {
                    'message': '테스트가 완료되었습니다.',
                    'status': 'test_completed',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"테스트 완료: {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"테스트 실행 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """현재 설정 조회"""
            try:
                if not self.simulator:
                    return jsonify({'error': '시뮬레이터가 초기화되지 않았습니다.'}), 400
                
                config = {
                    'simulation': self.simulator.config['simulation'],
                    'scheduling': self.simulator.config['scheduling'],
                    'database': self.simulator.config['database']
                }
                
                return jsonify(config), 200
                
            except Exception as e:
                logging.error(f"설정 조회 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            try:
                # MongoDB 연결 확인
                if self.simulator and self.simulator.client:
                    self.simulator.client.admin.command('ping')
                    db_status = 'connected'
                else:
                    db_status = 'disconnected'
                
                health_info = {
                    'status': 'healthy',
                    'database': db_status,
                    'simulator_running': self.is_running,
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(health_info), 200
                
            except Exception as e:
                logging.error(f"헬스 체크 오류: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_real_time_stats():
            """실시간 MongoDB 통계 조회"""
            try:
                if not self.mongo_stats:
                    return jsonify({
                        'error': 'MongoDB 연결이 없습니다',
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
                # 실시간 통계 조회
                stats = self.mongo_stats.get_real_time_stats()
                
                # 추가 정보
                stats['api_server_status'] = 'running'
                stats['simulator_running'] = self.is_running
                
                return jsonify(stats), 200
                
            except Exception as e:
                logging.error(f"통계 조회 API 오류: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/mongodb/health', methods=['GET'])
        def mongodb_health_check():
            """MongoDB 연결 상태 확인"""
            try:
                if not self.mongo_stats:
                    return jsonify({
                        'status': 'unavailable',
                        'error': 'MongoDB 연결이 설정되지 않았습니다',
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
                # MongoDB 상태 확인
                health_status = self.mongo_stats.get_health_status()
                
                return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 500
                
            except Exception as e:
                logging.error(f"MongoDB 헬스 체크 오류: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/stats/clear-cache', methods=['POST'])
        def clear_stats_cache():
            """통계 캐시 강제 초기화"""
            try:
                if not self.mongo_stats:
                    return jsonify({
                        'error': 'MongoDB 연결이 없습니다',
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
                self.mongo_stats.clear_cache()
                
                return jsonify({
                    'message': '통계 캐시가 초기화되었습니다',
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logging.error(f"캐시 초기화 오류: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # === 개별 로봇 제어 엔드포인트 ===
        
        @self.app.route('/api/robots', methods=['GET'])
        def get_all_robots():
            """모든 로봇 상태 조회"""
            try:
                result = self.robot_manager.get_all_robots_status()
                return jsonify(result), 200
            except Exception as e:
                logging.error(f"모든 로봇 상태 조회 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/<robot_id>', methods=['GET'])
        def get_robot_status(robot_id):
            """개별 로봇 상태 조회"""
            try:
                result = self.robot_manager.get_robot_status(robot_id)
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"로봇 {robot_id} 상태 조회 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/<robot_id>/start', methods=['POST'])
        def start_robot(robot_id):
            """개별 로봇 시작"""
            try:
                result = self.robot_manager.start_robot(robot_id)
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"로봇 {robot_id} 시작 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/<robot_id>/stop', methods=['POST'])
        def stop_robot(robot_id):
            """개별 로봇 정지"""
            try:
                result = self.robot_manager.stop_robot(robot_id)
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"로봇 {robot_id} 정지 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/<robot_id>/reset', methods=['POST'])
        def reset_robot(robot_id):
            """개별 로봇 리셋"""
            try:
                result = self.robot_manager.reset_robot(robot_id)
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"로봇 {robot_id} 리셋 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/start-all', methods=['POST'])
        def start_all_robots():
            """모든 로봇 시작"""
            try:
                result = self.robot_manager.start_all_robots()
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"전체 로봇 시작 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/stop-all', methods=['POST'])
        def stop_all_robots():
            """모든 로봇 정지"""
            try:
                result = self.robot_manager.stop_all_robots()
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"전체 로봇 정지 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/robots/reset-all', methods=['POST'])
        def reset_all_robots():
            """모든 로봇 리셋"""
            try:
                result = self.robot_manager.reset_all_robots()
                return jsonify(result), 200 if result['success'] else 400
            except Exception as e:
                logging.error(f"전체 로봇 리셋 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        # === 운영 통계 엔드포인트 ===
        
        @self.app.route('/api/stats/operational', methods=['GET'])
        def get_operational_stats():
            """운영 중심 통계"""
            try:
                result = self.robot_manager.get_operational_stats()
                return jsonify(result), 200
            except Exception as e:
                logging.error(f"운영 통계 조회 오류: {e}")
                return jsonify({'error': str(e)}), 500
        
        # 브라우저용 GET 엔드포인트 추가
        @self.app.route('/api/start-get', methods=['GET'])
        def start_simulator_get():
            """브라우저용 시뮬레이터 시작 (GET)"""
            try:
                if self.is_running:
                    return jsonify({'message': '시뮬레이터가 이미 실행 중입니다.', 'status': 'running'}), 400
                
                # 기본 설정으로 시작
                self._start_simulator_thread(seed=12345, strict_mode=False, normalized_mode=False, interval=10)
                
                response = {
                    'message': '시뮬레이터가 시작되었습니다.',
                    'status': 'started',
                    'config': {
                        'seed': 12345,
                        'strict_mode': False,
                        'normalized_mode': False,
                        'interval': 10
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"시뮬레이터 시작 (GET): {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"시뮬레이터 시작 오류 (GET): {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stop-get', methods=['GET'])
        def stop_simulator_get():
            """브라우저용 시뮬레이터 정지 (GET)"""
            try:
                if not self.is_running:
                    return jsonify({'message': '시뮬레이터가 실행 중이 아닙니다.', 'status': 'stopped'}), 400
                
                self._stop_simulator_thread()
                
                response = {
                    'message': '시뮬레이터가 정지되었습니다.',
                    'status': 'stopped',
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                logging.info(f"시뮬레이터 정지 (GET): {response}")
                return jsonify(response), 200
                
            except Exception as e:
                self.error_message = str(e)
                logging.error(f"시뮬레이터 정지 오류 (GET): {e}")
                return jsonify({'error': str(e)}), 500
    
    def _start_simulator_thread(self, seed=None, strict_mode=False, normalized_mode=False, interval=10):
        """시뮬레이터를 별도 스레드에서 시작"""
        try:
            # 시뮬레이터 초기화
            self.simulator = RobotDataSimulator(self.config_file)
            
            # 설정 적용
            if seed is not None:
                self.simulator.config['simulation']['random_seed'] = seed
            self.simulator.config['simulation']['strict_mode'] = strict_mode
            self.simulator.config['simulation']['normalized_storage'] = normalized_mode
            self.simulator.config['scheduling']['mission_interval_minutes'] = interval
            
            # 시뮬레이터 스레드 시작
            self.simulator_thread = threading.Thread(target=self._run_simulator)
            self.simulator_thread.daemon = True
            self.simulator_thread.start()
            
            self.is_running = True
            self.start_time = datetime.now()
            self.last_status = "running"
            self.error_message = None
            
            logging.info(f"시뮬레이터 스레드 시작됨: seed={seed}, strict={strict_mode}, normalized={normalized_mode}, interval={interval}")
            
        except Exception as e:
            self.error_message = str(e)
            self.last_status = "error"
            logging.error(f"시뮬레이터 시작 실패: {e}")
            raise
    
    def _stop_simulator_thread(self):
        """시뮬레이터 스레드 정지"""
        try:
            if self.simulator:
                # 시뮬레이터 정지 신호
                self.simulator.stop_requested = True
                
                # 스레드 종료 대기
                if self.simulator_thread and self.simulator_thread.is_alive():
                    self.simulator_thread.join(timeout=10)
                
                # MongoDB 연결 종료
                if self.simulator.client:
                    self.simulator.client.close()
                
                self.simulator = None
                self.simulator_thread = None
            
            self.is_running = False
            self.last_status = "stopped"
            self.error_message = None
            
            logging.info("시뮬레이터 스레드 정지됨")
            
        except Exception as e:
            self.error_message = str(e)
            self.last_status = "error"
            logging.error(f"시뮬레이터 정지 실패: {e}")
            raise
    
    def _run_simulator(self):
        """시뮬레이터 실행 (스레드에서 호출)"""
        try:
            logging.info("시뮬레이터 실행 시작")
            self.simulator.run_simulator()
        except Exception as e:
            self.error_message = str(e)
            self.last_status = "error"
            self.is_running = False
            logging.error(f"시뮬레이터 실행 오류: {e}")
    
    def _run_test(self, seed=None, strict_mode=False, normalized_mode=False):
        """테스트 실행 (1회)"""
        try:
            # 임시 시뮬레이터 생성
            test_simulator = RobotDataSimulator(self.config_file)
            
            # 설정 적용
            if seed is not None:
                test_simulator.config['simulation']['random_seed'] = seed
            test_simulator.config['simulation']['strict_mode'] = strict_mode
            test_simulator.config['simulation']['normalized_storage'] = normalized_mode
            
            # 테스트 실행
            test_simulator.generate_and_save_missions()
            stats = test_simulator.get_statistics()
            
            # 연결 종료
            test_simulator.client.close()
            
            return {
                'missions_created': 30,
                'statistics': stats,
                'config_used': {
                    'seed': seed,
                    'strict_mode': strict_mode,
                    'normalized_mode': normalized_mode
                }
            }
            
        except Exception as e:
            logging.error(f"테스트 실행 오류: {e}")
            raise
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """API 서버 실행"""
        logging.info(f"API 서버 시작: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='로봇 데이터 시뮬레이터 API 서버')
    parser.add_argument('--config', default='simulator_config.json', help='설정 파일 경로')
    parser.add_argument('--host', default='0.0.0.0', help='서버 호스트')
    parser.add_argument('--port', type=int, default=5000, help='서버 포트')
    parser.add_argument('--debug', action='store_true', help='디버그 모드')
    
    args = parser.parse_args()
    
    try:
        # API 서버 생성 및 실행
        api_server = SimulatorAPI(args.config)
        api_server.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logging.error(f"API 서버 실행 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
