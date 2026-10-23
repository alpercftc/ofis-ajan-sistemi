import unittest
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from ayar import platform_al, seviye_modeli_al, model_haritasi_oku

class TestAyar(unittest.TestCase):
    def test_model_haritasi_var_mi(self):
        harita = model_haritasi_oku()
        self.assertIn("platformlar", harita)
        self.assertIn("antigravity", harita["platformlar"])
        self.assertIn("claude", harita["platformlar"])

    def test_seviye_modeli_al(self):
        model = seviye_modeli_al("yuksek", "antigravity")
        self.assertTrue(len(model) > 0)

if __name__ == "__main__":
    unittest.main()
