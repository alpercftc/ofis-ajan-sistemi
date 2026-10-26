#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Mesai Başlatıcı ve Orkestratör (ofis_baslat.py)
-----------------------------------------------------------------
Mesai başladığında (veya sabah 09:00'da Windows Görev Zamanlayıcı tetiklediğinde):
1. 'gunluk.py --sabah' çağrılarak staj tablosu senkronize edilir, sabah raporu üretilir ve Telegram'a bildirilir.
2. Bekleyen kuyrukları ve zincirleri işletmek için 'kos.py dekan' tetiklenir.
3. Mesai boyunca Telegram mesajlarını ve 15 dakikada bir yeni e-postaları dinlemek üzere 'telegram_dinle.py' arka planda başlatılır.
(Not: 'panel.py' görsel arayüzü Alper'in tercihine göre manuel bırakılmıştır, otomatik başlatılmaz.)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

import ayar  # noqa: E402


def telegram_dinleyici_calisiyor_mu() -> bool:
    """telegram_dinle.py sürecinin zaten arka planda çalışıp çalışmadığını kontrol eder."""
    try:
        cmd = 'Get-CimInstance Win32_Process -Filter "CommandLine LIKE \'%telegram_dinle.py%\'" | Select-Object -ExpandProperty ProcessId'
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
        return bool(res.stdout.strip())
    except Exception:
        return False


def telegram_dinleyici_baslat():
    """telegram_dinle.py betiğini bağımsız bir arka plan süreci olarak ayağa kaldırır."""
    if telegram_dinleyici_calisiyor_mu():
        print("[BİLGİ] Telegram dinleyicisi zaten arka planda aktif.")
        return

    betik = KOK_DIZIN / "bin" / "telegram_dinle.py"
    # Windows'ta arkaplanda bağımsız (detached) süreç olarak başlat
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    subprocess.Popen(
        [sys.executable, str(betik)],
        cwd=str(KOK_DIZIN),
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    print("[BİLGİ] Telegram ve 15 dk e-posta dinleyici arka planda başlatıldı.")


def mesai_baslat():
    sys.stdout.reconfigure(encoding="utf-8")
    print("==================================================")
    print(" 🏢 ÜNİVERSİTE VE İDARİ OFİS AJAN ŞİRKETİ - MESAİ BAŞLAT")
    print("==================================================")
    
    aktif_platform = ayar.platform_al()
    print(f"[BİLGİ] Aktif Platform: {aktif_platform}")
    print(f"[BİLGİ] Mesai Saati: {ayar.MESAI_METNI}")

    # 1. Sabah Günlüğü ve Staj Senkronunu Çalıştır
    print("\n[ADIM 1] Sabah özeti, staj senkronu ve Telegram sabah bildirimi hazırlanıyor...")
    subprocess.run([sys.executable, str(KOK_DIZIN / "bin" / "gunluk.py"), "--sabah"], cwd=str(KOK_DIZIN))

    # 2. Kuyruktaki işleri işletmek için Dekan'ı koştur
    print("\n[ADIM 2] Bekleyen kuyruk ve gündem için Dekan koşturuluyor...")
    subprocess.run([sys.executable, str(KOK_DIZIN / "bin" / "kos.py"), "dekan"], cwd=str(KOK_DIZIN))

    # 3. Telegram ve Periyodik E-Posta Dinleyicisini Başlat
    print("\n[ADIM 3] Canlı Telegram ve 15 dk e-posta dinleyici servisi başlatılıyor...")
    telegram_dinleyici_baslat()

    print("\n==================================================")
    print(" ✅ Mesai başarıyla açıldı. Sistem Telegram üzerinden aktif!")
    print("==================================================")


if __name__ == "__main__":
    mesai_baslat()
