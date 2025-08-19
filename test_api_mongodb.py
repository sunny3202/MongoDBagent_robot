#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 서버의 MongoDB 연결 테스트
"""

import json
from mongodb_stats import MongoDBStatsInterface
from pymongo import MongoClient

def test_api_mongodb_connection():
    """API 서버와 동일한 방식으로 MongoDB 연결 테스트"""
    
    # 1. 설정 파일 로드 (API 서버와 동일)
    with open('simulator_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("=== 설정 정보 ===")
    print(f"Connection String: {config['database']['connection_string']}")
    print(f"Database Name: {config['database']['database_name']}")
    print(f"Collection Name: {config['database']['collection_name']}")
    
    # 2. MongoDB 클라이언트 생성 (API 서버와 동일)
    try:
        client = MongoClient(config['database']['connection_string'])
        db = client[config['database']['database_name']]
        
        print(f"\n=== MongoDB 연결 테스트 ===")
        print(f"서버 정보: {client.server_info()['version']}")
        print(f"컬렉션 목록: {db.list_collection_names()}")
        
        # 3. MongoDBStatsInterface 테스트 (API 서버와 동일)
        print(f"\n=== MongoDBStatsInterface 테스트 ===")
        stats_interface = MongoDBStatsInterface(db, config)
        
        # 실시간 통계 조회
        stats = stats_interface.get_real_time_stats()
        print(f"통계 조회 결과:")
        print(f"  총 미션: {stats.get('total_missions')}")
        print(f"  총 데이터 포인트: {stats.get('total_data_points')}")
        print(f"  고유 로봇: {stats.get('unique_robots')}")
        print(f"  오류 여부: {stats.get('error')}")
        print(f"  데이터 품질: {stats.get('data_quality')}")
        
        if stats.get('battery_analysis'):
            battery = stats['battery_analysis']
            print(f"  배터리 - 시작: {battery.get('avg_start_battery')}%, 종료: {battery.get('avg_end_battery')}%")
        
        if stats.get('location_analysis'):
            locations = stats['location_analysis']
            print(f"  위치 - 총 위치: {locations.get('total_locations')}")
            print(f"  가장 바쁜 위치: {locations.get('busiest_locations', [])[:3]}")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_mongodb_connection()

