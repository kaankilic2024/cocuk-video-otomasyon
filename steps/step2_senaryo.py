# -*- coding: utf-8 -*-
"""
ADIM 2 - SENARYO URETIMI
Fikri alir; baslik, aciklama, etiketler ve sahne sahne senaryo uretir.
Her sahnenin hem Turkce seslendirme metni hem Ingilizce gorsel promptu olur.
"""
import random
import re
from typing import Any, Dict, List

import config
from utils import ai, logger

# Cocuk icerigine girmemesi gereken kelime kokleri.
# Kelime siniri (\b) ile aranir, boylece "kan" kelimesi "kanat" icinde eslesmez
# ve "oldu" gibi masum kelimeler "oldu"/"olum" ile karistirilmaz.
# 1) Turkce karakteri sart olanlar: bunlarin sapkasiz hali masum kelimelerle
#    karisir ("öldü" -> "oldu" = gerceklesti). Bu yuzden sadece dogru yazimla aranir.
YASAKLI_KESIN_YAZIM = [
    r"öld(ü|ür)", r"ölüm", r"ölü\b", r"ölecek",
]

# 2) Sapkasiz yazilsa da karismayanlar: metin sadelestirilerek aranir.
YASAKLI_SERBEST = [
    r"cenaze", r"mezar", r"tabut",
    r"silah", r"bicak", r"tabanca", r"tufek", r"bomba", r"patlama",
    r"savas", r"kavga", r"dovus", r"vurdu", r"yaralad", r"kan akt",
    r"korkunc", r"dehset", r"canavar", r"hayalet", r"cadi", r"seytan",
    r"cehennem", r"kabus", r"zombi", r"iblis", r"ejderha saldir",
    r"hastane", r"ameliyat", r"hastaland", r"zehir",
    r"aglad", r"hickir", r"yapayalniz kald", r"ceza verild",
    r"nefret", r"intikam", r"tehdit", r"hirsiz caldi",
]

_SAPKA = str.maketrans("çğıöşüâî", "cgiosuai")

HAREKETLER = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]

