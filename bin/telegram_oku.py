#!/usr/bin/env python3
"""Telegram gelen kutusu ve mesaj biçimlendirici (telegram_oku.py).

Kullanım:
  py -3 bin/telegram_oku.py --chat-id-bul   # bota bir mesaj at, sonra bunu koş, çıkanı .env'e yaz
  py -3 bin/telegram_oku.py --son 5         # son mesajları bas (durum değişmez)
  py -3 bin/telegram_oku.py --isle          # yeni mesajları takimlar/postaci/gelen/ altına yaz

Çıkış kodları: 0 tamam · 1 anahtar eksik · 2 token geçersiz (Telegram 401/403) · 3 ulaşılamadı (ağ).
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

TAKIM = "postaci"
URL = re.compile(r"https?://\S+")

TOKEN_KODU = 2      # 401/403 — token geçersiz
AG_KODU = 3         # ağ/sunucu — sonra tekrar denenebilir
PARCA_SINIRI = 3800


class TelegramHatasi(Exception):
    """Telegram API'si reddetti ya da ulaşılamadı. `kod` çıkış kodudur (2 token, 3 ağ)."""

    def __init__(self, mesaj, kod):
        super().__init__(mesaj)
        self.kod = kod


def _markdown_tablolarini_karta_cevir(metin: str) -> str:
    """
    Telegram'da bozulan Markdown boru tablolarını (`| Sütun 1 | Sütun 2 |`)
    mobil ekranda asla kaymayan dikey kutu kartlarına (`┌ ├ └`) dönüştürür.
    """
    satirlar = metin.splitlines()
    yeni_satirlar = []
    i = 0
    while i < len(satirlar):
        satir = satirlar[i].strip()
        if satir.startswith("|") and satir.endswith("|") and i + 1 < len(satirlar):
            ayirici = satirlar[i + 1].strip()
            if ayirici.startswith("|") and set(ayirici.replace("|", "").replace(":", "").replace("-", "").strip()) == set():
                basliklar = [h.strip().strip("*").strip() for h in satir.strip("|").split("|")]
                i += 2
                kartlar = []
                while i < len(satirlar) and satirlar[i].strip().startswith("|") and satirlar[i].strip().endswith("|"):
                    hucreler = [c.strip() for c in satirlar[i].strip().strip("|").split("|")]
                    if any(hucreler):
                         # 2 veya 3 sütunlu (Alan | Durum | Kanıt) tek öğrenci kriter tablosu mu?
                        if len(basliklar) <= 3 and any(k in basliklar[0].lower() for k in ("kriter", "alan", "belge")):
                            ilk = hucreler[0] if len(hucreler) > 0 else ""
                            ikinci = hucreler[1] if len(hucreler) > 1 else ""
                            ucuncu = hucreler[2] if len(hucreler) > 2 else ""
                            satir_str = f"• {ilk}: {ikinci}" + (f" — {ucuncu}" if ucuncu else "")
                            kartlar.append(satir_str)
                        else:
                            # Çok sütunlu öğrenci tablosu -> Dikey Öğrenci Kartı
                            baslik_parca = []
                            detaylar = []
                            for idx, deger in enumerate(hucreler):
                                sutun_adi = basliklar[idx] if idx < len(basliklar) else f"Alan {idx+1}"
                                if idx < 3 and sutun_adi.lower() in ("no", "sıra", "öğrenci no", "isim soyisim", "adı soyadı", "ad soyad"):
                                    baslik_parca.append(deger)
                                else:
                                    detaylar.append((sutun_adi, deger))
                            kart_satirlari = [f"🎓 {' — '.join(baslik_parca)}" if baslik_parca else "🎓 Kayıt"]
                            for d_idx, (k_ad, k_deg) in enumerate(detaylar):
                                on_ek = "┌" if d_idx == 0 else ("└" if d_idx == len(detaylar) - 1 else "├")
                                kart_satirlari.append(f"{on_ek} *{k_ad}:* {k_deg}")
                            kartlar.append("\n".join(kart_satirlari))
                    i += 1
                yeni_satirlar.append("\n\n".join(kartlar))
                continue
        yeni_satirlar.append(satirlar[i])
        i += 1
    return "\n".join(yeni_satirlar)


