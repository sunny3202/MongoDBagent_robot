# 🤖 실용적인 로봇 모니터링 시스템 설계

## 📊 운영자 중심 통계 재설계

### 1. 실시간 로봇 상태 (개별 제어)
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 로봇별 실시간 상태                                        │
├─────────────────────────────────────────────────────────────┤
│ AGV-001 🟢 작업중   배터리: 85%  마지막: 2분전  [정지] [재시작] │
│ AGV-002 🔴 정지됨   배터리: 23%  마지막: 1시간전 [시작] [점검]  │
│ AGV-003 🟡 대기중   배터리: 67%  마지막: 5분전  [시작] [설정]  │
│ AGV-004 ⚠️  오류    배터리: 45%  오류: 연결끊김  [재시작]     │
└─────────────────────────────────────────────────────────────┘
```

### 2. 의미있는 운영 통계
```
┌──────────────────┬──────────────────┬──────────────────┐
│ 📈 금일 처리 현황  │ ⚡ 실시간 상태    │ ⚠️  알림 및 경고  │
├──────────────────┼──────────────────┼──────────────────┤
│ 완료 미션: 145개  │ 작업중: 8대     │ 배터리부족: 3대   │
│ 진행중: 8개      │ 대기중: 15대    │ 연결끊김: 1대     │
│ 실패: 2개        │ 정지됨: 7대     │ 점검필요: 0대     │
│ 성공률: 98.6%    │ 오류: 0대       │ 긴급상황: 0건     │
└──────────────────┴──────────────────┴──────────────────┘
```

### 3. 시간대별 작업 현황
```
┌─────────────────────────────────────────────────────────────┐
│ 📅 시간대별 미션 처리 현황                                    │
├─────────────────────────────────────────────────────────────┤
│ 09:00-10:00  ████████████ 24개 (목표: 30개)               │
│ 10:00-11:00  ██████████████████ 32개 (목표: 30개)         │
│ 11:00-12:00  ████████████████ 28개 (진행중)               │
└─────────────────────────────────────────────────────────────┘
```

## 🎮 개별 로봇 제어 시스템

### 1. 로봇 상태 관리
```python
class RobotStatus:
    RUNNING = "running"      # 🟢 작업중
    IDLE = "idle"           # 🟡 대기중  
    STOPPED = "stopped"     # 🔴 정지됨
    ERROR = "error"         # ⚠️ 오류
    MAINTENANCE = "maintenance"  # 🔧 점검중

class IndividualRobotManager:
    def __init__(self):
        self.robot_states = {}  # AGV-001: {status, last_seen, battery, etc}
        self.robot_threads = {} # AGV-001: Thread object
        
    def start_robot(self, robot_id: str):
        """개별 로봇 시작"""
        
    def stop_robot(self, robot_id: str):
        """개별 로봇 정지"""
        
    def get_robot_status(self, robot_id: str):
        """개별 로봇 상태 조회"""
```

### 2. 실시간 모니터링 데이터
```python
class OperationalStats:
    def get_daily_stats(self) -> Dict:
        """금일 작업 통계"""
        return {
            "completed_missions": 145,
            "active_missions": 8,
            "failed_missions": 2,
            "success_rate": 98.6,
            "total_robots": 30,
            "active_robots": 8,
            "idle_robots": 15,
            "stopped_robots": 7,
            "error_robots": 0
        }
    
    def get_hourly_performance(self) -> List[Dict]:
        """시간대별 성과"""
        
    def get_critical_alerts(self) -> List[Dict]:
        """긴급 알림"""
        return [
            {"robot_id": "AGV-002", "type": "low_battery", "value": 23},
            {"robot_id": "AGV-015", "type": "connection_lost", "duration": 3600}
        ]
```

### 3. 프로세스 플로우 리셋
```python
class ProcessFlowManager:
    def __init__(self):
        self.active_flows = {}  # robot_id: ProcessFlowTracker
        
    def start_robot_flow(self, robot_id: str):
        """개별 로봇 프로세스 플로우 시작"""
        self.active_flows[robot_id] = ProcessFlowTracker()
        
    def reset_robot_flow(self, robot_id: str):
        """개별 로봇 프로세스 플로우 리셋"""
        if robot_id in self.active_flows:
            self.active_flows[robot_id].reset()
            
    def reset_all_flows(self):
        """모든 프로세스 플로우 리셋"""
        for tracker in self.active_flows.values():
            tracker.reset()
```

## 🌐 API 엔드포인트 확장

### 개별 로봇 제어
- `POST /api/robots/{robot_id}/start` - 개별 로봇 시작
- `POST /api/robots/{robot_id}/stop` - 개별 로봇 정지  
- `GET /api/robots/{robot_id}/status` - 개별 로봇 상태
- `POST /api/robots/{robot_id}/reset` - 개별 로봇 리셋

### 운영 통계
- `GET /api/stats/operational` - 운영 중심 통계
- `GET /api/stats/daily` - 금일 작업 현황
- `GET /api/stats/hourly` - 시간대별 현황
- `GET /api/alerts/critical` - 긴급 알림

### 대시보드 데이터
- `GET /api/dashboard/robots` - 로봇 목록 및 상태
- `GET /api/dashboard/performance` - 성과 대시보드
- `POST /api/dashboard/reset` - 전체 리셋

## 📱 웹 대시보드 개선

### 1. 로봇 목록 테이블
```html
<table class="robot-table">
  <tr>
    <th>로봇ID</th><th>상태</th><th>배터리</th><th>마지막작업</th><th>제어</th>
  </tr>
  <tr class="robot-row" data-robot="AGV-001">
    <td>AGV-001</td>
    <td><span class="status running">🟢 작업중</span></td>
    <td><span class="battery good">85%</span></td>
    <td>2분전</td>
    <td>
      <button onclick="stopRobot('AGV-001')">정지</button>
      <button onclick="resetRobot('AGV-001')">리셋</button>
    </td>
  </tr>
</table>
```

### 2. 실시간 알림 패널
```html
<div class="alerts-panel">
  <div class="alert critical">
    ⚠️ AGV-002 배터리 부족 (23%)
  </div>
  <div class="alert warning">
    🔴 AGV-015 연결 끊김 (1시간)
  </div>
</div>
```

## 🔄 데이터 리셋 전략

### 1. 시간 기반 리셋
- **일일 리셋**: 매일 자정에 일일 통계 초기화
- **시간별 리셋**: 매 시간 시간대별 통계 초기화
- **실시간 리셋**: 사용자 요청 시 즉시 리셋

### 2. 범위별 리셋
- **개별 로봇**: 특정 로봇만 리셋
- **그룹별**: 특정 라인/구역 로봇들만 리셋  
- **전체**: 모든 로봇 및 통계 리셋

### 3. 데이터 보존
```python
class DataRetention:
    def archive_daily_data(self):
        """일일 데이터 아카이브"""
        # 리셋 전 데이터를 history 컬렉션에 보관
        
    def cleanup_old_data(self):
        """오래된 데이터 정리"""
        # 30일 이상 된 상세 데이터 삭제
```

## 🎯 구현 우선순위

1. **개별 로봇 제어** (최우선)
2. **실시간 상태 모니터링** 
3. **프로세스 플로우 리셋**
4. **운영 중심 통계**
5. **알림 시스템**
6. **데이터 아카이브**

이렇게 하면 **실제 운영에 유용한** 모니터링 시스템이 됩니다!

