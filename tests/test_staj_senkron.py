import tempfile
import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

from staj_senkron import (
    ortak_tablodan_yeni_atananlari_suz,
    tarama_imleci_guncelle,
    tarama_imleci_oku,
)


class TestStajSenkron(unittest.TestCase):
    def test_tarama_imleci_yaz_oku(self):
        with tempfile.TemporaryDirectory() as tmp:
            durum_yolu = Path(tmp) / "durum.json"
            tarama_imleci_guncelle(
                "200A3609",
                "SONER ŞENGÜL",
                "2026-09-11 20:00:57",
                kisisel_tablo_son_satir=154,
                durum_yolu=durum_yolu,
            )
            imlec = tarama_imleci_oku(durum_yolu)
            self.assertEqual(imlec["aktif_sekme"], "Atölye")
            self.assertEqual(imlec["son_ogrenci_no"], "200A3609")
            self.assertEqual(imlec["kisisel_tablo_son_satir"], 154)

    def test_ortak_tablodan_yalnizca_imlec_sonrasi_alper_satirlarini_suzer(self):
        imlec = {
            "son_ogrenci_no": "200A3609",
            "son_zaman_damgasi": "2026-09-11 20:00:57",
        }
        ortak_satirlar = [
            {"ogrenci_no": "210A3070", "zaman_damgasi": "2026-09-10 10:00:00", "yetkili": "Alper ÇİFTÇİ"},
            {"ogrenci_no": "200A3609", "zaman_damgasi": "2026-09-11 20:00:57", "yetkili": "Alper ÇİFTÇİ"},
            {"ogrenci_no": "220A3999", "zaman_damgasi": "2026-09-12 09:00:00", "yetkili": "Başka Hoca"},
            {"ogrenci_no": "220A3888", "zaman_damgasi": "2026-09-12 11:30:00", "yetkili": "Alper ÇİFTÇİ"},
        ]
        yeni = ortak_tablodan_yeni_atananlari_suz(ortak_satirlar, imlec)
        self.assertEqual(len(yeni), 1)
        self.assertEqual(yeni[0]["ogrenci_no"], "220A3888")


if __name__ == "__main__":
    unittest.main()
