# -*- coding: utf-8 -*-
"""
ADIM 1 - ICERIK FIKRI URETIMI
Kanal kimligine uygun, daha once kullanilmamis bir video fikri uretir.
"""
import json
import random
from datetime import datetime
from typing import Any, Dict, List

import config
from utils import ai, logger

SISTEM = """Sen bir YouTube cocuk kanalinin yaratici icerik yoneticisisin.

KANAL: {kanal_adi}
TANIM: {kanal_tanimi}

GOREVIN: Kanala uygun, ozgun ve merak uyandiran TEK bir video fikri uretmek.

KESIN KURALLAR:
- Hedef kitle 3-8 yas Turk cocuklari. Dil sade, sicak ve neseli olmali.
- Korku, siddet, olum, hastalik, kavga, aglama, karanlik temalar YASAK.
- Marka, telifli karakter (Disney, Pixar, cizgi film kahramanlari) KULLANMA.
- Gercek kisi ismi kullanma.
- Fikir tek cumlede anlatilabilecek kadar net olmali.
- Cocugun ogrenecegi somut bir sey veya guzel bir mesaj icermeli.
- Verilen "kullanilmis konular" listesindekilere BENZEYEN fikir uretme.

Cevabini SADECE su JSON formatinda ver, baska hicbir sey yazma:
{{
  "konu": "Videonun konusu, kisa ve net (max 10 kelime)",
  "hedef_yas": "3-5 veya 5-8",
  "ozet": "Videoda ne anlatilacak, 2-3 cumle",
  "mesaj": "Cocugun edinecegi kazanim veya ana mesaj, tek cumle",
  "neden_ilgi_ceker": "Neden cocuklarin ilgisini ceker, tek cumle",
  "anahtar_kelimeler": ["5", "adet", "turkce", "anahtar", "kelime"]
}}"""

ISTEK = """Video tipi: {tip_ad} ({en_boy}, yaklasik {sure} saniye)
Bu tip icin uygun konu turleri: {konu_tipleri}
Bu videoda su tur one cikacak: {secilen_tur}

Daha once kullanilmis konular (bunlara benzeme):
{gecmis}

Simdi yeni ve ozgun bir fikir uret."""

MOCK_FIKIR = {
    "konu": "Kaybolan gokkusaginin renkleri",
    "hedef_yas": "3-5",
    "ozet": "Bir sabah gokkusagi uyandiginda renklerinin kayboldugunu fark eder. "
            "Kucuk bir kus ona yardim etmek icin doganin icinde renkleri tek tek arar. "
            "Her bulunan renk gokkusagina geri doner.",
    "mesaj": "Yardimlasmak zor gorunen isleri kolaylastirir.",
    "neden_ilgi_ceker": "Cocuklar renkleri tanirken bir arama oyununa katilmis gibi hisseder.",
    "anahtar_kelimeler": ["gokkusagi", "renkler", "cocuk masali", "yardimlasma", "egitici"],
}


# ------------------------------------------------------------------ gecmis
def _gecmis_oku() -> List[Dict[str, Any]]:
    try:
        return json.loads(config.FIKIR_GECMISI.read_text(encoding="utf-8"))
    except Exception:
        return []


def _gecmis_yaz(kayit: Dict[str, Any]) -> None:
    gecmis = _gecmis_oku()
    gecmis.append(kayit)
    gecmis = gecmis[-200:]          # son 200 kayit yeter
    config.FIKIR_GECMISI.write_text(
        json.dumps(gecmis, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _gecmis_metni(adet: int = 30) -> str:
    gecmis = _gecmis_oku()[-adet:]
    if not gecmis:
        return "(henuz kullanilmis konu yok)"
    return "\n".join(f"- {k['konu']}" for k in gecmis)


# ------------------------------------------------------------------ ana fonksiyon
def fikir_uret(video_tipi: str) -> Dict[str, Any]:
    """video_tipi: 'shorts' veya 'uzun'"""
    if video_tipi not in config.VIDEO_TIPLERI:
        raise ValueError(f"Bilinmeyen video tipi: {video_tipi}")

    profil = config.VIDEO_TIPLERI[video_tipi]
    secilen_tur = random.choice(profil["konu_tipleri"])

    logger.bilgi(f"Fikir araniyor... (tip: {profil['ad']}, tur: {secilen_tur})")

    sistem = SISTEM.format(
        kanal_adi=config.KANAL_ADI, kanal_tanimi=config.KANAL_TANIMI
    )
    istek = ISTEK.format(
        tip_ad=profil["ad"],
        en_boy=profil["en_boy"],
        sure=profil["hedef_saniye"],
        konu_tipleri=", ".join(profil["konu_tipleri"]),
        secilen_tur=secilen_tur,
        gecmis=_gecmis_metni(),
    )

    fikir = ai.sor(sistem, istek, sicaklik=1.0, mock_cevap=MOCK_FIKIR)

    # Zorunlu alan kontrolu
    for alan in ("konu", "ozet", "mesaj", "anahtar_kelimeler"):
        if not fikir.get(alan):
            raise ai.AIHatasi(f"Fikirde '{alan}' alani eksik: {fikir}")

    fikir["video_tipi"] = video_tipi
    fikir["konu_turu"] = secilen_tur
    fikir["tarih"] = datetime.now().isoformat(timespec="seconds")

    _gecmis_yaz({"konu": fikir["konu"], "tarih": fikir["tarih"], "tip": video_tipi})

    logger.ok(f"Fikir hazir: {fikir['konu']}")
    return fikir
