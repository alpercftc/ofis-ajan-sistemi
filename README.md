# Üniversite ve İdari Ofis Ajan Şirketi (Ofis)

YTÜ **GİDF** (**Gemi İnşaatı ve Denizcilik Fakültesi**) — **GMİM** (**Gemi Makineleri İşletme Mühendisliği**) Bölümü staj değerlendirme, kurumsal e-posta yönetimi ve idari evrak/denetim işlerini yürüten **8 yapay zekâ biriminden** oluşan kapalı döngü ofis otomasyon sistemidir.

> **Temel İlke (ANAYASA):** Yayın düğmesi daima insandadır (Alper). Hiçbir yapay zekâ ajanı açık Telegram veya masaüstü onayı olmadan dışarıya e-posta gönderemez veya resmi belge imzalayamaz. Sistem dosya tabanlıdır; ajanlar birbiriyle sohbet etmez, durum makinesi (`bin/dagitici.py`) ile koordine olur.

---

## 🏛️ Çekirdek Birimler (8 Ajan)

| # | Birim | Rol ve Sorumluluk | Seviye | Vardiya / Tetik Mekanizması |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `dekan` | Ana orkestratör, Alper'in tek muhatabı, Birleşik Gündem ve onay yöneticisi | `yuksek` | Mesai 09:00-18:00 (Telegram/kuyruk anlık, 09:00/18:00 özet) |
| **2** | `dekan-sekreteri` | Yönerge, mevzuat ve denetim kılavuzu PDF'lerini yapılandırılmış `.md` kural ağaçlarına derler | `yuksek` | Olay bazlı (yeni mevzuat PDF'i geldiğinde) |
| **3** | `staj-burosu` | `1 Koşu = 1 Öğrenci` atomik kuralıyla staj belgelerini 5 kritere göre inceler, imzalı sicil fişini hazırlar | `orta` | Sezonluk (Günde 1 kez 09:00 senkron kontrolü & Alper emriyle) |
| **4** | `postaci` | Kurumsal Outlook ve Gmail gelen kutularını tarar, Telegram sesli/yazılı notlarını iş planına döker | `hizli` | Mesai 09:00-18:00 (Saat başı ve Telegram anlık) |
| **5** | `memur` | MÜDEK denetimi, komisyon ve idari evrak kontrol listelerini ve resmi yazı taslaklarını hazırlar | `orta` | Duruma bağlı (Kuyruğa idari evrak/denetim görevi düştüğünde) |
| **6** | `ik-memuru` | Ajan kadrosunu, görev tanımlarını (`takim.md`), kuralları ve yetenek (`skills/`) entegrasyonlarını yönetir | `orta` | İstek üzerine (Kadro/kural güncellemesi istendiğinde) |
| **7** | `bilgi-islem` | `bin/*.py` Python araçlarını, sicil koordinat haritalarını ve `tests/*.py` testlerini geliştirir/onarır | `yuksek` | İstek üzerine (Teknik araç veya kalibrasyon gerektiğinde) |
| **8** | `mufettis` | Bağımsız denetçi; deterministik T.C. Kimlik mod-10, e-Devlet barkod doğrulaması, KVKK ve kanıt denetimi yapar | `denetci` | Her koşu sonrası anlık ve 18:00 gün sonu denetimi |

---

## ⚡ 0-Token Ön-Kontrol Mimarisi

Sistemde LLM'ler arka planda sürekli açık kalmaz ve boşta token tüketmez:
- Dinleyiciler (`bin/telegram_dinle.py`), e-posta tarayıcıları (`bin/posta_cek.py`), tablo senkronu (`bin/staj_senkron.py`) ve zamanlayıcılar (`bin/zamanla.py`, `bin/gunluk.py`) **%100 saf Python betikleridir (0 Token)**.
- Bir yapay zekâ ajanı yalnızca kuyruğunda bekleyen gerçek bir iş (`durum.json`) olduğunda uyanır, görevini tamamlar ve kapanır.

---

## 🛠️ Hızlı Başlangıç

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Birim testlerini ve KVKK güvenlik denetimini çalıştır
python -m pytest -q

# Kuru koşu ile durum ve kuyruk kontrolü
python bin/dagitici.py --kuru
python bin/gunluk.py --sabah --kuru
```

---

## 🔒 Güvenlik ve KVKK Disiplini
- `.env` ve şahsi ıslak imza (`imza.png`) `.gitignore` kapsamındadır ve hiçbir depoya sızmaz (`tests/test_kit.py` ile denetlenir).
- Öğrenci belgeleri ve kişisel veriler işlendikten ve Alper'in onayladığı e-posta Komisyon Başkanına iletildikten sonra diskten temizlenir.
