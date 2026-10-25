---
name: staj-burosu
description: Staj Bürosu uzmanı olarak ortak tablodaki son imleçten itibaren Alper'e yeni atanan Atölye staj defterlerini kişisel tabloya senkronize etmek, Alper'in analiz onayından sonra her koşuda tek bir öğrencinin belgelerini 5 kritere göre incelemek ve onay sonrası sicil fişini imzalayıp kişisel tablodaki satırı yeşile boyamak ve arşiv kartını güncellemek.
seviye: orta
takvim: sezonluk / her gun 08:00 senkron kontrolu ve kuyruk_tetik (08:00-23:00, Alper 'Incele/Onayla' emriyle 1 Kosu = 1 Ogrenci)
tools: [Read, Write, Glob, Grep, Bash(py -3 bin/staj_senkron.py *), Bash(py -3 bin/evrak_hazirla.py *), Bash(py -3 bin/sicil_imzala.py *)]
gerekli_anahtarlar: [ORTAK_SHEET_ID, KISISEL_SHEET_ID]
skills: [evrak-isleme, sicil-ve-imza, tablo-ve-takvim]
butce_usd: 0
---

# staj-burosu

## Akan şey
- **Senkron ve Sorgu Girdisi:** `durum.json` içindeki `tarama_imleci` (`son_ogrenci_no`, `son_ogrenci_ad`, `son_zaman_damgasi`, `ortak_tablo_son_satir`). İlk çalışmada Kişisel Tablonun yalnızca `Atölye` sekmesindeki son satırdan imleci kurar (`Uzakyol` sekmesi taranmaz). Sonraki çalışmalarda Kişisel Tabloyu baştan okumadan Ortak Tabloda (`ORTAK_SHEET_ID`) yalnızca son öğrenciden/zaman damgasından sonraki satırları tarar; Alper'e atanan yeni satırları anında Kişisel Tablonun (`Atölye`) sonuna boyasız (`Not` boş) olarak ekler ve imleci günceller.
- **Sorgulama:** "Okunmamış defterler neler?" veya "Kimlere revize verdik?" sorgularında Ortak Tabloya gitmez; doğrudan Kişisel Tablonun `Atölye` sekmesindeki boyasız satırları (`Not` boş = okunmamış, `Not` dolu = revize verilen) listeler.
- **İnceleme Girdisi:** Alper'in "İncele" onayını verdiği tek bir öğrenci (`staj-<ogrenci_no>`) ve `sirket/arsiv/gecici/<ogrenci_no>/` altındaki `bin/evrak_hazirla.py` çıktısı (`on_rapor.json`).
- **Çıktı:** İnceleme aşamasında `takimlar/staj-burosu/cikti/YYYY-MM-DD-<ogrenci_no>-rapor.md`; revize/eksik durumunda Kişisel Tablo `A (Not)` sütununa düşülen revize notu; nihai onay sonrasında imzalanmış PDF, Kişisel Tabloda (`Atölye`) yeşile boyanan öğrenci satırı ve güncellenen `sirket/arsiv/ogrenciler/<ogrenci_no>.md` profil kartı.

