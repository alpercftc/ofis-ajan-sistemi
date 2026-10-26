#!/usr/bin/env python3
"""
Ofis Ajan Şirketi — Mesai Başlatıcı, Bekçi (Watchdog) ve Orkestratör (ofis_baslat.py)
-------------------------------------------------------------------------------------
1. Bilgisayar açıldığında (Startup), sabah 09:00'da veya mesai içi 15 dk nöbet tetiğinde çalışır.
2. Mesai saatleri (09:00-18:00) dışındaysa (`--zorla` verilmedikçe) hiçbir şey başlatmadan çıkar.
3. Mesai saatleri içindeyse:
   - Bugünün sabah raporu (`sirket-log/rapor/YYYY-MM-DD-sabah.md`) henüz üretilmediyse `gunluk.py --sabah`
     çalıştırarak ortak staj tablosunu senkronize eder ve sabah Telegram bildirimini gönderir.
   - Bekleyen kuyrukları ve iş zincirini yürütmek için `dagitici.py` çalıştırır.
   - `telegram_dinle.py` arka planda çalışmıyorsa tekil kilit güvencesiyle başlatır.
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

import ayar  # noqa: E402


def telegram_dinleyici_calisiyor_mu() -> bool:
    """`sirket-log/telegram-dinle.lock` dosyası üzerinde aktif kilit olup olmadığını kontrol eder."""
    kilit_yolu = KOK_DIZIN / "sirket-log" / "telegram-dinle.lock"
    if not kilit_yolu.exists():
        return False
    try:
        with open(kilit_yolu, "a+", encoding="utf-8") as dosya:
            if os.name == "nt":
                import msvcrt

                dosya.seek(0)
                try:
                    msvcrt.locking(dosya.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(dosya.fileno(), msvcrt.LK_UNLCK, 1)
                    return False  # Kilit alınabildiyse süreç çalışmıyor demektir
                except OSError:
                    return True  # Kilit alınamadıysa telegram_dinle.py aktif çalışıyor
            else:
                import fcntl

                try:
                    fcntl.flock(dosya.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(dosya.fileno(), fcntl.LOCK_UN)
                    return False
                except BlockingIOError:
                    return True
    except Exception:
        return False


def telegram_dinleyici_baslat(kuru: bool = False, sessiz: bool = False) -> bool:
    if telegram_dinleyici_calisiyor_mu():
        if not sessiz:
            print("[BİLGİ] Telegram dinleyicisi zaten arka planda aktif.")
        return False

    if kuru:
        if not sessiz:
            print("[BİLGİ] (Kuru) Telegram dinleyicisi başlatılacaktı.")
        return True

    betik = KOK_DIZIN / "bin" / "telegram_dinle.py"
    log_dizin = KOK_DIZIN / "sirket-log"
    log_dizin.mkdir(parents=True, exist_ok=True)

    py_exe = Path(sys.executable)
    if py_exe.name.lower() == "pythonw.exe":
        normal_py = py_exe.with_name("python.exe")
        if normal_py.exists():
            py_exe = normal_py

    creationflags = 0
    if os.name == "nt":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        creationflags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

    log_dosya = open(log_dizin / "telegram-dinle-baslat.log", "a", encoding="utf-8")
    subprocess.Popen(
        [str(py_exe), str(betik)],
        cwd=str(KOK_DIZIN),
        stdin=subprocess.DEVNULL,
        stdout=log_dosya,
        stderr=log_dosya,
        creationflags=creationflags,
        close_fds=False,
    )
    if not sessiz:
        print("[BİLGİ] Telegram ve periyodik e-posta/staj dinleyicisi arka planda başlatıldı.")
    return True


def mesai_baslat(zorla: bool = False, sessiz_nobet: bool = False, kuru: bool = False) -> int:
    for _akis in (sys.stdout, sys.stderr):
        if _akis is not None and hasattr(_akis, "reconfigure"):
            try:
                _akis.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    ayar.ortam_yukle()

    an = datetime.now().astimezone()
    if not zorla and not ayar.mesaide_mi(an):
        if not sessiz_nobet:
            print(f"[BİLGİ] Şu an mesai dışı ({ayar.MESAI_METNI}). Sistem beklemede.")
        return 0

    sabah_rapor_yolu = KOK_DIZIN / "sirket-log" / "rapor" / f"{an:%Y-%m-%d}-sabah.md"

    if not sessiz_nobet:
        print("==================================================")
        print(" 🏢 ÜNİVERSİTE VE İDARİ OFİS AJAN ŞİRKETİ - MESAİ AKTİF")
        print("==================================================")
        print(f"[BİLGİ] Aktif Platform: {ayar.platform_al()} | Mesai: {ayar.MESAI_METNI}")

    if kuru:
        if not sessiz_nobet:
            print("[BİLGİ] (Kuru) Mesai başlatıcı kontrolleri tamamlandı.")
        return 0

    # 1. Bugün sabah özeti ve staj senkronu henüz çalışmadıysa çalıştır
    if not sabah_rapor_yolu.exists():
        print("[ADIM 1] Bugünün sabah özeti, ortak staj senkronu ve Telegram bildirimi hazırlanıyor...")
        subprocess.run(
            [sys.executable, str(KOK_DIZIN / "bin" / "gunluk.py"), "--sabah"],
            cwd=str(KOK_DIZIN),
        )
    else:
        # Sabah raporu zaten üretilmişse yalnızca bekleyen kuyrukları ve zinciri kontrol et
        subprocess.run(
            [sys.executable, str(KOK_DIZIN / "bin" / "dagitici.py")],
            cwd=str(KOK_DIZIN),
        )

    # 2. Telegram ve Periyodik E-Posta / Staj Dinleyicisini Başlat (çalışmıyorsa ayağa kaldır)
    telegram_dinleyici_baslat(kuru=kuru, sessiz=sessiz_nobet)

    if not sessiz_nobet:
        print("==================================================")
        print(" ✅ Ofis sistemi ayakta. Telegram ve masaüstü emirleri dinleniyor!")
        print("==================================================")
    return 0


if __name__ == "__main__":
    zorla_bayrak = "--zorla" in sys.argv
    nobet_bayrak = "--nobet" in sys.argv
    kuru_bayrak = "--kuru" in sys.argv
    raise SystemExit(mesai_baslat(zorla=zorla_bayrak, sessiz_nobet=nobet_bayrak, kuru=kuru_bayrak))
