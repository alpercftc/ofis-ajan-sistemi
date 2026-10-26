import unittest
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "bin"))

from kos import (
    KOSU_SURESI_SN,
    ajan_kos,
    _bekleyen_gorevler_metni,
    _kosu_kaydini_garantile,
    istem,
)
import ayar


class TestKos(unittest.TestCase):
    def test_zaman_asimi_tavani(self):
        # 15 dakika = 900 saniye güvenlik tavanı
        self.assertEqual(KOSU_SURESI_SN, 900)

    def test_kuru_kosu_var_olmayan_ajan(self):
        sonuc = ajan_kos("olmayan-ajan", kuru=True)
        self.assertFalse(sonuc)

    def test_kuru_kosu_mevcut_ajanlar(self):
        self.assertTrue(ajan_kos("bilgi-islem", kuru=True))
        self.assertTrue(ajan_kos("dekan", kuru=True))

    def test_bekleyen_gorevler_kaynak_kafesi(self):
        metin = _bekleyen_gorevler_metni("bilgi-islem", KOK)
        if "durum.json" in metin:
            self.assertIn("<kaynak>", metin)
            self.assertIn("</kaynak>", metin)

    def test_istem_anayasaya_ve_kurallara_uygun_mu(self):
        fm = ayar.takim_bilgisi("bilgi-islem", KOK)
        kosu_yolu = KOK / "takimlar" / "bilgi-islem" / "kosu" / "test-kosu.md"
        prompt = istem("bilgi-islem", fm, kosu_yolu, "2026-10-26T12:00:00+03:00", KOK)
        self.assertIn("ANAYASA.md", prompt)
        self.assertIn("sirket/AJAN-KIMLIGI.md", prompt)
        self.assertIn("takimlar/bilgi-islem/kurallar.md", prompt)
        self.assertIn("Sen `bilgi-islem` ajanısın", prompt)

    def test_kosu_kaydini_garantile(self):
        gecici_kosu = KOK / "takimlar" / "bilgi-islem" / "kosu" / "_test_garanti_kosu.md"
        try:
            if gecici_kosu.exists():
                gecici_kosu.unlink()
            sonuc = {"sonuc": "Birim testi başarılı", "maliyet": 0.0, "sure_sn": 1.2, "model": "test-model"}
            _kosu_kaydini_garantile("bilgi-islem", gecici_kosu, "2026-10-26T12:00:00+03:00", sonuc, ["bt-test-1"])
            self.assertTrue(gecici_kosu.exists())
            icerik = gecici_kosu.read_text(encoding="utf-8")
            self.assertIn("# Koşu Kaydı — `bilgi-islem`", icerik)
            self.assertIn("bt-test-1", icerik)
            self.assertIn("maliyet:", icerik)
        finally:
            if gecici_kosu.exists():
                gecici_kosu.unlink()


if __name__ == "__main__":
    unittest.main()