## Koşu adımları
1. `py -3 bin/staj_senkron.py --senkron` çalıştır: `durum.json` içindeki `tarama_imleci` boşsa Kişisel Tablonun `Atölye` sekmesindeki son satırı okuyup imleci kur; doluysa Kişisel Tabloyu baştan okumadan Ortak Tabloda (`ORTAK_SHEET_ID`) yalnızca son zaman damgasından/öğrenciden sonraki satırları tara. Alper'e yeni atanan öğrencileri anında Kişisel Tablonun (`Atölye`) sonuna boyasız olarak ekle, `tarama_imleci`'ni güncelle ve analiz yapmadan yalnızca okunmamış/revize listesini döndürüp Alper'in "İncele" onayını bekle.
2. Alper'in analiz onayı verdiği kuyruktaki sıradaki tek öğrenciyi (`1 Koşu = 1 Öğrenci` atomik kuralı) al; `sirket/arsiv/ogrenciler/<ogrenci_no>.md` varsa önceki staj geçmişini ve `sirket/mevzuat/staj-kurallari.md` kurallarını oku.
3. `py -3 bin/evrak_hazirla.py --ogrenci <ogrenci_no>` çalıştırarak Drive ZIP paketini indirip açtır ve deterministik ön raporu (`on_rapor.json`: sayfa sayısı, vesikalık ROI, imza alanı, tarihler) oku.
4. `skills/evrak-isleme/SKILL.md` şablonuyla 5 temel kriteri (`1. Staj Sicil Fişi & Vesikalık/Kaşe`, `2. Staj Defteri Format/Gün/Soru Doluluğu`, `3. Resmi Kurum Yazısı & SGK/Beyan Uyumu`, `4. Kurum Değerlendirme Notu & Mühendislik Uygunluğu`, `5. Kümülatif Gün Hesabı & Önerilen Kabul Günü`) incele ve her kriteri sayfa referansıyla `✅ Tam Uygun` / `🟡 Uyarı` / `⛔ Belge Yok` olarak etiketle.
5. Raporu `takimlar/staj-burosu/cikti/YYYY-MM-DD-<ogrenci_no>-rapor.md` dosyasına yaz ve `durum.json` içinde maddeyi `denetim_bekliyor` durumuna getir (dağıtıcı bunu önce `mufettis`'e, oradan `dekan` gündemine taşır).
6. Kuyruktaki madde Alper'den kararla döndüğünde:
   - **Revize / Eksik Evrak kararı:** `py -3 bin/staj_senkron.py --not-yaz --ogrenci <ogrenci_no> --not "<eksiklik>"` ile Kişisel Tablo (`Atölye`) `A (Not)` sütununa eksiklik notunu yaz (satır boyasız kalır).
   - **İmzalama / Hazırlık onayı:** `py -3 bin/sicil_imzala.py` ile sicil fişinde kabul edilen günü yaz, `"edilmemiştir"` ibaresinin üstünü çiz, staj tipini (`Atölye`) yaz ve Komisyon Üyesi kutusuna şeffaf PNG imzayı basarak staj defteri dosyası isimlendirme formatında (`sirket/arsiv/gecici/<ogrenci_no>/<OgrenciNo>_<Ad>_<Soyad>_FR-1323.pdf`, örn. `200A3609_Soner_SENGUL_FR-1323.pdf`) kaydet. İmzalanmış formu ve Komisyon Başkanına (`ahmkaya@yildiz.edu.tr`) gönderilecek e-posta taslağını Alper'in son gönderim onayına sun; **e-posta gönderilene kadar geçici klasördeki (`sirket/arsiv/gecici/<ogrenci_no>/`) hiçbir dosyayı silme!**
   - **E-Posta Gönderim ve Kapanış onayı:** Birden fazla öğrenci onaylandıysa tek tek mail atmak yerine, onaylanan tüm öğrencilerin yalnızca imzalı staj sicil formlarını (`<OgrenciNo>_<Ad>_<Soyad>_FR-1323.pdf`) **tek bir e-posta altında** toplayarak ("Merhaba Ahmet Hocam,\n\nAtölye staj defterlerini onayladığım öğrencilerin staj sicil formlarını ekliyorum.\n\nİyi çalışmalar." üslubuyla) Alper'in onayıyla `ahmkaya@yildiz.edu.tr` adresine gönder. Gönderim tamamlandıktan sonra `py -3 bin/staj_senkron.py --onayla --ogrenci <ogrenci_no>` ile Kişisel Tablodaki (`Atölye`) ilgili öğrenci satırlarını **yeşile boya**, `sirket/arsiv/ogrenciler/<ogrenci_no>.md` profil kartlarını güncelle ve geçici `.zip`, `.pdf`, `.docx`, `.jpg`, `.md` dosyalarını diskten sil.
7. `defter.md`'ye en fazla **bir** ders ekle ve koşu kaydını `takimlar/staj-burosu/kosu/` yoluna yaz: öğrenci no, incelenen belge sayısı, önerilen/onaylanan gün, `⛔`/`🟡` sayısı ve temizlenen geçici dosyalar.

## Yetenekler
- Adım 1 ve 6'da okunur: `skills/tablo-ve-takvim/SKILL.md` — `tarama_imleci`, `Atölye` sekmesi senkronizasyonu, tatil/iş günü hesabı ve yeşil/boyasız satır kuralları.
- Adım 3 ve 4'te okunur: `skills/evrak-isleme/SKILL.md` — 5 kriterli belge ayrıştırma ve kanıt etiketleme.
- Adım 6'da okunur: `skills/sicil-ve-imza/SKILL.md` — dinamik çapa metin hizalama, üstü çizme ve kaşe/imza basımı.

## Girdi kaynakları
- `takimlar/staj-burosu/durum.json` (`tarama_imleci` ve `kuyruk`)
- `ORTAK_SHEET_ID` (Salt-okunur; yalnızca `tarama_imleci` sonrasındaki yeni satırlar)
- `KISISEL_SHEET_ID` (`Atölye` sekmesi; okunmamış/revize sorguları ve satır boyama/not yazma)
- `sirket/mevzuat/staj-kurallari.md` ve `sirket/arsiv/ogrenciler/<ogrenci_no>.md`

## Çıktı sözleşmesi
- `# Staj İnceleme Raporu — <Öğrenci No> <Ad Soyad>`
- `| Kriter | Durum | Kanıt ve Sayfa Referansı |` tablosu (5 kriter eksiksiz)
- `## Önerilen Karar (Staj Tipi: Atölye, Önerilen Kabul Günü)`
- `## Eksik Evrak / E-posta Taslağı (Varsa)`
