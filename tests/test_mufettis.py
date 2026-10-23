import unittest
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from mufettis import tc_kimlik_dogrula, kvkk_kontrol, cikti_denetle

class TestMufettis(unittest.TestCase):
    def test_gecersiz_tc(self):
        self.assertFalse(tc_kimlik_dogrula("11111111111"))
        self.assertFalse(tc_kimlik_dogrula("01234567890"))
        self.assertFalse(tc_kimlik_dogrula("123"))

    def test_cikti_denetimi_temiz(self):
        rapor = "Öğrenci staj defteri eksiksiz tamamlanmıştır."
        sonuc = cikti_denetle(rapor)
        self.assertTrue(sonuc["gecerli"])
        self.assertEqual(sonuc["durum"], "ONAYLANDI")

if __name__ == "__main__":
    unittest.main()
