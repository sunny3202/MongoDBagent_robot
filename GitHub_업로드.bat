@echo off
chcp 65001 > nul
echo 🚀 GitHub 업로드 시작...

REM Git이 설치되어 있는지 확인
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git이 설치되어 있지 않습니다.
    echo 📥 Git을 먼저 설치해주세요: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git 설치 확인됨

REM Git 초기화
echo 🔄 Git 저장소 초기화...
git init

REM 원격 저장소 추가
echo 🔗 원격 저장소 연결...
git remote add origin https://github.com/sunny3202/MongoDBagent_robot.git

REM 모든 파일 추가
echo 📁 파일 추가 중...
git add .

REM 첫 번째 커밋
echo 💾 첫 번째 커밋...
git commit -m "Initial commit: 로봇 데이터 MongoDB 시뮬레이터 v2.0"

REM GitHub에 푸시
echo 🚀 GitHub에 업로드 중...
git branch -M main
git push -u origin main

echo ✅ 업로드 완료!
echo 🌐 https://github.com/sunny3202/MongoDBagent_robot 에서 확인하세요.
pause
