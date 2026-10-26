---
name: ses-ve-iletisim
description: Telegram sesli notlarını yerel metne çevirme, Gmail ve kurumsal e-posta protokolü, Telegram onay kartları ve buton şablonları.
kaynak: https://github.com/SYSTRAN/faster-whisper ve https://github.com/AzureAD/microsoft-authentication-library-for-python
lisans: MIT
takimlar: [postaci, dekan]
---

# Ses ve İletişim Yeteneği

## ⛔ KESİN YASAKLAR VE NEGATİF SINIRLAR (Negative Constraints)
1. **Onaysız E-Posta Gönderme Yasağı:** Alper'in açık Telegram onayı olmadan hiçbir e-posta dışarıya gönderilemez; yalnızca taslak oluşturulabilir.
2. **Posta Silme Yasağı:** Gelen e-postalar Alper'in açık emri olmadan asla kalıcı olarak silinemez.
3. **Bulut Ses API'si Yasağı:** Alper'in sesli notları dış bulut servislerine gönderilemez; yerel makinede `faster-whisper` ile çözülür.
4. **Telegram'da Yatay Boru Tablosu (`|---|---|`) ve İç Sistem Özeti Yasağı:** Telegram mesajlarında `| Sütun 1 | Sütun 2 |` şeklinde yatay boru tabloları, `[dosya](file:///...)` linkleri ve `durum.json`/`defter.md` güncellendiğine dair iç sistem özetleri kesinlikle yazılmaz.

## 1. Kullanılan Kütüphaneler ve Standartlar
- `faster-whisper`: Telegram sesli notlarını yerel CPU/GPU üzerinde Türkçe metne dönüştürme.
- `imaplib` & `email`: Gmail gelen kutusunu Uygulama Şifresi ile tarama ve ekleri alma.
- `msal` & `pymsalruntime`: Kurumsal YTÜ e-postasını Microsoft Graph API üzerinden yerel WAM / DPAPI şifreli token önbelleğiyle okuma.

## 2. İletişim ve Telegram Kart Şablonları
- **Birleşik Gündem Bildirimi:** Tek üst mesajda tüm bekleyen işler özetlenir.
- **Öğrenci Onay / Revize Kartı:** Mobil ekranda asla kaymayan dikey kutu (`┌ ├ └`) formatında 5 kriterli kanıt kartı (`📋 1. Sicil Fişi`, `📓 2. Staj Defteri`, `🏛️ 3. SGK Giriş-Çıkış`, `⭐ 4. Kurum Uygunluğu`, `📊 5. Kümülatif Gün / Karar`).

## 3. Öğrenilenler
- Telegram üzerinden rapor veya öğrenci analizi istendiğinde yatay Markdown tablosu (`|...|`) yerine her öğrencinin altında `┌ ├ └` ağaç/kutu satırları ve `✅ / ❌ / ⚠️` emojileri bulunan dikey kartlar kullanılmalıdır.
