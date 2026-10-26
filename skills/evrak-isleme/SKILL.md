---
name: evrak-isleme
description: PDF, Word (.docx) ve görselleri bağlamı şişirmeden yapılandırılmış temiz Markdown formatına dönüştürme kuralları.
kaynak: https://github.com/microsoft/markitdown ve https://github.com/pymupdf/PyMuPDF
lisans: MIT
takimlar: [staj-burosu, dekan-sekreteri, memur]
---

# Evrak İşleme Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Asla Veri Uydurma:** Belgede veya ZIP içeriğinde açıkça bulunmayan tarih, gün sayısı, kurum adı veya imza varlığı hakkında asla varsayımda bulunulamaz. Belge yoksa sonuç hücresine istisnasız `❌ Yok` yazılır.
2. **Edebi Özetleme Yasağı:** 30-40 sayfalık staj defteri veya resmi kılavuzlar edebi metin olarak özetlenemez. Yalnızca başlıklar, soru cevaplarının doluluğu, gün sayısı ve gömülü görsel adedi taranır.
3. **Bellek Şişirme Yasağı:** Ham PDF veya Word içeriği doğrudan prompta yapıştırılamaz; daima `bin/evrak_hazirla.py` ile dönüştürülen standart `hazir_paket.md` çıktısı kullanılır.
4. **Telegram'da Yatay Boru Tablosu (`|---|---|`) Yasağı:** Telegram mobil ekranında `| Sütun 1 | Sütun 2 |` şeklindeki geniş yatay Markdown tabloları kayarak okunaksız hale gelir. Telegram'a gidecek yanıtlarda kesinlikle yatay boru tablosu (`|`) kullanılmaz; bunun yerine aşağıdaki **Dikey Kutu Kartı (`┌ ├ └`)** şablonu kullanılır.

## 1. Kullanılan Kütüphaneler ve Standartlar
- `Microsoft MarkItDown`: Word (.docx), Excel ve düz metin dönüşümleri.
- `PyMuPDF (fitz)` & `PyMuPDF4LLM`: PDF sayfa ayrıştırma, tablo yakalama ve gömülü görsel (`len(page.get_images())`) sayımı.
- `python-docx`: Word şablonu içindeki tabloları ve günlük kayıtlarını ayrıştırma.

## 2. Çalışma Standartları
- Belgeler dosya adına göre değil (`1.pdf`, `Doc1.pdf` yanıltıcı olabilir), içindeki anahtar metin kalıplarına göre tespit edilir:
  - "STAJ SİCİL FORMU" / "PRATİK ÇALIŞMA" ➔ Staj Sicil Fişi
  - "SGK" / "4A İŞE GİRİŞ" / "SİGORTALI İŞE GİRİŞ BİLDİRGESİ" ➔ SGK Belgesi
  - "GÜNLÜK ÇALIŞMA" / "SORULAR" / "İŞ RAPORU" ➔ Staj Defteri

## 3. Telegram Dikey Öğrenci Analiz Kartı Şablonu (Zorunlu Standart)
Telegram'a gönderilecek staj inceleme ve revize raporlarında (Soner ŞENGÜL örnek raporunda olduğu gibi) her öğrenci için asla bozulmayan şu dikey kart şablonu kullanılır:

```text
🎓 *200A3609 — SONER ŞENGÜL* (`✅ ONAY` veya `❌ REVİZE`)
📧 `ogrenci@eposta.com` | 🏢 *Kurum:* Unikal Kalibrasyon Ltd. Şti.
┌ 📋 *1. Sicil Fişi (FR-1323):* ✅ Tam Uygun (Vesikalık + Mühendis Kaşe/İmza tam)
├ 📓 *2. Staj Defteri (FR-0955):* ✅ 19 dolu gün | 77/80 soru | 22 görsel
├ 🏛️ *3. SGK Giriş-Çıkış (4A):* ✅ 10.08.2026 – 31.08.2026 (19 iş günü uyumlu)
├ ⭐ *4. Kurum Notu (FR-1392):* ✅ Çok İyi (4 Gemi Mak. Mühendisi mevcut)
└ 📊 *5. Kümülatif Gün Hesabı:* ✅ 64 + 35 (Muafiyet) + 19 = *118 / 115 gün*
🎯 *Karar / Aksiyon:* 19 iş günü Atölye stajı kabul edildi (veya eksik evrak listesi).
```

## Öğrenilenler
- **Telegram Mobil Uyumluluk Kuralı:** Telegram yanıtlarında yatay `| Sütun | Sütun |` boru tabloları ve `file:///` dosya linkleri veya iç sistem (`durum.json`, `ANAYASA.md`) açıklamaları asla yer almamalıdır; yalnızca `┌ ├ └` dikey öğrenci kartları ve emoji tık işaretleri (`✅`, `❌`, `⚠️`) kullanılmalıdır.
