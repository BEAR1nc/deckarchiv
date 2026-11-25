"""Liest die MTG-Display-Preise der Schweizer Händler aus und schreibt
shopping/data/offers.json, shopping/data/status.json und die Excel-Datei.

Läuft täglich per GitHub Action (.github/workflows/shopping.yml).
Schlägt ein Shop fehl, bleiben seine letzten Preise stehen (mit altem Datum).
"""
import datetime as dt
import html
import json
import os
import re
import sys
import time
import traceback
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(__file__))
import normalize as N  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'shopping', 'data')
TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).strftime('%Y-%m-%d')

S = requests.Session()
S.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
    'Accept-Language': 'de-CH,de;q=0.9,en;q=0.8',
})
EXCL_JS = re.compile(r'draft|jumpstart|beyond|epilog|commander[- ]?deck|bundle|prerelease|case|karton|faltbox|deck ?box|sleeve|hülle|leer|empty|starter|collection|gift|scene box|single booster|einzel|foil|near mint|played|acryl|unsanctioned', re.I)


LAST = {}


def get(url, **kw):
    for i in range(3):
        try:
            r = S.get(url, timeout=40, **kw)
            if r.status_code in (429, 503):
                time.sleep(5 * (i + 1))
                continue
            LAST.update(status=r.status_code, size=len(r.content), url=r.url[:120],
                        title=(re.search(r'<title>(.*?)</title>', r.text[:20000], re.S | re.I) or [None, ''])[1].strip()[:80])
            return r
        except requests.RequestException:
            if i == 2:
                raise
            time.sleep(3)
    return r


def soup(url, **kw):
    r = get(url, **kw)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def is_display(t):
    return re.search(r'display|booster ?-?box', t, re.I) and not EXCL_JS.search(t)


# ---------------------------------------------------------------- Plattformen
def shopify(base):
    items = []
    for p in range(1, 41):
        r = get(f'{base}/products.json?limit=250&page={p}')
        r.raise_for_status()
        prods = r.json().get('products', [])
        if not prods:
            break
        for pr in prods:
            t = pr['title']
            meta = ' '.join([t, pr.get('product_type', ''), ' '.join(pr.get('tags', []) or []), pr.get('vendor', '')]).lower()
            if not re.search(r'magic|mtg|wizards', meta) or not is_display(t):
                continue
            vs = pr['variants']
            for v in vs:
                name = t + (f" {{{v['title']}}}" if len(vs) > 1 else '')
                items.append((name, v['price'], bool(v.get('available'))))
    return items


def woocommerce(base, query='display'):
    items = []
    for p in range(1, 11):
        r = get(f'{base}/wp-json/wc/store/v1/products', params={'search': query, 'per_page': 100, 'page': p,
                                                                 '_fields': 'name,prices,is_in_stock,categories'})
        r.raise_for_status()
        j = r.json()
        if not j:
            break
        for d in j:
            t = html.unescape(d['name'])
            cats = ' '.join(c.get('name', '') for c in d.get('categories', []))
            if not re.search(r'magic|mtg', t + ' ' + cats, re.I) or not is_display(t):
                continue
            pr = int(d['prices']['price']) / 10 ** d['prices']['currency_minor_unit']
            items.append((t, pr, bool(d.get('is_in_stock'))))
        if len(j) < 100:
            break
    return items


def molo13():
    """Molo 13 (Pregassona/Lugano), ePages-REST-API."""
    items = []
    for q in ('display', 'booster box'):
        for page in range(1, 11):
            r = get('https://molo13.ch/rs/shops/180252/products', params={'q': q, 'resultsPerPage': 100, 'page': page},
                    headers={'Accept': 'application/vnd.epages.v1+json'})
            r.raise_for_status()
            j = r.json()
            for d in j.get('items', []):
                t = re.sub(r'^\d{2}\.\d{2}\.\d{4}\s*', '', d.get('name') or '').strip()
                if not re.search(r'magic|mtg', t, re.I) or not is_display(t):
                    continue
                pr = ((d.get('priceInfo') or {}).get('price') or {}).get('amount')
                if pr is None:
                    continue
                items.append((t, float(pr), d.get('availability') in ('OnStock', 'WarnStock') and d.get('forSale') is not False))
            if page * 100 >= j.get('results', 0):
                break
    return items