SISTEM = """Sen 3-8 yas cocuklar icin video senaryosu yazan bir uzmansin.

KANAL: {kanal_adi}
TANIM: {kanal_tanimi}

GOREVIN: Verilen fikri, sahne sahne bir video senaryosuna cevirmek.

ANLATIM METNI KURALLARI (Turkce):
- Cok sade Turkce. Kisa cumleler. Bir cumlede tek fikir.
- Sicak, neseli, merak uyandiran bir anlatici sesi.
- Yabanci kelime, karmasik terim, uzun sifat zinciri kullanma.
- Rakamlari yaziyla yaz (3 degil "uc"), kisaltma kullanma (vb., ör. gibi).
- Noktalama isaretlerini duzgun kullan; seslendirme motoru bunlara gore duraklar.
- Ilk sahne ilk 3 saniyede merak uyandirmali (soru sor veya sasirtici bir sey soyle).
- Son sahne izleyiciyi selamlamali ve abone olmaya nazikce davet etmeli.
- Korku, siddet, uzuntu, olum, hastalik, ceza temasi KESINLIKLE YASAK.
- Telifli karakter veya marka ismi KULLANMA.
- SAYI KURALI: Ekranda kac nesne oldugunu soyleyen cumle KURMA.
  ("Tabakta dort elma var", "Ucu birlikte zipladi" gibi.) Gorsel uretici
  nesneleri dogru sayida cizemez; cocuga yanlis sey ogretmis oluruz.
  Tek bir nesneden bahsetmek serbesttir ("bir kelebek kondu").
- Kapanis cumlesinde dogru Turkce kullan: "abone olmayi ve begenmeyi unutmayin"
  gibi. "Bizi sevmeyi unutma" gibi garip ifadeler kullanma.
- NEZAKET KELIMELERI KURALI: Kibar sozleri DOGRU baglamda kullan.
  Bir sey ALAN kisi "tesekkur ederim" der. Tesekkuru DUYAN kisi "rica ederim" der.
  Bir sey ISTEYEN kisi "lutfen" der. Bunlari karistirirsan cocuga yanlis ogretmis
  olursun; ozellikle nezaket konulu videolarda cok dikkatli ol.

GORSEL PROMPT KURALLARI (Ingilizce yaz):
- Her sahne icin tek bir durgun goruntu tarif et. Hareket tarif etme.
- SADECE sunlari yaz: ortam/mekan, karakterin ne yaptigi, isik, kompozisyon.
- KARAKTERIN GORUNUSUNU YAZMA (renk, kiyafet, tur, goz). Sistem onu otomatik
  ekleyecek. Sen sadece "resting on its back", "waving happily" gibi eylemi yaz.
- STIL KELIMESI YAZMA. "3d render", "illustration", "cartoon", "animation style",
  "digital art", "storybook" gibi ifadeler KULLANMA. Sistem otomatik ekleyecek.
- Goruntude yazi, harf, rakam olmasin.
- Belirsiz cogul yazma ("some apples", "many flowers"). Ya tek nesne yaz
  ("a red apple"), ya da "a few" gibi mugalak ifadeler yerine sahneyi
  nesne yigini olmadan tarif et.
- KARAKTERIN ADINI/TURUNU TEKRAR YAZMA. Prompta dogrudan eylemle basla:
  DOGRU: "bending down near a closed flower bud, soft morning light, wide shot"
  YANLIS: "A rabbit bending down near a closed flower bud..."
- CESITLILIK: Ardisik sahneler ayni goruntuye benzemesin. Her sahnede
  cekim olcegini degistir (wide shot / medium shot / close-up / low angle /
  high angle) ve mekani veya aciyi kaydir. Ayni pozu ust uste tekrarlama.

- RENK OGRETME KURALI (cok onemli):
  Anlatimda belirli bir rengi ogretiyorsan ("kirmizi", "sari" gibi), o sahnenin
  goruntusunde SADECE O RENK one cikmali. Aksi halde cocuk "kirmizi" duyup
  ekranda bes renk gorur ve hicbir sey ogrenmez.
  O sahne icin:
    * "karakter_sahnede" alanini FALSE yap (karakterin kendi renkleri karistirir)
    * Tek bir nesne tarif et, o rengte
    * Arka plani acikca notr yap: "on a plain soft white background"
    * Baska renkli nesne, desen veya dekor EKLEME
  DOGRU ornek: "a single bright red apple on a plain soft white background,
                soft even lighting, centered close-up"
  YANLIS ornek: "a red wagon of a colorful train in a flower filled garden"
- Prompt 20-35 kelime olsun.

KARAKTER SAYFASI KURALLARI:
- SADECE gorunus yaz: tur, renk, boyut, goz, kiyafet, aksesuar.
- RENKLERI ACIKCA YAZ. Ozellikle GOZ RENGI ve govde rengi mutlaka belirtilsin.
  Bu renkler videonun her sahnesinde ayni kalmali; yazmazsan her sahnede degisir.
- Nerede oldugunu, ne yaptigini, hangi pozda oldugunu YAZMA. Bunlar sahneye gore
  degisir; karakter sayfasina yazarsan her sahneyi bozar.
- DOGRU ornek: "a small round yellow bird, brown eyes, orange beak, tiny blue scarf"
- YANLIS ornek: "a yellow bird flying over the blue sea and smiling"

SAHNEDE KARAKTER VAR MI:
- Her sahne icin "karakter_sahnede" alanini doldur.
- Ana karakter o goruntude gorunuyorsa true, gorunmuyorsa false yaz.
- Ilk sahnede bilerek merak uyandiriyorsan (karakteri henuz gostermiyorsan) false yaz.

POZ KURALI (hareket icin):
- Her sahne icin karakterin IKI pozunu yaz: "poz_1" ve "poz_2".
- Bu ikisi arasinda yumusak gecis yapilarak karakter hareket ediyormus gibi
  gorunecek. Bu yuzden:
    * AYNI karakter, AYNI mekan, AYNI aci olmali
    * SADECE vucut duruşu ve yuz ifadesi degismeli
    * Mekan, isik, kamera acisi, kiyafet ASLA degismemeli
- Poz ifadeleri kisa olsun (3-8 kelime, Ingilizce).
- DOGRU: poz_1 "standing calmly, wings lowered, gentle smile"
         poz_2 "wings raised high, joyful open-mouth smile"
- YANLIS: poz_1 "standing in the snow"
          poz_2 "swimming in the ocean"      (mekan degisti -- olmaz)
- Karakter sahnede yoksa ("karakter_sahnede": false) poz alanlarini bos birak.

Cevabini SADECE su JSON formatinda ver, baska hicbir sey yazma:
{{
  "baslik": "YouTube basligi, 60 karakteri gecmesin, merak uyandirsin, emoji olabilir",
  "aciklama": "YouTube aciklamasi. 3-4 cumle tanitim, sonra bos satir, sonra 5 hashtag.",
  "etiketler": ["10", "adet", "turkce", "youtube", "etiketi"],
  "karakter_sayfasi": "Ana karakterin SADECE gorunus tarifi (Ingilizce). Karakter yoksa bos birak.",
  "sahneler": [
    {{
      "no": 1,
      "anlatim": "Bu sahnede seslendirilecek Turkce metin",
      "karakter_sahnede": true,
      "gorsel_prompt": "English: setting, light, composition -- NO pose, no character look, no style words",
      "poz_1": "starting pose, short English phrase",
      "poz_2": "ending pose, short English phrase, same place and angle"
    }}
  ]
}}"""

