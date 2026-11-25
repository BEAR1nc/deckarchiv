"""Einmaliger Test neuer Shops (wird danach wieder entfernt)."""
import os, re, requests
URLS = {
 'zw_product': 'https://www.zwergenschmiede.ch/aetherdrift-play-booster-display-en.html',
 'zw_home': 'https://www.zwergenschmiede.ch/',
 'zw_products_json': 'https://www.zwergenschmiede.ch/products.json?limit=1',
 'zw_search_magento': 'https://www.zwergenschmiede.ch/catalogsearch/result/?q=play+booster+display',
 'zw_search_sw': 'https://www.zwergenschmiede.ch/search?search=play+booster+display',
}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', 'Accept-Language': 'de-CH,de;q=0.9'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'probe'); os.makedirs(out, exist_ok=True)
for k, u in URLS.items():
    try:
        r = requests.get(u, headers=H, timeout=40); t = r.text
        links = sorted(set(re.findall(r'href="([^"]*(?:magic|mtg|display|booster|search|suche)[^"]*)"', t, re.I)))[:120]
        snips = [t[max(0, m.start()-900):m.start()+900] for m in list(re.finditer(r'Booster Display', t))[:3]]
        forms = re.findall(r'<form[^>]*>', t)[:6]
        open(os.path.join(out, k + '.txt'), 'w').write(
            f'URL {u}\nFINAL {r.url}\nSTATUS {r.status_code}\nLEN {len(t)}\nGEN {re.findall(r"generator\" content=\"([^\"]+)", t)[:3]}\n'
            f'MAGENTO {"mage/" in t or "Magento" in t} SHOPWARE {"shopware" in t.lower()} SHOPIFY {"cdn.shopify" in t} JTL {"jtl" in t.lower()}\nFORMS {forms}\n\nLINKS\n' + '\n'.join(links) + '\n\nSNIPPETS\n' + '\n-----\n'.join(snips))
    except Exception as e:
        open(os.path.join(out, k + '.txt'), 'w').write(f'URL {u}\nERROR {e}\n')
