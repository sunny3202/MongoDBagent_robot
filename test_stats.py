#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 통계 테스트 스크립트
"""

from pymongo import MongoClient
import json

def test_basic_stats():
    """기본 MongoDB 통계 테스트"""
    try:
        # MongoDB 연결
        client = MongoClient('mongodb://localhost:27017/')
        db = client['robot_data']
        collection = db['robot_missions']
        
        print("=== MongoDB 기본 정보 ===")
        print(f"총 미션 수 (count_documents): {collection.count_documents({})}")
        print(f"컬렉션 목록: {db.list_collection_names()}")
        
        # 가장 간단한 aggregation 테스트
        print("\n=== 간단한 Aggregation 테스트 ===")
        simple_result = list(collection.aggregate([
            {"$count": "total"}
        ]))
        print(f"$count 결과: {simple_result}")
        
        # $facet 테스트
        print("\n=== $facet Aggregation 테스트 ===")
        facet_result = list(collection.aggregate([
            {
                "$facet": {
                    "total_missions": [{"$count": "count"}],
                    "unique_robots": [
                        {"$group": {"_id": "$robot_id"}},
                        {"$count": "count"}
                    ]
                }
            }
        ]))
        print(f"$facet 결과: {json.dumps(facet_result[0], indent=2, default=str)}")
        
        # 배터리 통계 테스트 (타입 확인)
        print("\n=== 배터리 필드 타입 확인 ===")
        sample = collection.find_one({}, {"mission_start_battery_state": 1, "mission_end_battery_state": 1})
        print(f"샘플 배터리 데이터: {sample}")
        print(f"시작 배터리 타입: {type(sample.get('mission_start_battery_state'))}")
        print(f"종료 배터리 타입: {type(sample.get('mission_end_battery_state'))}")
        
        # 간단한 배터리 평균 테스트
        print("\n=== 간단한 배터리 통계 테스트 ===")
        battery_result = list(collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "avg_start": {"$avg": "$mission_start_battery_state"},
                    "avg_end": {"$avg": "$mission_end_battery_state"},
                    "count": {"$sum": 1}
                }
            }
        ]))
        print(f"배터리 통계 결과: {battery_result}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_stats()

