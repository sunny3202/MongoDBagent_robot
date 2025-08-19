@echo off
title 포터블 패키지 생성기
echo ===============================================
echo    📦 로봇 시뮬레이터 포터블 패키지 생성
echo ===============================================
echo.

REM 패키지 폴더 생성
set PACKAGE_NAME=RobotSimulator_Portable
if exist "%PACKAGE_NAME%" rmdir /s /q "%PACKAGE_NAME%"
mkdir "%PACKAGE_NAME%"

echo 📁 폴더 생성 중...

REM 필요한 파일들 복사
copy "*.py" "%PACKAGE_NAME%\"
copy "*.json" "%PACKAGE_NAME%\"
copy "*.txt" "%PACKAGE_NAME%\"
copy "*.bat" "%PACKAGE_NAME%\"
copy "*.md" "%PACKAGE_NAME%\"

REM templates 폴더 복사
if exist "templates" (
    mkdir "%PACKAGE_NAME%\templates"
    copy "templates\*" "%PACKAGE_NAME%\templates\"
)

REM 사용 설명서 생성
echo 🤖 로봇 시뮬레이터 포터블 버전 > "%PACKAGE_NAME%\사용법.txt"
echo ================================== >> "%PACKAGE_NAME%\사용법.txt"
echo. >> "%PACKAGE_NAME%\사용법.txt"
echo 📋 사용 순서: >> "%PACKAGE_NAME%\사용법.txt"
echo 1. MongoDB가 실행 중인지 확인 >> "%PACKAGE_NAME%\사용법.txt"
echo 2. simulator_config.json에서 MongoDB 주소 수정 >> "%PACKAGE_NAME%\사용법.txt"
echo 3. 서버시작.bat 더블클릭 >> "%PACKAGE_NAME%\사용법.txt"
echo 4. 브라우저에서 http://localhost:8080 접속 >> "%PACKAGE_NAME%\사용법.txt"
echo. >> "%PACKAGE_NAME%\사용법.txt"
echo 📝 MongoDB 설정: >> "%PACKAGE_NAME%\사용법.txt"
echo - 로컬: mongodb://localhost:27017/ >> "%PACKAGE_NAME%\사용법.txt"
echo - 원격: mongodb://IP주소:27017/ >> "%PACKAGE_NAME%\사용법.txt"
echo. >> "%PACKAGE_NAME%\사용법.txt"
echo ❓ 문제 해결: >> "%PACKAGE_NAME%\사용법.txt"
echo - Python 오류: Python 3.11 이상 설치 필요 >> "%PACKAGE_NAME%\사용법.txt"
echo - MongoDB 연결 오류: simulator_config.json 확인 >> "%PACKAGE_NAME%\사용법.txt"

echo ✅ 패키지 생성 완료: %PACKAGE_NAME% 폴더
echo 💾 이 폴더를 다른 PC로 복사해서 사용하세요!
echo.
pause
