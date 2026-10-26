#!/usr/bin/env python3
"""Telegram dinleyici — bota mesaj düştüğü anda ilgili ofis birimi koşar.

Kullanım:
  py -3 bin/telegram_dinle.py            # sonsuz long-poll döngüsü
  py -3 bin/telegram_dinle.py --bir-kez  # tek tur döner (test)

Offset yönetimi ve chat id filtresi `bin/telegram_oku.py`'dedir (`takimlar/postaci/gelen/`).
Yönlendirme `takim_sec`'te tek yerdedir:
  - İçinde "yönerge", "mevzuat", "kılavuz" geçen veya PDF/belge ekiyle kural derleme isteyen mesaj → `dekan-sekreteri`
  - İçinde "staj", "defter", "sicil" geçen mesaj → `staj-burosu`
  - İçinde "müdek", "komisyon", "tutanak" geçen mesaj → `memur`
  - Sesli not veya genel e-posta/iş mesajı → `dekan` (veya `postaci`)
"""
import collections
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import telegram_oku  # noqa: E402

KOK = ayar.KOK
TAKIM = telegram_oku.TAKIM  # postaci — gelen kutusu ve offset burada tutulur

MEVZUAT_DESEN = re.compile(r"(yönerge|yonerge|mevzuat|kılavuz|kilavuz)", re.IGNORECASE)
STAJ_DESEN = re.compile(r"(staj|defter|sicil)", re.IGNORECASE)
MEMUR_DESEN = re.compile(r"(müdek|mudek|komisyon|tutanak|denetim)", re.IGNORECASE)

KUYRUK_ONEKI = {
    "dekan": "dkn",
    "dekan-sekreteri": "sek",
    "staj-burosu": "staj",
    "memur": "mmr",
    "postaci": "pst",
}

BEKLEME_SN = 15
TUR_ARASI_SN = 2
NOT_SINIRI = 200
LOG_ADI = "telegram-dinle.log"

_SIRLAR = []


def sir_ekle(deger):
    if deger and deger not in _SIRLAR:
        _SIRLAR.append(deger)
    return len(_SIRLAR)


def _log(kok, satir):
    for sir in _SIRLAR:
        satir = satir.replace(sir, "***")
    damga = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[BİLGİ] {damga} | {satir}", flush=True)
    yol = Path(kok) / "sirket-log" / LOG_ADI
    try:
        yol.parent.mkdir(parents=True, exist_ok=True)
        with open(yol, "a", encoding="utf-8") as dosya:
            dosya.write(f"[BİLGİ] {damga} | {satir}\n")
    except OSError:
        pass


def _temiz(metin, sinir=NOT_SINIRI):
    tek_satir = " ".join(str(metin or "").split())
    return tek_satir[:sinir] + ("…" if len(tek_satir) > sinir else "")


def takim_sec(mesaj: dict) -> str | None:
    """Mesajı hangi birim karşılar?"""
    metin = (mesaj.get("metin") or "").strip()
    if metin.startswith("/start"):
        return None
    if MEVZUAT_DESEN.search(metin):
        return "dekan-sekreteri"
    if STAJ_DESEN.search(metin):
        return "staj-burosu"
    if MEMUR_DESEN.search(metin):
        return "memur"
    if mesaj.get("ek_turu") == "ses":
        return "postaci"
    if metin or mesaj.get("ek_turu"):
        return "dekan"
    return None


def kuyruk_maddesi(mesaj: dict, takim: str) -> tuple[str, str]:
    parcalar = [f"telegram {str(mesaj.get('zaman') or '')[:16]}"]
    if mesaj.get("dosya_adi"):
        parcalar.append(f"dosya: {mesaj['dosya_adi']}")
    notu = _temiz(mesaj.get("not") or mesaj.get("metin"))
    if notu:
        parcalar.append(f"not: {notu}")
    onek = KUYRUK_ONEKI.get(takim, "tg")
    return f"{onek}-{mesaj['update_id']}", " · ".join(parcalar)


