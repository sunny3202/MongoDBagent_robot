#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 API 서버 테스트 클라이언트
모니터링 앱에서 사용할 수 있는 API 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

class SimulatorAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        """API 클라이언트 초기화"""
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_status(self):
        """시뮬레이터 상태 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"상태 조회 실패: {e}")
            return None
    
    def start_simulator(self, seed=None, strict_mode=False, normalized_mode=False, interval=10):
        """시뮬레이터 시작"""
        try:
            data = {
                'seed': seed,
                'strict_mode': strict_mode,
                'normalized_mode': normalized_mode,
                'interval': interval
            }
            
            response = self.session.post(f"{self.base_url}/api/start", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"시뮬레이터 시작 실패: {e}")
            return None
    
    def stop_simulator(self):
        """시뮬레이터 정지"""
        try:
            response = self.session.post(f"{self.base_url}/api/stop")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"시뮬레이터 정지 실패: {e}")
            return None
    
    def restart_simulator(self):
        """시뮬레이터 재시작"""
        try:
            response = self.session.post(f"{self.base_url}/api/restart")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"시뮬레이터 재시작 실패: {e}")
            return None
    
    def test_simulator(self, seed=None, strict_mode=False, normalized_mode=False):
        """시뮬레이터 테스트"""
        try:
            data = {
                'seed': seed,
                'strict_mode': strict_mode,
                'normalized_mode': normalized_mode
            }
            
            response = self.session.post(f"{self.base_url}/api/test", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"시뮬레이터 테스트 실패: {e}")
            return None
    
    def get_config(self):
        """설정 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/config")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"설정 조회 실패: {e}")
            return None
    
    def health_check(self):
        """헬스 체크"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"헬스 체크 실패: {e}")
            return None

def print_status(status):
    """상태 정보 출력"""
    if not status:
        print("❌ 상태 정보를 가져올 수 없습니다.")
        return
    
    print(f"\n📊 시뮬레이터 상태:")
    print(f"   상태: {status.get('status', 'unknown')}")
    print(f"   실행 중: {'✅' if status.get('is_running') else '❌'}")
    
    if status.get('start_time'):
        start_time = datetime.fromisoformat(status['start_time'].replace('Z', '+00:00'))
        uptime = status.get('uptime_seconds', 0)
        print(f"   시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   실행 시간: {uptime:.0f}초")
    
    if status.get('error_message'):
        print(f"   오류: {status['error_message']}")
    
    print(f"   타임스탬프: {status.get('timestamp', 'unknown')}")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='시뮬레이터 API 테스트 클라이언트')
    parser.add_argument('--url', default='http://localhost:5000', help='API 서버 URL')
    parser.add_argument('--action', choices=['status', 'start', 'stop', 'restart', 'test', 'config', 'health'], 
                       default='status', help='실행할 액션')
    parser.add_argument('--seed', type=int, help='랜덤 시드')
    parser.add_argument('--strict', action='store_true', help='엄격 모드')
    parser.add_argument('--normalized', action='store_true', help='정규화 모드')
    parser.add_argument('--interval', type=int, default=10, help='미션 간격 (분)')
    parser.add_argument('--monitor', action='store_true', help='상태 모니터링 (5초마다)')
    
    args = parser.parse_args()
    
    # API 클라이언트 생성
    client = SimulatorAPIClient(args.url)
    
    try:
        if args.action == 'status':
            status = client.get_status()
            print_status(status)
            
            if args.monitor:
                print("\n🔄 상태 모니터링 시작 (5초마다, Ctrl+C로 종료)")
                try:
                    while True:
                        time.sleep(5)
                        status = client.get_status()
                        print_status(status)
                except KeyboardInterrupt:
                    print("\n⏹️ 모니터링 종료")
        
        elif args.action == 'start':
            print(f"🚀 시뮬레이터 시작 중...")
            result = client.start_simulator(
                seed=args.seed,
                strict_mode=args.strict,
                normalized_mode=args.normalized,
                interval=args.interval
            )
            if result:
                print(f"✅ {result.get('message', '시작됨')}")
                print(f"   설정: {result.get('config', {})}")
            else:
                print("❌ 시작 실패")
        
        elif args.action == 'stop':
            print(f"🛑 시뮬레이터 정지 중...")
            result = client.stop_simulator()
            if result:
                print(f"✅ {result.get('message', '정지됨')}")
                if result.get('uptime_seconds'):
                    print(f"   실행 시간: {result['uptime_seconds']:.0f}초")
            else:
                print("❌ 정지 실패")
        
        elif args.action == 'restart':
            print(f"🔄 시뮬레이터 재시작 중...")
            result = client.restart_simulator()
            if result:
                print(f"✅ {result.get('message', '재시작됨')}")
                print(f"   설정: {result.get('config', {})}")
            else:
                print("❌ 재시작 실패")
        
        elif args.action == 'test':
            print(f"🧪 시뮬레이터 테스트 실행 중...")
            result = client.test_simulator(
                seed=args.seed,
                strict_mode=args.strict,
                normalized_mode=args.normalized
            )
            if result:
                print(f"✅ {result.get('message', '테스트 완료')}")
                test_result = result.get('result', {})
                print(f"   생성된 미션: {test_result.get('missions_created', 0)}개")
                print(f"   설정: {test_result.get('config_used', {})}")
            else:
                print("❌ 테스트 실패")
        
        elif args.action == 'config':
            print(f"⚙️ 설정 조회 중...")
            config = client.get_config()
            if config:
                print("✅ 설정 정보:")
                print(json.dumps(config, indent=2, ensure_ascii=False))
            else:
                print("❌ 설정 조회 실패")
        
        elif args.action == 'health':
            print(f"🏥 헬스 체크 중...")
            health = client.health_check()
            if health:
                print(f"✅ 상태: {health.get('status', 'unknown')}")
                print(f"   데이터베이스: {health.get('database', 'unknown')}")
                print(f"   시뮬레이터 실행: {'✅' if health.get('simulator_running') else '❌'}")
            else:
                print("❌ 헬스 체크 실패")
    
    except KeyboardInterrupt:
        print("\n⏹️ 작업 중단됨")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
