#!/usr/bin/env python3
"""Günlük tetik — sabah ofis birimlerini/dağıtıcıyı başlatır ve rapor yazar, akşam günü denetler. LLM çağırmaz.

Kullanım:
  py -3 bin/gunluk.py --sabah        # dağıtıcıyı koştur + sabah raporu yaz
  py -3 bin/gunluk.py --aksam        # denetim raporu yaz (hiçbir şey koşturmaz)
  py -3 bin/gunluk.py --sabah --kuru # hiçbir birimi başlatma, raporu ekrana bas

Rapor `sirket-log/rapor/YYYY-MM-DD-{sabah,aksam}.md` dosyasına yazılır.
Zamanlayıcıyı `bin/zamanla.py` kurar.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import dagitici  # noqa: E402

KOK = ayar.KOK
RAPOR_DIZINI = "sirket-log/rapor"
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

BIRIMLER = [
    "dekan",
    "dekan-sekreteri",
    "staj-burosu",
    "postaci",
    "memur",
    "ik-memuru",
    "bilgi-islem",
    "mufettis",
]


def _durum_satirlari(kok: Path) -> list[str]:
    satirlar = [
        "| Birim | Durum | Bekleyen İş | Son Koşu | Müfettiş Son Karar |",
        "| :--- | :--- | :---: | :--- | :--- |",
    ]
    for birim in BIRIMLER:
        d = ayar.durum_oku(birim, kok)
        kuyruk = d.get("kuyruk") or []
        bekleyen = sum(1 for k in kuyruk if k.get("durum") in ("bekliyor", "denetim_bekliyor"))
        son_kosu = d.get("son_kosu") or "—"
        muf_karar = (d.get("mufettis") or {}).get("son_karar") or "—"
        satirlar.append(f"| `{birim}` | {d.get('durum', 'bosta')} | {bekleyen} | {son_kosu} | {muf_karar} |")
    return satirlar


def sabah_raporu(kok=None, kuru: bool = False) -> str:
    kok = Path(kok or KOK)
    an = datetime.now().astimezone()
    gun_adi = GUNLER[an.weekday()]
    aktarilan = 0 if kuru else dagitici.kuyruklari_tara()
    satirlar = [
        f"# 🌅 Sabah Ofis Özeti — {an:%Y-%m-%d} ({gun_adi})",
        "",
        f"- **Mesai Saatleri:** `{ayar.MESAI_METNI}`",
        f"- **Aktif Platform:** `{ayar.platform_al()}`",
        f"- **Dağıtıcı Aktarılan İş:** `{aktarilan}` {'(kuru mod)' if kuru else ''}",
        "",
        "## Birim Durum Tablosu",
        *_durum_satirlari(kok),
        "",
    ]
    metin = "\n".join(satirlar)
    if not kuru:
        hedef = kok / RAPOR_DIZINI / f"{an:%Y-%m-%d}-sabah.md"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(metin, encoding="utf-8")
    return metin


def aksam_raporu(kok=None, kuru: bool = False) -> str:
    kok = Path(kok or KOK)
    an = datetime.now().astimezone()
    gun_adi = GUNLER[an.weekday()]
    bugun_kosular = list((kok / "takimlar").glob(f"*/kosu/{an:%Y-%m-%d}*.md"))
    satirlar = [
        f"# 🌇 Akşam Gün Sonu Denetim Raporu — {an:%Y-%m-%d} ({gun_adi})",
        "",
        f"- **Bugün Kaydedilen Koşu Sayısı:** `{len(bugun_kosular)}`",
        "",
        "## Birim Kapanış Durumu",
        *_durum_satirlari(kok),
        "",
    ]
    metin = "\n".join(satirlar)
    if not kuru:
        hedef = kok / RAPOR_DIZINI / f"{an:%Y-%m-%d}-aksam.md"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(metin, encoding="utf-8")
    return metin


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    kuru = "--kuru" in argv
    if "--sabah" in argv:
        print(sabah_raporu(KOK, kuru=kuru))
        return 0
    if "--aksam" in argv:
        print(aksam_raporu(KOK, kuru=kuru))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