# ------------------------------------------------------------------- einzelne
def carab():
    items = []
    for p in range(1, 61):
        r = get('https://www.carab.ch/shop/api/products', params={'page': p, 'limit': 100, 'sort': 'creationDate-desc', 'q': 'display'})
        r.raise_for_status()
        data = r.json().get('data') or []
        if not data:
            break
        for d in data:
            if not re.search('magic', (d.get('parent') or '') + d['name'], re.I) or not is_display(d['name']):
                continue
            items.append((f"{d['name']} {{{d.get('variantname')}}}", d.get('discountPrice') or d['price'], (d.get('stock') or 0) > 0))
    return items


def goodgames():
    sp = soup('https://www.goodgamesbern.ch/', params={'dispatch': 'products.search', 'match': 'all', 'subcats': 'Y', 'pname': 'Y',
                                                      'search_performed': 'Y', 'q': 'magic display', 'items_per_page': 192})
    items = []
    for it in sp.select('.ty-grid-list__item, .ut2-gl__item'):
        a = it.select_one('a.product-title, .product-title')
        p = it.select_one('.ty-price-num')
        if not a or not p:
            continue
        txt = it.get_text(' ', strip=True)
        items.append((a.get_text(strip=True), p.get_text(strip=True), not re.search(r'nicht auf lager|ausverkauft', txt, re.I)))
    return items


def kabooom():
    items = []
    for p in range(0, 10):
        sp = soup('https://shop.kabooom.ch/store/search.asp', params={'keyword': 'magic display', 'page': p})
        for s in sp(['script', 'style']):
            s.decompose()
        lines = [re.sub(r'\s+', ' ', x).strip() for x in sp.get_text('\n').split('\n')]
        lines = [x for x in lines if x]
        n = 0
        for i, ln in enumerate(lines):
            if re.match(r'^Magic .*Display', ln, re.I):
                nxt = lines[i + 1:i + 4]
                prices = re.findall(r'CHF\s?([\d,.]+)', ' '.join(nxt[:2]))
                if not prices:
                    continue
                price = prices[-1].replace(',', '')
                av = not any('out of stock' in x.lower() for x in nxt)
                items.append((ln, price, av))
                n += 1
        m = re.search(r'products (\d+) to (\d+)', ' '.join(lines))
        tot = re.search(r'(\d+) products were found', ' '.join(lines))
        if not m or not tot or int(m.group(2)) >= int(tot.group(1)):
            break
    return items


def magictrade():
    items = []
    for p in range(1, 15):
        sp = soup('https://magictrade.ch/shop/de/displays', params={'next_page': p} if p > 1 else None)
        boxes = sp.select('div.section.panel')
        found = 0
        for b in boxes:
            t = b.select_one('.title .h4') or b.select_one('.title p') or b.select_one('.title')
            pr = b.select_one('.product-price')
            st = b.select_one('.product-stock')
            if not t or not pr:
                continue
            name = t.get_text(' ', strip=True)
            if not is_display(name):
                continue
            stock = re.search(r'Lagerbestand\s*(\d+)', st.get_text(' ', strip=True) if st else '')
            items.append((name, pr.get_text(strip=True), bool(stock and int(stock.group(1)) > 0)))
            found += 1
        if not found:
            break
    return items


def pokeboka():
    r = get('https://pokeboka.ch/api/public/shop-products')
    r.raise_for_status()
    items = []
    for p in r.json().get('products', []):
        t = p.get('title', '')
        if not re.search(r'magic|mtg', t + ' ' + str(p.get('vendor')) + str(p.get('game')), re.I) or not is_display(t):
            continue
        if re.search(r'\((IT|ES|PT)\)', t):
            continue
        items.append((t.replace(' | ', ' - '), p.get('price'), bool(p.get('available')) and not p.get('outOfStock')))
    return items


def softridge():
    items = []
    for p in range(1, 15):
        r = get('https://www.softridge.ch/api/shop/products', params={
            'loadingType': 79, 'languageId': 2, 'navigationId': 25982, 'filterByAllCategories': 'True', 'onlineExclusive': '',
            'displayType': 1, 'searchTerms': 'mtg display', 'sort': 6, 'filter': 'null', 'page': p})
        r.raise_for_status()
        j = r.json()
        for d in j.get('products', []):
            t = d.get('fullTitle', '')
            if not is_display(t):
                continue
            items.append((t, d.get('salesPrice'), d.get('cartLinkType') == 0))
        if not j.get('hasMore'):
            break
    return items


