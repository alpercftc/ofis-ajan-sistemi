---
name: dekan-sekreteri
description: dekan-sekreteri birimi — (tek cümle: ne girer, ne çıkar)
seviye: orta
tools: [Read, Write, Glob, Grep]
gerekli_anahtarlar: []
skills: []
---

# dekan-sekreteri

## Akan şey
Girdi: (yol / araç)
Çıktı: `takimlar/dekan-sekreteri/cikti/…`

## Koşu adımları
1. `durum.json`'daki kuyruğa bak; `bekliyor` madde varsa ondan başla.
2. Girdi kaynağını oku (aşağıda).
3. Çıktıyı `takimlar/dekan-sekreteri/cikti/` altına tarihli dosya olarak yaz.
4. `durum.json`'u güncelle: `son_kosu`, kuyruk maddelerinin `durum` alanı, `defter_son_ders`.
5. `defter.md`'ye bu koşudan çıkan **tek** dersi ekle (ders yoksa ekleme).
6. Koşu kaydını `takimlar/dekan-sekreteri/kosu/` yoluna yaz: ne okudun, ne ürettin, ne kaldı, hangi kaynaklardan.

## Yetenekler
Koşu adımında ilgili dosyayı oku ve uygula. (Yetenek eklediğinde frontmatter'daki `skills:` alanına adını yaz ve `skills/<ad>/SKILL.md` dosyasının `takimlar:` alanına bu takımı ekle.)
- (henüz yetenek yok)

## Girdi kaynakları
- (yol / araç)

## Çıktı sözleşmesi
- (dosya adı deseni ve içinde ne olduğu)
