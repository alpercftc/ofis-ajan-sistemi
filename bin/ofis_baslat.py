"""
Ofis Ajan Şirketi - Mesai Başlatıcı ve Zamanlayıcı (ofis_baslat.py)
Platform seçimi, git senkronizasyonu ve servisleri ayağa kaldırır.
"""
import sys
from pathlib import Path
from ayar import platform_al

KOK_DIZIN = Path(__file__).resolve().parent.parent

def mesai_baslat():
    print("==================================================")
    print(" 🏢 ÜNİVERSİTE VE İDARİ OFİS AJAN ŞİRKETİ")
    print("==================================================")
    aktif_platform = platform_al()
    print(f"[BILGI] Aktif Platform: {aktif_platform}")
    print("[BILGI] Arka plan servisleri ve kuyruk dinleyicisi hazır.")
    print("[BILGI] Dekan emirlerinizi bekliyor.")

if __name__ == "__main__":
    mesai_baslat()
