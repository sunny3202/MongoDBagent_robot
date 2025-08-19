@echo off
title 로봇 시뮬레이터 서버
echo ===============================================
echo    🤖 로봇 데이터 시뮬레이터 서버 시작 중...
echo ===============================================
echo.

REM 현재 디렉터리를 스크립트 위치로 변경
cd /d "%~dp0"

REM Python 경로 자동 감지
set PYTHON_PATH=
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i

REM Python이 PATH에 없으면 일반적인 위치들 확인
if "%PYTHON_PATH%"=="" (
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
        set PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
        set PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
        set PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    ) else (
        echo ❌ Python을 찾을 수 없습니다!
        echo    Python을 설치하거나 경로를 확인해주세요.
        pause
        exit /b 1
    )
)

echo 📍 Python 경로: %PYTHON_PATH%
echo 📁 작업 디렉터리: %CD%
echo.

REM 필요한 패키지 설치 확인
echo 📦 필요한 패키지 설치 중...
"%PYTHON_PATH%" -m pip install -r requirements.txt > nul 2>&1

REM 서버 시작
echo 🚀 서버 시작 중... (포트 8080)
echo 웹 브라우저에서 http://localhost:8080 으로 접속하세요!
echo.
echo ⚠️  서버를 종료하려면 Ctrl+C를 누르세요.
echo ===============================================
echo.

"%PYTHON_PATH%" api_server.py --port 8080

pause
