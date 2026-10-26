#!/usr/bin/env python3
"""Zamanlayıcı ve Başlangıç kurucusu — Windows Görev Zamanlayıcı (schtasks) + Windows Startup.

Kurulan tetikler:
  sabah  → Her gün 09:00 · `py -3 bin/ofis_baslat.py` (sabah raporu, staj senkronu, dağıtıcı, telegram dinle)
  nobet  → 15 dakikada bir · `py -3 bin/ofis_baslat.py --nobet` (mesai içi bekçi/watchdog + kuyruk dağıtımı)
  aksam  → Her gün 18:00 · `py -3 bin/gunluk.py --aksam` (gün sonu denetim raporu, servis kapatma, git yedek)
  acilis → Windows kullanıcı oturumu açıldığında (`Startup` klasörü `.vbs` başlatıcı) · `ofis_baslat.py`

Saatler `bin/ayar.py`'den türer (ANAYASA §4 tek yerde).

Kullanım:
  py -3 bin/zamanla.py --kuru     # kurulacak görev komutlarını bas, hiçbir şeye dokunma
  py -3 bin/zamanla.py --kur      # görevleri Windows Task Scheduler ve Startup klasörüne yükle
  py -3 bin/zamanla.py --durum    # yüklü mü, ne zaman koşacak
  py -3 bin/zamanla.py --kaldir   # tetikleri kaldır (rapor dosyalarına dokunmaz)
"""
import hashlib
import os
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
        "tip": "DAILY",
        "saat": ayar.MESAI_BASLANGIC,
        "dakika": 0,
        "betik": "ofis_baslat.py",
        "bayrak": "",
        "ne": "ofis başlatıcı + staj senkronu + dağıtıcı + telegram dinleyici",
    },
    {
        "ad": "nobet",
        "tip": "MINUTE",
        "aralik_dk": 15,
        "saat": ayar.MESAI_BASLANGIC,
        "dakika": 0,
        "betik": "ofis_baslat.py",
        "bayrak": "--nobet",
        "ne": "mesai içi 15 dk bekçi (telegram dinleyici + bekleyen kuyruk kontrolü)",
    },
    {
        "ad": "aksam",
        "tip": "DAILY",
        "saat": ayar.MESAI_BITIS,
        "dakika": 0,
        "betik": "gunluk.py",
        "bayrak": "--aksam",
        "ne": "gün sonu denetim raporu (0-token) + telegram bildirimi + servis kapatma + git yedek",
    },
]


def kok_imzasi(kok=None) -> str:
    yol = str(Path(kok or KOK).resolve()).encode("utf-8")
    return hashlib.sha1(yol).hexdigest()[:8]


def gorev_adi(ad: str, kok=None) -> str:
    return f"{ON_EK}_{kok_imzasi(kok)}_{ad}"


def _pythonw_veya_python() -> str:
    py_exe = Path(sys.executable)
    pyw_exe = py_exe.with_name("pythonw.exe")
    return str(pyw_exe if pyw_exe.exists() else py_exe)


def gorev_komutu(tetik: dict, kok=None) -> str:
    kok_yol = Path(kok or KOK).resolve()
    betik_adi = tetik.get("betik", "gunluk.py")
    betik = kok_yol / "bin" / betik_adi
    bayrak = f" {tetik['bayrak']}" if tetik.get("bayrak") else ""
    calistirici = _pythonw_veya_python()
    return f'"{calistirici}" "{betik}"{bayrak}'


def startup_vbs_yolu() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
        / f"{ON_EK}_Baslangic.vbs"
    )


def _startup_vbs_kur(kok=None) -> dict:
    kok_yol = Path(kok or KOK).resolve()
    betik = kok_yol / "bin" / "ofis_baslat.py"
    calistirici = _pythonw_veya_python()
    vbs_icerik = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.CurrentDirectory = "{kok_yol}"\n'
        f'WshShell.Run """{calistirici}"" ""{betik}""", 0, False\n'
    )
    hedef = startup_vbs_yolu()
    try:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(vbs_icerik, encoding="utf-8")
        return {"ad": "acilis", "gorev": str(hedef.name), "mesaj": "yüklendi (Windows Startup)"}
    except OSError as exc:
        return {"ad": "acilis", "gorev": str(hedef.name), "mesaj": f"yüklenemedi: {exc}"}


