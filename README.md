# Üniversite ve İdari Ofis Ajan Şirketi (Ofis)

Üniversite fakülte/bölüm sekreterlikleri, staj komisyonları, kurumsal e-posta yönetimi ve idari evrak/denetim işlerini yürüten **8 yapay zekâ biriminden** oluşan çoklu platform (Google Antigravity & Claude Code) kapalı döngü ofis otomasyon sistemidir.

> **Temel İlke (ANAYASA):** Yayın düğmesi daima **Yönetici/İnsan**'dadır. Hiçbir yapay zekâ ajanı açık Telegram veya masaüstü onayı olmadan dışarıya e-posta gönderemez veya resmi belge imzalayamaz. Sistem dosya tabanlıdır; ajanlar canlı sohbet etmez, durum makinesi (`bin/dagitici.py`) ile koordine olur.

---

## 🚀 1. Yapay Zekâya Sistemi Otomatik Kuran Prompt

Bu repoyu klonladıktan sonra yapay zekâ kodlama asistanına (Antigravity veya Claude Code) aşağıdaki promptu vermen yeterlidir. Asistan sana birkaç temel soru soracak ve şirketini senin kurumuna göre kuracaktır:

```markdown
Sen bir Kurumsal Ofis Ajan Şirketi Mimarisini kuran uzman ajansın.
Şu depodaki mimariyi benim ofisime göre kurmanı istiyorum: https://github.com/alpercftc/ofis-ajan-sistemi

Kuruluma başlamadan önce lütfen bana sırayla şu 5 soruyu sor ve yanıtlarımı bekle:
1. Yönetici Adı / Unvanı: (Sistemin sana ve raporlarda hitap edeceği isim, örn: "Prof. Dr. Ahmet YILMAZ" veya "Ahmet")
2. Kurum / Bölüm Adı: (Örn: "YTÜ GMİM", "İTÜ Gemi İnşaatı", "Hukuk Fakültesi Dekanlığı" vb.)
3. Hangi platformda koşacaksın?: (Antigravity veya Claude Code)
4. Hangi görevleri devretmek istiyorsun?: (Örn: Staj değerlendirme, Gelen e-posta tarama/taslaklama, MÜDEK/Akreditasyon denetim hazırlığı, Resmi yazı taslakları)
5. Bildirimleri nereden almak istersin?: (Telegram Botu mu, Masaüstü terminal mi?)

Ben bu soruları yanıtladıktan sonra:
- `ANAYASA.md`, `AGENTS.md` ve `takimlar/*/takim.md` dosyalarını yanıtlarıma göre kişiselleştir.
- `bin/agents_uret.py` koşturup ilgili platform profillerini (.agents veya .claude) üret.
- `.env.example` dosyasını gösterip hangi API anahtarlarını gireceğimi listele.
- `python -m pytest` ile kurulumu test edip sonucu bana raporla.
```

---

## 🌅 2. Sistemin Sabahları Başlatılması ve Çalışma Rutini

Sistem **09:00 – 18:00** mesai saatleri içinde **0-Token Ön-Kontrol Mimarisi** ile çalışır. Boşta beklerken hiçbir yapay zekâ tokenı harcanmaz.

### Sabah Mesai Başlangıcı (Güne Başlarken)
Her sabah terminalde veya VS Code / Antigravity ortamında tek komut çalıştırman yeterlidir:
```bash
python bin/ofis_baslat.py
```
Bu komut:
1. `bin/gunluk.py --sabah` ile dağıtıcıyı çalıştırır, gece veya sabah gelen işleri sıralar ve `sirket-log/rapor/` altına sabah ofis özetini yazar.
2. `bin/telegram_dinle.py` arka plan dinleyicisini ayağa kaldırır (Telegram'dan gelen sesli veya yazılı notları karşılar).
3. Dekan birimini uyandırarak güne dair **Birleşik Ofis Gündemini** hazırlar.

### Gün İçinde Sürekli / Arka Planda Çalıştırma
Telegram dinleyicisini terminalde sürekli açık tutmak için:
```bash
python bin/telegram_dinle.py
```
*(Bu süreç saf Python'dur, token harcamaz. Yalnızca Telegram botuna bir evrak veya ses kaydı attığında ilgili ajanı 30 saniyeliğine uyandırır).*

---

## 🏛️ Çekirdek Birimler (8 Ajan)

| # | Birim | Rol ve Sorumluluk | Seviye | Vardiya / Tetik Mekanizması |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `dekan` | Ana orkestratör, Yöneticinin tek muhatabı, Birleşik Gündem ve onay yöneticisi | `yuksek` | Mesai 09:00-18:00 (Telegram/kuyruk anlık, 09:00/18:00 özet) |
| **2** | `dekan-sekreteri` | Yönerge, mevzuat ve denetim kılavuzu PDF'lerini yapılandırılmış `.md` kural ağaçlarına derler | `yuksek` | Olay bazlı (yeni mevzuat PDF'i geldiğinde) |
| **3** | `staj-burosu` | `1 Koşu = 1 Öğrenci` atomik kuralıyla staj belgelerini 5 kritere göre inceler, imzalı sicil fişini hazırlar | `orta` | Sezonluk (Günde 1 kez 09:00 senkron kontrolü & Yönetici emriyle) |
| **4** | `postaci` | Kurumsal Outlook ve Gmail gelen kutularını tarar, Telegram sesli/yazılı notlarını iş planına döker | `hizli` | Mesai 09:00-18:00 (Saat başı ve Telegram anlık) |
| **5** | `memur` | MÜDEK denetimi, komisyon ve idari evrak kontrol listelerini ve resmi yazı taslaklarını hazırlar | `orta` | Duruma bağlı (Kuyruğa idari evrak/denetim görevi düştüğünde) |
| **6** | `ik-memuru` | Ajan kadrosunu, görev tanımlarını (`takim.md`), kuralları ve yetenek (`skills/`) entegrasyonlarını yönetir | `orta` | İstek üzerine (Kadro/kural güncellemesi istendiğinde) |
| **7** | `bilgi-islem` | `bin/*.py` Python araçlarını, sicil koordinat haritalarını ve `tests/*.py` testlerini geliştirir/onarır | `yuksek` | İstek üzerine (Teknik araç veya kalibrasyon gerektiğinde) |
| **8** | `mufettis` | Bağımsız denetçi; deterministik T.C. Kimlik mod-10, e-Devlet barkod doğrulaması, KVKK ve kanıt denetimi yapar | `denetci` | Her koşu sonrası anlık ve 18:00 gün sonu denetimi |

---

## 🛠️ Hızlı Kurulum ve Test

```bash
# 1. Depoyu klonla
git clone https://github.com/alpercftc/ofis-ajan-sistemi.git
cd ofis-ajan-sistemi

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Ortam değişkenlerini hazırla
cp .env.example .env
# .env dosyasını kendi Telegram / E-posta anahtarlarınla doldur

# 4. Testleri çalıştır
python -m pytest -q
```
