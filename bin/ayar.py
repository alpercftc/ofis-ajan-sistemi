"""
Ofis Ajan Şirketi - Yapılandırma ve Model Seviyesi Yöneticisi (ayar.py)
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

KOK_DIZIN = Path(__file__).resolve().parent.parent
load_dotenv(KOK_DIZIN / ".env")

def model_haritasi_oku() -> dict:
    harita_yolu = KOK_DIZIN / "sirket" / "model-haritasi.json"
    if not harita_yolu.exists():
        return {}
    with open(harita_yolu, "r", encoding="utf-8") as f:
        return json.load(f)

def platform_al() -> str:
    return os.getenv("VARSAYILAN_PLATFORM", "antigravity").lower()

def seviye_modeli_al(seviye: str, platform: str = None) -> str:
    if platform is None:
        platform = platform_al()
    harita = model_haritasi_oku()
    platform_haritasi = harita.get("platformlar", {}).get(platform, {})
    return platform_haritasi.get(seviye, "gemini-2.5-flash")

if __name__ == "__main__":
    aktif_platform = platform_al()
    print(f"[BILGI] Aktif Platform: {aktif_platform}")
    print(f"[BILGI] Yuksek Seviye Modeli: {seviye_modeli_al('yuksek', aktif_platform)}")
    print(f"[BILGI] Hizli Seviye Modeli: {seviye_modeli_al('hizli', aktif_platform)}")
