#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Google Sheets / Excel Staj Senkronizasyon Aracı (staj_senkron.py)
- Yalnızca Kişisel Tablonun 'Atölye' sekmesini baz alır (Uzakyol taranmaz).
- takimlar/staj-burosu/durum.json içindeki 'tarama_imleci' ile son öğrenci/zaman damgasını tutar.
- Ortak tabloda yalnızca son imleçten sonraki yeni satırları tarar ve yeni atananları anında Kişisel Tablonun ('Atölye') sonuna boyasız olarak ekler.
- Okunmamış (boyasız + Not boş) ve Revize (boyasız + Not dolu) sorgularını doğrudan Kişisel Tablodan yanıtlar.
- Onaylanan satırı yeşile boyar, revize verilen satırın A (Not) sütununa açıklama yazar.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from ayar import KOK_DIZIN, TAKIMLAR_DIZINI

STAJ_DURUM_YOLU = TAKIMLAR_DIZINI / "staj-burosu" / "durum.json"
AKTIF_SEKME = "Atölye"
YETKILI_KISI = "Alper ÇİFTÇİ"
ORTAK_SHEET_ID = os.getenv("ORTAK_SHEET_ID", "")
KISISEL_SHEET_ID = os.getenv("KISISEL_SHEET_ID", "")
VARSAYILAN_YEREL_XLSX = Path(
    r"C:\Users\alper\OneDrive - Yildiz Technical University\Staj Defterleri\Staj_Defterlerim.xlsx"
)


def _online_xlsx_indir(sheet_id: str):
    """Google Sheets/Drive üzerindeki tabloyu online olarak (export=xlsx) bellek içine çeker."""
    import io
    import urllib.request
    import openpyxl

    for url in (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx",
        f"https://drive.google.com/uc?export=download&id={sheet_id}",
    ):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                veri = resp.read()
            if veri[:2] == b"PK":  # Geçerli ZIP/XLSX başlığı
                return openpyxl.load_workbook(io.BytesIO(veri))
        except Exception:
            continue
    return None


def durum_oku(durum_yolu: Path = STAJ_DURUM_YOLU) -> dict:
    if not durum_yolu.exists():
        return {"takim": "staj-burosu", "tarama_imleci": {}, "kuyruk": []}
    return json.loads(durum_yolu.read_text(encoding="utf-8"))


def durum_yaz(veri: dict, durum_yolu: Path = STAJ_DURUM_YOLU) -> None:
    durum_yolu.parent.mkdir(parents=True, exist_ok=True)
    durum_yolu.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tarama_imleci_oku(durum_yolu: Path = STAJ_DURUM_YOLU) -> dict:
    veri = durum_oku(durum_yolu)
    return veri.get("tarama_imleci") or {}


def tarama_imleci_guncelle(
    son_ogrenci_no: str,
    son_ogrenci_ad: str,
    son_zaman_damgasi: str,
    kisisel_tablo_son_satir: Optional[int] = None,
    ortak_tablo_son_satir: Optional[int] = None,
    durum_yolu: Path = STAJ_DURUM_YOLU,
) -> dict:
    veri = durum_oku(durum_yolu)
    imlec = veri.get("tarama_imleci") or {}
    imlec.update(
        {
            "aktif_sekme": AKTIF_SEKME,
            "son_ogrenci_no": str(son_ogrenci_no).strip(),
            "son_ogrenci_ad": str(son_ogrenci_ad).strip(),
            "son_zaman_damgasi": str(son_zaman_damgasi).strip(),
        }
    )
    if kisisel_tablo_son_satir is not None:
        imlec["kisisel_tablo_son_satir"] = int(kisisel_tablo_son_satir)
    if ortak_tablo_son_satir is not None:
        imlec["ortak_tablo_son_satir"] = int(ortak_tablo_son_satir)
    veri["tarama_imleci"] = imlec
    durum_yaz(veri, durum_yolu)
    return imlec


def _hucre_boyali_mi(cell) -> bool:
    """Hücrenin yeşil/dolgulu (onaylanmış) olup olmadığını kontrol eder."""
    fill = getattr(cell, "fill", None)
    if not fill or fill.fill_type != "solid":
        return False
    fg = getattr(fill, "start_color", None)
    if not fg:
        return False
    if getattr(fg, "theme", None) is not None and isinstance(fg.theme, int):
        return True
    rgb = getattr(fg, "rgb", None)
    if isinstance(rgb, str) and rgb not in ("00000000", "FFFFFFFF", "FFFFFF"):
        return True
    return False


