#!/usr/bin/env python3
"""
Ofis Ajan Şirketi — Dağıtıcı ve İş Zinciri Durum Makinesi (dagitici.py)
LLM çağırmayan saf Python durum makinesi; tamamlanan işleri ZINCIR tablosuna göre sıradaki birime devreder.

Kullanım:
  py -3 bin/dagitici.py --kuru    (ZİNCİR ve tetik kararlarını bas, hiçbir şey yazma/başlatma)
  py -3 bin/dagitici.py           (ZİNCİR'i uygula, kuyruklara yaz ve mesai/tavan uygunsa tetikle)
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

KOK_DIZIN = ayar.KOK
KOK = KOK_DIZIN
LOG = KOK / "sirket-log" / "dagitici.log"
KOSU_DOSYA_ADI = re.compile(r"^(\d{4}-\d{2}-\d{2})-\d{4}\.md$")
MALIYET_DESENI = re.compile(r"maliyet:\s*([\d.]+)\s*USD", re.IGNORECASE)
KUYRUK_DURUMLARI = {"bekliyor", "yapiliyor", "tamam", "kacti"}

AJANLAR = [
    "dekan",
    "dekan-sekreteri",
    "staj-burosu",
    "postaci",
    "memur",
    "ik-memuru",
    "bilgi-islem",
    "mufettis",
]

# Kuyruk id deseni → sonraki birimin kuyruğu. Zincir burada, kodda değil.
ZINCIR = [
    {
        "ad": "staj-inceleme-onay-karti",
        "kaynak_takim": "staj-burosu",
        "desen": re.compile(r"^staj-(?!onay-)([A-Za-z0-9_-]+)$"),
        "takim": "dekan",
        "id": "staj-onay-{0}",
        "not": "staj-burosu incelemeyi ve imzalı FR-1323 hazırlığını tamamladı; Birleşik Gündem onay kartına ekle",
    },
    {
        "ad": "mevzuat-derleme-ozeti",
        "kaynak_takim": "dekan-sekreteri",
        "desen": re.compile(r"^mevzuat-(?!onay-)([A-Za-z0-9_-]+)$"),
        "takim": "dekan",
        "id": "mevzuat-onay-{0}",
        "not": "dekan-sekreteri mevzuat derlemesini tamamladı; Birleşik Gündem özetine ekle",
    },
    {
        "ad": "posta-idari-gorev",
        "kaynak_takim": "postaci",
        "desen": re.compile(r"^posta-idari-([A-Za-z0-9_-]+)$"),
        "takim": "memur",
        "id": "idari-{0}",
        "not": "postaci idari e-posta/görev tespit etti; Memur evrak/kontrol listesini hazırla",
    },
    {
        "ad": "posta-staj-bildirimi",
        "kaynak_takim": "postaci",
        "desen": re.compile(r"^posta-staj-([A-Za-z0-9_-]+)$"),
        "takim": "staj-burosu",
        "id": "staj-{0}",
        "not": "postaci staj bildirimi/revizesi tespit etti; Staj Bürosu kontrol et",
    },
    {
        "ad": "posta-gundem-bildirimi",
        "kaynak_takim": "postaci",
        "desen": re.compile(r"^posta-([A-Za-z0-9_-]+)$"),
        "takim": "dekan",
        "id": "gundem-{0}",
        "not": "postaci gelen e-posta/Telegram mesaj özetini çıkardı; Birleşik Gündem'e ekle",
    },
    {
        "ad": "idari-evrak-onay",
        "kaynak_takim": "memur",
        "desen": re.compile(r"^idari-([A-Za-z0-9_-]+)$"),
        "takim": "dekan",
        "id": "evrak-onay-{0}",
        "not": "memur idari evrak/kontrol listesini hazırladı; Dekan onay gündemine ekle",
    },
]


def _slug(metin: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", (metin or "")).strip("-")


def zincir_esle(id_: str, kaynak_takim: str = None):
    """Kuyruk id'sine uyan ilk zincir maddesinin isteğini döner; yoksa None."""
    for kural in ZINCIR:
        if kaynak_takim and kural.get("kaynak_takim") and kural["kaynak_takim"] != kaynak_takim:
            continue
        eslesme = kural["desen"].match(id_ or "")
        if not eslesme:
            continue
        gruplar = [_slug(g) for g in eslesme.groups()]
        return {
            "ad": kural["ad"],
            "takim": kural["takim"],
            "id": kural["id"].format(*gruplar),
            "not": kural["not"],
        }
    return None


