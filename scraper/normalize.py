import re

# canonical set name, release (yyyy-mm) for sorting, play-booster era?
SETS = [
    ('Nauctis: The Sunken Realm', '2027-02', ['nauctis']),
    ('Marvel: Darkhold Destiny', '2027-04', ['darkhold']),
    ('Star Trek', '2026-11', ['star trek']),
    ('Reality Fracture', '2026-10', ['reality fracture', 'zersplittert', 'réalité fracturée', 'realite fracturee']),
    ('The Hobbit', '2026-08', ['hobbit']),
    ('Marvel Super Heroes', '2026-06', ['marvel super heroes']),
    ('Secrets of Strixhaven', '2026-04', ['secrets of strixhaven', 'geheimnisse von strixhaven']),
    ('Teenage Mutant Ninja Turtles', '2026-03', ['ninja turtles']),
    ('Lorwyn Eclipsed', '2026-01', ['lorwyn eclipsed', 'lorwyns finsternis']),
    ('Avatar: The Last Airbender', '2025-11', ['avatar']),
    ("Marvel's Spider-Man", '2025-09', ['spider']),
    ('Edge of Eternities', '2025-08', ['edge of eternities', 'am rande der ewigkeiten']),
    ('Final Fantasy', '2025-06', ['final fantasy']),
    ('Tarkir: Dragonstorm', '2025-04', ['dragonstorm', 'drachensturm', 'tempête des dragons']),
    ('Aetherdrift', '2025-02', ['aetherdrift', 'ätherdrift']),
    ('Innistrad Remastered', '2025-01', ['innistrad remastered']),
    ('Foundations', '2024-11', ['foundations', 'grundstein']),
    ('Duskmourn: House of Horror', '2024-09', ['duskmourn']),
    ('Bloomburrow', '2024-08', ['bloomburrow']),
    ("Assassin's Creed", '2024-07', ["assassin"]),
    ('Modern Horizons 3', '2024-06', ['modern horizons 3', 'modern horizons iii']),
    ('Outlaws of Thunder Junction', '2024-04', ['thunder junction']),
    ('Fallout', '2024-03', ['fallout']),
    ('Murders at Karlov Manor', '2024-02', ['karlov']),
    # --- before here: Play-Booster era; below: Set/Draft era
    ('Ravnica Remastered', '2024-01', ['ravnica remastered']),
    ('The Lost Caverns of Ixalan', '2023-11', ['lost caverns', 'verlorenen höhlen', 'verlorenen hoehlen']),
    ('Doctor Who', '2023-10', ['doctor who']),
    ('Wilds of Eldraine', '2023-09', ['wilds of eldraine', 'wildnis von eldraine']),
    ('Commander Masters', '2023-08', ['commander masters']),
    ('The Lord of the Rings: Tales of Middle-earth', '2023-06', ['lord of the rings', 'herr der ringe']),
    ('March of the Machine: The Aftermath', '2023-05', ['aftermath', 'nachhall']),
    ('March of the Machine', '2023-04', ['march of the machine', 'marsch der maschine']),
    ('Phyrexia: All Will Be One', '2023-02', ['all will be one', 'alles wird eins']),
    ('Dominaria Remastered', '2023-01', ['dominaria remastered']),
    ("The Brothers' War", '2022-11', ['brothers', 'krieg der brüder', 'krieg der brueder']),
    ('Unfinity', '2022-10', ['unfinity']),
    ('Dominaria United', '2022-09', ['dominaria united', 'dominarias bund']),
    ('Double Masters 2022', '2022-07', ['double masters 2022']),
    ("Commander Legends: Battle for Baldur's Gate", '2022-06', ['baldur']),
    ('Streets of New Capenna', '2022-04', ['capenna']),
    ('Kamigawa: Neon Dynasty', '2022-02', ['neon']),
    ('Innistrad: Crimson Vow', '2021-11', ['crimson vow', 'blutroter bund']),
    ('Innistrad: Midnight Hunt', '2021-09', ['midnight hunt', 'mitternachtsjagd']),
    ('Adventures in the Forgotten Realms', '2021-07', ['forgotten realms']),
    ('Modern Horizons 2', '2021-06', ['modern horizons 2', 'moderne horizonte 2']),
    ('Strixhaven: School of Mages', '2021-04', ['strixhaven']),
    ('Kaldheim', '2021-02', ['kaldheim']),
    ('Commander Legends', '2020-11', ['commander legends']),
    ('Zendikar Rising', '2020-09', ['zendikar rising']),
    ('Core Set 2021', '2020-07', ['core set 2021', 'core 2021', 'hauptset 2021']),
    ('Ikoria: Lair of Behemoths', '2020-04', ['ikoria']),
    ('Theros Beyond Death', '2020-01', ['theros beyond death']),
    ('Throne of Eldraine', '2019-10', ['throne of eldraine', 'thron von eldraine']),
]
PLAY_ERA_START = '2024-02'  # Murders at Karlov Manor: ab hier Play-Booster statt Draft/Set
ORDER = {s[0]: s[1] for s in SETS}


