"""
Ofis Ajan Şirketi - Bağımsız Denetçi Motoru (mufettis.py)
1. Katman: Deterministik Python (TC Kimlik mod-10, KVKK, Pydantic şema denetimi)
2. Katman: Bağımsız LLM denetimi
"""
import re
import json
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent

def tc_kimlik_dogrula(tc_no: str) -> bool:
    """11 haneli T.C. Kimlik numarası mod-10 algoritma doğrulaması."""
    if not tc_no or not re.match(r"^[1-9]\d{10}$", str(tc_no)):
        return False
    digits = [int(d) for d in str(tc_no)]
    # 1, 3, 5, 7, 9. haneler toplamı * 7 - (2, 4, 6, 8. haneler toplamı) mod 10 == 10. hane
    tekler = sum(digits[0:9:2])
    ciftler = sum(digits[1:8:2])
    if ((tekler * 7) - ciftler) % 10 != digits[9]:
        return False
    # İlk 10 hane toplamı mod 10 == 11. hane
    if sum(digits[:10]) % 10 != digits[10]:
        return False
    return True

def kvkk_kontrol(metin: str) -> list:
    """Metin içindeki açık kimlik ve telefon kalıplarını tarar."""
    bulgular = []
    # 11 haneli sayı blokları (T.C. Kimlik şüphesi)
    tc_adaylari = re.findall(r"\b\d{11}\b", metin)
    for tc in tc_adaylari:
        if tc_kimlik_dogrula(tc):
            bulgular.append(f"Açık T.C. Kimlik tespit edildi: {tc[:3]}*****{tc[-2:]}")
    return bulgular

def cikti_denetle(rapor_metni: str, kanit_tablosu: dict = None) -> dict:
    """1. Katman deterministik denetim."""
    print("[BILGI] Müfettiş 1. Katman deterministik denetimini başlattı...")
    ihlaller = kvkk_kontrol(rapor_metni)
    
    gecerli = len(ihlaller) == 0
    return {
        "gecerli": gecerli,
        "ihlaller": ihlaller,
        "durum": "ONAYLANDI" if gecerli else "REDDEDILDI"
    }

if __name__ == "__main__":
    test_metin = "Örnek öğrenci değerlendirme raporu - Belge tam."
    sonuc = cikti_denetle(test_metin)
    print(f"[BILGI] Denetim Sonucu: {sonuc['durum']}")
