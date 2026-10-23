---
name: tablo-ve-takvim
description: Google Sheets senkronizasyonu, holidays.Turkey ile tatil hesabı ve Türkçe doğal dil tarih ayrıştırma kuralları.
kaynak: https://github.com/burnash/gspread ve https://github.com/vacanza/python-holidays
lisans: MIT
---

# Tablo ve Takvim Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Resmi Tatili İş Günü Sayma Yasağı:** Türkiye Cumhuriyeti resmi ve dini tatilleri (`holidays.Turkey()`) kesinlikle iş günü olarak sayılamaz; hesaplamada otomatik düşülür.
2. **Ortak Tabloyu Bozma Yasağı:** Ortak Google Sheets tablosu (`1d3w-ejJArUhjwbzXYfR32HHqmSwbM4nmHJsESMDyq8M`) yalnızca **salt-okunur** olarak taranır; oraya asla doğrudan yazma veya boyama yapılamaz. Yazma ve boyama işlemleri yalnızca Alper'in kişisel takip tablosuna yapılır.
3. **Manuel Eşleştirme Çakışması:** Eşleşmeyen satırlar veya belirsiz tarihler otomatik varsayımla ezilemez; Alper'in dikkatine sunulur.

## 1. Kullanılan Kütüphaneler
- `gspread`: Google Sheets API üzerinden tabloları okuma ve kişisel tabloyu boyama/güncelleme.
- `holidays`: Türkiye resmi, dini ve milli tatil takvimi.
- `dateparser`: Türkçe metinlerden ve doğal dilden (*"haftaya cuma"*, *"15 Temmuz sonrası"*) standart ISO tarihleri üretme.

## 2. Gün Hesabı Protokolü
- İşe Başlangıç Tarihi: $T_{basla}$
- İşe Bitiş Tarihi: $T_{bitis}$
- Net İş Günü = $T_{basla}$ ile $T_{bitis}$ arasındaki pazar günleri ve resmi tatiller hariç kalan günler.
