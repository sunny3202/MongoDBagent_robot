#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 서버
"""

from flask import Flask, jsonify
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "테스트 서버가 실행 중입니다!", "status": "running"})

@app.route('/api/status')
def status():
    return jsonify({
        "status": "stopped",
        "is_running": False,
        "message": "테스트 서버 정상 작동"
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "message": "서버 정상"
    })

if __name__ == "__main__":
    print("🚀 테스트 서버 시작 중...")
    app.run(host='0.0.0.0', port=8080, debug=True)