ISTEK = """FIKIR
Konu: {konu}
Hedef yas: {hedef_yas}
Ozet: {ozet}
Ana mesaj: {mesaj}

FORMAT
Video tipi: {tip_ad} ({en_boy})
Hedef sure: yaklasik {sure} saniye
Sahne sayisi: TAM OLARAK {sahne_min} ile {sahne_max} arasinda olsun
Her sahnenin anlatim metni: {kelime_min}-{kelime_max} kelime

Simdi senaryoyu yaz."""

MOCK_SENARYO = {
    "baslik": "Gokkusaginin Kayip Renkleri 🌈",
    "aciklama": "Bir sabah gokkusagi uyandiginda butun renklerinin kayboldugunu fark etti! "
                "Kucuk kus Pili, arkadasina yardim etmek icin dogayi karis karis geziyor. "
                "Acaba renkleri bulabilecek mi? Cocuklarla birlikte renkleri ogreniyoruz.\n\n"
                "#cocukmasali #gokkusagi #renklerogreniyorum #egiticicizgifilm #minikkesif",
    "etiketler": ["cocuk masali", "gokkusagi", "renkler", "egitici video",
                  "okul oncesi", "turkce masal", "renk ogrenme", "cizgi film",
                  "cocuk hikayesi", "minik kesif"],
    # Karakter sayfasi: SADECE gorunus, konum/eylem yok
    "karakter_sayfasi": "a small round yellow bird, big friendly dark eyes, orange beak, "
                        "tiny blue scarf around its neck",
    "sahneler": [
        {"no": 1, "karakter_sahnede": False,
         "anlatim": "Bir sabah gokyuzunde cok garip bir sey oldu. Gokkusagi bembeyaz uyandi!",
         "gorsel_prompt": "a completely white colorless rainbow arching over a green meadow "
                          "at sunrise, soft morning light, gentle clouds, wide shot"},
        {"no": 2, "karakter_sahnede": True,
         "poz_1": "flying fast with wings spread wide, surprised look",
         "poz_2": "hovering with wings tucked, curious tilted head",
         "anlatim": "Kucuk kus Pili bunu gorunce cok sasirdi. Hemen yardima kostu.",
         "gorsel_prompt": "flying quickly toward the pale white rainbow above a green meadow, "
                          "morning light, surprised pose, wide shot"},
        {"no": 3, "karakter_sahnede": True,
         "poz_1": "standing still, looking down at the flowers",
         "poz_2": "wings lifted, beak open in delight",
         "anlatim": "Once kirmizi rengi aradi. Onu kocaman bir gelincik tarlasinda buldu!",
         "gorsel_prompt": "standing in a huge field of bright red poppies, warm sunny sky, "
                          "looking amazed at the flowers, medium shot"},
        {"no": 4, "karakter_sahnede": True,
         "poz_1": "looking up, wings at sides",
         "poz_2": "wings raised high toward the sun, joyful",
         "anlatim": "Sonra sariyi buldu. Sari, gunesin icinde saklaniyordu.",
         "gorsel_prompt": "looking up at a big warm golden sun, glowing yellow light filling "
                          "the sky, joyful pose, low angle"},
        {"no": 5, "karakter_sahnede": True,
         "poz_1": "standing calmly facing forward",
         "poz_2": "one wing raised, celebrating",
         "anlatim": "En sonunda maviyi denizde buldu. Gokkusagi yeniden rengarenk oldu!",
         "gorsel_prompt": "in front of a full colorful rainbow over a calm blue sea, "
                          "celebrating happily, bright daylight, wide shot"},
        {"no": 6, "karakter_sahnede": True,
         "poz_1": "waving one wing, gentle smile",
         "poz_2": "both wings up, wide happy smile",
         "anlatim": "Yardimlasinca her sey ne kadar kolay, degil mi? Abone olmayi unutma!",
         "gorsel_prompt": "waving goodbye under a bright rainbow, flowers and butterflies "
                          "around, warm sunset light, medium shot"},
    ],
}


