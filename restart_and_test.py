#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 서버 재시작 후 테스트
"""

import requests
import json
import time

def test_after_restart():
    """API 서버 재시작 후 테스트"""
    base_url = "http://localhost:8080"
    
    print("=== API 서버 재시작 후 테스트 ===")
    
    # 잠깐 대기 (서버 완전 시작 대기)
    print("서버 완전 시작 대기 중...")
    time.sleep(3)
    
    # 1. 헬스 체크
    try:
        health_response = requests.get(f"{base_url}/api/mongodb/health")
        print(f"1. MongoDB 헬스: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   ✅ MongoDB 정상: {health_response.json()['status']}")
    except Exception as e:
        print(f"   ❌ 헬스 체크 실패: {e}")
        return
    
    # 2. 캐시 클리어 (혹시 모르니)
    try:
        clear_response = requests.post(f"{base_url}/api/stats/clear-cache")
        print(f"2. 캐시 클리어: {clear_response.status_code}")
    except Exception as e:
        print(f"   ❌ 캐시 클리어 실패: {e}")
    
    # 3. 운영 통계 API 테스트 (핵심!)
    try:
        operational_response = requests.get(f"{base_url}/api/stats/operational")
        print(f"3. 운영 통계 API: {operational_response.status_code}")
        
        if operational_response.status_code == 200:
            data = operational_response.json()
            
            # 🎯 대시보드가 확인하는 필드들
            success_field = data.get('success')
            robot_status = data.get('robot_status')
            battery_stats = data.get('battery_stats')
            daily_stats = data.get('daily_stats')
            
            print(f"   📋 API 응답 분석:")
            print(f"     - success 필드: {success_field} ({'✅ 있음' if success_field is not None else '❌ 없음'})")
            print(f"     - robot_status: {'✅ 있음' if robot_status else '❌ 없음'}")
            print(f"     - battery_stats: {'✅ 있음' if battery_stats else '❌ 없음'}")
            print(f"     - daily_stats: {'✅ 있음' if daily_stats else '❌ 없음'}")
            
            if success_field and robot_status and battery_stats:
                print(f"   🎉 대시보드 호환 형식 완료!")
                print(f"     - 작업중 로봇: {robot_status.get('working', 0)}대")
                print(f"     - 평균 배터리: {battery_stats.get('average', 0)}%")
                print(f"     - 완료 미션: {daily_stats.get('completed_missions', 0)}개")
            else:
                print(f"   ⚠️ 대시보드 호환 형식 미완성")
                print(f"   전체 응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ❌ API 호출 실패: {operational_response.text}")
            
    except Exception as e:
        print(f"   ❌ 운영 통계 API 실패: {e}")

    # 4. 기본 통계 API 확인
    try:
        stats_response = requests.get(f"{base_url}/api/stats")
        print(f"4. 기본 통계 API: {stats_response.status_code}")
        if stats_response.status_code == 200:
            data = stats_response.json()
            print(f"   총 미션: {data.get('total_missions')}")
            print(f"   고유 로봇: {data.get('unique_robots')}")
            print(f"   오류 여부: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ 기본 통계 실패: {e}")

if __name__ == "__main__":
    test_after_restart()

