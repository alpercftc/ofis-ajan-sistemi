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
        "| Birim | Vardiya / Takvim (`takim.md`) | Durum | Bekleyen İş | Son Koşu | Müfettiş Son Karar |",
        "| :--- | :--- | :--- | :---: | :--- | :--- |",
    ]
    for birim in BIRIMLER:
        d = ayar.durum_oku(birim, kok)
        fm = ayar.takim_bilgisi(birim, kok) or {}
        takvim = fm.get("takvim") or "—"
        kuyruk = d.get("kuyruk") or []
        bekleyen = sum(1 for k in kuyruk if k.get("durum") in ("bekliyor", "denetim_bekliyor"))
        son_kosu = d.get("son_kosu") or "—"
        muf_karar = (d.get("mufettis") or {}).get("son_karar") or "—"
        satirlar.append(
            f"| `{birim}` | {takvim} | {d.get('durum', 'bosta')} | {bekleyen} | {son_kosu} | {muf_karar} |"
        )
    return satirlar


def sabah_raporu(kok=None, kuru: bool = False) -> str:
    kok = Path(kok or KOK)
    an = datetime.now().astimezone()
    gun_adi = GUNLER[an.weekday()]

    # 1. Staj Bürosu: Ortak Tablodaki yeni Atölye staj defterlerini otomatik tara ve senkronize et (0-token)
    staj_durumu = "atlandı (kuru mod)"
    if not kuru:
        try:
            import staj_senkron
            senk_sonuc = staj_senkron.senkron_kontrol()
            yeni_sayisi = len(senk_sonuc.get("yeni_eklenenler", []))
            staj_durumu = f"{yeni_sayisi} yeni defter atandı" if yeni_sayisi else "yeni atanan defter yok"
        except Exception as e:
            staj_durumu = f"senkron hatası: {e}"

    # 2. Dağıtıcı: Bekleyen kuyruk maddelerini ve zinciri işlet
    sonuc = dagitici.dagit(kok, an, kuru=kuru)
    aktarilan = len(sonuc.get("zincir") or [])

    satirlar = [
        f"# 🌅 Sabah Ofis Özeti — {an:%Y-%m-%d} ({gun_adi})",
        "",
        f"- **Mesai Saatleri:** `{ayar.MESAI_METNI}`",
        f"- **Aktif Platform:** `{ayar.platform_al()}`",
        f"- **Atölye Staj Senkronu:** `{staj_durumu}`",
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

        # Sabah Telegram bildirimi
        try:
            import os
            import telegram_oku
            ayar.ortam_yukle()
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            ham_id = os.environ.get("TELEGRAM_CHAT_ID")
            if token and ham_id:
                tg_mesaj = (
                    f"🌅 *Sabah Ofis Özeti ({an:%d.%m.%Y})*\n\n"
                    f"• Mesai: `{ayar.MESAI_METNI}`\n"
                    f"• Atölye Staj Senkronu: `{staj_durumu}`\n"
                    f"• Dağıtıcı Aktarılan İş: `{aktarilan}`\n\n"
                    f"Mesai başladı, sistem emirlerinizi bekliyor."
                )
                telegram_oku.mesaj_gonder(token, int(ham_id), tg_mesaj)
        except Exception:
            pass

    return metin


def arka_plan_servislerini_kapat():
    """Mesai bitiminde (18:00) çalışan arka plan dinleyicilerini temiz bir şekilde kapatır."""
    import subprocess
    try:
        # telegram_dinle.py sürecini sonlandır
        cmd = 'Get-CimInstance Win32_Process -Filter "CommandLine LIKE \'%telegram_dinle.py%\'" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }'
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=10)
    except Exception:
        pass


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
        
        # 1. Mesai bitimi: Arka plan servislerini kapat
        arka_plan_servislerini_kapat()
        
        # 2. Telegram üzerinden Alper'e gün sonu özetini bildir
        try:
            import os
            import telegram_oku
            ayar.ortam_yukle()
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            ham_id = os.environ.get("TELEGRAM_CHAT_ID")
            if token and ham_id:
                ozet_mesaj = (
                    f"🌇 *Akşam Gün Sonu Denetim Raporu ({an:%d.%m.%Y})*\n\n"
                    f"• Bugün Tamamlanan Koşu: `{len(bugun_kosular)}`\n"
                    f"• Mesai kapandı, arka plan dinleyicileri uykuya alındı.\n"
                    f"İyi akşamlar dilerim."
                )
                telegram_oku.mesaj_gonder(token, int(ham_id), ozet_mesaj)
        except Exception:
            pass

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
