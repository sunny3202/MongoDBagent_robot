#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드가 호출하는 API 응답 형식 확인
"""

import requests
import json

def test_dashboard_apis():
    """대시보드가 사용하는 모든 API 엔드포인트 테스트"""
    base_url = "http://localhost:8080"
    
    print("=== 대시보드 API 응답 형식 확인 ===")
    
    # 1. /api/stats/operational - 운영 통계
    print("\n1. /api/stats/operational")
    try:
        response = requests.get(f"{base_url}/api/stats/operational")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답 구조:")
            print(f"     - success 필드: {data.get('success')}")
            print(f"     - daily_stats: {data.get('daily_stats')}")
            print(f"     - robot_status: {data.get('robot_status')}")  
            print(f"     - battery_stats: {data.get('battery_stats')}")
            print(f"   전체 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   오류: {response.text}")
    except Exception as e:
        print(f"   예외: {e}")
    
    # 2. /api/robots - 로봇 상태
    print("\n2. /api/robots")
    try:
        response = requests.get(f"{base_url}/api/robots")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답 구조:")
            print(f"     - success 필드: {data.get('success')}")
            print(f"     - robots 필드: {type(data.get('robots'))}")
            if data.get('robots'):
                print(f"     - robots 길이: {len(data.get('robots', []))}")
                if len(data.get('robots', [])) > 0:
                    print(f"     - 첫 번째 로봇: {data['robots'][0]}")
            print(f"   전체 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   오류: {response.text}")
    except Exception as e:
        print(f"   예외: {e}")
    
    # 3. /api/stats - 기본 통계
    print("\n3. /api/stats")
    try:
        response = requests.get(f"{base_url}/api/stats")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답 구조:")
            print(f"     - total_missions: {data.get('total_missions')}")
            print(f"     - total_data_points: {data.get('total_data_points')}")
            print(f"     - unique_robots: {data.get('unique_robots')}")
            print(f"     - battery_analysis: {data.get('battery_analysis')}")
            print(f"     - error: {data.get('error')}")
        else:
            print(f"   오류: {response.text}")
    except Exception as e:
        print(f"   예외: {e}")

if __name__ == "__main__":
    test_dashboard_apis()

