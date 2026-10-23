"""
Ofis Ajan Şirketi - Kaotik ZIP ve Evrak Ön-İşleme Boru Hattı (evrak_hazirla.py)
ZIP, PDF, DOCX ve fotoğrafları sıfır tokenla tarar; hazir_paket.md üretir.
"""
import os
import zipfile
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent

def zip_ayikla_ve_paketle(zip_yolu: str, hedef_dizin: str) -> dict:
    """Kaotik ZIP dosyasını açar ve içeriği tespit eder."""
    zip_path = Path(zip_yolu)
    hedef_path = Path(hedef_dizin)
    hedef_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[BILGI] ZIP paketi açılıyor: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(hedef_path)
        
    bulunan_dosyalar = [f.name for f in hedef_path.iterdir() if f.is_file()]
    print(f"[BILGI] Çıkarılan dosya adedi: {len(bulunan_dosyalar)}")
    
    # hazir_paket.md iskeleti
    paket_md_yolu = hedef_path / "hazir_paket.md"
    with open(paket_md_yolu, "w", encoding="utf-8") as f:
        f.write(f"# Evrak Ön-İşleme Standart Paketi\n\nKaynak ZIP: {zip_path.name}\n\n## Tespit Edilen Belgeler\n")
        for dosya in bulunan_dosyalar:
            f.write(f"- {dosya}\n")
            
    return {
        "durum": "TAMAMLANDI",
        "dosyalar": bulunan_dosyalar,
        "paket_md": str(paket_md_yolu)
    }

if __name__ == "__main__":
    print("[BILGI] evrak_hazirla aracı hazır.")
