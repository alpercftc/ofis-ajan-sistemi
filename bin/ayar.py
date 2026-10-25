#!/usr/bin/env python3
"""
Ofis Ajan Şirketi — Tek Ayar ve Model Seviyesi Yöneticisi (ayar.py)
Bütün betikler buradan okur; hiçbir sayı ikinci bir yerde yazılmaz.
Anahtarlar repo kökündeki `.env` dosyasındadır (`.env.example` kopyası) ve git'e girmez.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

KOK_DIZIN = Path(__file__).resolve().parent.parent
KOK = KOK_DIZIN
TAKIMLAR_DIZINI = KOK_DIZIN / "takimlar"
TAKIMLAR = TAKIMLAR_DIZINI
SKILLS_DIZINI = KOK_DIZIN / "skills"
SIRKET_DIZINI = KOK_DIZIN / "sirket"
ENV_DOSYASI = KOK_DIZIN / ".env"

load_dotenv(ENV_DOSYASI)

# --- mesai (ANAYASA 4) -----------------------------------------------------
MESAI_BASLANGIC = 8   # 08:00 dahil
MESAI_BITIS = 23      # 23:00 hariç
MESAI_METNI = f"{MESAI_BASLANGIC:02d}:00-{MESAI_BITIS:02d}:00"

# --- tavanlar (ANAYASA 4) --------------------------------------------------
KOSU_BUTCESI_USD = 2.0            # tek koşunun para tavanı
KOSU_SURESI_SN = 15 * 60          # tek koşunun süre tavanı (900 sn)
KOSULAR_ARASI_DK = 0              # aynı takımın iki koşusu arası — 0: bekleme yok
GUNLUK_KOSU_TAVANI = 20           # birim başına günlük koşu tavanı
GUNLUK_MALIYET_TAVANI_USD = 10.0  # tüm şirket, gün
ES_ZAMANLI_TAVAN = 2              # dağıtıcının aynı anda başlattığı birim sayısı

ENV_SATIRI = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def simdi_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# --- anahtarlar ------------------------------------------------------------

def env_yukle(yol=None) -> dict:
    """`.env` dosyasını sözlük olarak okur; `export` ve tırnak toleranslı. Yoksa boş sözlük."""
    try:
        satirlar = Path(yol or ENV_DOSYASI).read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    sonuc = {}
    for satir in satirlar:
        if satir.lstrip().startswith("#"):
            continue
        eslesme = ENV_SATIRI.match(satir)
        if eslesme:
            sonuc[eslesme.group(1)] = eslesme.group(2).strip("'\"")
    return sonuc


def ortam_yukle(yol=None) -> dict:
    """`.env` içeriğini ortama yazar. Proje `.env`'i kazanır."""
    for anahtar, deger in env_yukle(yol).items():
        os.environ[anahtar] = deger
    return dict(os.environ)


def eksik_anahtarlar(gerekli, ortam=None) -> list[str]:
    ortam = ortam if ortam is not None else os.environ
    return [a for a in (gerekli or []) if not ortam.get(a)]


# --- mesai -----------------------------------------------------------------

def mesaide_mi(simdi=None) -> bool:
    an = simdi or datetime.now()
    return MESAI_BASLANGIC <= an.hour < MESAI_BITIS


def sonraki_mesai(simdi=None):
    an = simdi or datetime.now()
    aday = an.replace(hour=MESAI_BASLANGIC, minute=0, second=0, microsecond=0)
    return aday if aday > an else aday + timedelta(days=1)


# --- takim.md frontmatter --------------------------------------------------

def _deger(ham: str):
    ham = ham.strip()
    if ham.startswith("[") and ham.endswith("]"):
        ic = ham[1:-1].strip()
        return [p.strip().strip("'\"") for p in ic.split(",") if p.strip()] if ic else []
    return ham.strip("'\"")


def frontmatter(metin: str) -> tuple[dict, str]:
    """Basit YAML frontmatter: `anahtar: değer` ve `[a, b]` listeleri. (fm, gövde) döner."""
    if not metin.startswith("---"):
        return {}, metin
    parcalar = metin.split("---", 2)
    if len(parcalar) < 3:
        return {}, metin
    fm = {}
    for satir in parcalar[1].splitlines():
        if ":" not in satir or satir.lstrip().startswith("#"):
            continue
        anahtar, ham = satir.split(":", 1)
        fm[anahtar.strip()] = _deger(ham)
    return fm, parcalar[2].lstrip("\r\n")


def takim_bilgisi(takim: str, kok=None):
    """`takimlar/<takim>/takim.md` frontmatter'ı; dosya yoksa None."""
    yol = Path(kok or KOK) / "takimlar" / takim / "takim.md"
    if not yol.is_file():
        return None
    fm, _ = frontmatter(yol.read_text(encoding="utf-8"))
    return fm


# --- durum.json ------------------------------------------------------------

def durum_yolu(takim: str, kok=None) -> Path:
    return Path(kok or KOK) / "takimlar" / takim / "durum.json"


def durum_oku(takim: str, kok=None) -> dict:
    try:
        return json.loads(durum_yolu(takim, kok).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def durum_guncelle(takim: str, yama: dict, kok=None) -> dict:
    """Yeni sözlük yazar (immutable birleştirme); yazılan durumu döner."""
    yol = durum_yolu(takim, kok)
    yeni = {**durum_oku(takim, kok), **yama}
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(yeni, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return yeni


# --- platform ve model haritası --------------------------------------------

def model_haritasi_oku() -> dict:
    harita_yolu = KOK_DIZIN / "sirket" / "model-haritasi.json"
    if not harita_yolu.exists():
        return {}
    with open(harita_yolu, "r", encoding="utf-8") as f:
        return json.load(f)


def platform_al() -> str:
    return os.getenv("VARSAYILAN_PLATFORM", "antigravity").lower()


def seviye_modeli_al(seviye: str, platform: str = None) -> str:
    if platform is None:
        platform = platform_al()
    harita = model_haritasi_oku()
    platform_haritasi = harita.get("platformlar", {}).get(platform, {})
    return platform_haritasi.get(seviye, "gemini-3.8-flash-medium")


def ozet(simdi=None) -> str:
    """`py -3 bin/ayar.py` çıktısı."""
    ortam_yukle()
    an = simdi or datetime.now().astimezone()
    durum = "içinde" if mesaide_mi(an) else "dışında"
    aktif_platform = platform_al()
    return "\n".join([
        f"{an:%Y-%m-%d %H:%M} — mesai {durum} ({MESAI_METNI}), sonraki açılış {sonraki_mesai(an):%a %H:%M}",
        f"tavanlar: koşu {KOSU_BUTCESI_USD} USD / {KOSU_SURESI_SN // 60} dk · "
        f"birim günde {GUNLUK_KOSU_TAVANI} koşu · arası {KOSULAR_ARASI_DK} dk · "
        f"şirket günde {GUNLUK_MALIYET_TAVANI_USD} USD",
        f"platform: {aktif_platform} · yüksek={seviye_modeli_al('yuksek', aktif_platform)} · "
        f"hızlı={seviye_modeli_al('hizli', aktif_platform)} · .env: {'var' if Path(ENV_DOSYASI).exists() else 'yok'}",
    ])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(ozet())
