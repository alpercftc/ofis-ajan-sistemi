@echo off
echo ====================================================
echo  Ofis Ajan Sirketi - Telegram Dinleyici Kapatiliyor
echo ====================================================

rem 1. Calisan Python ve Wscript dinleme sureclerini sonlandir
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%%telegram_dinle.py%%' OR CommandLine LIKE '%%telegram_servis%%'\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

rem 2. Windows baslangic kaydini kaldir (otomatik baslamasin)
powershell -NoProfile -Command "Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'Ofis_Telegram_Servisi' -ErrorAction SilentlyContinue"

echo.
echo [TAMAM] Telegram dinleme servisi kapatildi ve baslangic kaydi kaldirildi.
echo Istediginiz zaman 'bin\telegram_baslat.cmd' ile tekrar acabilsiniz.
echo ====================================================
