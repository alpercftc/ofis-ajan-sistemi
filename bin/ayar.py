"""
Ofis Ajan Şirketi - Yapılandırma ve Model Seviyesi Yöneticisi (ayar.py)
"""
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv

KOK_DIZIN = Path(__file__).resolve().parent.parent
KOK = KOK_DIZIN
TAKIMLAR_DIZINI = KOK_DIZIN / "takimlar"
SKILLS_DIZINI = KOK_DIZIN / "skills"
SIRKET_DIZINI = KOK_DIZIN / "sirket"
load_dotenv(KOK_DIZIN / ".env")


def frontmatter(metin: str) -> tuple[dict, str]:
    """Markdown YAML frontmatter'ını (dict, govde) olarak ayrıştırır."""
    if not metin.startswith("---"):
        return {}, metin
    parcalar = metin.split("---", 2)
    if len(parcalar) < 3:
        return {}, metin
    fm_ham, govde = parcalar[1], parcalar[2].lstrip("\r\n")
    fm = {}
    for satir in fm_ham.splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#") or ":" not in satir:
            continue
        anahtar, deger = satir.split(":", 1)
        anahtar = anahtar.strip()
        deger = deger.strip()
        if deger.startswith("[") and deger.endswith("]"):
            ic = deger[1:-1].strip()
            fm[anahtar] = [x.strip() for x in ic.split(",") if x.strip()] if ic else []
        else:
            fm[anahtar] = deger
    return fm, govde


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
    return platform_haritasi.get(seviye, "gemini-3.8-flash-medium")


if __name__ == "__main__":
    aktif_platform = platform_al()
    print(f"[BİLGİ] Aktif Platform: {aktif_platform}")
    print(f"[BİLGİ] Yüksek Seviye Modeli: {seviye_modeli_al('yuksek', aktif_platform)}")
    print(f"[BİLGİ] Hızlı Seviye Modeli: {seviye_modeli_al('hizli', aktif_platform)}")
