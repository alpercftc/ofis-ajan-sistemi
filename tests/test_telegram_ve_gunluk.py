import unittest
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN / "bin"))

import telegram_oku  # noqa: E402
import telegram_dinle  # noqa: E402
import gunluk  # noqa: E402
import zamanla  # noqa: E402


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

    def test_gunluk_ve_zamanla_kuru(self):
        rapor = gunluk.sabah_raporu(KOK_DIZIN, kuru=True)
        self.assertIn("Sabah Ofis Özeti", rapor)
        self.assertEqual(zamanla.main(["--kuru"]), 0)


if __name__ == "__main__":
    unittest.main()
