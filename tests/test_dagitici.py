import unittest
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from dagitici import AJANLAR, kuyruk_tara

class TestDagitici(unittest.TestCase):
    def test_ajanlar_listesi_tam_mi(self):
        self.assertEqual(len(AJANLAR), 8)
        self.assertIn("dekan", AJANLAR)
        self.assertIn("staj-burosu", AJANLAR)
        self.assertIn("mufettis", AJANLAR)

    def test_kuyruk_tara_calisiyor_mu(self):
        # Hata fırlatmadan çalışmalı
        try:
            kuyruk_tara()
            basarili = True
        except Exception:
            basarili = False
        self.assertTrue(basarili)

if __name__ == "__main__":
    unittest.main()
