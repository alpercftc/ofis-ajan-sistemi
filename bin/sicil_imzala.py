#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Koordinatlı Sicil Fişi Doldurma ve İmzalama Aracı (sicil_imzala.py)
Dinamik çapa metin arama, üstü çizme, gün/tip ve şeffaf PNG imza basımı, OpenCV vesikalık kontrolü.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
import pymupdf as fitz

KOK_DIZIN = Path(__file__).resolve().parent.parent
SABLON_DIZINI = KOK_DIZIN / "sirket" / "sablonlar"
VARSAYILAN_HARITA = SABLON_DIZINI / "sicil-haritasi.json"
VARSAYILAN_IMZA = SABLON_DIZINI / "imza.png"


def harita_yukle(harita_yolu: Optional[Path] = None) -> dict:
    yol = Path(harita_yolu) if harita_yolu else VARSAYILAN_HARITA
    if not yol.exists():
        raise FileNotFoundError(f"Sicil haritası bulunamadı: {yol}")
    with open(yol, "r", encoding="utf-8") as f:
        return json.load(f)


def vesikalik_kontrol_et(sicil_pdf_yolu: str, harita_yolu: Optional[str] = None) -> Dict[str, object]:
    """
    OpenCV (cv2) ile Staj Sicil Fişi üzerindeki 1_fotograf bölgesini kırpar,
    parlaklık ve Laplacian varyansı (bulanıklık) kontrollerini yapar.
    """
    harita = harita_yukle(Path(harita_yolu) if harita_yolu else None)
    b_foto = harita["bolgeler"].get("1_fotograf", {})
    oranlar = b_foto.get("oranlar", [0.7307, 0.0725, 0.9474, 0.2827])

    doc = fitz.open(sicil_pdf_yolu)
    page = doc[0]
    w, h = page.rect.width, page.rect.height

    rect = fitz.Rect(oranlar[0] * w, oranlar[1] * h, oranlar[2] * w, oranlar[3] * h)
    pix = page.get_pixmap(clip=rect, dpi=150)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))

    if pix.n == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    elif pix.n == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img

    parlaklik = float(np.mean(gray))
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    kararmis = parlaklik < 40.0
    patlamis = parlaklik > 250.0
    bulanik = laplacian_var < 50.0

    gecerli = not (kararmis or patlamis or bulanik)
    uyarilar = []
    if kararmis:
        uyarilar.append("Fotoğraf çok karanlık/okunaksız")
    if patlamis:
        uyarilar.append("Fotoğraf aşırı parlak/boş olabilir")
    if bulanik:
        uyarilar.append("Fotoğraf bulanık")

    doc.close()
    return {
        "gecerli": gecerli,
        "parlaklik": round(parlaklik, 2),
        "netlik_skoru": round(laplacian_var, 2),
        "uyarilar": uyarilar,
        "durum": "GECERLI" if gecerli else "UYARI_FOTOGRAF_KUSURLU",
    }


