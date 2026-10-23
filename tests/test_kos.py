import unittest
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from kos import KOSU_SURESI_SN, ajan_kos

class TestKos(unittest.TestCase):
    def test_zaman_asimi_tavani(self):
        # 15 dakika = 900 saniye güvenlik tavanı
        self.assertEqual(KOSU_SURESI_SN, 900)

    def test_kuru_kosu_var_olmayan_ajan(self):
        sonuc = ajan_kos("olmayan-ajan", kuru=True)
        self.assertFalse(sonuc)

if __name__ == "__main__":
    unittest.main()
