#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 설정 관리자 - MongoDB 설정을 웹에서 관리하는 모듈
"""

import json
import logging
from pymongo import MongoClient
from datetime import datetime
from flask import Blueprint, request, jsonify

class ConfigManager:
    def __init__(self, config_file="simulator_config.json"):
        self.config_file = config_file
        
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"설정 파일 로드 실패: {e}")
            return {}
    
    def save_config(self, config):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"설정 파일 저장 실패: {e}")
            return False
    
    def get_mongodb_config(self):
        """현재 MongoDB 설정 조회"""
        config = self.load_config()
        db_config = config.get('database', {})
        return {
            "connection_string": db_config.get('connection_string', 'mongodb://localhost:27017/'),
            "database_name": db_config.get('database_name', 'robot_data'),
            "collection_name": db_config.get('collection_name', 'robot_missions')
        }
    
    def update_mongodb_config(self, connection_string=None, database_name=None, collection_name=None):
        """MongoDB 설정 업데이트"""
        try:
            config = self.load_config()
            
            if 'database' not in config:
                config['database'] = {}
            
            if connection_string:
                config['database']['connection_string'] = connection_string
            if database_name:
                config['database']['database_name'] = database_name
            if collection_name:
                config['database']['collection_name'] = collection_name
            
            return self.save_config(config)
        except Exception as e:
            logging.error(f"MongoDB 설정 업데이트 실패: {e}")
            return False
    
    def test_mongodb_connection(self, connection_string, database_name):
        """MongoDB 연결 테스트"""
        try:
            # 테스트 연결 (5초 타임아웃)
            test_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            test_db = test_client[database_name]
            
            # 연결 테스트
            test_db.client.admin.command('ping')
            
            # 컬렉션 목록 가져오기
            collections = test_db.list_collection_names()
            
            # 서버 정보 가져오기
            server_info = test_db.client.server_info()
            
            test_client.close()
            
            return {
                "success": True,
                "message": "✅ 연결 성공!",
                "database_name": database_name,
                "collections": collections,
                "server_version": server_info.get('version', 'Unknown'),
                "connection_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ 연결 실패: {str(e)}",
                "error": str(e)
            }

def create_config_blueprint(config_manager):
    """설정 관리 Blueprint 생성"""
    bp = Blueprint('config', __name__)
    
    @bp.route('/api/mongodb/config', methods=['GET'])
    def get_mongodb_config():
        """현재 MongoDB 설정 조회"""
        try:
            config = config_manager.get_mongodb_config()
            return jsonify({
                "success": True,
                "config": config
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @bp.route('/api/mongodb/config', methods=['POST'])
    def update_mongodb_config():
        """MongoDB 설정 업데이트"""
        try:
            data = request.get_json()
            
            connection_string = data.get('connection_string')
            database_name = data.get('database_name')
            collection_name = data.get('collection_name')
            
            success = config_manager.update_mongodb_config(
                connection_string=connection_string,
                database_name=database_name,
                collection_name=collection_name
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "✅ 설정이 성공적으로 업데이트되었습니다!"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "❌ 설정 업데이트에 실패했습니다"
                })
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            })
    
    @bp.route('/api/mongodb/test', methods=['POST'])
    def test_mongodb_connection():
        """MongoDB 연결 테스트"""
        try:
            data = request.get_json()
            connection_string = data.get('connection_string', 'mongodb://localhost:27017/')
            database_name = data.get('database_name', 'robot_data')
            
            result = config_manager.test_mongodb_connection(connection_string, database_name)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"❌ 테스트 실패: {str(e)}",
                "error": str(e)
            })
    
    return bp
