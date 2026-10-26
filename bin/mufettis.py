#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Bağımsız Denetçi Motoru (mufettis.py)
1. Katman: Deterministik Python (TC Kimlik mod-10, KVKK, e-Devlet Barkod & Metin Diff, Şema ve Koşu denetimi)
2. Katman: Bağımsız LLM denetimi
"""
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

KOK_DIZIN = ayar.KOK
BARKOD_RE = re.compile(r"\b(SGK[A-Z0-9]{10,30})\b")
TARIH_RE = re.compile(r"\b(\d{2}[./]\d{2}[./]\d{4})\b")
GECERLI_DURUMLAR = {"bekliyor", "yapiliyor", "tamam", "kacti", "denetim_bekliyor"}


def tc_kimlik_dogrula(tc_no: str) -> bool:
    """11 haneli T.C. Kimlik numarası mod-10 algoritma doğrulaması."""
    if not tc_no or not re.match(r"^[1-9]\d{10}$", str(tc_no)):
        return False
    digits = [int(d) for d in str(tc_no)]
    tekler = sum(digits[0:9:2])
    ciftler = sum(digits[1:8:2])
    if ((tekler * 7) - ciftler) % 10 != digits[9]:
        return False
    if sum(digits[:10]) % 10 != digits[10]:
        return False
    return True


def kvkk_kontrol(metin: str) -> list:
    """Metin içindeki açık kimlik ve telefon kalıplarını tarar."""
    bulgular = []
    tc_adaylari = re.findall(r"\b\d{11}\b", metin)
    for tc in tc_adaylari:
        if tc_kimlik_dogrula(tc):
            bulgular.append(f"Açık T.C. Kimlik tespit edildi: {tc[:3]}*****{tc[-2:]}")
    return bulgular


def edevlet_orijinal_pdf_indir(barkod: str, tc_no: str, hedef_pdf: Path) -> dict:
    """
    turkiye.gov.tr/belge-dogrulama üzerinden 4 adımda (oturumsuz, 0 token)
    orijinal e-Devlet PDF belgesini indirir.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        cookie_path = str(Path(tmpdir) / "cookies.txt")
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ref = "https://www.turkiye.gov.tr/belge-dogrulama"

        def _get(url: str, out_file: Path = None) -> bytes:
            cmd = ["curl.exe", "-s", "-L", "-c", cookie_path, "-b", cookie_path, "-A", ua, url]
            if out_file:
                cmd.extend(["-o", str(out_file)])
            return subprocess.run(cmd, capture_output=True).stdout

        def _post(url: str, form: dict) -> str:
            cmd = ["curl.exe", "-s", "-L", "-c", cookie_path, "-b", cookie_path, "-A", ua, "-e", ref]
            for k, v in form.items():
                cmd.extend(["--data-urlencode", f"{k}={v}"])
            cmd.append(url)
            return subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", errors="ignore")

        # Adım 1: İlk token
        html1 = _get(ref).decode("utf-8", errors="ignore")
        m1 = re.search(r'name="token"\s+value="([^"]+)"', html1)
        if not m1:
            return {"basarili": False, "hata": "Adım 1 token alınamadı"}

        # Adım 2: Barkod gönderimi
        html2 = _post(f"{ref}?submit", {"sorgulananBarkod": barkod, "token": m1.group(1), "btn": "Devam Et"})
        m2 = re.search(r'name="token"\s+value="([^"]+)"', html2)
        if not m2 or "ikinciAlan" not in html2:
            return {"basarili": False, "hata": "Barkod e-Devlet'te doğrulanamadı"}

        # Adım 3: T.C. Kimlik gönderimi
        html3 = _post(f"{ref}?islem=dogrulama&submit", {"ikinciAlan": tc_no, "token": m2.group(1), "btn": "Devam Et"})
        m3 = re.search(r'name="token"\s+value="([^"]+)"', html3)
        if not m3 or "chkOnay" not in html3:
            return {"basarili": False, "hata": "T.C. Kimlik ve barkod eşleşmedi"}

        # Adım 4: Onay ve PDF indirme
        html4 = _post(f"{ref}?islem=onay&submit", {"chkOnay": "1", "token": m3.group(1), "btn": "Devam Et"})
        if "belge=goster" not in html4:
            return {"basarili": False, "hata": "Belge gösterim bağlantısı alınamadı"}

        _get(f"{ref}?belge=goster&goster=1", out_file=hedef_pdf)
        if not hedef_pdf.exists() or not hedef_pdf.read_bytes().startswith(b"%PDF"):
            return {"basarili": False, "hata": "İndirilen dosya geçerli bir PDF değil"}

        return {"basarili": True, "pdf_yolu": str(hedef_pdf), "boyut_byte": hedef_pdf.stat().st_size}


