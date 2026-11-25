"""Einmaliger Test: lädt Seiten neuer Shops und speichert Ausschnitte (wird danach wieder entfernt)."""
import os, re, requests
URLS = {
 'wartavern_search17': 'https://wartavern.ch/recherche?controller=search&s=magic+display',
 'wartavern_search16': 'https://wartavern.ch/search?controller=search&search_query=magic+display&n=100',
 'wartavern_home': 'https://wartavern.ch/',
 'brack_search': 'https://www.brack.ch/search?query=magic%20booster%20display',
 'buchmann_search': 'https://www.buchmann.ch/de/advanced_search_result.php?keywords=magic+booster+display',
 'buchmann_home': 'https://www.buchmann.ch/',
}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
     'Accept-Language': 'de-CH,de;q=0.9'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'probe')
os.makedirs(out, exist_ok=True)
for k, u in URLS.items():
    try:
        r = requests.get(u, headers=H, timeout=40)
        t = r.text
        links = sorted(set(re.findall(r'href="([^"]*(?:magic|mtg|display|booster|categor|search|recherche)[^"]*)"', t, re.I)))[:150]
        # Ausschnitte rund um "Display"
        snips = [t[max(0, m.start()-700):m.start()+500] for m in list(re.finditer(r'Play[- ]Booster[- ]Display|Collector[- ]Booster[- ]Display', t))[:3]]
        open(os.path.join(out, k + '.txt'), 'w').write(
            f'URL {u}\nFINAL {r.url}\nSTATUS {r.status_code}\nLEN {len(t)}\nGEN {re.findall(r"generator\" content=\"([^\"]+)", t)[:3]}\n'
            f'NEXT {"__NEXT_DATA__" in t} JSONLD {t.count("application/ld+json")} PRESTA {"prestashop" in t.lower()}\n\nLINKS\n' + '\n'.join(links) +
            '\n\nSNIPPETS\n' + '\n-----\n'.join(snips))
    except Exception as e:
        open(os.path.join(out, k + '.txt'), 'w').write(f'URL {u}\nERROR {e}\n')
