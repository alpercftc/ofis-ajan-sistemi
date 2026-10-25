# Kurallar — staj-burosu

> Müfettiş bu dosyayı okur ve koşu kaydını buna göre denetler. Yalnızca insan (Alper) değiştirir.

## Neye göre çalışır
- `ANAYASA.md` ve `sirket/AJAN-KIMLIGI.md`'nin tamamı; özellikle Madde 1 (onaysız imza/gönderim yasağı), Madde 2 (sıfır uydurma) ve Madde 4 (`1 Koşu = 1 Öğrenci` ve anında temizlik).
- Yalnızca Kişisel Tablonun `Atölye` sekmesi aktiftir (`Uzakyol` komisyonu görevi sona erdiği için `Uzakyol` sekmesi taranmaz).
- Ortak Tablo (`ORTAK_SHEET_ID`) taramasında `durum.json` içindeki `tarama_imleci`'nden sonraki satırlar okunur ve Alper'e yeni atananlar anında Kişisel Tablonun (`Atölye`) sonuna boyasız olarak eklenir.

## Asla yapmaz
- Alper'den açıkça "İncele / Başla" onayı gelmeden (yeni atanan 1 öğrenci bile olsa) Drive ZIP paketini indirip evrak analizine başlamaz; önce sadece listeler.
- "Okunmamış defter var mı?" veya "Kimlere revize verdik?" sorularında Ortak Tabloyu baştan taramaz; doğrudan Kişisel Tablonun `Atölye` sekmesindeki boyasız satırlara (`Not` boş = okunmamış, `Not` dolu = revize) bakar.
- ZIP paketinde olmayan belge için tarih veya gün sayısı tahmin etmez; tabloya `⛔ Belge Yok` yazar.
- Alper'in onayı olmadan `bin/sicil_imzala.py` çalıştırmaz, Komisyon Başkanına (`ahmkaya@yildiz.edu.tr`) e-posta göndermez ve Kişisel Tablodaki satırı yeşile boyamaz.
- İmzalanıp doldurulan `FR-1323` Staj Sicil Formunu ve maile eklenecek PDF/defter dosyalarını (`sirket/arsiv/gecici/<ogrenci_no>/`), Alper imzalı formu görüp e-posta gönderim onayını verene ve e-posta Komisyon Başkanına (`ahmkaya@yildiz.edu.tr`) PDF ekleriyle birlikte fiilen gönderilene kadar **asla silmez**.
- `ORTAK_SHEET_ID` tablosuna hiçbir koşulda yazma veya boyama yapmaz (salt-okunur).
- Bir koşuda birden fazla öğrenci işlemez.

## Çıktı kalite ölçütleri
- 5 inceleme kriterinin tamamında rozet (`✅ Tam Uygun` / `🟡 Uyarı` / `⛔ Belge Yok`) + belge adı ve sayfa numarası referansı bulunur.
- Onaylanan öğrencinin imzalı `FR-1323` Staj Sicil Formu ve ilgili PDF'leri e-posta gönderimine kadar `sirket/arsiv/gecici/<ogrenci_no>/` altında korunur; Komisyon Başkanına (`ahmkaya@yildiz.edu.tr`) e-posta gönderildikten hemen sonra geçici dosyalar silinip yalnızca `sirket/arsiv/ogrenciler/<ogrenci_no>.md` profil kartı bırakılır.
