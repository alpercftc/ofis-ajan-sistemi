#!/usr/bin/env python3
"""Telegram dinleyici ve Dekan orkestrasyon servisi (telegram_dinle.py).

ANAYASA Kuralı: Alper'in tek muhatabı Dekan'dır.
1. Alper Telegram'dan yazdığı anda Dekan mesajı karşılar ve ilgili birimi (`takim_sec`) belirler.
2. Anlık sorguları (staj listeleme, senkron, onay boyama) sıfır gecikmeyle yanıtlar ve kuyrukta `tamam` işaretler.
3. Ajan çalışması gerektiren işleri (staj inceleme, Bilgi İşlem kod/hatası çözümü, mevzuat, idari yazı vb.)
   ilgili birimin kuyruğuna yazar, `bin/kos.py <birim>` + `bin/dagitici.py` ile koşturur ve sonucu Telegram'dan bildirir.
4. Mesai saatleri içinde 15 dakikada bir e-postaları, 30 dakikada bir ortak staj tablosunu otomatik kontrol eder.
"""
import collections
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import dagitici  # noqa: E402
import staj_senkron  # noqa: E402
import telegram_oku  # noqa: E402

KOK = ayar.KOK
TAKIM = "postaci"

BEKLEME_SN = 15
TUR_ARASI_SN = 2
NOT_SINIRI = 200
LOG_ADI = "telegram-dinle.log"

_SIRLAR: list[str] = []

OGRENCI_NO_RE = re.compile(r"\b(\d{2,4}[A-Za-z]\d{3,5})\b")