def uncommon():
    links = {}
    for p in range(1, 9):
        url = 'https://theuncommonshop.ch/' + (f'page/{p}/' if p > 1 else '')
        sp = soup(url, params={'s': 'magic display', 'post_type': 'product'})
        n0 = len(links)
        for a in sp.find_all('a', href=True):
            t = a.get_text(' ', strip=True)
            if re.match(r'^Magic\s*[–-].*Display', t, re.I) and is_display(t) and re.search(r'/produkt|/product', a['href']):
                links[a['href'].split('?')[0]] = t
        if len(links) == n0 and p > 2:
            break
    items = []
    for u, t in links.items():
        sp = soup(u)
        f = sp.select_one('form.variations_form')
        if f and f.get('data-product_variations') not in (None, 'false'):
            for v in json.loads(html.unescape(f['data-product_variations'])):
                lang = ','.join(str(x) for x in v.get('attributes', {}).values())
                items.append((f'{t} {{{lang}}}', v.get('display_price'), bool(v.get('is_in_stock'))))
        else:
            pr = sp.select_one('.summary .price')
            prod = sp.select_one('div.product')
            oos = prod is not None and 'outofstock' in ' '.join(prod.get('class', []))
            if pr:
                prices = re.findall(r'[\d\']+\.\d{2}', pr.get_text(' ', strip=True))
                if prices:
                    items.append((t, prices[-1].replace("'", ''), not oos))
        time.sleep(0.3)
    return items


def twomoons():
    items = {}
    for q in ['play booster', 'collector booster', 'sammler', 'set booster', 'magic display']:
        for p in range(1, 6):
            sp = soup('https://www.twomoons.ch/search', params={'search': q, 'p': p})
            boxes = sp.select('.product-box')
            if not boxes:
                break
            for b in boxes:
                txt = b.get_text(' ', strip=True)
                if not re.search('magic', txt, re.I) or not re.search(r'booster box|display', txt, re.I):
                    continue
                if re.search(r'beginner|deck box|jumpstart|jumstart', txt, re.I):
                    continue
                nm = b.select_one('.product-name')
                props = re.sub(r'\s+', ' ', ' '.join(str(x) for x in b.find_all(string=re.compile(r'\|'))))
                m = re.search(r'Booster Box ?\| ?(Play|Collector|Set) ?\| ?(\w+)', props)
                if not nm or not m:
                    continue
                prices = re.findall(r'CHF\s?([\d\'.]+)', txt)
                if not prices:
                    continue
                lang = {'Englisch': 'EN', 'Deutsch': 'DE', 'Japanisch': 'JP', 'Französisch': 'FR'}.get(m.group(2), m.group(2))
                name = f"{nm.get_text(' ', strip=True)} {m.group(1)} Booster Display ({lang})"
                items[name] = (name, prices[0].replace("'", ''), not re.search(r'nicht mehr verf|ausverkauft', txt, re.I))
    return list(items.values())


def manashop():
    items = []
    for p in range(1, 8):
        sp = soup('https://themanashop.ch/en/25-booster-boxes-display', params={'n': 100, 'p': p})
        blocks = sp.select('.ajax_block_product')
        if not blocks:
            break
        new = 0
        for b in blocks:
            a = b.select_one('a.product-name') or b.select_one('a[title]')
            pr = b.select_one('.content_price .price') or b.select_one('.price')
            av = b.select_one('.availability')
            if not a or not pr:
                continue
            name = (a.get('title') or a.get_text(strip=True)).strip()
            if not is_display(name + ' display'):
                continue
            avt = av.get_text(' ', strip=True) if av else ''
            items.append((name, pr.get_text(strip=True), not re.search('out of stock', avt, re.I)))
            new += 1
        if not new:
            break
    return items


def wog():
    sp = soup('https://www.wog.ch/de/index.cfm/search/searchTerm/' + quote('magic the gathering display') + '/orderBy/relevance')
    items = {}
    for tile in sp.select('.product-tile'):
        a = tile.select_one('a[href*="/product/"]')
        if not a:
            continue
        slug = a['href'].rstrip('/').split('/')[-1]
        slug = requests.utils.unquote(slug)
        name = slug.split('-', 1)[1].replace('-', ' ') if '-' in slug else slug
        txt = tile.get_text(' | ', strip=True)
        m = re.search(r"CHF\s?([\d'.]+)", txt)
        if not m or not name.lower().startswith('magic') or not is_display(name):
            continue
        last = txt.split('|')[-1].strip()
        av = (bool(re.fullmatch(r'\d+\+?', last)) or 'Release' in txt) and 'nicht mehr lieferbar' not in txt
        items[name] = (name, m.group(1).replace("'", ''), av)
    return list(items.values())


