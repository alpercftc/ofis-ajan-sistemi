#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Kaotik ZIP, Staj Evrakı ve İki Modlu Mevzuat/Kılavuz Ön-İşleme Aracı (evrak_hazirla.py)
1. Öğrenci ZIP paketlerini açar ve deterministik ön rapor (hazir_paket.md / on_rapor.json) üretir.
2. Mevzuat ve denetim kılavuzlarını iki modlu olarak ayrıştırır:
   - --mod tekil (Varsayılan): Tek bir kural .md dosyası üretir.
   - --mod bolumlu: Dokümanı bölümlere (bolum-01-..., bolum-02-...) ayırır ve
     token tasarruflu referans indeks dosyası (index_<dokuman_adi>.md) oluşturur.
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List

from ayar import KOK_DIZIN, SIRKET_DIZINI

MEVZUAT_DIZINI = SIRKET_DIZINI / "mevzuat"


def _slug_uret(metin: str) -> str:
    tr_harita = str.maketrans("çğıöşüÇĞİÖŞÜ ", "cgiosuCGIOSU-")
    temiz = metin.translate(tr_harita).lower()
    temiz = re.sub(r"[^a-z0-9-]+", "-", temiz)
    return re.sub(r"-+", "-", temiz).strip("-") or "bolum"


