import unittest
from pathlib import Path
import tempfile
import fitz

from bin.sicil_imzala import harita_yukle, sicil_imzala_ve_tamamla, vesikalik_kontrol_et

KOK_DIZIN = Path(__file__).resolve().parent.parent
SABLON_DIZINI = KOK_DIZIN / "sirket" / "sablonlar"
TEST_PDF = KOK_DIZIN / "sirket" / "arsiv" / "gecici" / "200A3609" / "FR-1323 - Staj Sicil Formu.pdf"


class TestSicilImzala(unittest.TestCase):
    def test_harita_yukle(self):
        harita = harita_yukle()
        self.assertIn("bolgeler", harita)
        bolgeler = harita["bolgeler"]
        for i in range(1, 10):
            anahtar = [k for k in bolgeler.keys() if k.startswith(f"{i}_")]
            self.assertTrue(len(anahtar) > 0, f"Bölge {i} haritada bulunamadı")

    def test_vesikalik_kontrol_et(self):
        if not TEST_PDF.exists():
            self.skipTest("Test PDF mevcut değil")
        sonuc = vesikalik_kontrol_et(str(TEST_PDF))
        self.assertIn("gecerli", sonuc)
        self.assertIn("parlaklik", sonuc)
        self.assertIn("netlik_skoru", sonuc)
        self.assertTrue(sonuc["gecerli"])

    def test_sicil_imzala_ve_tamamla(self):
        if not TEST_PDF.exists():
            self.skipTest("Test PDF mevcut değil")
        with tempfile.TemporaryDirectory() as tmpdir:
            cikti_pdf = Path(tmpdir) / "FR-1323_imzali_test.pdf"
            basarili = sicil_imzala_ve_tamamla(
                ogrenci_no="200A3609",
                kabul_gun=19,
                staj_tipi="Atölye",
                sicil_pdf_yolu=str(TEST_PDF),
                cikti_pdf_yolu=str(cikti_pdf),
            )
            self.assertTrue(basarili)
            self.assertTrue(cikti_pdf.exists())

            doc = fitz.open(cikti_pdf)
            page = doc[0]
            # Kontrol: En az bir görsel (şeffaf imza) eklenmiş olmalı
            self.assertGreaterEqual(len(page.get_images()), 1)
            # Kontrol: Çizgi çizilmiş olmalı
            self.assertGreaterEqual(len(page.get_drawings()), 1)
            # Kontrol: Gün sayısı veya metin bulunmalı
            metin = page.get_text()
            self.assertTrue("19" in metin or "Atölye" in metin)
            doc.close()


if __name__ == "__main__":
    unittest.main()