def kuyruga_yaz(kok, takim: str, id_: str, notu: str) -> bool:
    """Birimin kuyruğuna 'bekliyor' maddesi ekler (immutable). Yazıldıysa True.
    Aynı id zaten varsa dokunmaz — zincir iki kez tetiklenirse tekrar iş açılmaz."""
    durum = ayar.durum_oku(takim, kok)
    if not durum:
        return False
    kuyruk = durum.get("kuyruk") or []
    if any(isinstance(o, dict) and o.get("id") == id_ for o in kuyruk):
        return False
    ayar.durum_guncelle(
        takim,
        {"kuyruk": [*kuyruk, {"id": id_, "durum": "bekliyor", "not": notu}]},
        kok,
    )
    return True


def zinciri_isle(kok, takim: str, kuru: bool = False) -> list[dict]:
    """Birimin kuyruğundaki 'tamam' maddeleri için zinciri kurar. Yazılan istekleri döner."""
    yazilan = []
    durum = ayar.durum_oku(takim, kok)
    # Üretici birimlerde Müfettiş RED verdiyse zincir ilerlemez (ANAYASA Madde 3)
    son_karar = (durum.get("mufettis") or {}).get("son_karar")
    if son_karar == "RED":
        return []
    for oge in durum.get("kuyruk") or []:
        if not isinstance(oge, dict) or oge.get("durum") != "tamam":
            continue
        istek = zincir_esle(oge.get("id"), kaynak_takim=takim)
        if not istek:
            continue
        hedef_kuyruk = ayar.durum_oku(istek["takim"], kok).get("kuyruk") or []
        varsa = any(isinstance(k, dict) and k.get("id") == istek["id"] for k in hedef_kuyruk)
        if varsa:
            continue
        if kuru or kuyruga_yaz(kok, istek["takim"], istek["id"], istek["not"]):
            yazilan.append({**istek, "kaynak_takim": takim, "kaynak_id": oge.get("id")})
    return yazilan


def _dt(metin):
    try:
        deger = datetime.fromisoformat(str(metin))
    except (TypeError, ValueError):
        return None
    return deger.astimezone() if deger.tzinfo else deger.astimezone()


def bekleyen_sayisi(durum: dict) -> int:
    return sum(
        1
        for o in (durum.get("kuyruk") or [])
        if isinstance(o, dict) and o.get("durum") == "bekliyor"
    )


def bugunku_kosu_sayisi(kok, takim: str, bugun: str) -> int:
    dizin = Path(kok) / "takimlar" / takim / "kosu"
    if not dizin.is_dir():
        return 0
    return sum(1 for p in dizin.glob("*.md") if KOSU_DOSYA_ADI.match(p.name) and p.name.startswith(bugun))


def gunluk_maliyet(kok, bugun: str) -> float:
    """Bugünkü bütün koşu kayıtlarındaki `maliyet: N USD` satırlarının toplamı."""
    toplam = 0.0
    for kosu in sorted((Path(kok) / "takimlar").glob(f"*/kosu/{bugun}*.md")):
        for ham in MALIYET_DESENI.findall(kosu.read_text(encoding="utf-8", errors="ignore")):
            try:
                toplam += float(ham)
            except ValueError:
                continue
    return toplam


def tetik_karari(kok, takim: str, simdi: datetime) -> tuple[bool, str]:
    """(kossun_mu, sebep) — bu birim şimdi koşmalı mı, neden?"""
    fm = ayar.takim_bilgisi(takim, kok)
    if fm is None:
        return False, "takim.md yok"
    durum = ayar.durum_oku(takim, kok)
    bekleyen = bekleyen_sayisi(durum)
    if not bekleyen:
        return False, "kuyrukta bekleyen madde yok"
    if not ayar.mesaide_mi(simdi):
        return False, f"kuyrukta {bekleyen} bekleyen madde · mesai dışı ({ayar.MESAI_METNI}); kuyruk {ayar.sonraki_mesai(simdi):%H:%M}'da açılır"
    son_kosu = _dt(durum.get("son_kosu"))
    if son_kosu is not None:
        gecen = int((simdi - son_kosu).total_seconds() // 60)
        if gecen < ayar.KOSULAR_ARASI_DK:
            return False, f"{ayar.KOSULAR_ARASI_DK} dk kuralı: {gecen} dk önce koştu"
    bugun = simdi.strftime("%Y-%m-%d")
    sayi = bugunku_kosu_sayisi(kok, takim, bugun)
    if sayi >= ayar.GUNLUK_KOSU_TAVANI:
        return False, f"günlük koşu tavanı: bugün {sayi} koşu (tavan {ayar.GUNLUK_KOSU_TAVANI})"
    maliyet = gunluk_maliyet(kok, bugun)
    if maliyet >= ayar.GUNLUK_MALIYET_TAVANI_USD:
        return False, (
            f"günlük bütçe doldu: {maliyet:.2f} USD "
            f"(tavan {ayar.GUNLUK_MALIYET_TAVANI_USD:.0f} USD)"
        )
    ne_zaman = (
        f"son koşu {int((simdi - son_kosu).total_seconds() // 60)} dk önce"
        if son_kosu
        else "bugün hiç koşmadı"
    )
    return True, f"kuyrukta {bekleyen} bekleyen madde; {ne_zaman}"


def takimlar(kok) -> list[str]:
    dizin = Path(kok) / "takimlar"
    if not dizin.is_dir():
        return []
    return sorted(
        p.name
        for p in dizin.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "takim.md").is_file()
    )


