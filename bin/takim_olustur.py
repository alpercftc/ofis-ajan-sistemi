#!/usr/bin/env python3
"""
Yeni birim/takım klasörü oluşturur (bin/takim-olustur.sh karşılığı).
Kullanım: py -3 bin/takim_olustur.py <takim-adi> [takim-adi-2 ...]
"""
import re
import shutil
import sys
from pathlib import Path

from ayar import TAKIMLAR_DIZINI

KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def takim_olustur(ad: str) -> Path:
    if not KEBAB_RE.match(ad):
        raise ValueError(
            f"Takım adı küçük harf, rakam ve tireden oluşmalı (ör: staj-burosu). Gelen: {ad}"
        )

    iskelet = TAKIMLAR_DIZINI / "_iskelet"
    hedef = TAKIMLAR_DIZINI / ad

    if hedef.exists():
        raise FileExistsError(f"Zaten var: {hedef}")

    shutil.copytree(iskelet, hedef)
    (hedef / "kosu").mkdir(exist_ok=True)
    (hedef / "cikti").mkdir(exist_ok=True)
    (hedef / "kosu" / ".gitkeep").write_text("# .gitkeep\n", encoding="utf-8")
    (hedef / "cikti" / ".gitkeep").write_text("# .gitkeep\n", encoding="utf-8")

    for dosya_adi in ("takim.md", "kurallar.md", "defter.md", "durum.json"):
        dosya = hedef / dosya_adi
        if dosya.exists():
            icerik = dosya.read_text(encoding="utf-8")
            icerik = icerik.replace("TAKIM", ad).replace("{takim_adi}", ad)
            dosya.write_text(icerik, encoding="utf-8")

    print(f"Oluşturuldu: {hedef}")
    return hedef


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    adlar = sys.argv[1:]
    if not adlar:
        print("Kullanım: py -3 bin/takim_olustur.py <takim-adi> [...]", file=sys.stderr)
        return 1

    for ad in adlar:
        takim_olustur(ad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