# ------------------------------------------------------------------ kontroller
# Anlatimda gecerse gorselle celisme riski olan sayi kelimeleri
SAYI_KELIMELERI = [
    "iki", "üç", "uc", "dört", "dort", "beş", "bes", "altı", "alti",
    "yedi", "sekiz", "dokuz", "on tane", "ikisi", "üçü", "ucu", "dördü",
]


RENKLER = ["kırmızı", "sarı", "mavi", "yeşil", "turuncu", "mor", "pembe",
           "siyah", "beyaz", "kahverengi", "gri", "kirmizi", "sari", "yesil"]


def _renk_kontrol(sahneler: List[Dict[str, Any]]) -> List[str]:
    """Renk ogreten sahnede goruntu notr degilse uyarir.

    Gorsel uretici sahnede birden fazla renk gosterirse cocuk hangi rengin
    ogretildigini anlamaz. Bu sahnelerde tek nesne + duz zemin gerekir.
    """
    uyarilar = []
    for s in sahneler:
        metin = s["anlatim"].lower()
        gecen = [r for r in RENKLER if re.search(rf"\b{r}\b", metin)]
        if not gecen:
            continue
        prompt = s["gorsel_prompt"].lower()
        notr = "plain" in prompt or "solid color background" in prompt
        if not notr or s.get("karakter_sahnede"):
            uyarilar.append(f"sahne {s['no']} ({gecen[0]})")
    return uyarilar


def _sayi_kontrol(sahneler: List[Dict[str, Any]]) -> List[int]:
    """Anlatiminda nesne sayisi geciyor olabilecek sahnelerin numaralarini dondurur."""
    riskli = []
    for s in sahneler:
        metin = s["anlatim"].lower()
        for kelime in SAYI_KELIMELERI:
            if re.search(rf"\b{kelime}\b", metin):
                riskli.append(s["no"])
                break
    return riskli


def _benzerlik_kontrol(hamlar: List[tuple]) -> List[str]:
    """Ardisik UC sahnede de ayni nesne/mekan geciyorsa uyarir.

    Kelime ortusme orani bu is icin ise yaramiyor (ayni goruntuyu farkli
    kelimelerle tarif edince oran dusuk cikiyor). Bunun yerine art arda uc
    sahnede tekrar eden ikili kelime obeklerini ariyoruz -- "flower bud"
    uc sahnede de geciyorsa uc gorsel de birbirine benzeyecek demektir.
    """
    def obekler(metin: str) -> set:
        kelimeler = re.findall(r"[a-z]{3,}", metin.lower())
        return {f"{a} {b}" for a, b in zip(kelimeler, kelimeler[1:])}

    # Her sahnede gecen genel kelimeler sinyal degil, gurultu
    GURULTU = {"soft", "warm", "bright", "gentle", "light", "lighting", "shot",
               "background", "sunlight", "atmosphere", "colorful", "view"}

    uyarilar = []
    for i in range(len(hamlar) - 2):
        ucler = hamlar[i:i + 3]
        ortak = obekler(ucler[0][1]) & obekler(ucler[1][1]) & obekler(ucler[2][1])
        ortak = {o for o in ortak if not set(o.split()) & GURULTU}
        if ortak:
            nolar = "-".join(str(n) for n, _ in ucler)
            ornek = sorted(ortak)[0]
            uyarilar.append(f"sahne {nolar} (hepsinde '{ornek}' var)")
    return uyarilar


