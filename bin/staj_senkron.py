"""
Ofis Ajan Şirketi - Google Sheets Staj Senkronizasyon Aracı (staj_senkron.py)
Ortak genel tablo ile Alper'in kişisel takip tablosunu çapraz kontrol eder.
"""
import os
import sys
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent

def ortak_tablo_tara(ortak_sheet_id: str, yetkili_kisi: str = "Alper ÇİFTÇİ") -> list:
    """Ortak tablodan Alper ÇİFTÇİ'ye atanmış öğrencileri çeker."""
    print(f"[BILGI] Ortak tablo taranıyor: {ortak_sheet_id} (Yetkili: {yetkili_kisi})")
    # gspread veya CSV indirme mantığı
    return []

def kisisel_tabloya_aktar(kisisel_sheet_id: str, yeni_ogrenciler: list) -> int:
    """Yeni atanan öğrencileri kişisel takip tablosuna ekler."""
    print(f"[BILGI] Kişisel tablo güncelleniyor: {kisisel_sheet_id}")
    return len(yeni_ogrenciler)

if __name__ == "__main__":
    print("[BILGI] staj_senkron aracı hazır.")
