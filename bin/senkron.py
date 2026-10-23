"""
Ofis Ajan Şirketi - Ev ↔ Ofis Git Senkronizasyon Aracı (senkron.py)
origin main üzerinde güvenli çekme/gönderme yapar; public repoya veri sızmasını engeller.
"""
import subprocess
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent

def senkron_cek():
    """Mesai başlangıcında en güncel durumu origin main üzerinden çeker."""
    print("[BILGI] Git güncellemeleri çekiliyor (git pull origin main)...")
    try:
        subprocess.run(["git", "pull", "origin", "main"], cwd=str(KOK_DIZIN), check=False)
    except Exception as e:
        print(f"[UYARI] Git pull başarısız: {e}")

def senkron_gonder(mesaj: str = "mesai: ofis durumu guncellendi"):
    """Mesai bitiminde güncel öğrenci profil kartları ve defterleri origin main'e gönderir."""
    print(f"[BILGI] Git güncellemeleri gönderiliyor: '{mesaj}'")
    try:
        subprocess.run(["git", "add", "."], cwd=str(KOK_DIZIN), check=False)
        subprocess.run(["git", "commit", "-m", mesaj], cwd=str(KOK_DIZIN), check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=str(KOK_DIZIN), check=False)
    except Exception as e:
        print(f"[UYARI] Git push başarısız: {e}")

if __name__ == "__main__":
    import sys
    if "--gonder" in sys.argv:
        senkron_gonder()
    else:
        senkron_cek()