def _yasakli_kontrol(senaryo: Dict[str, Any]) -> List[str]:
    """Senaryoda cocuk icerigine uygun olmayan kelime var mi diye bakar."""
    parcalar = [s.get("anlatim", "") for s in senaryo["sahneler"]]
    parcalar.append(senaryo.get("baslik", ""))
    parcalar.append(senaryo.get("aciklama", ""))
    tum_metin = " ".join(parcalar).lower()

    sade_metin = tum_metin.translate(_SAPKA)

    bulunanlar = []
    for kalip in YASAKLI_KESIN_YAZIM:
        e = re.search(rf"\b{kalip}\w*", tum_metin, flags=re.UNICODE)
        if e:
            bulunanlar.append(e.group(0))

    for kalip in YASAKLI_SERBEST:
        e = re.search(rf"\b{kalip}\w*", sade_metin, flags=re.UNICODE)
        if e:
            bulunanlar.append(e.group(0))

    return sorted(set(bulunanlar))


def _temizle(metin: str) -> str:
    """Seslendirme icin metni duzeltir."""
    metin = re.sub(r"\s+", " ", metin).strip()
    metin = metin.replace("...", "…")
    # Cumle sonunda noktalama yoksa nokta ekle
    if metin and metin[-1] not in ".!?…":
        metin += "."
    return metin


# Model kurali unutup stil kelimesi yazarsa temizlemek icin
STIL_KALIPLARI = [
    r"\b3d\s+(render|animation|cartoon)(\s+style)?\b",
    r"\b(children'?s?\s+)?(book\s+)?illustration(\s+style)?\b",
    r"\bcartoon\s+style\b",
    r"\bdigital\s+art\b",
    r"\bstorybook(\s+style|\s+look)?\b",
    r"\bpixar\s+style\b",
    r"\banimation\s+style\b",
    r"\bvertical\s+composition\b",
    r"\bhigh\s+quality\b",
    r"\b4k\b", r"\b8k\b",
]


def _prompt_temizle(prompt: str) -> str:
    """Stil kelimelerini ve fazla noktalama isaretlerini ayiklar."""
    for kalip in STIL_KALIPLARI:
        prompt = re.sub(kalip, "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\s*[.,]\s*(?=[.,])", "", prompt)   # ",," -> ","
    prompt = re.sub(r"\s+", " ", prompt)
    prompt = re.sub(r"^[\s,.]+|[\s,.]+$", "", prompt)
    return prompt


