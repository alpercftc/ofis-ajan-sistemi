# Kurallar — bilgi-islem

> Müfettiş bu dosyayı okur ve koşu kaydını buna göre denetler. Yalnızca insan (Alper) değiştirir.

## Neye göre çalışır
- `ANAYASA.md` ve `sirket/AJAN-KIMLIGI.md`'nin tamamı; özellikle yetki sınırları ve test zorunluluğu.
- `skills/web-test-ve-log/SKILL.md` ve `skills/sicil-ve-imza/SKILL.md` kuralları.

## Asla yapmaz
- Yetki sınırını aşıp `ANAYASA.md`, `takimlar/*/kurallar.md` veya `takimlar/*/takim.md` dosyalarını değiştirmez (yalnızca `bin/*.py`, `tests/*.py` ve `sirket/sablonlar/*.json` dosyalarına dokunur).
- Birim testi (`tests/test_*.py`) yazılmamış veya testi başarısız olan bir aracı `tamam` / `denetim_bekliyor` olarak işaretlemez.
- Konsol veya disk loglarına emoji basmaz; endüstriyel `[BİLGİ]`, `[UYARI]`, `[HATA]` formatını kullanır.
- `.env` dosyasını okumaz ve `C:\Alper\vBeyin` dizinine dokunmaz.

## Çıktı kalite ölçütleri
- Her araç için birim testleri (`py -3 -m unittest`) %100 başarılıdır.
- Çıktı Türkçe; teknik terimler ve kod sembolleri orijinal hâliyle kalır.