def zip_ayikla_ve_paketle(zip_yolu: str, hedef_dizin: str) -> dict:
    """Kaotik ZIP dosyasını açar ve içeriği tespit eder."""
    zip_path = Path(zip_yolu)
    hedef_path = Path(hedef_dizin)
    hedef_path.mkdir(parents=True, exist_ok=True)

    print(f"[BILGI] ZIP paketi açılıyor: {zip_path.name}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(hedef_path)

    bulunan_dosyalar = [f.name for f in hedef_path.iterdir() if f.is_file()]
    print(f"[BILGI] Çıkarılan dosya adedi: {len(bulunan_dosyalar)}")

    paket_md_yolu = hedef_path / "hazir_paket.md"
    with open(paket_md_yolu, "w", encoding="utf-8") as f:
        f.write(
            f"# Evrak Ön-İşleme Standart Paketi\n\n"
            f"Kaynak ZIP: {zip_path.name}\n\n## Tespit Edilen Belgeler\n"
        )
        for dosya in bulunan_dosyalar:
            f.write(f"- {dosya}\n")

    return {
        "durum": "TAMAMLANDI",
        "dosyalar": bulunan_dosyalar,
        "paket_md": str(paket_md_yolu),
    }


def metni_bolumlere_ayir_ve_indeksle(
    dokuman_adi: str, ham_metin: str, hedef_kok: Path = MEVZUAT_DIZINI
) -> Dict[str, object]:
    """
    Çok bölümlü kılavuz metnini (# / ## / BÖLÜM / ÖLÇÜT / CHAPTER başlıklarına göre)
    ayrı .md dosyalarına böler ve index_<dokuman_adi>.md referans indeksini oluşturur.
    """
    dokuman_slug = _slug_uret(dokuman_adi)
    hedef_klasor = hedef_kok / dokuman_slug
    hedef_klasor.mkdir(parents=True, exist_ok=True)

    baslik_re = re.compile(
        r"^(?:#{1,2}\s+|(?:BÖLÜM|BOLUM|ÖLÇÜT|OLCUT|CHAPTER)\s+\d+[\s:.-]*)(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )
    eslesmeler = list(baslik_re.finditer(ham_metin))

    bolumler: List[Dict[str, str]] = []
    if not eslesmeler:
        eslesmeler_veri = [("Genel Kapsam", ham_metin.strip())]
    else:
        eslesmeler_veri = []
        for idx, m in enumerate(eslesmeler):
            baslik = m.group(1).strip()
            baslangic = m.start()
            bitis = eslesmeler[idx + 1].start() if idx + 1 < len(eslesmeler) else len(ham_metin)
            icerik = ham_metin[baslangic:bitis].strip()
            eslesmeler_veri.append((baslik, icerik))

    for sira, (baslik, icerik) in enumerate(eslesmeler_veri, start=1):
        bolum_slug = _slug_uret(baslik)[:40]
        dosya_adi = f"bolum-{sira:02d}-{bolum_slug}.md"
        dosya_yolu = hedef_klasor / dosya_adi
        dosya_yolu.write_text(
            f"# Bölüm {sira:02d}: {baslik}\n\n{icerik}\n",
            encoding="utf-8",
        )
        # Anahtar kelimeleri özetle (en az 4 harfli anlamlı kelimelerden ilk 8 tanesi)
        kelimeler = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]{4,}", icerik.lower())
        essiz_kelimeler = []
        for k in kelimeler:
            if k not in essiz_kelimeler:
                essiz_kelimeler.append(k)
            if len(essiz_kelimeler) >= 8:
                break

        bolumler.append(
            {
                "sira": f"Bölüm {sira:02d}",
                "baslik": baslik,
                "dosya_adi": dosya_adi,
                "goreceli_yol": f"sirket/mevzuat/{dokuman_slug}/{dosya_adi}",
                "anahtar_kavramlar": ", ".join(essiz_kelimeler) or baslik,
            }
        )

    index_yolu = hedef_klasor / f"index_{dokuman_slug}.md"
    satirlar = [
        f"# İndeks — {dokuman_adi}",
        "",
        "> **Token Tasarrufu Kuralı:** Bu kılavuzda arama veya kural kontrolü yaparken tüm bölüm dosyalarını okumayın. Önce bu indeks tablosundan aradığınız konunun hangi bölümde olduğunu bulun, ardından yalnızca ilgili `bolum-XX-*.md` dosyasını okuyun.",
        "",
        "| Bölüm & Alt Başlıklar | Dosya Adresi | Aranan Bilgi & Anahtar Kavramlar | Sayfa Aralığı | İlgili Bölümler |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for b in bolumler:
        satirlar.append(
            f"| **{b['sira']}: {b['baslik']}** | `{b['goreceli_yol']}` | {b['anahtar_kavramlar']} | Belge içi | - |"
        )

    index_yolu.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return {
        "mod": "bolumlu",
        "index_dosyasi": str(index_yolu),
        "bolum_sayisi": len(bolumler),
        "bolumler": bolumler,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Evrak ve Mevzuat Ön-İşleme Aracı")
    parser.add_argument("--zip", type=str, help="Açılacak öğrenci ZIP dosyası")
    parser.add_argument("--hedef", type=str, help="Çıktı hedef klasörü")
    parser.add_argument("--mevzuat", type=str, help="İşlenecek mevzuat/kılavuz dosyası")
    parser.add_argument(
        "--mod",
        choices=["tekil", "bolumlu"],
        default="tekil",
        help="Derleme modu: tekil (varsayılan kural dosyası) veya bolumlu (index_<dokuman>.md + bölümler)",
    )
    args = parser.parse_args()

    if args.zip and args.hedef:
        zip_ayikla_ve_paketle(args.zip, args.hedef)
        return 0

    if args.mevzuat:
        kaynak = Path(args.mevzuat)
        if not kaynak.exists():
            print(f"[HATA] Dosya bulunamadı: {kaynak}", file=sys.stderr)
            return 1
        metin = kaynak.read_text(encoding="utf-8", errors="ignore")
        if args.mod == "bolumlu":
            sonuc = metni_bolumlere_ayir_ve_indeksle(kaynak.stem, metin)
            print(
                f"[BILGI] Bölümlü kılavuz oluşturuldu: {sonuc['index_dosyasi']} "
                f"({sonuc['bolum_sayisi']} bölüm)"
            )
        else:
            hedef_md = MEVZUAT_DIZINI / f"{_slug_uret(kaynak.stem)}.md"
            hedef_md.write_text(metin, encoding="utf-8")
            print(f"[BILGI] Tekil kural dosyası oluşturuldu: {hedef_md}")
        return 0

    print("[BILGI] evrak_hazirla aracı hazır (Modlar: --zip, --mevzuat --mod tekil|bolumlu).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