def _alt_bolge_capalarini_bul(page) -> dict:
    """
    Sayfanın alt %25'lik kısmında (ÜNİVERSİTE TARAFINDAN DOLDURULACAKTIR bölümü)
    hem vektörel hem de bozuk OCR'lı taranmış PDF'lerde çalışan çapa koordinatlarını bulur.
    """
    w, h = page.rect.width, page.rect.height
    kelimeler = page.get_text("words")
    alt_kelimeler = [k for k in kelimeler if k[1] > h * 0.75]

    # 1) '/edilmemiştir' (veya bozuk OCR'da '/eollmemıŞtıt,' gibi '/' ile başlayan kelime)
    slash_rect = None
    for k in alt_kelimeler:
        metin = k[4].strip()
        if metin.startswith("/") and len(metin) >= 5:
            slash_rect = fitz.Rect(k[0], k[1], k[2], k[3])
            break

    if slash_rect is None:
        arama = page.search_for("edilmemiştir") or page.search_for("edilmem")
        alt_arama = [r for r in arama if r.y0 > h * 0.75]
        if alt_arama:
            slash_rect = alt_arama[0]

    # 2) 'TARAFINDAN' veya 'DOLDURULACAKTIR' başlık satırı (alt bölümdeki 2. TARAFINDAN)
    tarafindan_rect = None
    for k in alt_kelimeler:
        if "TARAFINDAN" in k[4].upper() or "DOLDURULACAKTIR" in k[4].upper():
            tarafindan_rect = fitz.Rect(k[0], k[1], k[2], k[3])
            break

    # 3) Karar satırı yüksekliği (y_satir)
    if slash_rect is not None:
        y_satir = slash_rect.y1 - 1.5
    elif tarafindan_rect is not None:
        y_satir = tarafindan_rect.y1 + 10.0
    else:
        y_satir = h * 0.832

    # 4) Vektörel PDF'te 'iş günü' varsa tam x koordinatını al, yoksa standart tablo oranını kullan
    is_gunu_arama = [r for r in (page.search_for("iş günü") or []) if r.y0 > h * 0.75]
    if is_gunu_arama:
        ig = is_gunu_arama[0]
        gun_pt = fitz.Point(ig.x0 - 20, y_satir)
        tur_pt = fitz.Point(ig.x1 + 14, y_satir)
    else:
        gun_pt = fitz.Point(w * 0.116, y_satir)
        tur_pt = fitz.Point(w * 0.205, y_satir)

    return {
        "gun_pt": gun_pt,
        "tur_pt": tur_pt,
        "slash_rect": slash_rect,
        "y_satir": y_satir,
    }


