import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

from posta_cek import (
    kaynak_kafesine_al,
    oncelik_siniflandir,
    staj_revize_ogrenci_bul,
)


class TestPostaCek(unittest.TestCase):
    def test_kaynak_kafesine_al(self):
        kafes = kaynak_kafesine_al("ogr@std.yildiz.edu.tr", "Staj Sicil", "Ekte gönderdim.")
        self.assertIn('<kaynak tip="eposta"', kafes)
        self.assertIn("</kaynak>", kafes)

    def test_oncelik_siniflandir_ve_ogrenci_bul(self):
        kat = oncelik_siniflandir(
            "denetci@yildiz.edu.tr", "MÜDEK Denetim Dosyaları", "Yarın teslim."
        )
        self.assertTrue(kat.startswith("🔴"))

        kat_staj = oncelik_siniflandir(
            "bedirhan@std.yildiz.edu.tr", "240A3027 Staj Sicil Eksik", "Sicil formum ektedir."
        )
        self.assertTrue(kat_staj.startswith("🟠"))
        self.assertEqual(staj_revize_ogrenci_bul("240A3027 Staj Sicil Eksik", ""), "240A3027")


if __name__ == "__main__":
    unittest.main()
