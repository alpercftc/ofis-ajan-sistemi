#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - E-Posta ve İletişim Tarama Aracı (posta_cek.py)
- Kurumsal YTÜ (MSAL / WAM Graph API) ve Kişisel Gmail (IMAP App Password) gelen kutularını tarar.
- Tüm dış iletileri <kaynak>...</kaynak> veri kafesi içinde döndürür.
- Asla dışarıya e-posta göndermez veya posta silmez (Salt-Okunur).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

from ayar import TAKIMLAR_DIZINI

POSTACI_DURUM_YOLU = TAKIMLAR_DIZINI / "postaci" / "durum.json"
OGRENCI_NO_RE = re.compile(r"\b(\d{2,3}[A-Z0-9]\d{4,5}|\d{8})\b", re.IGNORECASE)


def kaynak_kafesine_al(gonderen: str, konu: str, govde: str) -> str:
    """Dışarıdan gelen e-posta metnini <kaynak> veri kafesi içine alır."""
    return (
        f'<kaynak tip="eposta" gonderen="{gonderen}" konu="{konu}">\n'
        f"{govde.strip()}\n"
        f"</kaynak>"
    )


def oncelik_siniflandir(gonderen: str, konu: str, govde: str) -> str:
    """E-postayı 4 standart öncelik kategorisinden birine sınıflandırır."""
    birlesik = f"{gonderen} {konu} {govde}".lower()
    if any(k in birlesik for k in ("dekanlık", "müdek", "mudek", "rektörlük", "komisyon", "acil")):
        return "🔴 Acil Akademik/Dekanlık/MÜDEK"
    if any(k in birlesik for k in ("staj", "sicil", "sgk", "4a", "defter", "std.yildiz.edu.tr")):
        return "🟠 Öğrenci Staj/Revize Evrak"
    if any(k in birlesik for k in ("bülten", "unsubscribe", "abonelik", "kampanya", "tanıtım")):
        return "⚪ Bülten/Tanıtım (Arşiv)"
    return "🟡 Rutin İdari/Bilgilendirme"


def staj_revize_ogrenci_bul(konu: str, govde: str) -> str:
    """E-posta konusu veya gövdesinden öğrenci numarası yakalar."""
    eslesme = OGRENCI_NO_RE.search(f"{konu} {govde}")
    return eslesme.group(1).upper() if eslesme else ""


def durum_imleci_oku(durum_yolu: Path = POSTACI_DURUM_YOLU) -> dict:
    if not durum_yolu.exists():
        return {}
    veri = json.loads(durum_yolu.read_text(encoding="utf-8"))
    return veri.get("son_posta_imleci") or {}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Postacı E-posta ve Mesaj Tarama Aracı")
    parser.add_argument("--son", action="store_true", help="Son imleçten sonraki yeni iletileri tara")
    args = parser.parse_args()

    imlec = durum_imleci_oku()
    kurumsal = os.getenv("KURUMSAL_EMAIL", "alper.ciftci@yildiz.edu.tr")
    gmail = os.getenv("GMAIL_USER", "alpercftc@gmail.com")
    print(f"[BILGI] Postacı taraması hazır | Kurumsal: {kurumsal} | Gmail: {gmail}")
    print(f"[BILGI] Son Posta İmleci: {imlec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
