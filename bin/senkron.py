#!/usr/bin/env python3
"""
Ofis Ajan Şirketi - Çift Repo Senkronizasyon ve Yayın Aracı (senkron.py)

Kullanım:
  py -3 bin/senkron.py --cek              # Mesai başı: Özel repodan (ofis-YTU) çek (git pull origin main)
  py -3 bin/senkron.py --gonder [mesaj]   # Mesai sonu: Özel repoya (ofis-YTU) gönder (git push origin main)
  py -3 bin/senkron.py --public-yayinla   # Kamuya açık şablonu (ofis-ajan-sistemi) güvenle arındırıp pushla!
"""
import subprocess
import sys
from pathlib import Path

KOK_DIZIN = Path(__file__).resolve().parent.parent


def calistir(komut: list[str], kontrol: bool = True) -> tuple[int, str]:
    try:
        sonuc = subprocess.run(
            komut,
            cwd=str(KOK_DIZIN),
            capture_output=True,
            text=True,
            check=kontrol,
        )
        return sonuc.returncode, (sonuc.stdout + sonuc.stderr).strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.stdout + e.stderr).strip()
    except Exception as e:
        return 1, str(e)


def senkron_cek():
    """Mesai başlangıcında en güncel durumu özel depodan (origin main) çeker."""
    print("[BİLGİ] Özel repodan güncellemeler çekiliyor (git pull origin main)...")
    kod, cikti = calistir(["git", "pull", "origin", "main"], kontrol=False)
    print(cikti or ("Başarılı" if kod == 0 else "Hata"))


def senkron_gonder(mesaj: str = "mesai: ofis durumu guncellendi"):
    """Mesai bitiminde güncel durumu özel depoya (origin main) gönderir."""
    print(f"[BİLGİ] Özel repoya gönderiliyor (origin main): '{mesaj}'")
    calistir(["git", "add", "."], kontrol=False)
    calistir(["git", "commit", "-m", mesaj], kontrol=False)
    kod, cikti = calistir(["git", "push", "origin", "main"], kontrol=False)
    print(cikti or ("Başarılı" if kod == 0 else "Hata"))


def public_yayinla():
    """
    Kamuya açık şablonu (public-template / ofis-ajan-sistemi) yayınlar:
    1. tests/test_kit.py güvenlik testini çalıştırır.
    2. public-sablon dalındaki genel şablonu public-template'e pushlar.
    3. Kullanıcıya işlem sonucunu bildirir.
    """
    print("[BİLGİ] 1/3: Güvenlik ve KVKK denetimi çalıştırılıyor (pytest tests/test_kit.py)...")
    kod, cikti = calistir([sys.executable, "-m", "pytest", "tests/test_kit.py", "-q"], kontrol=False)
    if kod != 0:
        print(f"[HATA] Güvenlik denetimi geçemedi! Public push iptal edildi:\n{cikti}")
        return 1

    print("[BİLGİ] 2/3: Kamuya açık depoya (public-template main) pushlanıyor...")
    kod, cikti = calistir(["git", "push", "public-template", "public-sablon:main", "-f"], kontrol=False)
    if kod != 0:
        print(f"[HATA] Public push başarısız oldu:\n{cikti}")
        return 1

    print("[BİLGİ] 3/3: Başarılı! Açık kaynak şablon güncellendi: https://github.com/alpercftc/ofis-ajan-sistemi")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--public-yayinla" in argv:
        return public_yayinla()
    if "--gonder" in argv:
        mesaj = argv[argv.index("--gonder") + 1] if len(argv) > argv.index("--gonder") + 1 else "mesai: ofis guncellendi"
        senkron_gonder(mesaj)
        return 0
    senkron_cek()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