def galaxus():
    sp = soup('https://www.galaxus.ch/de/search', params={'q': 'magic the gathering display'})
    items = []
    for art in sp.select('article'):
        txt = art.get_text(' | ', strip=True)
        if not re.search(r'magic', txt, re.I) or not re.search(r'display|booster box', txt, re.I):
            continue
        m = re.search(r"CHF \| ([\d'.–]+)", txt)
        if not m:
            continue
        name = max(txt.split(' | '), key=len)
        items.append((name, m.group(1).replace("'", '').replace('.–', ''), True))
    if not items:
        raise RuntimeError('keine Treffer (Seite vermutlich blockiert)')
    return items


def zwergenschmiede():
    """Lightspeed-Shop: Marken-Seite als JSON, danach jede Display-Produktseite als JSON."""
    base = 'https://www.zwergenschmiede.ch/'
    urls = {}
    for p in range(1, 15):
        page = 'brands/magic-the-gathering/' + (f'page{p}.html' if p > 1 else '')
        r = get(base + page, params={'format': 'json', 'limit': 100})
        r.raise_for_status()
        col = r.json().get('collection', {})
        prods = col.get('products') or {}
        if isinstance(prods, dict):
            prods = list(prods.values())
        for pr in prods:
            t = pr.get('fulltitle') or pr.get('title') or ''
            if is_display(t):
                urls[pr.get('url')] = t
        if not col.get('page_next') or p >= (col.get('pages') or 1):
            break
    items = []
    for u in urls:
        if not u:
            continue
        r = get(base + u.lstrip('/'), params={'format': 'json'})
        r.raise_for_status()
        pr = r.json().get('product', {})
        t = pr.get('fulltitle') or pr.get('title') or ''
        price = (pr.get('price') or {}).get('price_incl')
        stock = pr.get('stock') or {}
        items.append((t, price, bool(stock.get('available'))))
        time.sleep(0.3)
    return items


def drachehoehli():
    """Preisliste auf der Website (kein Warenkorb): Lieferbarkeit nicht angegeben."""
    sp = soup('https://xn--drachehhli-kcb.ch/drachehoehli/63-2/magic/')
    for s in sp(['script', 'style', 'nav', 'header', 'footer']):
        s.decompose()
    lines = [re.sub(r'\s+', ' ', x).strip() for x in sp.get_text('\n').split('\n')]
    lines = [x for x in lines if x]
    items = []
    for i, ln in enumerate(lines):
        if not re.match(r'magic', ln, re.I) or not is_display(ln) or 'CHF' in ln:
            continue
        for nxt in lines[i + 1:i + 4]:
            m = re.search(r'CHF\s?([\d\'.]+)', nxt)
            if m:
                items.append((ln, m.group(1).replace("'", '').rstrip('.'), True))
                break
    return items