def _guvenli_xlsx_oku(xlsx_yolu: Path):
    """Excel'de açık kilitli dosyaları da FILE_SHARE_READ|WRITE ile bellek üzerinden okur."""
    import io
    import openpyxl

    try:
        return openpyxl.load_workbook(xlsx_yolu)
    except PermissionError:
        import win32con
        import win32file

        handle = win32file.CreateFile(
            str(xlsx_yolu),
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        try:
            _, veri = win32file.ReadFile(handle, os.path.getsize(xlsx_yolu))
        finally:
            win32file.CloseHandle(handle)
        return openpyxl.load_workbook(io.BytesIO(veri))


def kisisel_tablo_durum_listele(
    sheet_id: Optional[str] = None, xlsx_yolu: Path = VARSAYILAN_YEREL_XLSX
) -> Dict[str, List[dict]]:
    """
    Ortak tabloya gitmeden doğrudan Kişisel Tablonun (öncelikle KISISEL_SHEET_ID üzerinden online,
    erişilemezse yerel yedekten) 'Atölye' sekmesindeki okunmamış ve revize bekleyen satırları döner.
    """
    sonuc = {"kaynak": None, "okunmamis": [], "revize_bekleyen": [], "son_satir": None}
    hedef_id = sheet_id or KISISEL_SHEET_ID
    wb = None
    if hedef_id:
        wb = _online_xlsx_indir(hedef_id)
        if wb is not None:
            sonuc["kaynak"] = f"online:{hedef_id}"

    if wb is None:
        if not xlsx_yolu.exists():
            return sonuc
        wb = _guvenli_xlsx_oku(xlsx_yolu)
        sonuc["kaynak"] = f"yerel:{xlsx_yolu.name}"

    if AKTIF_SEKME not in wb.sheetnames:
        return sonuc
    ws = wb[AKTIF_SEKME]

    for r in range(2, ws.max_row + 1):
        ogr_no = ws.cell(r, 5).value
        ad_soyad = ws.cell(r, 7).value
        if not ogr_no and not ad_soyad:
            continue
        not_degeri = ws.cell(r, 1).value
        zaman_damgasi = ws.cell(r, 3).value
        drive_link = ws.cell(r, 9).value
        boyali = _hucre_boyali_mi(ws.cell(r, 5))

        kayit = {
            "satir": r,
            "ogrenci_no": str(ogr_no or "").strip(),
            "ad_soyad": str(ad_soyad or "").strip(),
            "zaman_damgasi": str(zaman_damgasi or "").strip(),
            "not": str(not_degeri or "").strip(),
            "drive_link": str(drive_link or "").strip(),
            "onayli_boyali": boyali,
        }
        sonuc["son_satir"] = kayit
        if not boyali:
            if kayit["not"]:
                sonuc["revize_bekleyen"].append(kayit)
            else:
                sonuc["okunmamis"].append(kayit)

    return sonuc


def ortak_tablodan_yeni_atananlari_suz(
    ortak_satirlar: List[dict], imlec: dict, yetkili_kisi: str = YETKILI_KISI
) -> List[dict]:
    """
    Ortak tablodaki satırlardan yalnızca tarama_imleci'ndeki son öğrenci/zaman damgasından
    sonra gelen ve Alper ÇİFTÇİ'ye atanmış Atölye stajlarını süzer.
    """
    son_no = (imlec.get("son_ogrenci_no") or "").strip()
    son_zaman = (imlec.get("son_zaman_damgasi") or "").strip()

    imlec_bulundu = not bool(son_no or son_zaman)
    yeni_liste = []

    for satir in ortak_satirlar:
        ogr_no = str(satir.get("ogrenci_no", "")).strip()
        zaman = str(satir.get("zaman_damgasi", "")).strip()
        yetkili = str(satir.get("yetkili", "")).strip()

        if not imlec_bulundu:
            if (son_no and ogr_no == son_no) and (not son_zaman or zaman == son_zaman):
                imlec_bulundu = True
            elif son_zaman and zaman > son_zaman:
                imlec_bulundu = True
                if yetkili == yetkili_kisi:
                    yeni_liste.append(satir)
            continue

        if yetkili == yetkili_kisi:
            yeni_liste.append(satir)

    return yeni_liste


def kisisel_tablo_not_yaz(
    ogrenci_no: str, revize_notu: str, xlsx_yolu: Path = VARSAYILAN_YEREL_XLSX
) -> bool:
    """Kişisel Tablonun Atölye sekmesinde ilgili öğrencinin A (Not) sütununa revize notu yazar."""
    if not xlsx_yolu.exists():
        return False
    import openpyxl
    import shutil
    import tempfile

    try:
        wb = openpyxl.load_workbook(xlsx_yolu)
    except PermissionError:
        # Dosya Excel'de açıksa geçici kopya üzerinden oku
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            shutil.copy2(xlsx_yolu, tmp_path)
        except PermissionError:
            import subprocess
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Copy-Item -LiteralPath '{xlsx_yolu}' -Destination '{tmp_path}' -Force"],
                check=False,
            )
        wb = openpyxl.load_workbook(tmp_path)
        tmp_path.unlink(missing_ok=True)
    ws = wb[AKTIF_SEKME]
    hedef_satir = None
    for r in range(ws.max_row, 1, -1):
        if str(ws.cell(r, 5).value or "").strip() == str(ogrenci_no).strip():
            hedef_satir = r
            break
    if hedef_satir is None:
        return False
    ws.cell(hedef_satir, 1).value = revize_notu
    wb.save(xlsx_yolu)
    return True