def sicil_imzala_ve_tamamla(
    ogrenci_no: str,
    kabul_gun: int,
    staj_tipi: str,
    sicil_pdf_yolu: str,
    cikti_pdf_yolu: Optional[str] = None,
    imza_png_yolu: Optional[str] = None,
    harita_yolu: Optional[str] = None,
) -> bool:
    """
    Onaylanan staj için sicil fişine PyMuPDF ile:
    1. 7_kabul_gun_ve_tur alanına gün ve staj türünü basar,
    2. 8_karar_cizgi alanında 'edilmemiştir' kelimesinin üstünü çizer,
    3. 9_komisyon_uyesi_imza alanına şeffaf PNG imzayı basar.
    """
    girdi_path = Path(sicil_pdf_yolu)
    if not girdi_path.exists():
        print(f"[HATA] Sicil PDF bulunamadı: {girdi_path}", file=sys.stderr)
        return False

    harita = harita_yukle(Path(harita_yolu) if harita_yolu else None)
    imza_path = Path(imza_png_yolu) if imza_png_yolu else VARSAYILAN_IMZA
    if not imza_path.exists():
        print(f"[HATA] İmza PNG bulunamadı: {imza_path}", file=sys.stderr)
        return False

    cikti_path = Path(cikti_pdf_yolu) if cikti_pdf_yolu else girdi_path.with_name(f"{girdi_path.stem}_imzali.pdf")
    cikti_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[BİLGİ] Sicil imzalama işlemi başlatıldı: {ogrenci_no} (Gün: {kabul_gun}, Tip: {staj_tipi})")

    doc = fitz.open(girdi_path)
    page = doc[0]
    w, h = page.rect.width, page.rect.height

    bolgeler = harita.get("bolgeler", {})
    b8 = bolgeler.get("8_karar_cizgi", {})
    b9 = bolgeler.get("9_komisyon_uyesi_imza", {})

    capalar = _alt_bolge_capalarini_bul(page)

    # 1. 7_kabul_gun_ve_tur: Gün ve Staj Türünü Yazma (Türkçe karakter destekli insert_htmlbox / helv)
    gun_pt = capalar["gun_pt"]
    tur_pt = capalar["tur_pt"]
    page.insert_text(gun_pt, str(kabul_gun), fontsize=10.5, fontname="helv", color=(0.0, 0.1, 0.65))
    tur_kutu = fitz.Rect(tur_pt.x, tur_pt.y - 11, tur_pt.x + 70, tur_pt.y + 4)
    page.insert_htmlbox(
        tur_kutu,
        f'<span style="font-family: sans-serif; font-size: 10pt; font-weight: bold; color: #001a99;">{staj_tipi}</span>',
    )

    # 2. 8_karar_cizgi: "edilmemiştir" Kelimesinin Üstünü Çizme
    if capalar["slash_rect"] is not None:
        sr = capalar["slash_rect"]
        mid_y = (sr.y0 + sr.y1) / 2.0
        p1 = fitz.Point(sr.x0 + 2, mid_y)
        p2 = fitz.Point(sr.x1, mid_y)
    else:
        c1 = b8.get("cizgi_baslangic_oran", [0.418, 0.830])
        c2 = b8.get("cizgi_bitis_oran", [0.488, 0.830])
        p1 = fitz.Point(c1[0] * w, c1[1] * h)
        p2 = fitz.Point(c2[0] * w, c2[1] * h)

    page.draw_line(p1, p2, color=(0.85, 0.0, 0.0), width=1.6)

    # 3. 9_komisyon_uyesi_imza: Şeffaf PNG İmzayı Yerleştirme (':' işaretlerinin sağına, +w_imza/2 = +37.5 pt kaydırılmış)
    imza_oran = b9.get("oranlar", [0.2450, 0.8530, 0.4340, 0.9268])
    imza_rect = fitz.Rect(imza_oran[0] * w, imza_oran[1] * h, imza_oran[2] * w, imza_oran[3] * h)

    komisyon_arama = (
        page.search_for("Komisyon Üyesi")
        or page.search_for("Komisyon yesi")
        or page.search_for("Öğretim Üyesi")
    )
    alt_komisyon = [r for r in komisyon_arama if r.y0 > h * 0.80 and r.x0 < w * 0.35]
    if alt_komisyon:
        k_rect = alt_komisyon[0]
        imza_rect = fitz.Rect(
            k_rect.x1 + 52.5,
            k_rect.y0 - 4,
            min(w * 0.52, k_rect.x1 + 202.5),
            min(h * 0.96, k_rect.y0 + 58),
        )

    page.insert_image(imza_rect, filename=str(imza_path), keep_proportion=True)

    doc.save(cikti_path)
    doc.close()

    print(f"[BİLGİ] İmzalı sicil fişi kaydedildi: {cikti_path}")
    return True


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Sicil Fişi İmzalama ve Doldurma Aracı")
    parser.add_argument("--ogrenci", type=str, required=True, help="Öğrenci Numarası")
    parser.add_argument("--gun", type=int, required=True, help="Kabul edilen gün sayısı")
    parser.add_argument("--tip", type=str, required=True, help="Staj Tipi (Atölye / Uzakyol)")
    parser.add_argument("--pdf", type=str, required=True, help="Girdi Sicil PDF yolu")
    parser.add_argument("--cikti", type=str, help="Çıktı İmzalı Sicil PDF yolu")
    parser.add_argument("--harita", type=str, help="Özel sicil haritası JSON yolu")
    parser.add_argument("--imza", type=str, help="Özel imza PNG yolu")
    parser.add_argument("--kontrol", action="store_true", help="Vesikalık kontrolünü çalıştır")
    args = parser.parse_args()

    if args.kontrol:
        sonuc = vesikalik_kontrol_et(args.pdf, args.harita)
        print(json.dumps(sonuc, indent=2, ensure_ascii=False))

    basarili = sicil_imzala_ve_tamamla(
        ogrenci_no=args.ogrenci,
        kabul_gun=args.gun,
        staj_tipi=args.tip,
        sicil_pdf_yolu=args.pdf,
        cikti_pdf_yolu=args.cikti,
        imza_png_yolu=args.imza,
        harita_yolu=args.harita,
    )
    return 0 if basarili else 1


if __name__ == "__main__":
    raise SystemExit(main())
