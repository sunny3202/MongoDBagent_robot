#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 서버 캐시 클리어 및 통계 테스트
"""

import requests
import json

def clear_and_test():
    """캐시 클리어 후 통계 테스트"""
    base_url = "http://localhost:8080"
    
    print("=== API 서버 캐시 클리어 및 테스트 ===")
    
    # 1. 캐시 클리어
    try:
        clear_response = requests.post(f"{base_url}/api/stats/clear-cache")
        print(f"캐시 클리어 결과: {clear_response.status_code}")
        if clear_response.status_code == 200:
            print(f"  응답: {clear_response.json()}")
    except Exception as e:
        print(f"캐시 클리어 실패: {e}")
    
    # 2. MongoDB 헬스 체크
    try:
        health_response = requests.get(f"{base_url}/api/mongodb/health")
        print(f"\nMongoDB 헬스 체크: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"  상태: {health_data.get('status')}")
            print(f"  데이터베이스: {health_data.get('database_name')}")
            print(f"  컬렉션: {health_data.get('collections')}")
            print(f"  데이터 존재: {health_data.get('has_data')}")
    except Exception as e:
        print(f"헬스 체크 실패: {e}")
    
    # 3. 통계 조회 (캐시 클리어 후)
    try:
        stats_response = requests.get(f"{base_url}/api/stats")
        print(f"\n통계 조회: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"  총 미션: {stats_data.get('total_missions')}")
            print(f"  총 데이터 포인트: {stats_data.get('total_data_points')}")
            print(f"  고유 로봇: {stats_data.get('unique_robots')}")
            print(f"  오류 여부: {stats_data.get('error')}")
            print(f"  데이터 품질: {stats_data.get('data_quality')}")
            
            if stats_data.get('battery_analysis'):
                battery = stats_data['battery_analysis']
                print(f"  배터리: 시작 {battery.get('avg_start_battery')}%, 종료 {battery.get('avg_end_battery')}%")
        else:
            print(f"  오류 응답: {stats_response.text}")
    except Exception as e:
        print(f"통계 조회 실패: {e}")
    
    # 4. 운영 통계 조회
    try:
        operational_response = requests.get(f"{base_url}/api/stats/operational")
        print(f"\n운영 통계 조회: {operational_response.status_code}")
        if operational_response.status_code == 200:
            op_data = operational_response.json()
            print(f"  운영 통계: {json.dumps(op_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"운영 통계 조회 실패: {e}")

if __name__ == "__main__":
    clear_and_test()