def _startup_vbs_kaldir() -> dict:
    hedef = startup_vbs_yolu()
    try:
        if hedef.exists():
            hedef.unlink()
            return {"ad": "acilis", "gorev": str(hedef.name), "mesaj": "kaldırıldı"}
        return {"ad": "acilis", "gorev": str(hedef.name), "mesaj": "zaten yoktu"}
    except OSError as exc:
        return {"ad": "acilis", "gorev": str(hedef.name), "mesaj": f"hata: {exc}"}


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
        if tetik.get("tip") == "MINUTE":
            kod, cikti = _schtasks(
                "/Create",
                "/SC",
                "MINUTE",
                "/MO",
                str(tetik.get("aralik_dk", 15)),
                "/TN",
                ad,
                "/TR",
                komut,
                "/F",
            )
        else:
            kod, cikti = _schtasks("/Create", "/SC", "DAILY", "/TN", ad, "/TR", komut, "/ST", saat_str, "/F")
        sonuclar.append(
            {
                "ad": tetik["ad"],
                "gorev": ad,
                "mesaj": "yüklendi" if kod == 0 else f"yüklenemedi: {cikti or kod}",
            }
        )
    sonuclar.append(_startup_vbs_kur(kok))
    return sonuclar


def kaldir(kok=None) -> list[dict]:
    sonuclar = []
    for tetik in TETIKLER:
        ad = gorev_adi(tetik["ad"], kok)
        kod, cikti = _schtasks("/Delete", "/TN", ad, "/F")
        sonuclar.append(
            {
                "ad": tetik["ad"],
                "gorev": ad,
                "mesaj": "kaldırıldı" if kod == 0 else f"zaten yoktu ({cikti or kod})",
            }
        )
    sonuclar.append(_startup_vbs_kaldir())
    return sonuclar


def durum(kok=None) -> list[dict]:
    sonuclar = []
    for tetik in TETIKLER:
        ad = gorev_adi(tetik["ad"], kok)
        kod, _ = _schtasks("/Query", "/TN", ad)
        sonuclar.append(
            {
                **tetik,
                "gorev": ad,
                "yuklu": kod == 0,
            }
        )
    vbs = startup_vbs_yolu()
    sonuclar.append(
        {
            "ad": "acilis",
            "saat": 0,
            "dakika": 0,
            "ne": "PC açıldığında mesai saatleri içindeyse ofis sistemini otomatik başlatır",
            "gorev": vbs.name,
            "yuklu": vbs.exists(),
        }
    )
    return sonuclar


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--kuru" in argv:
        for tetik in TETIKLER:
            zaman_etiketi = (
                f"her {tetik['aralik_dk']} dk"
                if tetik.get("tip") == "MINUTE"
                else f"her gün {tetik['saat']:02d}:{tetik['dakika']:02d}"
            )
            print(f"--- {gorev_adi(tetik['ad'])} · {zaman_etiketi} · {tetik['ne']}")
            print(f"Komut: {gorev_komutu(tetik)}")
        print(f"--- Startup VBS: {startup_vbs_yolu()}")
        print("(kuru koşu: hiçbir dosya yazılmadı, Windows Görev Zamanlayıcı'ya dokunulmadı)")
        return 0
    if "--kur" in argv:
        for s in kur():
            print(f"{s['ad']:<8} {s['mesaj']} — {s['gorev']}")
        return 0
    if "--kaldir" in argv:
        for s in kaldir():
            print(f"{s['ad']:<8} {s['mesaj']}")
        return 0
    if "--durum" in argv:
        print(f"görev öneki: {ON_EK}_{kok_imzasi()}_<tetik>  ({KOK})")
        for s in durum():
            isaret = "✓ yüklü" if s["yuklu"] else "· kurulu değil"
            zaman_bilgi = (
                f"her {s['aralik_dk']} dk"
                if s.get("tip") == "MINUTE"
                else ("PC açılışında" if s["ad"] == "acilis" else f"her gün {s['saat']:02d}:{s['dakika']:02d}")
            )
            print(f"{s['ad']:<8} {zaman_bilgi:<16} {isaret:<16} {s['ne']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
