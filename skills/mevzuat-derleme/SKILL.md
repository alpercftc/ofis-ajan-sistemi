---
name: mevzuat-derleme
description: Üniversite staj yönergeleri, yönetmelikler ve denetim kılavuzlarını iki modlu (Tekil Kural .md ve Bölümlü/İndeksli index_<dokuman>.md + bölüm .md) yapıya dönüştürme protokolü.
kaynak: https://github.com/DS4SD/docling
lisans: MIT
takimlar: [dekan-sekreteri, memur]
---

# Mevzuat Derleme Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Kural Esnetme Yasağı:** Yönergedeki kesin şartlar (örneğin "en az 15 iş günü", "kurum kaşesi zorunludur") ajan tarafından kendi kendine esnetilemez veya yumuşatılamaz.
2. **Kişisel Yorum Katma Yasağı:** Mevzuat maddelerine kişisel tavsiye veya yorum eklenemez. Madde ne diyorsa doğrudan `[Madde X, Sayfa Y]` referansıyla aktarılır.
3. **Tekrarlı Ağır PDF ve Tüm Klasör Okuma Yasağı:**
   - Bir yönetmelik veya kılavuz derlendikten sonra diğer ajanlar ham PDF'i tekrar okuyamaz.
   - Bölümlere ayrılmış kılavuzlarda (`sirket/mevzuat/<dokuman_adi>/`) hiçbir ajan tüm bölüm dosyalarını aynı anda okuyamaz; **önce yalnızca `index_<dokuman_adi>.md` dosyasını okur**, aradığı bilginin hangi bölümde olduğunu bulur ve **yalnızca ilgili `bolum-XX-<slug>.md` dosyasını** açar.

## 1. İki Modlu Derleme Standardı

### Mod A · Varsayılan Tekil Kural Modu (`--mod tekil`)
**GMİM Staj Uygulama Esasları** (Gemi Makineleri İşletme Mühendisliği Bölümü staj kuralları) ve genel Staj Yönergesi gibi her koşuda tamamı kontrol edilen kurallar için tek bir `.md` dosyası (`sirket/mevzuat/staj-kurallari.md`) üretilir:
- `KURAL_ID` ve Konu Başlığı
- `ZORUNLU_SARTLAR` (`EĞER / İSE` atomik kural cümlesi + `[Madde X, Sayfa Y]`)
- `GECERSIZLIK_HALLERI` ve `ESNEKLIK_ALANI` (Alper'in inisiyatifinde olanlar)

### Mod B · Bölümlü ve İndeksli Kılavuz Modu (`--mod bolumlu`)
MÜDEK denetim kılavuzu gibi çok bölümlü (Chapter / Ölçüt) büyük dokümanlar için `sirket/mevzuat/<dokuman_adi>/` klasörü altında:
1. **`index_<dokuman_adi>.md` (Referans İndeks Dosyası):**
   ```markdown
   # İndeks — <Doküman Adı>
   | Bölüm & Alt Başlıklar | Dosya Adresi | Aranan Bilgi & Anahtar Kavramlar | Sayfa Aralığı | İlgili Bölümler |
   | :--- | :--- | :--- | :--- | :--- |
   ```
2. **`bolum-01-<slug>.md`, `bolum-02-<slug>.md` ...:**
   Her ana bölümün kendi alt başlıklarını ve sayfa numaralarını koruyan bağımsız `.md` dosyaları.
