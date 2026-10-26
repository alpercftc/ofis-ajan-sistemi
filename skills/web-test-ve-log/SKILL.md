---
name: web-test-ve-log
description: Araç geliştirme standartları (typer), pytest birim test zorunluluğu, ruff linter kuralları ve endüstriyel metin log standartları.
kaynak: https://github.com/fastapi/typer ve https://github.com/pytest-dev/pytest
lisans: MIT
takimlar: [ik-memuru, bilgi-islem]
---

# Web, Test ve Log Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Testsiz Araç Kaydetme Yasağı:** `tests/` altında birim testi yazılmamış ve `pytest` ile doğrulanmamış hiçbir betik `bin/` altına kalıcı araç olarak eklenemez.
2. **Log Dosyalarına Emoji Basma Yasağı:** Kod içi açıklama satırlarında emoji bulunabilir; ancak konsol, terminal ve disk log dosyalarına kesinlikle emoji basılamaz. Endüstriyel `[BİLGİ]`, `[UYARI]`, `[HATA]` formatı zorunludur.
3. **Yetkisiz Dış İstek Yasağı:** Üniversite iç duyuruları haricinde rastgele dış web sitelerine izinsiz web scraping yapılamaz.

## 1. Kullanılan Kütüphaneler ve Standartlar
- `typer`: Modern, tip güvenli CLI arayüzleri.
- `pytest`: Birim ve entegrasyon testleri.
- `ruff`: Kod kalitesi ve PEP 8 linter kontrolü.
- `Crawl4AI`: Üniversite ve bölüm web duyurularını yapılandırılmış metne çevirme.

## 2. Log Standartları
- `[BİLGİ] YYYY-MM-DD HH:MM:SS - Görev başlatıldı: <gorev_id>`
- `[UYARI] YYYY-MM-DD HH:MM:SS - Eksik evrak tespit edildi: <ogrenci_no>`
- `[HATA]  YYYY-MM-DD HH:MM:SS - Dosya ayrıştırma hatası: <hata_detayi>`

## Öğrenilenler
- **Windows UTF-8 Akış ve Konsol Çıktı Standardı:** Windows `cp1254` konsolunda standart `print` çağrıları `→` (`\u2192`) gibi Unicode sembollerinde `UnicodeEncodeError` verebilir. Modül seviyesinde (`ayar.py` ve `tests/__init__.py`) `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` uygulanmalı, konsol çıktılarında güvenli ASCII `->` sembolleri tercih edilmelidir. Ayrıca Türkçe arama ve karşılaştırmalarda `replace('İ', 'i').replace('I', 'ı')` adımı `.lower()` öncesinde uygulanmalıdır.

