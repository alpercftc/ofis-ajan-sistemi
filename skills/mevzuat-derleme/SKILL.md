---
name: mevzuat-derleme
description: Üniversite staj yönergeleri, yönetmelikler ve denetim kılavuzlarını yapılandırılmış kural maddelerine dönüştürme protokolü.
kaynak: https://github.com/DS4SD/docling
lisans: MIT
---

# Mevzuat Derleme Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Kural Esnetme Yasağı:** Yönergedeki kesin şartlar (örneğin "en az 20 iş günü", "kurum kaşesi zorunludur") ajan tarafından kendi kendine esnetilemez veya yumuşatılamaz.
2. **Kişisel Yorum Katma Yasağı:** Mevzuat maddelerine kişisel tavsiye veya yorum eklenemez. Madde ne diyorsa doğrudan o aktarılır.
3. **Tekrarlı Ağır PDF Okuma Yasağı:** Bir yönetmelik bir kez derlendikten sonra `sirket/mevzuat/kurallar/` altına kaydedilir. Diğer ajanlar ham PDF'i tekrar okuyamaz, yalnızca derlenmiş `.md` dosyasını okur.

## 1. Kullanılan Kütüphaneler
- `IBM Docling`: Çok sayfalı, iki sütunlu ve karmaşık tablolar içeren resmi yönerge ve yönetmelik PDF'lerini yapısal Markdown'a çevirme.

## 2. Derleme Standardı
- Her yönerge şu formatta derlenir:
  - `MADDE_NO`: Konu başlığı
  - `ZORUNLU_SARTLAR`: Sağlanması gereken kesin kurallar listesi
  - `GECERSIZLIK_HALLERI`: Stajın veya evrakın reddedilmesini gerektiren durumlar
  - `ESNEKLIK_ALANI`: Yalnızca patronun (Alper'in) inisiyatifinde olan alanlar
