@echo off
rem SmartCRM — все валидаторы закрытия шага одним вызовом.
rem Запуск: cmd /c scripts\check_step.cmd (из любого места — сам переходит в корень репо).
rem Обходит проблему PowerShell-обёртки Cursor, где python не возвращает exit code.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0.."

python backend\scripts\check_agent_step.py
if errorlevel 1 exit /b 1
python backend\scripts\check_rules_commit_conflict.py
if errorlevel 1 exit /b 1
python backend\scripts\session_state_validate.py
if errorlevel 1 exit /b 1

echo.
echo ALL OK: check_step
exit /b 0