def _telegram_icin_temizle(metin: str) -> str:
    """
    Ajan iç sistem notlarını (`🛡️ Güvenlik...`, `**Özet:**...`, `file:///` linklerini) temizler
    ve Markdown tablolarını mobil uyumlu dikey kartlara çevirir.
    """
    # 1. [etiket](file:///...) linklerini sadece `etiket` yap
    metin = re.sub(r"\[([^\]]+)\]\(file:///[^\)]+\)", r"`\1`", metin)
    # 2. İç sistem/kural/dosya kapanış paragraflarını kırp
    Temiz_satirlar = []
    for satir in metin.splitlines():
        s_str = satir.strip()
        if s_str.startswith("🛡️") and ("ANAYASA" in s_str or "durum.json" in s_str or "SIRKET_KOSU" in s_str):
            continue
        if (s_str.startswith("**Özet:**") or s_str.startswith("Özet:")) and (
            "durum.json" in s_str or "defter.md" in s_str or "görev başarıyla tamamlanmıştır" in s_str
        ):
            continue
        Temiz_satirlar.append(satir)
    metin = "\n".join(Temiz_satirlar).strip()
    # 3. Markdown boru tablolarını dikey Telegram kartlarına çevir
    metin = _markdown_tablolarini_karta_cevir(metin)
    # 4. Fazla yatay çizgileri (`---`) zarif ayırıcıya çevir
    metin = re.sub(r"(?m)^\s*---\s*$", "━━━━━━━━━━━━━━━━━━━━━━", metin)
    return metin.strip()


def _md_to_telegram_html(metin: str) -> str:
    """
    CommonMark / Markdown metnini Telegram'ın hatasız işlediği HTML (`<b>`, `<i>`, `<code>`, `<pre>`)
    formatına dönüştürür.
    """
    kod_bloklari = []

    def _kod_blok_sakla(eslesme):
        icerik = html.escape(eslesme.group(1).strip("\r\n"))
        kod_bloklari.append(f"<pre>{icerik}</pre>")
        return f"@@KODBLOK{len(kod_bloklari) - 1}@@"

    metin = re.sub(r"```(?:[a-zA-Z0-9_-]+)?\n(.*?)```", _kod_blok_sakla, metin, flags=re.DOTALL)

    satir_kodlari = []

    def _satir_ici_kod_sakla(eslesme):
        icerik = html.escape(eslesme.group(1))
        satir_kodlari.append(f"<code>{icerik}</code>")
        return f"@@SATIRKOD{len(satir_kodlari) - 1}@@"

    metin = re.sub(r"`([^`\n]+)`", _satir_ici_kod_sakla, metin)

    # Kalan metni HTML escape et
    metin = html.escape(metin)

    # Başlıkları (### Başlık) kalın satıra çevir
    metin = re.sub(r"(?m)^\s*#{1,6}\s+(.+)$", r"<b>\1</b>", metin)
    # **kalın** -> <b>kalın</b>
    metin = re.sub(r"\*\*([^\*\n]+)\*\*", r"<b>\1</b>", metin)
    # *kalın/vurgu* -> <b>vurgu</b>
    metin = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<b>\1</b>", metin)
    # _italik_ -> <i>italik</i> (yalnızca kelime sınırlarında, dosya adlarını bozmadan)
    metin = re.sub(r"(?<![A-Za-z0-9])_([^_\n]+)_(?![A-Za-z0-9])", r"<i>\1</i>", metin)

    for idx, kod_html in enumerate(satir_kodlari):
        metin = metin.replace(f"@@SATIRKOD{idx}@@", kod_html)
    for idx, blok_html in enumerate(kod_bloklari):
        metin = metin.replace(f"@@KODBLOK{idx}@@", blok_html)

    return metin


def _tek_parca_gonder(token: str, chat_id: int, parca: str) -> bool:
    html_parca = _md_to_telegram_html(parca)
    for yuk in (
        {"chat_id": chat_id, "text": html_parca, "parse_mode": "HTML"},
        {"chat_id": chat_id, "text": parca},
    ):
        try:
            veri = json.dumps(yuk, ensure_ascii=False).encode("utf-8")
            istek = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=veri,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "ofis-ajan-sistemi/1.0",
                },
            )
            with urllib.request.urlopen(istek, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    return True
        except Exception:
            continue
    return False


def mesaj_gonder(token: str, chat_id: int, metin: str) -> bool:
    """Telegram üzerinden kullanıcıya mobil uyumlu, dikey kart formatlı saf UTF-8 mesaj gönderir."""
    metin = _telegram_icin_temizle(str(metin or ""))
    if not metin:
        return False
    if len(metin) <= PARCA_SINIRI:
        return _tek_parca_gonder(token, chat_id, metin)

    parcalar = []
    kalan = metin
    while kalan:
        if len(kalan) <= PARCA_SINIRI:
            parcalar.append(kalan)
            break
        kesim = kalan.rfind("\n", 0, PARCA_SINIRI)
        if kesim <= 0:
            kesim = PARCA_SINIRI
        parcalar.append(kalan[:kesim].strip())
        kalan = kalan[kesim:].strip()

    basarili = True
    for parca in parcalar:
        if parca and not _tek_parca_gonder(token, chat_id, parca):
            basarili = False
    return basarili


def _api(token, yontem, **parametreler):
    sorgu = urllib.parse.urlencode(
        {k: v for k, v in parametreler.items() if v is not None},
        encoding="utf-8",
    )
    istek = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{yontem}?{sorgu}",
        headers={"User-Agent": "ofis-ajan-sistemi/1.0"},
    )
    try:
        with urllib.request.urlopen(istek, timeout=20 + int(parametreler.get("timeout") or 0)) as yanit:
            veri = json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise TelegramHatasi(
                f"telegram: token geçersiz ({exc.code}) — `.env` içindeki TELEGRAM_BOT_TOKEN'ı "
                "@BotFather'dan aldığın değerle karşılaştır",
                TOKEN_KODU,
            ) from exc
        raise TelegramHatasi(f"telegram: sunucu hatası ({exc.code})", AG_KODU) from exc
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        raise TelegramHatasi(f"telegram: ulaşılamadı — {type(exc).__name__}", AG_KODU) from exc
    return veri.get("result", []) if veri.get("ok") else []


