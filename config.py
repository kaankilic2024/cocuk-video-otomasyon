# -*- coding: utf-8 -*-
"""
Merkezi ayar dosyasi. Degistirmek istedigin her sey burada.
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------- KLASORLER
KOK = Path(__file__).parent
OUTPUT_DIR = KOK / "output"
DATA_DIR = KOK / "data"
ASSETS_DIR = KOK / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"

for _d in (OUTPUT_DIR, DATA_DIR, ASSETS_DIR, MUSIC_DIR, SFX_DIR):
    _d.mkdir(parents=True, exist_ok=True)

FIKIR_GECMISI = DATA_DIR / "fikir_gecmisi.json"

# ---------------------------------------------------------------- API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Yeni modeller cevap yazmadan once "dusunuyor"; bu da token sinirindan
# dusuyor. Butceyi sinirlamak cevaba yer birakir ve maliyeti azaltir.
# None yaparsan sinir konmaz (modelin varsayilani kullanilir).
GEMINI_DUSUNME_BUTCESI = 512
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)
GEMINI_MODEL_LISTESI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
)

# ---------------------------------------------------------------- KANAL KIMLIGI
# Senaryo uretilirken yapay zekaya verilen kanal tarifi.
KANAL_ADI = "Minik Kesif"
KANAL_TANIMI = (
    "3-8 yas arasi Turk cocuklari icin egitici, sicak ve neseli videolar. "
    "Hikayeler her zaman olumlu bir mesajla biter. Korkutucu, siddet iceren, "
    "uzucu veya yas grubuna uygun olmayan hicbir unsur bulunmaz."
)

# Gorsellerin ortak stili (Ingilizce -- gorsel modeli Ingilizce daha iyi anliyor)
GORSEL_STIL = (
    "soft 3D cartoon illustration for young children, rounded friendly shapes, "
    "warm pastel color palette, gentle soft lighting, storybook look, "
    "consistent art style, smooth clean render, "
    "not photorealistic, not a plush toy photo, "
    "no text, no letters, no watermark"
)

# ---------------------------------------------------------------- VIDEO TIPLERI
VIDEO_TIPLERI = {
    "shorts": {
        "ad": "Shorts (dikey)",
        "genislik": 1080,
        "yukseklik": 1920,
        "en_boy": "9:16",
        "hedef_saniye": 45,
        "kompozisyon": "vertical 9:16 framing, subject fills most of the frame, "
                       "no large empty space at the bottom",
        "sahne_sayisi": (5, 7),
        "sahne_kelime": (10, 15),   # olculen hiza gore kalibre edildi
        "konu_tipleri": [
            "bilmece", "kisa tekerleme", "biliyor muydun",
            "karsit kavramlar (buyuk-kucuk, hizli-yavas)",
            "renk ogrenme", "hayvan sesi tanima", "cok kisa mini hikaye",
        ],
        # NOT: "sayma oyunu" bilerek cikarildi. Gorsel ureticiler nesne sayisini
        # dogru cizemiyor (5 meyve isteyip 12 meyve cizebiliyor) ve bu cocuga
        # yanlis bilgi verir. Adim 3-5 bittikten sonra, gorselleri kodla yan yana
        # dizen bir yontemle geri eklenecek.
    },
    "uzun": {
        "ad": "Uzun video (yatay)",
        "genislik": 1920,
        "yukseklik": 1080,
        "en_boy": "16:9",
        "hedef_saniye": 240,
        "kompozisyon": "horizontal 16:9 cinematic framing, balanced composition",
        "sahne_sayisi": (20, 26),
        "sahne_kelime": (14, 20),   # olculen hiza gore kalibre edildi
        "konu_tipleri": [
            "masal", "dostluk hikayesi", "hayvanlar dunyasi", "uzay ve gezegenler",
            "meslekleri taniyalim", "mevsimler ve doga", "iyi aliskanliklar hikayesi",
        ],
    },
}

# Gunluk uretim plani: kac tane hangi tipte
GUNLUK_PLAN = {"shorts": 2, "uzun": 2}

# ---------------------------------------------------------------- GORSEL URETIMI
# Pollinations.ai - API anahtari gerektirmez, ucretsizdir.
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"
GORSEL_MODEL = os.getenv("GORSEL_MODEL", "flux")
GORSEL_DENEME = 5           # basarisiz gorsel kac kez tekrar denensin
GORSEL_BEKLEME = 3          # gorseller arasi bekleme (saniye)
GORSEL_ZAMAN_ASIMI = 110    # tek gorsel icin en fazla bekleme (saniye)
                            # (sunucu takilirsa erken vazgecip tekrar dene)

# Seed, goruntunun kompozisyonunu belirler.
#   "sahne_basi" -> her sahnede farkli seed. Kadraj ve aci degisir, video
#                   canli olur. Karakter tutarliligi prompta birakilir.
#   "sabit"      -> tum sahnelerde ayni seed. Karakter daha tutarli olur ama
#                   butun kareler ayni kompozisyonda cikar (video donuk gorunur).
SEED_MODU = os.getenv("SEED_MODU", "sahne_basi")

# ---------------------------------------------------------------- SESLENDIRME
# edge-tts (Microsoft nöral sesler) - ucretsiz, anahtar gerektirmez.
# Turkce'de iki nöral ses var: Emel (kadin), Ahmet (erkek).
# Hiz ve perde ayariyla bunlardan farkli karakterler cikarabiliyoruz.
#
# Hepsini dinlemek icin:  python main.py --ton-dene
SES_TONLARI = {
    "sakin": {
        "ses": "tr-TR-EmelNeural", "hiz": "-5%", "perde": "+0Hz",
        "aciklama": "Yavas ve yumusak - uyku masallari icin",
    },
    "normal": {
        "ses": "tr-TR-EmelNeural", "hiz": "+0%", "perde": "+5Hz",
        "aciklama": "Dengeli anlatim",
    },
    "canli": {
        "ses": "tr-TR-EmelNeural", "hiz": "+10%", "perde": "+18Hz",
        "aciklama": "Enerjik ve genc - cocuk videolari icin onerilir",
    },
    "cok_canli": {
        "ses": "tr-TR-EmelNeural", "hiz": "+18%", "perde": "+30Hz",
        "aciklama": "Cok hizli ve tiz - Shorts icin dikkat cekici",
    },
    "neseli_erkek": {
        "ses": "tr-TR-AhmetNeural", "hiz": "+12%", "perde": "+20Hz",
        "aciklama": "Erkek ses, enerjik",
    },
    "sakin_erkek": {
        "ses": "tr-TR-AhmetNeural", "hiz": "+0%", "perde": "+0Hz",
        "aciklama": "Erkek ses, klasik anlatici",
    },
}

SES_TONU = os.getenv("SES_TONU", "canli")

_ton = SES_TONLARI.get(SES_TONU, SES_TONLARI["canli"])
SES_ADI = os.getenv("SES_ADI", _ton["ses"])
SES_HIZI = os.getenv("SES_HIZI", _ton["hiz"])
SES_PERDESI = os.getenv("SES_PERDESI", _ton["perde"])


def _hiz_carpani(hiz: str) -> float:
    """'+10%' -> 1.10. Konusma hizi tahminini duzeltmek icin."""
    try:
        return 1 + int(hiz.replace("%", "")) / 100
    except Exception:
        return 1.0


# Olculen temel konusma hizi (-5% ayarinda 1.65 kelime/sn idi).
# Secilen tona gore otomatik olceklenir.
KELIME_HIZI = round(1.65 / _hiz_carpani("-5%") * _hiz_carpani(SES_HIZI), 2)

# edge-tts dosyalarin basina/sonuna ~1 sn sessizlik ekliyor. Bu, sahne
# aralarinin gereginden uzun olmasina yol aciyor; kirpip kendi bosluğumuzu
# (SAHNE_ARASI_BOSLUK) koyuyoruz.
SESSIZLIK_KIRP = True
SESSIZLIK_ESIGI = "-50dB"

# edge-tts cumle aralarinda ~1.1 sn susuyor. Cocuk videosunda bu cok uzun;
# duraklamalari bu degere indiriyoruz. Cok kucultursen konusma bogucu olur.
CUMLE_ARASI_DURAKLAMA = 0.45   # saniye

# ---------------------------------------------------------------- MONTAJ
FPS = 30
X264_KALITE = 23            # kucuk sayi = daha kaliteli, daha buyuk dosya (18-28)
X264_HIZI = "veryfast"      # ultrafast / veryfast / fast / medium / slow
ZOOM_MIKTARI = 0.12         # Ken Burns yakinlasma orani (%12)
ZOOM_ON_OLCEK = 1.3         # titremeyi azaltmak icin gorseli buyutme carpani
# IKI KARELI HAREKET
# Her sahne icin ayni seed ile iki gorsel uretilir (ayni yer, farkli poz) ve
# aralarinda gecis yapilir; karakter hareket ediyormus gibi gorunur.
# Kapatirsan gorsel uretimi iki kat hizlanir ama video daha donuk olur.
IKI_KARE = True
POZ_GECIS_SURESI = 0.9      # pozlar arasi gecis suresi (saniye)
POZ_GECIS_KONUMU = 0.45     # gecis sahnenin neresinde basliyor (0-1)

# KARAOKE ALTYAZI
# Kelimeler konusmayla senkron ekranda belirir. 5-8 yas icin okuma destegi,
# ayrica sesi kapali izleyenleri tutar.
ALTYAZI_GOM = True
# Yazi tipi isletim sistemine gore secilir; GitHub Actions (Linux) uzerinde
# Verdana bulunmadigi icin orada DejaVu Sans kullanilir.
_varsayilan_yazi = "Verdana" if sys.platform == "win32" else "DejaVu Sans"
ALTYAZI_YAZI_TIPI = os.getenv("ALTYAZI_YAZI_TIPI", _varsayilan_yazi)
ALTYAZI_BOYUT_ORANI = 0.055         # video yuksekliginin orani
ALTYAZI_KONUM = 0.80                # 0=ust, 1=alt (0.80 = alt uctelik)
ALTYAZI_RENK = "&H00FFFFFF"         # beyaz (ASS formati: &HAABBGGRR)
ALTYAZI_KENAR_RENGI = "&H00202020"  # koyu gri kenarlik
ALTYAZI_KELIME_SAYISI = 3           # bir parcada en fazla kac kelime
ALTYAZI_ASGARI_SURE = 0.45          # bir parca en az kac saniye ekranda kalsin

SAHNE_ARASI_BOSLUK = 0.4    # her sahnenin sonuna eklenen sessizlik (saniye)
SON_SAHNE_BOSLUK = 0.15     # son sahnede daha kisa (Shorts basa donuyor)
GECICI_DOSYALARI_SIL = True

# Arka plan muzigi: assets/music klasorune telifsiz mp3 koyarsan otomatik kullanilir
MUZIK_KULLAN = True
MUZIK_SESI = 0.1           # 0.05-0.12 arasi uygundur; konusmayi bastirmamali

# YouTube sesi -14 LUFS'a normalize eder. Kendi videomuz bunun altinda kalirsa
# diger videolardan kisik duyulur.
# Sahne gecislerinde calan yumusak "ciiink" sesi. Dosya indirmene gerek yok,
# kod kendisi uretiyor. Video daha canli hissettirir.
SFX_KULLAN = True
SFX_SESI = 0.15            # 0.15-0.6 arasi; konusmayi bastirmamali
SFX_TEPE_GENLIK = 0.5      # uretilen efektin genligi (0-1)

# Efekt secenekleri: chime, pop, whoosh, arp, sparkle, marimba
# Hepsini dinlemek icin:  python main.py --efektler
# Kendi sesini kullanmak istersen assets/sfx/gecis.wav olarak kaydet;
# dosya varsa kod uretmez, seninkini kullanir.
SFX_TIPI = os.getenv("SFX_TIPI", "whoosh")

SES_NORMALIZE = True
HEDEF_SES_SEVIYESI = -15    # LUFS

# ---------------------------------------------------------------- YOUTUBE
# OAuth dosyalari (bkz. YUKLEME_KURULUM.md)
CLIENT_SECRET = DATA_DIR / "client_secret.json"   # Google Cloud'dan indirilen
TOKEN_DOSYASI = DATA_DIR / "youtube_token.json"   # otomatik olusur, PAYLASMA

YOUTUBE_KATEGORI_ID = "27"          # 27 = Education
# "public" = herkese acik, "unlisted" = link ile, "private" = sadece sen
# Ilk haftalarda "private" birakip her videoyu izlemek daha guvenli olur.
YOUTUBE_GIZLILIK = os.getenv("YOUTUBE_GIZLILIK", "public")
COCUKLAR_ICIN = True                 # COPPA -- yasal zorunluluk, degistirme
YOUTUBE_DIL = "tr"
ALTYAZI_YUKLE = True

# Her videonun aciklamasinin sonuna eklenir (kanal tanitimi, uyari vb.)
ACIKLAMA_SONU = ""

# ---------------------------------------------------------------- GENEL
# Sahne basina kelime hedefleri, secilen ses tonunun hizina gore hesaplanir.
# Ton degistiginde bu degerler kendiliginden guncellenir.
for _tip in VIDEO_TIPLERI.values():
    _s_min, _s_max = _tip["sahne_sayisi"]
    _ortalama_sahne = (_s_min + _s_max) / 2
    _kelime_ort = _tip["hedef_saniye"] * KELIME_HIZI / _ortalama_sahne
    _tip["sahne_kelime"] = (round(_kelime_ort * 0.8), round(_kelime_ort * 1.2))

MOCK = os.getenv("MOCK", "0") == "1"   # API'siz test modu
LOG_SEVIYESI = os.getenv("LOG_SEVIYESI", "INFO")