# --------------------------------------------------------------- Händlerliste
SHOPS = [
    # (Name, Link, Standardsprache, Funktion)
    ('Cards & Dice', 'https://cardsdice.ch', None, lambda: shopify('https://cardsdice.ch')),
    ('Cardmaniac', 'https://cardmaniac.ch', 'EN', lambda: shopify('https://cardmaniac.ch')),
    ('CARAB', 'https://www.carab.ch', None, carab),
    ('GameGalaxy', 'https://gamegalaxy.ch', None, lambda: shopify('https://gamegalaxy.ch')),
    ('GoodGames Bern', 'https://www.goodgamesbern.ch', None, goodgames),
    ('Hall of Trader', 'https://halloftrader.ch', None, lambda: shopify('https://halloftrader.ch')),
    ('Kabooom', 'https://shop.kabooom.ch', None, kabooom),
    ('MaRo Games', 'https://www.maro-shop.ch', None, lambda: shopify('https://www.maro-shop.ch')),
    ('Magic-Bros', 'https://www.magic-bros.ch', 'DE', None),
    ('Magictrade', 'https://magictrade.ch/shop/de/displays', None, magictrade),
    ('Mr. Packhouse', 'https://www.mrpackhouse.ch', None, lambda: shopify('https://www.mrpackhouse.ch')),
    ("Nook's", 'https://www.nooks.ch', None, lambda: woocommerce('https://www.nooks.ch')),
    ('Pikaversum', 'https://pikaversum.ch', None, lambda: shopify('https://pikaversum.ch')),
    ('POKEBOKA', 'https://pokeboka.ch/shop', None, pokeboka),
    ('Softridge', 'https://www.softridge.ch/de/tcg/magic-the-gathering', None, softridge),
    ('CardCollectors', 'https://cardcollectors.ch', None, lambda: woocommerce('https://cardcollectors.ch')),
    ('The Uncommon Shop', 'https://theuncommonshop.ch', None, uncommon),
    ('Toki', 'https://toki.ch', 'DE', lambda: shopify('https://toki.ch')),
    ('Trading Card Cave', 'https://www.tradingcardcave.ch', None, lambda: shopify('https://www.tradingcardcave.ch')),
    ('TwoMoons', 'https://www.twomoons.ch', None, twomoons),
    ('edujeu', 'https://edujeu.ch', None, lambda: woocommerce('https://edujeu.ch')),
    ('Galaxus', 'https://www.galaxus.ch', None, galaxus),
    ('Sky Spell', 'https://skyspell.ch/collections/magic-the-gathering', None, lambda: shopify('https://sky-spell.myshopify.com')),
    ('The Mana Shop', 'https://themanashop.ch/en/25-booster-boxes-display', 'EN', manashop),
    ('World of Games', 'https://www.wog.ch', None, wog),
    ('Zadoys', 'https://zadoys.ch', None, lambda: shopify('https://zadoys.ch')),
    ('Drachehöhli', 'https://xn--drachehhli-kcb.ch/drachehoehli/63-2/magic/', None, drachehoehli),
    ('Le Maître de Jeux', 'https://shop.lemaitredejeux.ch', None, lambda: woocommerce('https://shop.lemaitredejeux.ch')),
    ('Molo 13', 'https://molo13.ch/de/c/magic-the-gathering', None, molo13),
    ('Zwergenschmiede', 'https://www.zwergenschmiede.ch/brands/magic-the-gathering/', None, zwergenschmiede),
]


def main():
    only = set(sys.argv[1:])
    try:
        r = get('https://api.scryfall.com/sets', headers={'Accept': 'application/json'})
        N.add_scryfall_sets(r.json().get('data', []))
    except Exception as e:  # nicht kritisch
        print('Scryfall-Sets nicht geladen:', e)

    offers_path = os.path.join(DATA, 'offers.json')
    status_path = os.path.join(DATA, 'status.json')
    offers = json.load(open(offers_path, encoding='utf-8')) if os.path.exists(offers_path) else []
    status = json.load(open(status_path, encoding='utf-8')) if os.path.exists(status_path) else {}

    for name, link, deflang, fn in SHOPS:
        if only and name not in only:
            continue
        st = status.get(name, {})
        st['link'] = link
        if fn is None:
            st.update(ok=None, note='nicht automatisch (letzter Stand bleibt)')
            status[name] = st
            continue
        t0 = time.time()
        try:
            LAST.clear()
            raw = list(dict.fromkeys(fn()))  # Duplikate entfernen
            rows = N.normalize(name, deflang, raw)
            if raw and not rows:
                raise RuntimeError(f'{len(raw)} Produkte gefunden, aber keine erkannt')
            if not raw:
                raise RuntimeError(f'keine Produkte gefunden (letzte Antwort: {LAST})')
            for x in rows:
                x['stand'] = TODAY
            offers = [o for o in offers if o['shop'] != name] + rows
            st.update(ok=True, last_ok=TODAY, count=len(rows), error=None, note=None)
            print(f'OK   {name}: {len(raw)} roh -> {len(rows)} ({time.time() - t0:.0f}s)')
        except Exception as e:
            msg = f'{type(e).__name__}: {e}'
            if '403' in msg:
                msg = 'Shop blockiert automatische Abfragen (HTTP 403) – letzter bekannter Stand bleibt'
            st.update(ok=False, last_try=TODAY, error=msg[:300])
            print(f'FAIL {name}: {e}')
            traceback.print_exc(limit=1)
        status[name] = st

    offers.sort(key=lambda o: (o['shop'], o['set'], o['type'], o['lang'], o['price']))
    json.dump(offers, open(offers_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    meta = {'updated': dt.datetime.now(dt.timezone.utc).isoformat(timespec='minutes'),
            'shops': [{'name': n, 'link': l} for n, l, _, _ in SHOPS]}
    status['_meta'] = meta
    json.dump(status, open(status_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    import excel
    excel.build(offers, status, os.path.join(ROOT, 'shopping', 'MTG_Display_Preisvergleich_EN.xlsx'))


if __name__ == '__main__':
    main()
