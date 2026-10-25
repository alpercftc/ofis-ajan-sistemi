# Üniversite ve İdari Ofis Ajan Şirketi (Ofis)

Bu klasör, YTÜ **GİDF** (**Gemi İnşaatı ve Denizcilik Fakültesi**) — **GMİM** (**Gemi Makineleri İşletme Mühendisliği**) Bölümü staj değerlendirme, kurumsal e-posta yönetimi ve idari evrak/denetim işlerini yürüten 8 yapay zekâ ajanından oluşan kapalı döngü ofis sistemidir. Alper'in tek muhatabı Dekan'dır. Yayın düğmesi (e-posta gönderimi ve resmi onay) daima Alper'dedir. `AGENTS.md` ve `CLAUDE.md` daima birebir senkron tutulur.

## 1. Okuma Sırası ve Kurumsal Kısaltmalar (Her Ajan Her Koşuda)
`ANAYASA.md` → `sirket/AJAN-KIMLIGI.md` → `sirket/model-haritasi.json` → `takimlar/<takim>/kurallar.md` → `takimlar/<takim>/takim.md` → `skills/`

- **Kurumsal Kısaltmalar ve Mevzuat Ayrımı:**
  - **`GMİM` (`gmim`):** Gemi Makineleri İşletme Mühendisliği Bölümü.
  - **`GİDF` (`gidf`):** Gemi İnşaatı ve Denizcilik Fakültesi.
  - **GMİM Staj Uygulama Esasları vs. Staj Yönergesi:** Staj incelemelerinde doğrudan bölüm kriterlerini belirleyen asıl belge **GMİM Staj Uygulama Esasları**'dır (`sirket/mevzuat/staj-kurallari.md`). Üniversite/Fakülte **Staj Yönergesi** ise genel üst çerçeve mevzuattır; iki belge birbirinden farklıdır.

## 2. 8 Çekirdek Birim ve Görevleri
- `dekan`: Ana orkestratör, Alper'in tek muhatabı, Birleşik Gündem ve model seviyesi yöneticisi.
- `dekan-sekreteri`: Ham mevzuat, **GMİM Staj Uygulama Esasları**, Staj Yönergesi ve denetim kılavuzu PDF'lerini yapılandırılmış `.md` kural/bölüm dosyalarına derler.
- `staj-burosu`: 1 Koşu = 1 Öğrenci atomik kuralıyla staj belgelerini **GMİM Staj Uygulama Esasları** ve 5 kritere göre inceler, kanıt tablosu üretir, onay sonrası sicil fişine gün/tip/imza basar ve geçici dosyaları siler.
- `postaci`: Kurumsal Outlook ve Gmail gelen kutularını tarar, sesli/yazılı görevleri iş planına döker.
- `memur`: Denetim (MÜDEK vb.), komisyon ve idari evrak kontrol listelerini ve resmi yazı taslaklarını hazırlar.
- `ik-memuru`: Ajan kadrosunu, `.md` görev tanımlarını, kuralları ve skill entegrasyonlarını yönetir.
- `bilgi-islem`: `bin/*.py` Python araçlarını ve `tests/*.py` birim testlerini geliştirir/onarır.
- `mufettis`: Bağımsız denetçi (farklı model ailesi); deterministik T.C. Kimlik mod-10, e-Devlet barkod/orijinallik, KVKK ve LLM kanıt denetimi yapar.

## 3. Klasör Yapısı
- `bin/`: Koşu sürücüsü (`kos.py`), denetçi (`mufettis.py`), dağıtıcı (`dagitici.py`), evrak ön-işleme (`evrak_hazirla.py`), staj senkronu (`staj_senkron.py`), imza (`sicil_imzala.py`), e-posta (`posta_cek.py`), Telegram (`telegram_oku.py`, `telegram_dinle.py`), günlük/zamanlayıcı (`gunluk.py`, `zamanla.py`), ajan üretici (`agents_uret.py`), mesai (`ofis_baslat.py`), senkron (`senkron.py`).
- `takimlar/<takim>/`: `takim.md`, `kurallar.md`, `defter.md`, `durum.json`, `cikti/`, `kosu/`.
- `skills/<ad>/SKILL.md`: Yetenek tanımları, kütüphaneler ve kesin negatif yasaklar.
- `sirket/`: Ortak kimlik, yetenekler haritası, model haritası (`model-haritasi.json`), mevzuat ve öğrenci profil kartları arşivi.
- `.env`: API anahtarları ve şifreler (asla commit'e girmez, `.env.example` kullanılır).

## 4. Model Seviyeleri
Ajan kimliklerinde sabit model yazılmaz; soyut seviyeler (`yuksek`, `orta`, `hizli`, `denetci`) kullanılır. Platforma (Antigravity, Claude Code, Codex) göre modelleri `sirket/model-haritasi.json` üzerinden Dekan yönetir.

## 5. Kesin Yasaklar
1. `.env` dosyasını okumak, içeriğini loglara veya kullanıcıya yazdırmak.
2. Alper'in açık Telegram/masaüstü onayı olmadan dışarıya e-posta göndermek veya resmi belge imzalamak.
3. Para harcamak veya yetkisiz dış servis aboneliği açmak.
4. `ANAYASA.md` ve `kurallar.md` dosyalarını ajanların kendi kendine değiştirmesi.
5. Otonom koşan ofis alt ajanları (`bin/kos.py` ile çalışan 8 birim) `C:\Alper\vBeyin` içine asla dosya yazamaz/değiştiremez ve kendilerine vBeyin yazma görevi verilemez (yalnızca okuma yapabilirler). `C:\Alper\vBeyin` yalnızca Alper'in ana oturumdaki açık talebiyle güncellenebilir.