def guncellemeleri_cek(token, offset=None, bekleme=0):
    """`bekleme` saniye long-poll bekler (0 ise anında döner). `bin/telegram_dinle.py` 15 verir."""
    return _api(token, "getUpdates", offset=offset, timeout=bekleme, allowed_updates='["message"]')


def chat_idleri(guncellemeler):
    gorulen = []
    for g in guncellemeler:
        cid = (g.get("message") or {}).get("chat", {}).get("id")
        if cid is not None and cid not in gorulen:
            gorulen.append(cid)
    return gorulen


def _mesaj(g):
    m = g.get("message") or {}
    metin = m.get("text") or m.get("caption") or ""
    zaman = datetime.fromtimestamp(m.get("date", 0), tz=timezone.utc).astimezone()
    ek_turu = None
    dosya_id = None
    dosya_adi = None
    if m.get("document"):
        ek_turu = "belge"
        dosya_id = m["document"].get("file_id")
        dosya_adi = m["document"].get("file_name")
    elif m.get("voice"):
        ek_turu = "ses"
        dosya_id = m["voice"].get("file_id")
    return {
        "update_id": g["update_id"],
        "zaman": zaman.isoformat(timespec="seconds"),
        "metin": metin,
        "linkler": [l.rstrip(".,)") for l in URL.findall(metin)],
        "not": URL.sub("", metin).strip(),
        "ek_turu": ek_turu,
        "dosya_id": dosya_id,
        "dosya_adi": dosya_adi,
    }


def mesajlari_ayikla(guncellemeler, chat_id):
    return [
        _mesaj(g)
        for g in guncellemeler
        if (g.get("message") or {}).get("chat", {}).get("id") == chat_id and "update_id" in g
    ]


def isle(kok, guncellemeler, chat_id):
    """Yeni mesajları `takimlar/postaci/gelen/` altına yazar, offset'i durum.json'a işler."""
    durum = ayar.durum_oku(TAKIM, kok)
    onceki = int((durum.get("sayaclar") or {}).get("telegram_son_update", 0))
    son = onceki
    gelen = Path(kok) / "takimlar" / TAKIM / "gelen"
    gelen.mkdir(parents=True, exist_ok=True)
    yazilan = []
    for mesaj in mesajlari_ayikla(guncellemeler, chat_id):
        if mesaj["update_id"] <= son:
            continue
        yol = gelen / f"{mesaj['zaman'][:10]}-{mesaj['update_id']}.json"
        yol.write_text(json.dumps(mesaj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        yazilan.append(yol)
        son = mesaj["update_id"]
    if son != onceki:
        ayar.durum_guncelle(
            TAKIM,
            {"sayaclar": {**(durum.get("sayaclar") or {}), "telegram_son_update": son}},
            kok,
        )
    return yazilan


def _calistir(argv, token):
    if "--chat-id-bul" in argv:
        idler = chat_idleri(guncellemeleri_cek(token))
        print(json.dumps({"chat_idleri": idler}))
        if not idler:
            print(
                "chat id bulunamadı — telefonundan bota bir mesaj at, sonra bu komutu tekrar koş "
                "(Telegram yalnız son 24 saatin güncellemelerini verir)",
                file=sys.stderr,
            )
        return 0
    ham_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not ham_id:
        print("TELEGRAM_CHAT_ID yok (.env) — önce --chat-id-bul", file=sys.stderr)
        return 1
    chat_id = int(ham_id)
    if "--isle" in argv:
        son = int((ayar.durum_oku(TAKIM).get("sayaclar") or {}).get("telegram_son_update", 0))
        yazilan = isle(ayar.KOK, guncellemeleri_cek(token, offset=son + 1 if son else None), chat_id)
        print(json.dumps({"yeni": [y.name for y in yazilan]}, ensure_ascii=False))
        return 0
    adet = int(argv[argv.index("--son") + 1]) if "--son" in argv and len(argv) > argv.index("--son") + 1 else 5
    print(
        json.dumps(
            mesajlari_ayikla(guncellemeleri_cek(token), chat_id)[-adet:],
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ayar.ortam_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN yok (.env)", file=sys.stderr)
        return 1
    try:
        return _calistir(argv, token)
    except TelegramHatasi as exc:
        print(exc, file=sys.stderr)
        return exc.kod


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
