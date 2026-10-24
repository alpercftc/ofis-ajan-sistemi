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

## 1. Kullanılan Kütüphaneler ve Standartlar
- `faster-whisper`: Telegram sesli notlarını yerel CPU/GPU üzerinde Türkçe metne dönüştürme.
- `imaplib` & `email`: Gmail gelen kutusunu Uygulama Şifresi ile tarama ve ekleri alma.
- `msal` & `pymsalruntime`: Kurumsal YTÜ e-postasını Microsoft Graph API üzerinden yerel WAM / DPAPI şifreli token önbelleğiyle okuma.
- Telegram Bot API: Birleşik Gündem butonları (`[ 📁 STAJ DEFTERLERİNİ AÇ ]`, `[ 📂 KLASÖRÜ PC'DE AÇ ]`).

## 2. İletişim Şablonları
- **Birleşik Gündem Bildirimi:** Tek üst mesajda tüm bekleyen işler özetlenir.
- **Öğrenci Onay Kartı:** Kanıt tablosu (staj günü, tarih uyumu, kurum kaşesi, defter gün doluluğu, soru kontrolü, görsel sayısı, vesikalık durumu) + önizleme butonları.
