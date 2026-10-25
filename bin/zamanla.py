#!/usr/bin/env python3
"""Zamanlayıcı kurucusu — Windows Görev Zamanlayıcı (schtasks).
İki tetik kurar, başka hiçbir şey yapmaz:

  sabah  → `py -3 bin/gunluk.py --sabah`  · dağıtıcıyı koşturur, sabah raporunu yazar
  aksam  → `py -3 bin/gunluk.py --aksam`  · günün koşularını ve müfettiş kararlarını denetler

Saatler `bin/ayar.py`'den türer (ANAYASA §4 tek yerde): sabah mesai açılışında,
akşam mesai kapanışından bir saat önce.

Kullanım:
  py -3 bin/zamanla.py --kuru     # kurulacak görev komutlarını bas, hiçbir şeye dokunma
  py -3 bin/zamanla.py --kur      # görevleri Windows Task Scheduler'a yükle
  py -3 bin/zamanla.py --durum    # yüklü mü, ne zaman koşacak
  py -3 bin/zamanla.py --kaldir   # tetikleri kaldır (rapor dosyalarına dokunmaz)
"""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

KOK = ayar.KOK
ON_EK = "OfisAjanSirketi"

TETIKLER = [
    {
        "ad": "sabah",
        "saat": ayar.MESAI_BASLANGIC,
        "dakika": 0,
        "bayrak": "--sabah",
        "ne": "dağıtıcı + sabah raporu",
    },
    {
        "ad": "aksam",
        "saat": ayar.MESAI_BITIS - 1,
        "dakika": 0,
        "bayrak": "--aksam",
        "ne": "gün sonu denetim raporu",
    },
]


def kok_imzasi(kok=None) -> str:
    yol = str(Path(kok or KOK).resolve()).encode("utf-8")
    return hashlib.sha1(yol).hexdigest()[:8]


def gorev_adi(ad: str, kok=None) -> str:
    return f"{ON_EK}_{kok_imzasi(kok)}_{ad}"


def gorev_komutu(tetik: dict, kok=None) -> str:
    kok_yol = Path(kok or KOK).resolve()
    betik = kok_yol / "bin" / "gunluk.py"
    return f'"{sys.executable}" "{betik}" {tetik["bayrak"]}'


def _schtasks(*argv) -> tuple[int, str]:
    try:
        sonuc = subprocess.run(["schtasks.exe", *argv], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"schtasks çağrılamadı: {type(exc).__name__}"
    return sonuc.returncode, (sonuc.stdout + sonuc.stderr).strip()


def kur(kok=None) -> list[dict]:
    sonuclar = []
    for tetik in TETIKLER:
        ad = gorev_adi(tetik["ad"], kok)
        komut = gorev_komutu(tetik, kok)
        saat_str = f"{tetik['saat']:02d}:{tetik['dakika']:02d}"
        kod, cikti = _schtasks("/Create", "/SC", "DAILY", "/TN", ad, "/TR", komut, "/ST", saat_str, "/F")
        sonuclar.append({
            "ad": tetik["ad"],
            "gorev": ad,
            "mesaj": "yüklendi" if kod == 0 else f"yüklenemedi: {cikti or kod}",
        })
    return sonuclar


def kaldir(kok=None) -> list[dict]:
    sonuclar = []
    for tetik in TETIKLER:
        ad = gorev_adi(tetik["ad"], kok)
        kod, cikti = _schtasks("/Delete", "/TN", ad, "/F")
        sonuclar.append({
            "ad": tetik["ad"],
            "gorev": ad,
            "mesaj": "kaldırıldı" if kod == 0 else f"zaten yoktu ({cikti or kod})",
        })
    return sonuclar


def durum(kok=None) -> list[dict]:
    sonuclar = []
    for tetik in TETIKLER:
        ad = gorev_adi(tetik["ad"], kok)
        kod, _ = _schtasks("/Query", "/TN", ad)
        sonuclar.append({
            **tetik,
            "gorev": ad,
            "yuklu": kod == 0,
        })
    return sonuclar


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--kuru" in argv:
        for tetik in TETIKLER:
            print(
                f"--- {gorev_adi(tetik['ad'])} · her gün {tetik['saat']:02d}:{tetik['dakika']:02d} "
                f"· {tetik['ne']}"
            )
            print(f"Komut: {gorev_komutu(tetik)}")
        print("(kuru koşu: hiçbir dosya yazılmadı, Windows Görev Zamanlayıcı'ya dokunulmadı)")
        return 0
    if "--kur" in argv:
        for s in kur():
            print(f"{s['ad']:<6} {s['mesaj']} — {s['gorev']}")
        return 0
    if "--kaldir" in argv:
        for s in kaldir():
            print(f"{s['ad']:<6} {s['mesaj']}")
        return 0
    if "--durum" in argv:
        print(f"görev öneki: {ON_EK}_{kok_imzasi()}_<tetik>  ({KOK})")
        for s in durum():
            isaret = "✓ yüklü" if s["yuklu"] else "· kurulu değil"
            print(f"{s['ad']:<6} her gün {s['saat']:02d}:{s['dakika']:02d}  {isaret:<20} {s['ne']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
