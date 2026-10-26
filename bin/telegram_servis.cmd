@echo off
set "SCRIPT_DIR=C:\Alper\Ofis"
cd /d "%SCRIPT_DIR%"
:loop
"C:\Users\alper\AppData\Local\Programs\Python\Python314\python.exe" "C:\Alper\Ofis\bin\telegram_dinle.py" >> "C:\Alper\Ofis\sirket-log\daemon.log" 2>&1
timeout /t 5 /nobreak >nul
goto loop
