---
name: sicil-ve-imza
description: Staj Sicil Fişi üzerinde dinamik çapa metin hizalama, olumsuz cümle üstü çizme, gün/tip ve şeffaf PNG imza basımı, OpenCV vesikalık kontrolü.
kaynak: https://github.com/pymupdf/PyMuPDF ve https://github.com/opencv/opencv
lisans: Apache-2.0
takimlar: [staj-burosu, bilgi-islem]
---

# Sicil ve İmza Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Onaysız İmza Yasağı:** Alper'in açık Telegram veya masaüstü onayı olmadan hiçbir belgeye ıslak imza basılamaz, `bin/sicil_imzala.py` tetiklenemez.
2. **Koordinat Tahmin Yasağı:** İmzanın veya yazıların koordinatları LLM tarafından tahmin edilemez. Sabit ROI alanları `sirket/sablonlar/sicil-haritasi.json` içinden, ince hizalamalar ise dinamik çapa metin aramasından alınır.
3. **İmza Dosyası İfşa Yasağı:** `sirket/sablonlar/imza.png` dosyası asla dışarı aktarılamaz veya git'e commit edilemez.

## 1. Kullanılan Kütüphaneler ve Yöntemler
- `PyMuPDF (fitz)`: Vektörel PDF manipülasyonu, çapa metin arama (`page.search_for`), çizgi çizme (`page.draw_line`) ve şeffaf PNG imza yerleştirme (`page.insert_image`).
- `OpenCV (cv2)`: Vesikalık fotoğraf alanında parlaklık/kontrast histogramı (kararma kontrolü), Laplacian varyansı (bulanıklık kontrolü) ve yüz tespiti.

## 2. Çapa Metin ve İmza Kuralları
- **Olumsuz Cümle Çizgisi:** Sayfada `"onaylanmamıştır"` kelimesi aranır ve tam kelime kutusunun ortasından yatay bir çizgi çekilir.
- **Staj Türü ve Gün:** Belirlenen koordinat kutusuna kabul edilen iş günü sayısı ve staj tipi (`Uzakyol` veya `Atölye`) satır hizasında yazılır.
- **Vesikalık Kontrolü:** Kırpılan vesikalık alanında ortalama piksel değeri çok düşükse (kararmış) veya çok yüksekse (patlamış) raporda `⚠️ Fotoğraf Kararmış/Bozuk` uyarısı verilir.
