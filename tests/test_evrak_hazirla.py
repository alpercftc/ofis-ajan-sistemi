import tempfile
import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

from evrak_hazirla import metni_bolumlere_ayir_ve_indeksle


class TestEvrakHazirla(unittest.TestCase):
    def test_bolumlere_ayir_ve_indeksle(self):
        ornek_kilavuz = (
            "# Bölüm 1: Öğrenciler\n"
            "Yatay geçiş, staj ve kabul kuralları burada yer alır.\n\n"
            "# Bölüm 2: Program Eğitim Amaçları\n"
            "Mezunların kariyer hedefleri ve paydaş görüşleri.\n\n"
            "# Bölüm 3: Program Çıktıları\n"
            "Mühendislik bilgi ve beceri matrisi ölçme değerlendirme.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            hedef_kok = Path(tmp)
            sonuc = metni_bolumlere_ayir_ve_indeksle(
                "mudek_kilavuzu", ornek_kilavuz, hedef_kok=hedef_kok
            )
            self.assertEqual(sonuc["mod"], "bolumlu")
            self.assertEqual(sonuc["bolum_sayisi"], 3)

            index_path = Path(sonuc["index_dosyasi"])
            self.assertTrue(index_path.exists())
            self.assertEqual(index_path.name, "index_mudek-kilavuzu.md")
            icerik = index_path.read_text(encoding="utf-8")
            self.assertIn("bolum-01-bolum-1-ogrenciler.md", icerik)
            self.assertIn("bolum-03-bolum-3-program-ciktilari.md", icerik)


if __name__ == "__main__":
    unittest.main()
