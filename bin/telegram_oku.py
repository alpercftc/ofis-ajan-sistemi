#!/usr/bin/env python3
"""Telegram gelen kutusu — bota attığın mesajları, sesli notları ve belgeleri okur (getUpdates, stdlib).

Kullanım:
  py -3 bin/telegram_oku.py --chat-id-bul   # bota bir mesaj at, sonra bunu koş, çıkanı .env'e yaz
  py -3 bin/telegram_oku.py --son 5         # son mesajları bas (durum değişmez)
  py -3 bin/telegram_oku.py --isle          # yeni mesajları takimlar/postaci/gelen/ altına yaz

Çıkış kodları: 0 tamam · 1 anahtar eksik · 2 token geçersiz (Telegram 401/403) · 3 ulaşılamadı (ağ).

Anahtarlar `.env`'de: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. Yalnızca kendi chat id'nden gelen
mesajlar işlenir — bota başkası yazarsa görmezden gelinir.

Offset: en son işlenen `update_id` `takimlar/postaci/durum.json` → `sayaclar.telegram_son_update`
alanında durur. Telegram bir güncellemeyi `offset` ile onaylandıktan sonra bir daha vermez;
bu yüzden `--son` offset'i ilerletmez, `--isle` ilerletir.
"""
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


def _tek_parca_gonder(token: str, chat_id: int, parca: str) -> bool:
    for parse_mode in ("Markdown", None):
        try:
            yuk = {"chat_id": chat_id, "text": parca}
            if parse_mode:
                yuk["parse_mode"] = parse_mode
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
    """Telegram üzerinden kullanıcıya doğrudan saf UTF-8 mesaj gönderir (uzun metinleri otomatik böler)."""
    metin = str(metin or "").strip()
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
