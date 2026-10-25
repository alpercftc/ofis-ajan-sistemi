import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

import agents_uret  # noqa: E402


class TestAgentsUret(unittest.TestCase):
    def test_8_birim_uretim_ve_check(self):
        agents_uret.uret(KOK_DIZIN, sadece_kontrol=False)
        sapma = agents_uret.uret(KOK_DIZIN, sadece_kontrol=True)
        self.assertEqual(sapma, [])

        beklenen_birimler = [
            "dekan",
            "dekan-sekreteri",
            "staj-burosu",
            "postaci",
            "memur",
            "ik-memuru",
            "bilgi-islem",
            "mufettis",
        ]
        for birim in beklenen_birimler:
            claude_dosya = KOK_DIZIN / ".claude" / "agents" / f"{birim}.md"
            agents_dosya = KOK_DIZIN / ".agents" / "agents" / f"{birim}.md"
            self.assertTrue(claude_dosya.exists(), f"Eksik: {claude_dosya}")
            self.assertTrue(agents_dosya.exists(), f"Eksik: {agents_dosya}")
            icerik = claude_dosya.read_text(encoding="utf-8")
            self.assertIn(f"Sen `{birim}` ajanısın.", icerik)
            self.assertNotIn("gerekli_anahtarlar:", icerik.split("---")[1])
            self.assertNotIn("butce_usd:", icerik.split("---")[1])


if __name__ == "__main__":
    unittest.main()