def gelen_mesajlar(yollar):
    mesajlar = []
    for yol in yollar:
        try:
            mesajlar.append(json.loads(Path(yol).read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return mesajlar


def kuyruga_ekle(takim: str, madde_id: str, baslik: str, kok=None):
    durum = ayar.durum_oku(takim, kok)
    kuyruk = list(durum.get("kuyruk") or [])
    if any(m.get("id") == madde_id for m in kuyruk):
        return False
    kuyruk.append({"id": madde_id, "baslik": baslik, "durum": "bekliyor", "zaman": ayar.simdi_iso()})
    ayar.durum_guncelle(takim, {"kuyruk": kuyruk}, kok)
    return True


def tek_tur(kok, token, chat_id, bekleme=BEKLEME_SN, kosucu=None):
    son = int((ayar.durum_oku(TAKIM, kok).get("sayaclar") or {}).get("telegram_son_update", 0))
    try:
        guncellemeler = telegram_oku.guncellemeleri_cek(
            token, offset=son + 1 if son else None, bekleme=bekleme
        )
    except telegram_oku.TelegramHatasi as exc:
        _log(kok, f"{exc} (kod={exc.kod}) — tur atlandı")
        return []
    yazilan = telegram_oku.isle(kok, guncellemeler, chat_id)
    if not yazilan:
        return []
    hedefler = collections.OrderedDict()
    for mesaj in gelen_mesajlar(yazilan):
        hedef = takim_sec(mesaj)
        if not hedef:
            _log(kok, f"yoksayıldı update_id={mesaj.get('update_id')}")
            continue
        madde_id, notu = kuyruk_maddesi(mesaj, hedef)
        kuyruga_ekle(hedef, madde_id, notu, kok=kok)
        hedefler.setdefault(hedef, []).append(madde_id)
    if not hedefler:
        return []
    baslatilan = []
    for hedef, maddeler in hedefler.items():
        if not ayar.mesaide_mi():
            _log(kok, f"kuyruğa eklendi ({hedef}): {', '.join(maddeler)} — mesai dışı, koşu sabah")
            continue
        _log(kok, f"koşu başlıyor ({hedef}): {', '.join(maddeler)}")
        kod = (kosucu or _kos)(kok, hedef)
        _log(kok, f"koşu bitti ({hedef}): kod={kod}")
        if kod == 0:
            baslatilan.extend(maddeler)
    return baslatilan


def _kos(kok, takim):
    # E?er do?rudan h?zl? bir durum sorgusu geldiyse an?nda yan?t ?ret
    durum = ayar.durum_oku(takim, kok)
    kuyruk = durum.get("kuyruk") or []
    son_madde = kuyruk[-1] if kuyruk else {}
    baslik = (son_madde.get("baslik") or "").lower()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    ham_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and ham_id:
        chat_id = int(ham_id)
        # Staj sorgusu ise h?zl?ca Ki?isel Tablo durumunu d?nd?r
        if any(k in baslik for k in ["okunmayan", "okunmamis", "kac adet", "defter var", "yeni staj"]):
            try:
                import staj_senkron
                ozet = staj_senkron.kisisel_tablo_durum_listele()
                okunmamis_sayisi = len(ozet.get("okunmamis") or [])
                revize_sayisi = len(ozet.get("revize_bekleyen") or [])
                cevap = (
                    f"?? *Staj B?rosu Anl?k Durum Raporu*\n\n"
                    f"? *Okunmam?? Defter Say?s?:* `{okunmamis_sayisi}` adet\n"
                    f"? *Revize Bekleyen Defter Say?s?:* `{revize_sayisi}` adet\n"
                    f"? *Kaynak:* `{ozet.get('kaynak')}`\n\n"
                    f"?ncelemeye ba?lamak i?in *'?ncele'* veya *'Ba?la'* diyebilirsiniz."
                )
                telegram_oku.mesaj_gonder(token, chat_id, cevap)
            except Exception as e:
                _log(kok, f"H?zl? yan?t hatas?: {e}")

    sonuc = subprocess.run([sys.executable, str(Path(kok) / "bin" / "kos.py"), takim], cwd=str(kok))
    return sonuc.returncode


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ayar.ortam_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    ham_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not ham_id:
        return 0
    sir_ekle(token)
    chat_id = int(ham_id)
    if "--bir-kez" in argv:
        tek_tur(KOK, token, chat_id, bekleme=0)
        return 0
    _log(KOK, f"dinleyici başladı (varsayılan={TAKIM}, long-poll={BEKLEME_SN}sn)")
    son_posta_kontrol = 0.0
    try:
        while True:
            tek_tur(KOK, token, chat_id, bekleme=BEKLEME_SN)
            # Her 15 dakikada bir (900 sn) 0-token yeni e-posta kontrolü
            simdi = time.time()
            if ayar.mesaide_mi() and (simdi - son_posta_kontrol >= 900):
                son_posta_kontrol = simdi
                try:
                    subprocess.run(
                        [sys.executable, str(Path(KOK) / "bin" / "posta_cek.py"), "--son"],
                        cwd=str(KOK),
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                except Exception as e:
                    _log(KOK, f"periyodik eposta kontrol hatası: {e}")
            time.sleep(TUR_ARASI_SN)
    except KeyboardInterrupt:
        _log(KOK, "dinleyici durdu (SIGINT)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
