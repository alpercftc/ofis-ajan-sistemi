"""
Ofis Ajan Şirketi - Durum Dağıtıcısı (dagitici.py)
LLM çağırmayan saf Python durum makinesi; tamamlanan işleri sıradaki ajana devreder.
"""
import json
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent

AJANLAR = [
    "dekan",
    "dekan-sekreteri",
    "staj-burosu",
    "postaci",
    "memur",
    "ik-memuru",
    "bilgi-islem",
    "mufettis"
]

def kuyruk_tara():
    print("[BILGI] Dağıtıcı kuyruk taramasını başlattı...")
    tamamlanan_sayisi = 0

    for ajan in AJANLAR:
        durum_yolu = KOK_DIZIN / "takimlar" / ajan / "durum.json"
        if not durum_yolu.exists():
            continue
        try:
            with open(durum_yolu, "r", encoding="utf-8") as f:
                veri = json.load(f)
            # Tamamlanan işleri sonraki ajana aktarma kontrolü
            for g in veri.get("kuyruk", []):
                if g.get("durum") == "tamam" and not g.get("aktarildi"):
                    print(f"[BILGI] Aktarılacak iş bulundu: {ajan} -> {g.get('id')}")
                    g["aktarildi"] = True
                    tamamlanan_sayisi += 1
            with open(durum_yolu, "w", encoding="utf-8") as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[HATA] {ajan} durumu okunurken hata: {e}")

    print(f"[BILGI] Dağıtım döngüsü tamamlandı. Aktarılan iş adedi: {tamamlanan_sayisi}")

if __name__ == "__main__":
    kuyruk_tara()
