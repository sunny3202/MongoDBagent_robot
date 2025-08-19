# 🤖 로봇 데이터 MongoDB 시뮬레이터 v2.0

실시간 로봇 센서 데이터를 생성하고 MongoDB에 저장하는 고성능 시뮬레이터입니다.

## 📋 목차

- [아키텍처](#-아키텍처)
- [핵심 기능](#-핵심-기능)
- [설치](#-설치)
- [사용법](#-사용법)
- [API 서버](#-api-서버)
- [실시간 모니터링](#-실시간-모니터링)
- [MongoDB 인터페이스](#-mongodb-인터페이스)
- [설정](#-설정)
- [모니터링 앱 연동](#-모니터링-앱-연동)

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   웹 대시보드    │◄──►│   API 서버      │◄──►│  MongoDB        │
│                 │    │                 │    │                 │
│ - 실시간 통계   │    │ - 상태 관리     │    │ - robot_missions│
│ - 프로세스 플로우│    │ - 통계 조회     │    │ - 실시간 집계   │
│ - 제어 인터페이스│    │ - MongoDB 연동  │    │ - 성능 최적화   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 로봇 시뮬레이터  │
                    │                 │
                    │ - 데이터 생성   │
                    │ - 프로세스 추적 │
                    │ - 상세 응답 처리│
                    └─────────────────┘
```

## 🚀 핵심 기능

### ⭐ v2.0 신규 기능
- **🔄 실시간 프로세스 플로우**: 7단계 프로세스 시각화 (초기화→설정→MongoDB→스케줄링→미션생성→센서데이터→저장)
- **📊 실시간 MongoDB 통계**: 실제 DB 데이터 기반 통계 (가짜 시뮬레이션 제거)
- **💾 MongoDB 응답 처리**: 상세한 저장 결과 및 성능 지표 제공
- **🎯 프로세스 추적**: 실제 진행 상황 모니터링 (처리된 로봇 수, 생성된 데이터 포인트 등)
- **⚡ 성능 최적화**: 집계 쿼리 캐싱 및 병렬 처리

### 🔧 기존 기능
- **실시간 데이터 생성**: 30개 로봇의 센서 데이터를 주기적으로 생성
- **MongoDB 저장**: 단일 컬렉션 또는 정규화된 구조로 데이터 저장
- **다양한 모드**: 엄격 모드, 정규화 모드, 디버그 모드 지원
- **REST API**: 모니터링 앱과 연동 가능한 HTTP API 제공
- **자동 인덱스 관리**: 성능 최적화를 위한 인덱스 자동 생성
- **로깅 시스템**: 상세한 로그 기록 및 로테이션

## 📦 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. MongoDB 설정

MongoDB가 실행 중인지 확인하세요:

```bash
# MongoDB 상태 확인
mongosh --eval "db.runCommand('ping')"
```

## 🎮 사용법

### 기본 시뮬레이터 실행

```bash
# 기본 실행
python robot_data_simulator.py

# 엄격 모드
python robot_data_simulator.py --strict

# 정규화 모드
python robot_data_simulator.py --normalized

# 디버그 모드
python robot_data_simulator.py --debug

# 랜덤 시드 설정
python robot_data_simulator.py --seed 12345
```

### API 서버 실행

```bash
# 기본 API 서버 실행 (포트 5000)
python api_server.py

# 다른 포트로 실행
python api_server.py --port 8080

# 디버그 모드
python api_server.py --debug
```

## 🌐 API 서버

### 웹 대시보드

브라우저에서 `http://localhost:8080`으로 접속하여 실시간 모니터링 대시보드를 사용할 수 있습니다.

#### 🎮 대시보드 기능
- **시뮬레이터 제어**: 시작/정지/재시작/테스트 버튼
- **실시간 프로세스 플로우**: 7단계 진행 상황 시각화
- **실시간 통계**: MongoDB에서 직접 가져온 실제 데이터
- **상세 진행 상황**: 처리된 로봇 수, 생성된 데이터 포인트, 다음 실행까지 시간
- **실시간 로그**: 시뮬레이터 작업 로그 스트리밍

### API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/` | 웹 대시보드 |
| GET | `/api/status` | 시뮬레이터 상태 조회 |
| POST | `/api/start` | 시뮬레이터 시작 |
| POST | `/api/stop` | 시뮬레이터 정지 |
| POST | `/api/restart` | 시뮬레이터 재시작 |
| POST | `/api/test` | 테스트 실행 (1회) |
| GET | `/api/config` | 설정 조회 |
| GET | `/api/health` | 헬스 체크 |
| **GET** | **`/api/stats`** | **실시간 MongoDB 통계** |
| **GET** | **`/api/mongodb/health`** | **MongoDB 연결 상태** |
| GET | `/api/start-get` | 브라우저용 시작 (GET) |
| GET | `/api/stop-get` | 브라우저용 정지 (GET) |

### API 사용 예시

#### 시뮬레이터 시작
```bash
curl -X POST http://localhost:5000/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "seed": 12345,
    "strict_mode": false,
    "normalized_mode": false,
    "interval": 10
  }'
```

#### 상태 조회
```bash
curl http://localhost:5000/api/status
```

#### 시뮬레이터 정지
```bash
curl -X POST http://localhost:5000/api/stop
```

#### 실시간 통계 조회
```bash
curl http://localhost:8080/api/stats
```

**응답 예시:**
```json
{
  "total_missions": 1500,
  "total_data_points": 12000,
  "active_robots": 30,
  "recent_missions": 30,
  "avg_battery_start": 87.5,
  "avg_battery_end": 72.3,
  "last_update": "2025-01-15T10:30:00Z",
  "query_execution_time": 45.2
}
```

#### MongoDB 연결 상태 확인
```bash
curl http://localhost:8080/api/mongodb/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "collections": ["robot_missions", "robot_data_points"],
  "connection_time": "2025-01-15T10:30:00Z"
}
```

### API 클라이언트 사용

```bash
# 상태 조회
python test_api_client.py --action status

# 시뮬레이터 시작
python test_api_client.py --action start --seed 12345 --strict

# 상태 모니터링
python test_api_client.py --action status --monitor

# 테스트 실행
python test_api_client.py --action test --normalized
```

## 📊 실시간 모니터링

### 🔄 프로세스 플로우 단계

1. **🚀 시뮬레이터 초기화**: 설정 파일 로드, 랜덤 시드 설정
2. **⚙️ 설정 로드**: 데이터베이스 연결 정보, 시뮬레이션 파라미터
3. **🗄️ MongoDB 연결**: 데이터베이스 연결 및 인덱스 생성
4. **⏰ 스케줄링**: 10분 간격 미션 생성 스케줄 설정
5. **🤖 미션 생성**: 30개 로봇별 미션 데이터 생성
6. **📊 센서 데이터**: 각 로봇의 센서 데이터 포인트 생성
7. **💾 MongoDB 저장**: 생성된 데이터를 MongoDB에 저장

### 📈 실시간 통계 지표

- **총 미션 수**: MongoDB에 저장된 전체 미션 개수
- **총 데이터 포인트**: 모든 센서 데이터 포인트 개수
- **활성 로봇**: 데이터를 생성한 로봇 수
- **최근 미션**: 지난 1시간 내 생성된 미션 수
- **평균 배터리**: 시작/종료 배터리 상태 평균
- **쿼리 실행 시간**: 통계 조회 성능 지표

## 🗄️ MongoDB 인터페이스

### MongoDB 응답 처리 강화

```python
class MongoDBResponse:
    def __init__(self, success: bool, inserted_id=None, 
                 modified_count=0, error_message=None, 
                 execution_time=0.0):
        self.success = success
        self.inserted_id = inserted_id
        self.modified_count = modified_count
        self.error_message = error_message
        self.execution_time = execution_time
        self.timestamp = datetime.now()
```

### 실시간 통계 집계 쿼리

```javascript
// 병렬 집계 쿼리로 성능 최적화
db.robot_missions.aggregate([
  {
    "$facet": {
      "total_missions": [{"$count": "count"}],
      "total_data_points": [
        {"$unwind": "$data_points"},
        {"$count": "count"}
      ],
      "active_robots": [
        {"$group": {"_id": "$robot_id"}},
        {"$count": "count"}
      ],
      "recent_missions": [
        {"$match": {
          "mission_start_date": {
            "$gte": new Date(Date.now() - 3600000)  // 1시간 전
          }
        }},
        {"$count": "count"}
      ]
    }
  }
])
```

### 성능 최적화

- **캐싱**: 5초 간격 통계 캐싱으로 DB 부하 감소
- **인덱스**: 자동 복합 인덱스 생성으로 쿼리 성능 향상
- **병렬 처리**: `$facet` 집계 파이프라인으로 여러 통계 동시 계산

## ⚙️ 설정

### simulator_config.json

```json
{
  "database": {
    "connection_string": "mongodb://localhost:27017/",
    "database_name": "robot_data",
    "collection_name": "robot_missions"
  },
  "simulation": {
    "robot_count": 30,
    "mission_duration_min": 4,
    "mission_duration_max": 10,
    "time_grid_minutes": 10,
    "data_points_min": 5,
    "data_points_max": 10,
    "strict_mode": false,
    "normalized_storage": false,
    "random_seed": null
  },
  "battery": {
    "start_min": 70,
    "start_max": 100,
    "drain_min": 5,
    "drain_max": 20
  },
  "scheduling": {
    "mission_interval_minutes": 10
  },
  "locations": {
    "sites": ["H1", "H2", "H3", "K1", "K2", "P1", "P2", "P3", "P4"],
    "lines": ["1L", "2L", "3L", "4L", "5L", "6L", "7L", "8L", "9L", "10L", "11L", "12L", "13L", "14L", "15L", "16L", "17L", "18L", "19L"],
    "floors": ["1F", "B1F", "2F"],
    "area": "GCB"
  },
  "sensor_ranges": {
    "localization_score": [70, 100],
    "pos_x": [1000, 20000],
    "pos_y": [1000, 20000],
    "theta": [0, 360],
    "tilt_x": [-1.0, 1.0],
    "tilt_y": [-1.0, 1.0],
    "illuminance": [500, 1000],
    "noise": [40, 70],
    "temperature": [20, 30],
    "humidity": [30, 60],
    "NH3": [0, 5],
    "H2S": [0, 2],
    "VOCs": [0, 10],
    "F2": [0, 0.1],
    "HF": [0, 0.5]
  },
  "logging": {
    "level": "INFO",
    "file": "simulator.log",
    "max_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  }
}
```

## 📱 모니터링 앱 연동

### 1. API 서버 시작

```bash
python api_server.py --port 5000
```

### 2. 모니터링 앱에서 API 호출

#### JavaScript 예시
```javascript
// 시뮬레이터 시작
async function startSimulator() {
  const response = await fetch('http://localhost:8080/api/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      seed: 12345,
      strict_mode: false,
      normalized_mode: false,
      interval: 10
    })
  });
  
  const result = await response.json();
  console.log('시뮬레이터 시작:', result);
}

// 실시간 통계 모니터링
async function monitorRealTimeStats() {
  const response = await fetch('http://localhost:8080/api/stats');
  const stats = await response.json();
  
  console.log('실시간 통계:', stats);
  
  // 대시보드 업데이트
  document.getElementById('totalMissions').textContent = stats.total_missions;
  document.getElementById('totalDataPoints').textContent = stats.total_data_points;
  document.getElementById('activeRobots').textContent = stats.active_robots;
  
  // 5초마다 통계 업데이트
  setTimeout(monitorRealTimeStats, 5000);
}

// MongoDB 연결 상태 확인
async function checkMongoDBHealth() {
  const response = await fetch('http://localhost:8080/api/mongodb/health');
  const health = await response.json();
  
  if (health.status === 'healthy') {
    console.log('MongoDB 연결 정상:', health.collections);
  } else {
    console.error('MongoDB 연결 오류:', health.error);
  }
}

// 시뮬레이터 정지
async function stopSimulator() {
  const response = await fetch('http://localhost:8080/api/stop', {
    method: 'POST'
  });
  
  const result = await response.json();
  console.log('시뮬레이터 정지:', result);
}
```

#### Python 예시
```python
import requests
import time

# 시뮬레이터 시작
def start_simulator():
    response = requests.post('http://localhost:8080/api/start', json={
        'seed': 12345,
        'strict_mode': False,
        'normalized_mode': False,
        'interval': 10
    })
    return response.json()

# 실시간 통계 조회
def get_real_time_stats():
    response = requests.get('http://localhost:8080/api/stats')
    return response.json()

# MongoDB 연결 상태 확인
def check_mongodb_health():
    response = requests.get('http://localhost:8080/api/mongodb/health')
    return response.json()

# 상태 조회
def get_status():
    response = requests.get('http://localhost:8080/api/status')
    return response.json()

# 실시간 모니터링 루프
def monitor_simulator():
    while True:
        try:
            stats = get_real_time_stats()
            print(f"총 미션: {stats['total_missions']}, "
                  f"데이터 포인트: {stats['total_data_points']}, "
                  f"활성 로봇: {stats['active_robots']}")
            
            status = get_status()
            print(f"시뮬레이터 상태: {status['status']}")
            
            time.sleep(5)  # 5초마다 업데이트
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"모니터링 오류: {e}")
            time.sleep(5)

# 시뮬레이터 정지
def stop_simulator():
    response = requests.post('http://localhost:8080/api/stop')
    return response.json()
```

### 3. 스케줄링 예시

```python
import schedule
import time
import requests

def start_simulator_at_9am():
    """매일 오전 9시에 시뮬레이터 시작"""
    # MongoDB 상태 확인
    health = requests.get('http://localhost:8080/api/mongodb/health').json()
    if health['status'] != 'healthy':
        print(f"MongoDB 연결 오류: {health.get('error', 'Unknown')}")
        return
    
    # 시뮬레이터 시작
    requests.post('http://localhost:8080/api/start', json={
        'seed': int(time.time()),
        'strict_mode': False,
        'normalized_mode': False,
        'interval': 10
    })
    print("시뮬레이터가 스케줄에 따라 시작되었습니다.")

def stop_simulator_at_6pm():
    """매일 오후 6시에 시뮬레이터 정지"""
    result = requests.post('http://localhost:8080/api/stop').json()
    print(f"시뮬레이터가 스케줄에 따라 정지되었습니다: {result.get('uptime_seconds', 0)}초 실행")

# 스케줄 설정
schedule.every().day.at("09:00").do(start_simulator_at_9am)
schedule.every().day.at("18:00").do(stop_simulator_at_6pm)

# 스케줄 실행
while True:
    schedule.run_pending()
    time.sleep(1)
```

## 📊 데이터 구조

### 단일 컬렉션 모드
```json
{
  "_id": ObjectId("..."),
  "robot_id": "AGV-001",
  "mission_start_date": ISODate("2025-01-15T10:00:00Z"),
  "mission_end_date": ISODate("2025-01-15T10:05:00Z"),
  "mission_start_battery_state": 85,
  "mission_end_battery_state": 78,
  "route_name": "ROUTE1",
  "location": {
    "site": "H3",
    "line": "17L",
    "floor": "1F",
    "area": "GCB"
  },
  "data_points": [
    {
      "timestamp": ISODate("2025-01-15T10:00:00Z"),
      "unix_time": 1737014400.0,
      "localization_score": 95.2,
      "pos_x": 15000.5,
      "pos_y": 12000.3,
      "theta": 45.0,
      "tilt_x": 0.1,
      "tilt_y": -0.05,
      "illuminance": 750.0,
      "noise": 55.2,
      "temperature": 25.5,
      "humidity": 45.0,
      "NH3": 1.2,
      "H2S": 0.5,
      "VOCs": 3.1,
      "F2": 0.02,
      "HF": 0.1
    }
  ],
  "simulated_at": ISODate("2025-01-15T10:00:00Z")
}
```

### 정규화 모드
```json
// robot_missions 컬렉션
{
  "_id": ObjectId("..."),
  "robot_id": "AGV-001",
  "mission_start_date": ISODate("2025-01-15T10:00:00Z"),
  "mission_end_date": ISODate("2025-01-15T10:05:00Z"),
  "mission_start_battery_state": 85,
  "mission_end_battery_state": 78,
  "route_name": "ROUTE1",
  "location": {
    "site": "H3",
    "line": "17L",
    "floor": "1F",
    "area": "GCB"
  },
  "simulated_at": ISODate("2025-01-15T10:00:00Z")
}

// robot_data_points 컬렉션
{
  "_id": ObjectId("..."),
  "mission_id": ObjectId("..."),
  "robot_id": "AGV-001",
  "timestamp": ISODate("2025-01-15T10:00:00Z"),
  "unix_time": 1737014400.0,
  "localization_score": 95.2,
  "pos_x": 15000.5,
  "pos_y": 12000.3,
  "theta": 45.0,
  "tilt_x": 0.1,
  "tilt_y": -0.05,
  "illuminance": 750.0,
  "noise": 55.2,
  "temperature": 25.5,
  "humidity": 45.0,
  "NH3": 1.2,
  "H2S": 0.5,
  "VOCs": 3.1,
  "F2": 0.02,
  "HF": 0.1
}
```

## 🔧 문제 해결

### MongoDB 연결 오류
```bash
# MongoDB 상태 확인
mongosh --eval "db.runCommand('ping')"

# API를 통한 MongoDB 상태 확인
curl http://localhost:8080/api/mongodb/health

# MongoDB 서비스 재시작
net stop MongoDB
net start MongoDB
```

### 실시간 통계가 업데이트되지 않는 경우
```bash
# 통계 API 직접 확인
curl http://localhost:8080/api/stats

# 캐시 확인 (5초 간격으로 업데이트됨)
# 브라우저 개발자 도구에서 네트워크 탭 확인
```

### 프로세스 플로우가 멈춘 경우
```bash
# 시뮬레이터 로그 확인
tail -f simulator.log

# API 서버 로그 확인
tail -f api_server.log

# 시뮬레이터 재시작
curl -X POST http://localhost:8080/api/restart
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -ano | findstr :8080

# 다른 포트로 실행
python api_server.py --port 9000
```

### 웹 대시보드 접속 불가
```bash
# API 서버 상태 확인
curl http://localhost:8080/api/health

# 방화벽 확인
# Windows Defender 방화벽에서 Python 허용 확인

# 브라우저 캐시 삭제
# Ctrl+Shift+R (강력 새로고침)
```

### 성능 이슈
```bash
# MongoDB 인덱스 확인
mongosh robot_data --eval "db.robot_missions.getIndexes()"

# 쿼리 실행 시간 확인
curl http://localhost:8080/api/stats | jq .query_execution_time

# 로그 레벨 조정 (INFO → WARNING)
# simulator_config.json에서 logging.level 변경
```

## 📝 로그

### 로그 파일
- `simulator.log`: 시뮬레이터 실행 로그 (데이터 생성, MongoDB 저장 등)
- `api_server.log`: API 서버 로그 (HTTP 요청, 응답, 오류 등)
- 로그 로테이션: 10MB, 5개 백업 파일 자동 관리

### 실시간 로그 모니터링
```bash
# 시뮬레이터 로그 실시간 확인
tail -f simulator.log

# API 서버 로그 실시간 확인  
tail -f api_server.log

# 특정 키워드 필터링
tail -f simulator.log | grep "ERROR\|미션 생성"
```

### 로그 레벨
- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 일반적인 실행 정보 (기본값)
- **WARNING**: 경고 메시지
- **ERROR**: 오류 메시지

### 웹 대시보드 로그
웹 대시보드에서 실시간 로그를 확인할 수 있습니다:
- 🟢 INFO: 정상 작업
- 🟡 WARNING: 경고 메시지  
- 🔴 ERROR: 오류 발생

## 🤝 기여

버그 리포트나 기능 요청은 이슈로 등록해 주세요.

## 📄 라이선스

MIT License
