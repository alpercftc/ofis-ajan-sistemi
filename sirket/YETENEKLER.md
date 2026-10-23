# Şirket Yetenekler ve Araçlar Matrisi

Bu belge, 8 çekirdek birimin hangi yetenekleri (`skills/`) okuduğunu ve hangi Python araçlarını (`bin/`) çalıştırdığını gösteren resmi görev matrisidir.

| # | Ajan Kodu | Görev Tanımı | Kullandığı Yetenekler (`skills/`) | Çalıştırdığı / Kullandığı Araçlar (`bin/`) |
|---|---|---|---|---|
| **1** | `dekan` | Ana Yönetici & Orkestratör | `skills/ses-ve-iletisim`, `skills/guvenlik-ve-denetim` | `bin/ofis_baslat.py`, `bin/telegram_koprusu.py`, `bin/ayar.py`, `bin/agents_uret.py` |
| **2** | `dekan-sekreteri` | Mevzuat Derleyici | `skills/mevzuat-derleme`, `skills/evrak-isleme` | `bin/ayar.py` |
| **3** | `staj-burosu` | Staj ve Çapraz Kontrol | `skills/evrak-isleme`, `skills/sicil-ve-imza`, `skills/tablo-ve-takvim` | `bin/evrak_hazirla.py`, `bin/staj_senkron.py`, `bin/sicil_imzala.py` |
| **4** | `postaci` | İletişim ve İş Planlayıcı | `skills/ses-ve-iletisim`, `skills/tablo-ve-takvim` | `bin/postaci_outlook.py`, `bin/telegram_koprusu.py` |
| **5** | `memur` | İdari Evrak ve Denetim | `skills/evrak-isleme`, `skills/tablo-ve-takvim` | `bin/ayar.py` |
| **6** | `ik-memuru` | Personel ve Kural Yöneticisi | `skills/web-test-ve-log`, `skills/guvenlik-ve-denetim` | `bin/agents_uret.py` |
| **7** | `bilgi-islem` | Python ve Test Geliştirici | `skills/web-test-ve-log`, `skills/sicil-ve-imza` | `bin/*.py` (geliştirme), `pytest`, `ruff` |
| **8** | `mufettis` | Bağımsız Denetçi | `skills/guvenlik-ve-denetim` | `bin/mufettis.py` |

## 1. Yetenek (`skills/`) Kataloğu
1. **`evrak-isleme`:** PDF, Word (.docx) ve görselleri bağlamı şişirmeden temiz Markdown'a çevirme kuralları.
2. **`mevzuat-derleme`:** Kalın yönerge ve kılavuz PDF'lerini kural maddelerine dönüştürme protokolü.
3. **`sicil-ve-imza`:** Dinamik çapa metin arama, olumsuz cümlenin üstünü çizme, koordinatlı imza ve OpenCV vesikalık kontrolü.
4. **`tablo-ve-takvim`:** Google Sheets senkronizasyonu, holidays.Turkey ile tatil düşme ve Türkçe doğal dil tarih ayrıştırma.
5. **`ses-ve-iletisim`:** faster-whisper ile yerel sesli not çevirme, Gmail IMAP ve MSAL kurumsal e-posta protokolü.
6. **`guvenlik-ve-denetim`:** T.C. Kimlik mod-10 algoritması, Pydantic şema denetimi ve veri kafesi kuralları.
7. **`web-test-ve-log`:** CLI araç standartları (typer), pytest test zorunluluğu ve endüstriyel log formatı.