@contextlib.contextmanager
def _tekil_dinleyici_kilidi(kok: Path):
    """Aynı anda yalnızca tek bir telegram_dinle.py sürecinin çalışmasını sağlar."""
    kilit_dizin = Path(kok) / "sirket-log"
    kilit_dizin.mkdir(parents=True, exist_ok=True)
    kilit_yolu = kilit_dizin / "telegram-dinle.lock"
    dosya = open(kilit_yolu, "a+", encoding="utf-8")
    kilitlendi = False
    try:
        if os.name == "nt":
            import msvcrt

            dosya.seek(0)
            if dosya.tell() == 0:
                dosya.write(f"{os.getpid()}\n")
                dosya.flush()
            dosya.seek(0)
            try:
                msvcrt.locking(dosya.fileno(), msvcrt.LK_NBLCK, 1)
                kilitlendi = True
            except OSError:
                kilitlendi = False
        else:
            import fcntl

            try:
                fcntl.flock(dosya.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                kilitlendi = True
            except BlockingIOError:
                kilitlendi = False
        yield kilitlendi
    finally:
        if kilitlendi:
            try:
                if os.name == "nt":
                    import msvcrt

                    dosya.seek(0)
                    msvcrt.locking(dosya.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(dosya.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        dosya.close()


def sir_ekle(deger):
    if deger and deger not in _SIRLAR:
        _SIRLAR.append(deger)
    return len(_SIRLAR)


def _log(kok, satir):
    for sir in _SIRLAR:
        satir = satir.replace(sir, "***")
    damga = datetime.now().astimezone().isoformat(timespec="seconds")
    if sys.stdout is not None:
        try:
            print(f"[BİLGİ] {damga} | {satir}", flush=True)
        except Exception:
            pass
    yol = Path(kok) / "sirket-log" / LOG_ADI
    try:
        yol.parent.mkdir(parents=True, exist_ok=True)
        with open(yol, "a", encoding="utf-8") as dosya:
            dosya.write(f"[BİLGİ] {damga} | {satir}\n")
    except OSError:
        pass


def _temiz(metin, sinir=NOT_SINIRI):
    tek_satir = " ".join(str(metin or "").split())
    return tek_satir[:sinir] + ("…" if len(tek_satir) > sinir else "")


def takim_sec(mesaj) -> str:
    """Mesaj içeriğine ve ek türüne göre hangi birimin görevlendirileceğini belirler."""
    if isinstance(mesaj, dict):
        metin = str(mesaj.get("metin") or mesaj.get("not") or "")
        ek_turu = mesaj.get("ek_turu")
        dosya_adi = str(mesaj.get("dosya_adi") or "")
    else:
        metin = str(mesaj or "")
        ek_turu = None
        dosya_adi = ""

    metin = metin.replace("İ", "i").replace("I", "ı").lower()
    dosya_adi = dosya_adi.replace("İ", "i").replace("I", "ı").lower()

    if ek_turu == "ses":
        return "postaci"

    # 1. Bilgi İşlem (BT): Kod, Türkçe karakter, hata, betik, test, araç sorunları, watchdog
    if any(
        k in metin
        for k in (
            "türkçe",
            "turkce",
            "karakter",
            "kodlama",
            "utf-8",
            "utf8",
            "bilgi işlem",
            "bilgi-islem",
            "bt ajan",
            "kod ",
            "betik",
            "python",
            "pytest",
            "unittest",
            "hata ",
            "bug",
            "çalışmıyor",
            "calismiyor",
            "onar",
            "watchdog",
            "bekçi",
            "bekci",
        )
    ):
        return "bilgi-islem"

    # 2. Dekan Sekreteri: Mevzuat, yönerge, uygulama esasları, kılavuz derleme
    if any(k in metin for k in ("yönerge", "yonerge", "mevzuat", "kılavuz", "kilavuz", "uygulama esas")):
        return "dekan-sekreteri"

    # 3. Staj Bürosu: Staj defteri, sicil fişi, öğrenci inceleme/onay/revize
    if any(
        k in metin
        for k in ("staj", "defter", "sicil", "incele", "onayla", "revize", "okunmayan", "atölye", "atolye")
    ) or any(k in dosya_adi for k in ("staj", "defter", "sicil")):
        return "staj-burosu"

    # 4. Memur: MÜDEK, komisyon, tutanak, resmi yazı, denetim listesi
    if any(k in metin for k in ("müdek", "mudek", "komisyon", "tutanak", "resmi yazı", "dilekçe")):
        return "memur"

    # 5. Postacı: E-posta, mail, gelen kutusu tarama
    if any(k in metin for k in ("eposta", "e-posta", "mail", "gmail", "outlook", "gelen kutu")):
        return "postaci"

    # 6. İK Memuru: Ajan kadrosu, yetenek/skill güncelleme
    if any(k in metin for k in ("ik-memuru", "kadro", "skill", "yetenek ekle")):
        return "ik-memuru"

    return "dekan"


def not_metni(mesaj: dict) -> str:
    Parcalar = []
    if mesaj.get("ek_turu"):
        ek_aciklama = f"[{mesaj['ek_turu']}: {mesaj.get('dosya_adi') or mesaj.get('dosya_id')}]"
        Parcalar.append(ek_aciklama)
    linkler = ", ".join(mesaj.get("linkler") or [])
    metin = _temiz(mesaj.get("not") or mesaj.get("metin"))
    if linkler and metin:
        Parcalar.append(f"{linkler} — {metin}")
    elif linkler or metin:
        Parcalar.append(linkler or metin)
    return " ".join(Parcalar) or "(boş mesaj)"


def kostur(kok, takim: str) -> int:
    """Seçilen birimi koşturur, ardından ZİNCİR devri için dağıtıcıyı tetikler."""
    sonuc = subprocess.run([sys.executable, str(Path(kok) / "bin" / "kos.py"), takim], cwd=str(kok))
    subprocess.run([sys.executable, str(Path(kok) / "bin" / "dagitici.py")], cwd=str(kok))
    return sonuc.returncode


def _kuyruk_tamam_isaretle(kok, takim: str, id_: str, sonuc_notu: str = ""):
    durum = ayar.durum_oku(takim, kok)
    kuyruk = list(durum.get("kuyruk") or [])
    zaman = ayar.simdi_iso()
    bulundu = False
    for o in kuyruk:
        if isinstance(o, dict) and o.get("id") == id_:
            o["durum"] = "tamam"
            o["tamamlanma"] = zaman
            if sonuc_notu:
                o["sonuc"] = sonuc_notu
            bulundu = True
    if not bulundu:
        kuyruk.append({"id": id_, "durum": "tamam", "not": sonuc_notu, "tamamlanma": zaman})
    ayar.durum_guncelle(
        takim,
        {"durum": "bosta", "son_kosu": zaman, "son_sonuc": sonuc_notu or "tamam", "kuyruk": kuyruk},
        kok,
    )


def _hizli_komut_isle(kok, metin: str, update_id: int) -> tuple[bool, str]:
    """
    0-token ile anında yanıtlanabilecek tablo listeleme / senkron / onay boyama komutlarını işler.
    (islendi_mi, telegram_yaniti) döner.
    """
    m = (metin or "").strip()
    m_low = m.replace("İ", "i").replace("I", "ı").lower()

    # 1. Öğrenci staj onaylama ve yeşil (+ tekrarları sarı) boyama komutu
    ogr_eslesme = OGRENCI_NO_RE.search(m)
    if ogr_eslesme and any(k in m_low for k in ("onayla", "yeşile boya", "yesile boya")):
        ogr_no = ogr_eslesme.group(1).upper()
        ok = staj_senkron.kisisel_tablo_onayla_yesil_boya(ogr_no)
        _kuyruk_tamam_isaretle(kok, "staj-burosu", f"tg-{update_id}", f"{ogr_no} onaylandı ve boyandı ({ok})")
        if ok:
            return True, (
                f"🏛️ *Dekanlık — Staj Onay İşlemi*\n\n"
                f"✅ *{ogr_no}* numaralı öğrencinin son staj satırı online Kişisel Tabloda *yeşile* (`#D9EAD3`), "
                f"varsa önceki mükerrer satırları *sarıya* (`#FFF2CC`) boyandı."
            )
        return True, f"🏛️ *Dekanlık:* `{ogr_no}` satırı boyanırken online tablo bağlantısında sorun oluştu."

    # 2. Ortak tablodan senkronizasyon komutu
    if any(k in m_low for k in ("senkron", "güncelle", "guncelle", "yeni defter var mı", "atanmış mı")):
        try:
            res = staj_senkron.senkron_kontrol()
            yeni_liste = res.get("yeni_eklenenler") or []
            _kuyruk_tamam_isaretle(
                kok, "staj-burosu", f"tg-{update_id}", f"senkron tamam ({len(yeni_liste)} yeni tekil öğrenci)"
            )
            if yeni_liste:
                satirlar = [
                    f"🏛️ *Dekanlık:* Ortak tablo tarandı ve *{len(yeni_liste)} yeni tekil öğrenci* online Kişisel Tablonuza eklendi:",
                    "",
                ]
                for y in yeni_liste:
                    satirlar.append(f"• *{y['ogrenci_no']}* - {y['ad_soyad']}")
                return True, "\n".join(satirlar)
            return True, "🏛️ *Dekanlık:* Ortak tablo kontrol edildi. Son imleçten sonra üzerinize atanan yeni defter bulunmuyor."
        except Exception as e:
            return True, f"🏛️ *Dekanlık:* Senkronizasyon sırasında hata oluştu: {e}"

    # 3. Salt staj durum / okunmayan tekil öğrenci listeleme sorgusu (inceleme emri içermiyorsa)
    inceleme_istegi = any(k in m_low for k in ("incele", "değerlendir", "degerlendir", "kontrol et ve raporla"))
    listeleme_istegi = any(
        k in m_low for k in ("staj", "defter", "kaç adet", "kac adet", "okunmayan", "revize", "listele", "atanan", "durum")
    )
    if listeleme_istegi and not inceleme_istegi and not ogr_eslesme:
        try:
            ozet = staj_senkron.kisisel_tablo_durum_listele()
            okunmayan = ozet.get("okunmamis") or []
            revize = ozet.get("revize_bekleyen") or []

            satirlar = [
                "🏛️ *Dekanlık — Staj Durum Raporu*",
                "",
                f"Alper Bey, online Kişisel Tablonuz (`Atölye` sekmesi) tekil öğrenci dökümü:",
                "",
                f"🟡 *REVİZYON BEKLEYENLER ({len(revize)} Tekil Öğrenci):*",
            ]
            for r in revize:
                not_degeri = r.get("not_metni") or r.get("not") or "—"
                satirlar.append(f"• *{r.get('ogrenci_no')}* - {r.get('ad_soyad')} | Not: _{not_degeri}_")

            satirlar.append("")
            satirlar.append(f"⚪ *OKUNMAYAN DEFTERLER ({len(okunmayan)} Tekil Öğrenci):*")
            for o in okunmayan:
                tekrar_ek = (
                    f" _(Önceki tekrar satırı: {', '.join(map(str, o['onceki_tekrar_satirlar']))})_"
                    if o.get("onceki_tekrar_satirlar")
                    else ""
                )
                satirlar.append(f"• Satır {o.get('satir')}: *{o.get('ogrenci_no')}* - {o.get('ad_soyad')}{tekrar_ek}")

            satirlar.append("")
            satirlar.append("İncelemeyi başlatmak için *'<ÖğrenciNo> incele'* emri verebilirsiniz.")
            _kuyruk_tamam_isaretle(
                kok, "staj-burosu", f"tg-{update_id}", f"Tekil staj listesi sunuldu ({len(okunmayan)} okunmayan)"
            )
            return True, "\n".join(satirlar)
        except Exception as e:
            return True, f"🏛️ *Dekanlık:* Staj tablosu sorgulanırken hata oluştu: {e}"

    return False, ""


def tek_tur(kok, token, chat_id, bekleme=BEKLEME_SN):
    """Telegram'ı bir kez yoklar; yeni mesaj varsa Dekan olarak yanıtlar, kuyruğa yazar ve ilgili birimi koşturur."""
    son = int((ayar.durum_oku(TAKIM, kok).get("sayaclar") or {}).get("telegram_son_update", 0))
    try:
        guncellemeler = telegram_oku.guncellemeleri_cek(
            token, offset=son + 1 if son else None, bekleme=bekleme
        )
    except telegram_oku.TelegramHatasi as exc:
        _log(kok, f"{exc} (kod={exc.kod}) — tur atlandı")
        return []

    yazilan = telegram_oku.isle(kok, guncellemeler, chat_id)
    if not yazilan:
        return []

    gruplar = collections. OrderedDict()
    for yol in yazilan:
        try:
            mesaj = json.loads(Path(yol).read_text(encoding="utf-8"))
        except Exception:
            continue

        metin = mesaj.get("metin") or mesaj.get("not") or ""
        update_id = mesaj.get("update_id")

        # Önce 0-token hızlı sorgu mu kontrol et
        islendi, hizli_yanit = _hizli_komut_isle(kok, metin, update_id)
        if islendi:
            _log(kok, f"tg-{update_id} → Dekan hızlı yanıt üretti ve tamamlandı")
            telegram_oku.mesaj_gonder(token, chat_id, hizli_yanit)
            continue

        hedef_takim = takim_sec(mesaj)
        notu = f"telegram: {not_metni(mesaj)}"
        dagitici.kuyruga_yaz(kok, hedef_takim, f"tg-{update_id}", notu)
        _log(kok, f"tg-{update_id} -> {hedef_takim}: {notu}")
        gruplar.setdefault(hedef_takim, []).append(mesaj)

    # Ajan koşusu gerektiren birimleri tetikle ve sonucu Telegram'dan bildir
    for hedef_takim, mesajlar in gruplar.items():
        simdi = datetime.now().astimezone()
        kossun, sebep = dagitici.tetik_karari(kok, hedef_takim, simdi)
        if not kossun:
            # Tetik kararı olumsuzsa (mesai dışı, günlük bütçe/koşu tavanı vb.) kullanıcıyı bilgilendir
            telegram_oku.mesaj_gonder(
                token,
                chat_id,
                f"🏛️ *Dekanlık:* Emriniz alındı ve `{hedef_takim}` kuyruğuna eklendi ({sebep}).",
            )
            _log(kok, f"{hedef_takim} kuyrukta bekler — {sebep}")
            continue

        telegram_oku.mesaj_gonder(
            token,
            chat_id,
            f"🏛️ *Dekanlık:* Emriniz alındı Alper Bey. Görev `{hedef_takim}` birimine atandı ({len(mesajlar)} mesaj), koşu başlatılıyor...",
        )
        _log(kok, f"{hedef_takim} koşturuluyor ({len(mesajlar)} yeni mesaj)")
        kod = kostur(kok, hedef_takim)
        guncel_durum = ayar.durum_oku(hedef_takim, kok)
        son_sonuc = guncel_durum.get("son_sonuc") or f"çıkış={kod}"
        _log(kok, f"{hedef_takim} bitti (çıkış={kod}): {son_sonuc}")
        telegram_oku.mesaj_gonder(
            token,
            chat_id,
            f"🏛️ *Dekanlık — `{hedef_takim}` Raporu:*\n{son_sonuc}",
        )

    return yazilan


def _otomatik_staj_ve_eposta_kontrol(kok, token, chat_id, son_posta: float, son_staj: float) -> tuple[float, float]:
    """Mesai saatleri içinde 15 dk'da bir e-postaları, 30 dk'da bir ortak staj tablosunu kontrol eder."""
    simdi = time.time()
    if not ayar.mesaide_mi():
        return son_posta, son_staj

    # 15 dakikada bir e-posta kontrolü
    if simdi - son_posta >= 900:
        son_posta = simdi
        try:
            subprocess.run(
                [sys.executable, str(Path(kok) / "bin" / "posta_cek.py"), "--son"],
                cwd=str(kok),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        except Exception as e:
            _log(kok, f"periyodik e-posta kontrol hatası: {e}")

    # 30 dakikada bir ortak staj tablosu kontrolü (yeni defter atanmış mı?)
    if simdi - son_staj >= 1800:
        son_staj = simdi
        try:
            res = staj_senkron.senkron_kontrol()
            yeni_liste = res.get("yeni_eklenenler") or []
            if yeni_liste:
                _log(kok, f"Otomatik staj senkronu: {len(yeni_liste)} yeni tekil öğrenci tespit edildi")
                satirlar = [
                    f"🏛️ *Dekanlık — Otomatik Staj Bildirimi*",
                    f"Ortak tabloda üzerinize atanan *{len(yeni_liste)} yeni tekil staj defteri* tespit edildi ve online Kişisel Tablonuza eklendi:",
                    "",
                ]
                for y in yeni_liste:
                    satirlar.append(f"• *{y['ogrenci_no']}* - {y['ad_soyad']}")
                telegram_oku.mesaj_gonder(token, chat_id, "\n".join(satirlar))
        except Exception as e:
            _log(kok, f"periyodik staj senkron hatası: {e}")

    return son_posta, son_staj


def main(argv) -> int:
    for _akis in (sys.stdout, sys.stderr):
        if _akis is not None and hasattr(_akis, "reconfigure"):
            try:
                _akis.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    ayar.ortam_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    ham_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not ham_id:
        print(
            "telegram_dinle: TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID `.env` içinde tanımlı olmalı",
            file=sys.stderr,
        )
        return 1
    sir_ekle(token)
    chat_id = int(ham_id)
    if "--bir-kez" in argv:
        tek_tur(KOK, token, chat_id, bekleme=0)
        return 0

    with _tekil_dinleyici_kilidi(KOK) as kilit_alindi:
        if not kilit_alindi:
            print("[BİLGİ] telegram_dinle.py zaten başka bir süreçte çalışıyor; çıkılıyor.")
            return 0

        _log(KOK, f"dinleyici başladı (long-poll={BEKLEME_SN}sn, mesai={ayar.MESAI_METNI})")
        son_posta_kontrol = time.time()
        son_staj_kontrol = time.time()
        try:
            while True:
                try:
                    tek_tur(KOK, token, chat_id, bekleme=BEKLEME_SN)
                    son_posta_kontrol, son_staj_kontrol = _otomatik_staj_ve_eposta_kontrol(
                        KOK, token, chat_id, son_posta_kontrol, son_staj_kontrol
                    )
                except Exception as exc:
                    _log(KOK, f"beklenmeyen tur hatası (devam ediliyor): {exc}")
                time.sleep(TUR_ARASI_SN)
        except KeyboardInterrupt:
            _log(KOK, "dinleyici durdu (SIGINT)")
            return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
