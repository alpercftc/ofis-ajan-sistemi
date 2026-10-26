#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram dinleyici ve Dekan muhatap servisi (telegram_dinle.py).

ANAYASA Kuralı: Alper'in tek muhatabı Dekan'dır.
1. Alper Telegram'dan yazdığı anda doğrudan Dekan yanıt üretir.
2. Mesaj Dekan kuyruğuna alınır ve alt birimlere iş emri dağıtılır.
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
import ayar
import telegram_oku
import staj_senkron

KOK = ayar.KOK
TAKIM = "postaci"

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
    print(f"[BILGI] {damga} | {satir}", flush=True)
    yol = Path(kok) / "sirket-log" / LOG_ADI
    try:
        yol.parent.mkdir(parents=True, exist_ok=True)
        with open(yol, "a", encoding="utf-8") as dosya:
            dosya.write(f"[BILGI] {damga} | {satir}\n")
    except OSError:
        pass


def _temiz(metin, sinir=NOT_SINIRI):
    tek_satir = " ".join(str(metin or "").split())
    return tek_satir[:sinir] + ("..." if len(tek_satir) > sinir else "")


def kuyruga_ekle(takim: str, madde_id: str, baslik: str, kok=None):
    durum = ayar.durum_oku(takim, kok)
    kuyruk = list(durum.get("kuyruk") or [])
    if any(m.get("id") == madde_id for m in kuyruk):
        return False
    kuyruk.append({"id": madde_id, "baslik": baslik, "durum": "bekliyor", "zaman": ayar.simdi_iso()})
    ayar.durum_guncelle(takim, {"kuyruk": kuyruk}, kok)
    return True


def dekan_yaniti_uret(metin: str) -> str:
    """Alper'in mesajına Dekan olarak kurumsal ve anlık yanıt üretir."""
    m = (metin or "").lower()

    if any(k in m for k in ["staj", "defter", "kac adet", "okunmayan", "revize", "listele", "atanan"]):
        try:
            ozet = staj_senkron.kisisel_tablo_durum_listele()
            okunmayan = ozet.get("okunmamis") or []
            revize = ozet.get("revize_bekleyen") or []

            satirlar = [
                "🏛️ *Dekanlık — Staj Durum Raporu*",
                "",
                "Alper Bey, Kişisel Tablonuz (`Atölye` sekmesi) tam dökümü:",
                "",
                f"🟡 *REVİZYON BEKLEYENLER ({len(revize)} Adet):*"
            ]
            for r in revize:
                satirlar.append(f"• *{r.get('ogrenci_no')}* - {r.get('ad_soyad')} | Not: _{r.get('not_metni')}_")

            satirlar.append("")
            satirlar.append(f"⚪ *OKUNMAYAN DEFTERLER ({len(okunmayan)} Adet):*")
            for o in okunmayan:
                satirlar.append(f"• Satır {o.get('satir')}: *{o.get('ogrenci_no')}* - {o.get('ad_soyad')}")

            satirlar.append("")
            satirlar.append("İncelemeyi başlatmak için *'<ÖğrenciNo> İncele'* veya *'Başla'* emri verebilirsiniz.")
            return "\n".join(satirlar)
        except Exception as e:
            return f"🏛️ *Dekanlık:* Staj tablosu sorgulanırken hata oluştu: {e}"

    if any(k in m for k in ["güncelle", "guncelle", "senkron", "tekrar kontrol"]):
        try:
            res = staj_senkron.senkron_kontrol()
            yeni = len(res.get("yeni_eklenenler") or [])
            return f"🏛️ *Dekanlık:* Ortak tablo kontrol edildi. Üzerinize atanan yeni defter sayısı: `{yeni}`."
        except Exception as e:
            return f"🏛️ *Dekanlık:* Senkronizasyon hatası: {e}"

    return (
        f"🏛️ *Dekanlık:* Emriniz alındı Alper Bey: \"{metin}\".\n"
        f"Gerekli iş planı ve birim koordinasyonu yapılıyor."
    )


def tek_tur(kok, token, chat_id, bekleme=BEKLEME_SN):
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

    for yol in yazilan:
        try:
            mesaj = json.loads(Path(yol).read_text(encoding="utf-8"))
        except Exception:
            continue

        metin = mesaj.get("metin") or mesaj.get("not") or ""
        update_id = mesaj.get("update_id")
        _log(kok, f"Yeni mesaj: {update_id} -> Dekan devraldı: {metin}")

        # 1. Anında Alper'e Dekan olarak yanıt gönder
        try:
            yanit = dekan_yaniti_uret(metin)
            telegram_oku.mesaj_gonder(token, chat_id, yanit)
        except Exception as e:
            _log(kok, f"Dekan yanıt gönderim hatası: {e}")

        # 2. Kuyruğa Dekan maddesi olarak ekle
        madde_id = f"dkn-{update_id}"
        kuyruga_ekle("dekan", madde_id, f"telegram: {metin}", kok=kok)

        # 3. İlgili alt birim varsa onun kuyruğuna da iş emri bırak
        if re.search(r"(staj|defter|sicil)", metin, re.IGNORECASE):
            kuyruga_ekle("staj-burosu", f"staj-{update_id}", f"dekan emri: {metin}", kok=kok)
        elif re.search(r"(yönerge|yonerge|mevzuat|kılavuz|kilavuz)", metin, re.IGNORECASE):
            kuyruga_ekle("dekan-sekreteri", f"sek-{update_id}", f"dekan emri: {metin}", kok=kok)
        elif re.search(r"(müdek|mudek|komisyon|tutanak)", metin, re.IGNORECASE):
            kuyruga_ekle("memur", f"mmr-{update_id}", f"dekan emri: {metin}", kok=kok)

    return yazilan


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
    _log(KOK, f"dinleyici başladı (Dekan muhatap, long-poll={BEKLEME_SN}sn)")
    son_posta_kontrol = 0.0
    try:
        while True:
            tek_tur(KOK, token, chat_id, bekleme=BEKLEME_SN)
            # 15 dakikada bir e-posta kontrolü
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