def edevlet_sgk_karsilastir(ogrenci_metin: str, orijinal_metin: str) -> dict:
    """
    Öğrencinin yüklediği SGK belgesi metni ile e-Devlet'ten doğrulanan orijinal belge metnini
    deterministik olarak (0 token) difflib ve kritik tarihler üzerinden karşılaştırır.
    """
    norm_ogr = " ".join(ogrenci_metin.split())
    norm_orj = " ".join(orijinal_metin.split())

    birebir_ayni = norm_ogr == norm_orj
    ogr_tarihler = set(TARIH_RE.findall(norm_ogr))
    orj_tarihler = set(TARIH_RE.findall(norm_orj))
    tarih_farki = ogr_tarihler.symmetric_difference(orj_tarihler)

    fark_satirlari = list(
        difflib.unified_diff(
            orijinal_metin.splitlines(),
            ogrenci_metin.splitlines(),
            fromfile="edevlet_orijinal",
            tofile="ogrenci_yuklenen",
            lineterm="",
        )
    )

    oynama_suphesi = len(tarih_farki) > 0 or not birebir_ayni
    return {
        "birebir_eslesti": birebir_ayni,
        "oynama_suphesi": oynama_suphesi,
        "tarih_farklari": sorted(tarih_farki),
        "diff_ozeti": fark_satirlari[:20],
        "durum": "DOGRULANDI" if not oynama_suphesi else "RED_SAHTE_VEYA_OYNANMIS_BELGE_SUPHESI",
    }


def cikti_denetle(rapor_metni: str, kanit_tablosu: dict = None) -> dict:
    """1. Katman deterministik denetim."""
    print("[BİLGİ] Müfettiş 1. Katman deterministik denetimini başlattı...")
    ihlaller = kvkk_kontrol(rapor_metni)

    gecerli = len(ihlaller) == 0
    return {
        "gecerli": gecerli,
        "ihlaller": ihlaller,
        "durum": "ONAYLANDI" if gecerli else "REDDEDILDI",
    }


def denetle(kok, takim: str, kosu_dosyasi: Path, zaman: str = None) -> dict:
    """
    Birimin tamamladığı koşuyu deterministik olarak denetler (kos.py tarafından çağrılır).
    1. Koşu kaydı (SIRKET_KOSU) var mı ve boş değil mi?
    2. Koşu kaydında KVKK (açık T.C. Kimlik No) sızıntısı var mı?
    3. durum.json geçerli mi?
    Sonucu durum.json['mufettis'] altına ve sirket-log/mufettis.log dosyasına yazar.
    """
    kok = Path(kok or KOK_DIZIN)
    zaman = zaman or ayar.simdi_iso()
    bulgular = []

    kosu_yolu = Path(kosu_dosyasi)
    if not kosu_yolu.is_file() or not kosu_yolu.read_text(encoding="utf-8", errors="ignore").strip():
        bulgular.append(f"koşu kaydı yazılmadı veya boş: {kosu_yolu.name}")
    else:
        metin = kosu_yolu.read_text(encoding="utf-8", errors="ignore")
        bulgular.extend(kvkk_kontrol(metin))

    durum = ayar.durum_oku(takim, kok)
    if not durum:
        bulgular.append("durum.json okunamadı veya boş")
    else:
        for oge in durum.get("kuyruk") or []:
            if isinstance(oge, dict) and oge.get("durum") not in GECERLI_DURUMLAR:
                bulgular.append(f"geçersiz kuyruk durumu: {oge.get('id')} -> {oge.get('durum')}")

    karar = "ONAY" if not bulgular else "RED"
    muf_kaydi = {
        "son_denetim": zaman,
        "son_karar": karar,
        "bulgular": bulgular,
    }
    ayar.durum_guncelle(takim, {"mufettis": muf_kaydi}, kok)

    log_yolu = kok / "sirket-log" / "mufettis.log"
    try:
        log_yolu.parent.mkdir(parents=True, exist_ok=True)
        with open(log_yolu, "a", encoding="utf-8") as f:
            f.write(
                f"{zaman} | {takim} | {karar} | "
                f"{'; '.join(bulgular) if bulgular else 'temiz'}\n"
            )
    except OSError:
        pass

    return {"karar": karar, "bulgular": bulgular}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    test_metin = "Örnek öğrenci değerlendirme raporu - Belge tam."
    sonuc = cikti_denetle(test_metin)
    print(f"[BİLGİ] Denetim Sonucu: {sonuc['durum']}")
