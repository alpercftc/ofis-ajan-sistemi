---
name: tablo-ve-takvim
description: Google Sheets senkronizasyonu (Atölye imleç takibi ve satır boyama), holidays.Turkey ile tatil hesabı ve Türkçe doğal dil tarih ayrıştırma kuralları.
kaynak: https://github.com/burnash/gspread ve https://github.com/vacanza/python-holidays
lisans: MIT
takimlar: [staj-burosu]
---

# Tablo ve Takvim Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Resmi Tatili İş Günü Sayma Yasağı:** Türkiye Cumhuriyeti resmi ve dini tatilleri (`holidays.Turkey()`) kesinlikle iş günü olarak sayılamaz; hesaplamada otomatik düşülür.
2. **Ortak Tabloyu Bozma ve Baştan Tarama Yasağı:** Ortak Google Sheets tablosu (`1d3w-ejJArUhjwbzXYfR32HHqmSwbM4nmHJsESMDyq8M`) yalnızca **salt-okunur** olarak ve yalnızca `takimlar/staj-burosu/durum.json` içindeki `tarama_imleci` (son öğrenci / zaman damgası / satır) sonrasından itibaren taranır. Ortak tabloya asla yazma veya boyama yapılamaz.
3. **Uzakyol Sekmesi Tarama Yasağı:** Alper artık Uzakyol staj komisyonunda olmadığı için Kişisel Tabloda yalnızca **`Atölye`** sekmesi taranır ve güncellenir.
4. **Onaysız Yeşile Boyama Yasağı:** Alper'in nihai onayı olmadan Kişisel Tablodaki hiçbir öğrenci satırı yeşile boyanamaz.

## 1. Kullanılan Kütüphaneler
- `gspread` & `openpyxl`: Google Sheets API / Excel üzerinden tabloları okuma, `Atölye` sekmesine yeni satır ekleme, `A (Not)` sütununa revize yazma ve onaylanan satırı yeşile boyama.
- `holidays`: Türkiye resmi, dini ve milli tatil takvimi.
- `dateparser`: Türkçe metinlerden ve doğal dilden standart ISO tarihleri üretme.

## 2. Kişisel Tablo (`Atölye`) Sütun ve Renk Sözleşmesi
- **Sütun Yapısı (`A`–`I`):**
  - `A`: `Not` (Eksik evrak / revize açıklaması; ör. `"staj sicil eksik"`, `"foto eksik mail atıldı"`)
  - `B`: `Yetkili Akademik Personel` (`"Alper ÇİFTÇİ"`)
  - `C`: `Zaman damgası`
  - `D`: `E-posta Adresi`
  - `E`: `Öğrenci No`
  - `F`: `Bölümünüz`
  - `G`: `İsim Soyisim`
  - `H`: `Staj Türünü Seçiniz`
  - `I`: `Defter Teslim Evrak Dosyanızı Yükleyiniz` (Drive linki)
- **Durum ve Renk Kuralları:**
  - **Okunmamış / Yeni Atanan:** Satır **Boyasız (`Fill: None` / Beyaz)** ve `A (Not)` sütunu **boş**.
  - **Revize / Eksik Evrak Bekleyen:** Satır **Boyasız (`Fill: None` / Beyaz)** ve `A (Not)` sütunu **dolu** (eksiklik açıklaması yazılı).
  - **Onaylanmış ve İmzalanmış:** Satır **Yeşile Boyalı (`solid` yeşil dolgu / `#D9EAD3`)**.

## 3. Gün Hesabı Protokolü
- İşe Başlangıç Tarihi: $T_{basla}$
- İşe Bitiş Tarihi: $T_{bitis}$
- Net İş Günü = $T_{basla}$ ile $T_{bitis}$ arasındaki pazar günleri ve resmi tatiller hariç kalan günler.
