import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from dagitici import AJANLAR, dagit, kuyruk_tara, zincir_esle  # noqa: E402


class TestDagitici(unittest.TestCase):
    def test_ajanlar_listesi_tam_mi(self):
        self.assertEqual(len(AJANLAR), 8)
        self.assertIn("dekan", AJANLAR)
        self.assertIn("staj-burosu", AJANLAR)
        self.assertIn("mufettis", AJANLAR)

    def test_zincir_esle_kurallari(self):
        es1 = zincir_esle("staj-200A3609")
        self.assertIsNotNone(es1)
        self.assertEqual(es1["takim"], "dekan")
        self.assertEqual(es1["id"], "staj-onay-200A3609")

        es2 = zincir_esle("mevzuat-gmim-2026")
        self.assertIsNotNone(es2)
        self.assertEqual(es2["takim"], "dekan")
        self.assertEqual(es2["id"], "mevzuat-onay-gmim-2026")

        es3 = zincir_esle("posta-idari-mudek")
        self.assertIsNotNone(es3)
        self.assertEqual(es3["takim"], "memur")
        self.assertEqual(es3["id"], "idari-mudek")

    def test_kuyruk_tara_calisiyor_mu(self):
        sonuc = kuyruk_tara(kuru=True)
        self.assertIn("zincir", sonuc)
        self.assertIn("kararlar", sonuc)
        self.assertEqual(len(sonuc["kararlar"]), 8)


if __name__ == "__main__":
    unittest.main()
