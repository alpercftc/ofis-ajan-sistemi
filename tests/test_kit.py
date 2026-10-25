import re
import subprocess
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent


class TestGuvenlikVeKit(unittest.TestCase):
    """
    P10 GitHub Güvenlik ve KVKK Denetimi (tests/test_kit.py)
    Git tarafından izlenen dosyalarda hiçbir şifre, imza, açık T.C. Kimlik
    veya geçici öğrenci dosyasının bulunmadığını deterministik olarak doğrular.
    """

    def setUp(self):
        sonuc = subprocess.run(
            ["git", "ls-files"],
            cwd=str(KOK),
            capture_output=True,
            text=True,
            check=True,
        )
        self.izlenen_dosyalar = [satir.strip() for satir in sonuc.stdout.splitlines() if satir.strip()]

    def test_env_dosyasi_asla_git_takibinde_olamaz(self):
        for dosya in self.izlenen_dosyalar:
            self.assertNotEqual(dosya, ".env", "KRİTİK HATA: .env git takibinde!")
            self.assertFalse(dosya.endswith(".env"), f"KRİTİK HATA: {dosya} git takibinde!")

    def test_imza_png_asla_git_takibinde_olamaz(self):
        for dosya in self.izlenen_dosyalar:
            self.assertNotIn("imza.png", dosya.lower(), f"KRİTİK HATA: İmza dosyası ({dosya}) git takibinde!")
            self.assertNotIn("imza.jpeg", dosya.lower(), f"KRİTİK HATA: İmza dosyası ({dosya}) git takibinde!")

    def test_gecici_ogrenci_ve_cikti_dosyalari_git_takibinde_degil(self):
        for dosya in self.izlenen_dosyalar:
            self.assertFalse(
                dosya.startswith("sirket/arsiv/gecici/"),
                f"KRİTİK HATA: Geçici evrak klasörü ({dosya}) git takibinde!",
            )
            if dosya.startswith("sirket/arsiv/ogrenciler/") and not dosya.endswith(".gitkeep"):
                self.fail(f"KRİTİK HATA: Öğrenci profil kartı ({dosya}) git takibinde!")
            if dosya.startswith("takimlar/") and "/cikti/" in dosya and not dosya.endswith(".gitkeep"):
                self.fail(f"KRİTİK HATA: Ajan çıktısı ({dosya}) git takibinde!")
            if dosya.startswith("takimlar/") and "/gelen/" in dosya and not dosya.endswith(".gitkeep"):
                self.fail(f"KRİTİK HATA: Gelen mesaj/veri ({dosya}) git takibinde!")

    def test_ikili_evrak_dosyalari_git_takibinde_degil(self):
        yasakli_uzantilar = (".pdf", ".docx", ".doc", ".zip", ".jpg", ".jpeg", ".png")
        for dosya in self.izlenen_dosyalar:
            for uzanti in yasakli_uzantilar:
                self.assertFalse(
                    dosya.lower().endswith(uzanti),
                    f"KRİTİK HATA: İkili dosya ({dosya}) git takibinde!",
                )

    def test_izlenen_dosyalarda_acik_tc_kimlik_sizintisi_yok(self):
        tc_regex = re.compile(r"\b[1-9][0-9]{10}\b")
        for dosya in self.izlenen_dosyalar:
            if dosya.startswith("tests/"):
                continue  # Birim testlerindeki mock sahte test verileri muaf
            dosya_yolu = KOK / dosya
            if not dosya_yolu.is_file():
                continue
            metin = dosya_yolu.read_text(encoding="utf-8", errors="ignore")
            eslesmeler = tc_regex.findall(metin)
            self.assertEqual(
                eslesmeler,
                [],
                f"KVKK İHLALİ: {dosya} dosyasında açık 11 haneli T.C. Kimlik No bulundu: {eslesmeler}",
            )


if __name__ == "__main__":
    unittest.main()