def add_scryfall_sets(scry_sets):
    """Neue Sets automatisch aus Scryfall ergänzen (nur englische Namen)."""
    known = {k for _, _, keys in SETS for k in keys}
    for st in scry_sets:
        if st.get('set_type') not in ('expansion', 'core', 'masters', 'draft_innovation', 'funny'):
            continue
        if st.get('digital'):
            continue
        name = st['name']
        key = name.lower()
        if any(key in k or k in key for k in known):
            continue
        rel = (st.get('released_at') or '9999-99')[:7]
        SETS.insert(0, (name, rel, [key]))
        ORDER[name] = rel
        known.add(key)


EXCL = re.compile(r'draft|jumpstart|jumstart|beyond booster|epilog|scene box|commander[- ]?deck|special edition|\(4 decks\)|display - 4 stk|4 booster|bundle|binder|prerelease|theme deck|beginner', re.I)

GERMAN_HINT = re.compile(r'zersplittert|lorwyns finsternis|geheimnisse|der hobbit|ätherdrift|grundstein|am rande|drachensturm|mord in|haus des|marsch der|herr der elemente|sammler|outlaws von|wildnis|dominarias bund|strassen von|straßen von|krieg der|mitternachtsjagd|blutroter|abenteuer in|verlorenen höhlen|jenseits des', re.I)

def find_set(t):
    tl = t.lower()
    if 'baldur' in tl:
        return "Commander Legends: Battle for Baldur's Gate"
    if 'aftermath' in tl or 'nachhall' in tl:
        return 'March of the Machine: The Aftermath'
    keys = sorted(((k, name) for name, _, ks in SETS for k in ks), key=lambda x: -len(x[0]))
    for k, name in keys:
        if k in tl:
            return name
    return None


def find_type(t, setname):
    tl = t.lower()
    if re.search(r'collector|sammler', tl):
        return 'Collector'
    if re.search(r'set[- ]?booster|set display|set boosterbox|\| set \|', tl):
        return 'Set'
    if re.search(r'\bplay\b|play-?booster|booster de jeu|game booster|boosters de jeu', tl):
        return 'Play'
    # generic "Booster Display/Box" -> Play only in Play-Booster era
    if ORDER.get(setname, '0000') >= PLAY_ERA_START:
        return 'Play'
    return None


def find_lang(t, default):
    m = re.search(r'\{([^}]*)\}', t)
    cands = ([m.group(1)] if m else []) + [t]
    for s in cands:
        m2 = re.search(r'\((en|eng|de|deu|ger|fr|fra|jp|jap|jpn)\)', s, re.I)
        if m2:
            return {'en': 'EN', 'eng': 'EN', 'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'fr': 'FR', 'fra': 'FR'}.get(m2.group(1).lower(), 'JP')
        if re.search(r'japan', s, re.I) or re.search(r'\bJPN?\b|\bJAP\b|-J-', s): return 'JP'
        if re.search(r'franz|fran[cç]ais', s, re.I) or re.search(r'\bFR\b', s): return 'FR'
        if re.search(r'russisch', s, re.I) or re.search(r'\bRUS?\b|\bIT\b|\bES\b', s): return 'andere'
        if re.search(r'englisch|english|anglais', s, re.I) or re.search(r'\bEN\b|-E-|-EN-', s): return 'EN'
        if re.search(r'deutsch', s, re.I) or re.search(r'\bDE\b|-D-|-DE\b|-D\b|\bD\s*$', s): return 'DE'
    if GERMAN_HINT.search(t): return 'DE'
    return default or 'k.A.'


def parse_price(p):
    p = p.replace("'", '').replace('CHF', '').replace('From', '').replace('–', '00').strip()
    m = re.search(r'(\d+(?:\.\d+)?)', p)
    return float(m.group(1)) if m else None


def parse_avail(a):
    a = a.strip()
    if a in ('1', '0'):
        return a == '1'
    return bool(re.search(r'in stock|preorder|available|auf lager', a, re.I)) and not re.search(r'out of stock', a, re.I)




def normalize(shop, deflang, items):
    """items: Liste von (titel, preis, lieferbar). Gibt normalisierte Angebote zurück."""
    rows = []
    for title, price, avail in items:
        title = re.sub(r'\s+', ' ', str(title)).strip()
        if EXCL.search(title):
            continue
        st = find_set(title)
        if not st:
            continue
        ty = find_type(title, st)
        if not ty:
            continue
        pr = price if isinstance(price, (int, float)) else parse_price(str(price))
        if not pr or pr < 20:
            continue
        # Plausibilität: Einzelbooster, die fälschlich als Display gelistet sind, aussortieren
        if (ty == 'Collector' and pr < 120) or (ty in ('Play', 'Set') and pr < 50):
            continue
        lang = find_lang(title, deflang)
        if lang == 'andere':
            continue
        if not isinstance(avail, bool):
            avail = parse_avail(str(avail))
        rows.append(dict(shop=shop, title=title, set=st, type=ty, lang=lang,
                         price=round(float(pr), 2), avail=avail, release=ORDER[st]))
    return rows
