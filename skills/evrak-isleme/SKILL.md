---
name: evrak-isleme
description: PDF, Word (.docx) ve görselleri bağlamı şişirmeden yapılandırılmış temiz Markdown formatına dönüştürme kuralları.
kaynak: https://github.com/microsoft/markitdown ve https://github.com/pymupdf/PyMuPDF
lisans: MIT
takimlar: [staj-burosu, dekan-sekreteri]
---

# Evrak İşleme Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Asla Veri Uydurma:** Belgede veya ZIP içeriğinde açıkça bulunmayan tarih, gün sayısı, kurum adı veya imza varlığı hakkında asla varsayımda bulunulamaz. Belge yoksa sonuç hücresine istisnasız `⛔ Belge Yok` yazılır.
2. **Edebi Özetleme Yasağı:** 30-40 sayfalık staj defteri veya resmi kılavuzlar edebi metin olarak özetlenemez. Yalnızca başlıklar, soru cevaplarının doluluğu, gün sayısı ve gömülü görsel adedi taranır.
3. **Bellek Şişirme Yasağı:** Ham PDF veya Word içeriği doğrudan prompta yapıştırılamaz; daima `bin/evrak_hazirla.py` ile dönüştürülen standart `hazir_paket.md` çıktısı kullanılır.

## 1. Kullanılan Kütüphaneler ve Standartlar
- `Microsoft MarkItDown`: Word (.docx), Excel ve düz metin dönüşümleri.
- `PyMuPDF (fitz)` & `PyMuPDF4LLM`: PDF sayfa ayrıştırma, tablo yakalama ve gömülü görsel (`len(page.get_images())`) sayımı.
- `python-docx`: Word şablonu içindeki tabloları ve günlük kayıtlarını ayrıştırma.

## 2. Çalışma Standartları
- Belgeler dosya adına göre değil (`1.pdf`, `Doc1.pdf` yanıltıcı olabilir), içindeki anahtar metin kalıplarına göre tespit edilir:
  - "STAJ SİCİL FORMU" / "PRATİK ÇALIŞMA" ➔ Staj Sicil Fişi
  - "SGK" / "4A İŞE GİRİŞ" / "SİGORTALI İŞE GİRİŞ BİLDİRGESİ" ➔ SGK Belgesi
  - "GÜNLÜK ÇALIŞMA" / "SORULAR" / "İŞ RAPORU" ➔ Staj Defteri
