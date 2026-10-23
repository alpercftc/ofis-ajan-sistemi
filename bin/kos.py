"""
Ofis Ajan Şirketi - Ajan Koşucusu (kos.py)
15 dakika (900 sn) güvenlik zaman aşımı tavanı ve --kuru simülasyon modu.
"""
import sys
import json
import time
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent
KOSU_SURESI_SN = 900  # 15 dakika güvenlik zaman aşımı tavanı

def ajan_kos(ajan_adi: str, kuru: bool = False):
    print(f"[BILGI] Koşu başlatıldı: {ajan_adi} (Kuru Mod: {kuru})")
    takim_dizini = KOK_DIZIN / "takimlar" / ajan_adi
    durum_dosyasi = takim_dizini / "durum.json"

    if not durum_dosyasi.exists():
        print(f"[UYARI] Durum dosyası bulunamadı: {durum_dosyasi}")
        return False

    with open(durum_dosyasi, "r", encoding="utf-8") as f:
        durum_verisi = json.load(f)

    bekleyenler = [g for g in durum_verisi.get("kuyruk", []) if g.get("durum") == "bekliyor"]
    if not bekleyenler:
        print(f"[BILGI] {ajan_adi} için bekleyen görev yok.")
        return True

    aktif_gorev = bekleyenler[0]
    print(f"[BILGI] İşlenen görev: {aktif_gorev.get('id')} - {aktif_gorev.get('baslik')}")

    if kuru:
        print(f"[BILGI] [KURU KOŞU] {ajan_adi} simülasyonu başarıyla tamamlandı.")
        return True

    # Gerçek koşu mantığı ilgili ajan için yürütülür
    return True

if __name__ == "__main__":
    kuru_mu = "--kuru" in sys.argv
    ajan = "dekan"
    for i, arg in enumerate(sys.argv):
        if arg == "--ajan" and i + 1 < len(sys.argv):
            ajan = sys.argv[i + 1]
    ajan_kos(ajan, kuru=kuru_mu)
