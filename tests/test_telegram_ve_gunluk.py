import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

import telegram_oku  # noqa: E402
import telegram_dinle  # noqa: E402
import gunluk  # noqa: E402
import zamanla  # noqa: E402
import ofis_baslat  # noqa: E402


class TestTelegramVeGunluk(unittest.TestCase):
    def test_telegram_chat_idleri_ve_mesaj_ayikla(self):
        ornek_updates = [
            {
                "update_id": 101,
                "message": {
                    "date": 1700000000,
                    "chat": {"id": 999888777},
                    "text": "Staj defteri incele https://drive.google.com/ornek",
                },
            }
        ]
        self.assertEqual(telegram_oku.chat_idleri(ornek_updates), [999888777])
        ayiklanan = telegram_oku.mesajlari_ayikla(ornek_updates, 999888777)
        self.assertEqual(len(ayiklanan), 1)
        self.assertEqual(telegram_dinle.takim_sec(ayiklanan[0]), "staj-burosu")

    def test_turkce_karakter_ve_takim_sec(self):
        # Büyük Türkçe İ, I, Ş, Ğ, Ç, Ö, Ü ve eşleme testi
        self.assertEqual(telegram_dinle.takim_sec("İNCELE"), "staj-burosu")
        self.assertEqual(
            telegram_dinle.takim_sec("TÜRKÇE karakter kodlaması (UTF-8) ve hata onarımı"),
            "bilgi-islem",
        )
        self.assertEqual(
            telegram_dinle.takim_sec("Watchdog bekçi servisini kontrol et"),
            "bilgi-islem",
        )
        self.assertEqual(
            telegram_dinle.takim_sec("MÜDEK ve komisyon tutanağı hazırla"),
            "memur",
        )
        self.assertEqual(
            telegram_dinle.takim_sec("GMİM Staj Uygulama Esasları ve yönerge derlemesi"),
            "dekan-sekreteri",
        )
        self.assertEqual(
            telegram_dinle.takim_sec("E-POSTA ve gelen kutusu kontrolü"),
            "postaci",
        )

    def test_turkce_utf8_mesaj_ayiklama(self):
        ham_update = {
            "update_id": 202,
            "message": {
                "date": 1700000000,
                "chat": {"id": 12345},
                "text": "Çağatay Öztürk staj defteri incele",
            },
        }
        mesaj = telegram_oku._mesaj(ham_update)
        self.assertEqual(mesaj["metin"], "Çağatay Öztürk staj defteri incele")
        self.assertEqual(telegram_dinle.takim_sec(mesaj), "staj-burosu")

    def test_gunluk_ve_zamanla_kuru(self):
        rapor = gunluk.sabah_raporu(KOK_DIZIN, kuru=True)
        self.assertIn("Sabah Ofis Özeti", rapor)
        self.assertEqual(zamanla.main(["--kuru"]), 0)

    def test_zamanlayici_bekci_watchdog_yapilandirmasi(self):
        # 15 dakikalık nöbet (bekçi/watchdog) görevinin tanımlı olduğunu doğrula
        nobet_tetik = next((t for t in zamanla.TETIKLER if t["ad"] == "nobet"), None)
        self.assertIsNotNone(nobet_tetik)
        self.assertEqual(nobet_tetik["tip"], "MINUTE")
        self.assertEqual(nobet_tetik["aralik_dk"], 15)
        self.assertEqual(nobet_tetik["betik"], "ofis_baslat.py")
        self.assertEqual(nobet_tetik["bayrak"], "--nobet")

        komut = zamanla.gorev_komutu(nobet_tetik)
        self.assertIn("ofis_baslat.py", komut)
        self.assertIn("--nobet", komut)

    def test_ofis_baslat_bekci_kontrolu(self):
        # Bekçi kilit kontrolü ve mesai_baslat sessiz nöbet fonksiyonunu doğrula
        calisiyor = ofis_baslat.telegram_dinleyici_calisiyor_mu()
        self.assertIsInstance(calisiyor, bool)
        kod = ofis_baslat.mesai_baslat(zorla=False, sessiz_nobet=True, kuru=True)
        self.assertEqual(kod, 0)


if __name__ == "__main__":
    unittest.main()

