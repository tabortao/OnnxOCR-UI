@echo off
chcp 65001
pushd %~dp0
echo Current directory is: %cd%
echo The program is starting, please wait...
set PYTHON_PATH=.\.venv\Scripts\python.exe
timeout /t 3 /nobreak > nul 
"%PYTHON_PATH%" app-service.py
pause