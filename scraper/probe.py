"""Einmaliger Test neuer Shops (wird danach wieder entfernt)."""
import os, re, requests
URLS = {
 'zw_json_search': 'https://www.zwergenschmiede.ch/search/booster-display/?format=json',
 'zw_json_search2': 'https://www.zwergenschmiede.ch/search/booster-display/page2.html?format=json',
 'zw_json_product': 'https://www.zwergenschmiede.ch/aetherdrift-play-booster-display-en.html?format=json',
 'zw_html_search': 'https://www.zwergenschmiede.ch/search/booster-display/',
}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', 'Accept-Language': 'de-CH,de;q=0.9'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'probe'); os.makedirs(out, exist_ok=True)
for k, u in URLS.items():
    try:
        r = requests.get(u, headers=H, timeout=40); t = r.text
        links = sorted(set(re.findall(r'href="([^"]*(?:magic|mtg|display|booster|search|suche)[^"]*)"', t, re.I)))[:120]
        snips = [t[:6000]]
        forms = re.findall(r'<form[^>]*>', t)[:6]
        open(os.path.join(out, k + '.txt'), 'w').write(
            f'URL {u}\nFINAL {r.url}\nSTATUS {r.status_code}\nLEN {len(t)}\nGEN {re.findall(r"generator\" content=\"([^\"]+)", t)[:3]}\n'
            f'MAGENTO {"mage/" in t or "Magento" in t} SHOPWARE {"shopware" in t.lower()} SHOPIFY {"cdn.shopify" in t} JTL {"jtl" in t.lower()}\nFORMS {forms}\n\nLINKS\n' + '\n'.join(links) + '\n\nSNIPPETS\n' + '\n-----\n'.join(snips))
    except Exception as e:
        open(os.path.join(out, k + '.txt'), 'w').write(f'URL {u}\nERROR {e}\n')