def _kostur(kok, takim: str):
    """bin/kos.py <takim> arka planda; kilit kos.py'de, çağıran bloklanmaz."""
    (Path(kok) / "sirket-log").mkdir(parents=True, exist_ok=True)
    log = open(Path(kok) / "sirket-log" / f"{takim}-tetik.log", "a", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, str(Path(kok) / "bin" / "kos.py"), takim],
        stdout=log,
        stderr=log,
        cwd=str(kok),
        start_new_session=True,
    )


def _log_yaz(kok, satirlar: list[dict], simdi: datetime):
    if not satirlar:
        return
    yol = Path(kok) / "sirket-log" / "dagitici.log"
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "a", encoding="utf-8") as dosya:
        for satir in satirlar:
            dosya.write(
                f"{simdi.isoformat(timespec='seconds')} | {satir['takim']} | "
                f"{satir['sonuc']} | {satir['sebep']}\n"
            )


def dagit(kok, simdi=None, kuru: bool = False) -> dict:
    """Önce zinciri kurar, sonra tetik kararlarını verir ve uygun birimleri başlatır."""
    simdi = simdi or datetime.now().astimezone()
    zincir = [z for takim in takimlar(kok) for z in zinciri_isle(kok, takim, kuru)]
    kararlar, baslatilan = [], 0
    for takim in takimlar(kok):
        kossun, sebep = tetik_karari(kok, takim, simdi)
        if not kossun:
            kararlar.append({"takim": takim, "sebep": sebep, "sonuc": "bekletildi"})
        elif baslatilan >= ayar.ES_ZAMANLI_TAVAN:
            kararlar.append(
                {
                    "takim": takim,
                    "sonuc": "sirada",
                    "sebep": f"{sebep} · eşzamanlı tavan {ayar.ES_ZAMANLI_TAVAN}",
                }
            )
        else:
            baslatilan += 1
            if not kuru:
                _kostur(kok, takim)
            kararlar.append({"takim": takim, "sebep": sebep, "sonuc": "kostu"})
    if not kuru:
        _log_yaz(kok, [k for k in kararlar if k["sonuc"] != "bekletildi"], simdi)
    return {"zincir": zincir, "kararlar": kararlar}


ETIKET = {"kostu": "KOŞ  ", "sirada": "SIRA ", "bekletildi": "BEKLE"}


def bas(sonuc: dict, simdi: datetime, kuru: bool):
    print(f"dağıtıcı — {simdi:%Y-%m-%d %H:%M}")
    for z in sonuc["zincir"]:
        print(f"  ZİNCİR {z['kaynak_takim']}/{z['kaynak_id']} -> {z['takim']}/{z['id']} ({z['ad']})")
    if not sonuc["zincir"]:
        print("  ZİNCİR (yeni bağlantı yok)")
    for k in sonuc["kararlar"]:
        print(f"  {ETIKET[k['sonuc']]} {k['takim']:<16} — {k['sebep']}")
    kosan = [k["takim"] for k in sonuc["kararlar"] if k["sonuc"] == "kostu"]
    print(f"  -> {len(kosan)} birim koşar: {', '.join(kosan) if kosan else '(yok)'}")
    if kuru:
        print("  (kuru koşu: kuyruğa yazılmadı, hiçbir birim başlatılmadı)")


def kuyruk_tara(kuru: bool = True) -> dict:
    """Geriye dönük uyumluluk ve birim testleri için kuru/canlı dağıtım sarmalayıcısı."""
    simdi = datetime.now().astimezone()
    sonuc = dagit(KOK, simdi, kuru=kuru)
    bas(sonuc, simdi, kuru=kuru)
    return sonuc


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    kuru = "--kuru" in argv
    simdi = datetime.now().astimezone()
    bas(dagit(KOK, simdi, kuru=kuru), simdi, kuru)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