def kisisel_tablo_onayla_yesil_boya(
    ogrenci_no: str, xlsx_yolu: Path = VARSAYILAN_YEREL_XLSX
) -> bool:
    """Onaylanan öğrencinin Kişisel Tablo (Atölye) satırını yeşile boyar."""
    if not xlsx_yolu.exists():
        return False
    import openpyxl
    from openpyxl.styles import PatternFill

    wb = openpyxl.load_workbook(xlsx_yolu)
    ws = wb[AKTIF_SEKME]
    hedef_satir = None
    for r in range(ws.max_row, 1, -1):
        if str(ws.cell(r, 5).value or "").strip() == str(ogrenci_no).strip():
            hedef_satir = r
            break
    if hedef_satir is None:
        return False

    yesil_dolgu = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")
    for col in range(1, 10):
        ws.cell(hedef_satir, col).fill = yesil_dolgu
    wb.save(xlsx_yolu)
    return True


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Staj Tablo Senkronizasyon ve Sorgu Aracı")
    parser.add_argument("--senkron", action="store_true", help="İmleci kontrol et ve durumu listele")
    parser.add_argument("--listele", action="store_true", help="Kişisel tablodan okunmamış ve revize defterleri listele")
    parser.add_argument("--not-yaz", action="store_true", help="Öğrenci satırına revize notu yaz")
    parser.add_argument("--onayla", action="store_true", help="Öğrenci satırını yeşile boya")
    parser.add_argument("--ogrenci", type=str, help="Öğrenci numarası")
    parser.add_argument("--not-metni", type=str, default="", help="Yazılacak revize/eksik evrak notu")
    args = parser.parse_args()

    if args.not_yaz and args.ogrenci:
        ok = kisisel_tablo_not_yaz(args.ogrenci, args.not_metni)
        print(f"[BILGI] Revize notu yazıldı ({args.ogrenci}): {ok}")
        return 0 if ok else 1

    if args.onayla and args.ogrenci:
        ok = kisisel_tablo_onayla_yesil_boya(args.ogrenci)
        print(f"[BILGI] Satır yeşile boyandı ({args.ogrenci}): {ok}")
        return 0 if ok else 1

    durum_ozeti = kisisel_tablo_durum_listele()
    imlec = tarama_imleci_oku()
    if not imlec.get("son_ogrenci_no") and durum_ozeti.get("son_satir"):
        son = durum_ozeti["son_satir"]
        imlec = tarama_imleci_guncelle(
            son["ogrenci_no"],
            son["ad_soyad"],
            son["zaman_damgasi"],
            kisisel_tablo_son_satir=son["satir"],
        )

    print(f"[BILGI] Kaynak: {durum_ozeti.get('kaynak')} | Aktif Sekme: {AKTIF_SEKME}")
    print(
        f"[BILGI] Son İmleç: {imlec.get('son_ogrenci_no')} - "
        f"{imlec.get('son_ogrenci_ad')} ({imlec.get('son_zaman_damgasi')})"
    )
    print(f"[BILGI] Okunmamış (Boyasız, Not Boş) Defter Sayısı: {len(durum_ozeti['okunmamis'])}")
    for o in durum_ozeti["okunmamis"]:
        print(f"  - [OKUNMADI] Satır {o['satir']}: {o['ogrenci_no']} | {o['ad_soyad']}")

    print(f"[BILGI] Revize Bekleyen (Boyasız, Not Dolu) Defter Sayısı: {len(durum_ozeti['revize_bekleyen'])}")
    for r in durum_ozeti["revize_bekleyen"]:
        print(f"  - [REVİZE]   Satır {r['satir']}: {r['ogrenci_no']} | {r['ad_soyad']} -> Not: {r['not']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