# ------------------------------------------------------------------ ana fonksiyon
def senaryo_uret(fikir: Dict[str, Any]) -> Dict[str, Any]:
    video_tipi = fikir["video_tipi"]
    profil = config.VIDEO_TIPLERI[video_tipi]
    s_min, s_max = profil["sahne_sayisi"]
    k_min, k_max = profil["sahne_kelime"]

    logger.bilgi(f"Senaryo yaziliyor... ({s_min}-{s_max} sahne)")

    sistem = SISTEM.format(
        kanal_adi=config.KANAL_ADI, kanal_tanimi=config.KANAL_TANIMI
    )
    istek = ISTEK.format(
        konu=fikir["konu"],
        hedef_yas=fikir.get("hedef_yas", "3-8"),
        ozet=fikir["ozet"],
        mesaj=fikir["mesaj"],
        tip_ad=profil["ad"],
        en_boy=profil["en_boy"],
        sure=profil["hedef_saniye"],
        sahne_min=s_min, sahne_max=s_max,
        kelime_min=k_min, kelime_max=k_max,
    )

    senaryo = ai.sor(sistem, istek, sicaklik=0.85, mock_cevap=MOCK_SENARYO)

    # --- yapisal dogrulama
    if not senaryo.get("sahneler"):
        raise ai.AIHatasi("Senaryoda sahne yok.")
    if not senaryo.get("baslik"):
        raise ai.AIHatasi("Senaryoda baslik yok.")

    sahne_sayisi = len(senaryo["sahneler"])
    if not (s_min - 2 <= sahne_sayisi <= s_max + 4):
        logger.uyari(
            f"Sahne sayisi beklenenin disinda: {sahne_sayisi} "
            f"(beklenen {s_min}-{s_max}). Yine de devam ediliyor."
        )

    # --- icerik guvenlik kontrolu
    bulunanlar = _yasakli_kontrol(senaryo)
    if bulunanlar:
        logger.uyari(f"Dikkat! Senaryoda riskli kelimeler var: {bulunanlar}")
        senaryo["_uyari"] = bulunanlar

    # --- sahneleri normalize et
    stil = config.GORSEL_STIL
    kompozisyon = profil.get("kompozisyon", "")
    karakter = (senaryo.get("karakter_sayfasi") or "").strip().rstrip(".,")

    temiz_sahneler = []
    ham_promptlar = []          # benzerlik kontrolu icin (karakter/stil eki haric)
    onceki_hareket = None

    for i, sahne in enumerate(senaryo["sahneler"], start=1):
        anlatim = _temizle(str(sahne.get("anlatim", "")))
        prompt = _prompt_temizle(str(sahne.get("gorsel_prompt", "")))

        if not anlatim or not prompt:
            logger.uyari(f"Sahne {i} eksik, atlaniyor.")
            continue

        # Karakter tarifi SADECE o sahnede karakter varsa eklenir.
        # Alan hic yoksa guvenli varsayim: ilk sahne haric karakter vardir.
        ham_promptlar.append((i, prompt))   # enjeksiyondan ONCEKI hali

        karakter_var = bool(sahne.get("karakter_sahnede", i > 1))
        # Iki poz: ayni sahne, farkli durus. Aralarinda gecis yapilarak
        # karakter hareket ediyormus gibi gorunecek.
        poz_1 = str(sahne.get("poz_1", "")).strip().rstrip(".,")
        poz_2 = str(sahne.get("poz_2", "")).strip().rstrip(".,")

        def tam_prompt(poz: str) -> str:
            p = prompt
            if karakter and karakter_var:
                bas = f"{karakter}, consistent character design"
                p = f"{bas}, {poz}, {p}" if poz else f"{bas}, {p}"
            if kompozisyon:
                p = f"{p}, {kompozisyon}"
            return f"{p}, {stil}"

        prompt_1 = tam_prompt(poz_1)
        prompt_2 = tam_prompt(poz_2) if (karakter_var and poz_2 and poz_1 != poz_2) else ""

        # Ayni kamera hareketi arka arkaya gelmesin
        secenekler = [h for h in HAREKETLER if h != onceki_hareket]
        hareket = random.choice(secenekler)
        onceki_hareket = hareket

        kayit = {
            "no": i,
            "anlatim": anlatim,
            "karakter_sahnede": karakter_var,
            "gorsel_prompt": prompt_1,
            "hareket": hareket,
        }
        if config.IKI_KARE and prompt_2:
            kayit["gorsel_prompt_2"] = prompt_2
        temiz_sahneler.append(kayit)

    senaryo["sahneler"] = temiz_sahneler
    senaryo["baslik"] = senaryo["baslik"].strip()[:95]

    # Etiketler
    etiketler = senaryo.get("etiketler") or fikir.get("anahtar_kelimeler", [])
    senaryo["etiketler"] = [str(e).strip() for e in etiketler][:15]

    # Meta bilgiler
    senaryo["video_tipi"] = video_tipi
    senaryo["genislik"] = profil["genislik"]
    senaryo["yukseklik"] = profil["yukseklik"]
    senaryo["fikir"] = fikir

    toplam_kelime = sum(len(s["anlatim"].split()) for s in temiz_sahneler)
    tahmini_sure = round(toplam_kelime / config.KELIME_HIZI)

    # Nesne sayisina dayali anlatim var mi?
    sayili = _sayi_kontrol(temiz_sahneler)
    if sayili:
        logger.uyari(
            f"Su sahnelerde sayi gecen ifade var: {sayili}. "
            "Gorsel dogru sayida nesne cizmeyebilir, kontrol et."
        )
        senaryo["_sayi_uyarisi"] = sayili

    # Renk ogreten sahnelerde goruntu notr mu?
    renk = _renk_kontrol(temiz_sahneler)
    if renk:
        logger.uyari(
            "Renk gecen ama goruntusu notr olmayan sahneler: " + ", ".join(renk)
            + ". Ekranda birden fazla renk cikabilir."
        )
        senaryo["_renk_uyarisi"] = renk

    # Ardisik sahneler birbirine cok mu benziyor?
    benzer = _benzerlik_kontrol(ham_promptlar)
    if benzer:
        logger.uyari("Benzer gorunecek ardisik sahneler: " + ", ".join(benzer))
        senaryo["_benzerlik_uyarisi"] = benzer

    senaryo["tahmini_sure_sn"] = tahmini_sure
    senaryo["toplam_kelime"] = toplam_kelime

    logger.ok(
        f"Senaryo hazir: {len(temiz_sahneler)} sahne, "
        f"{toplam_kelime} kelime, ~{tahmini_sure} sn"
    )
    return senaryo
