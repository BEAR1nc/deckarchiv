"""Einmaliger Test: welche Shops sind erreichbar, welche Plattform, gibt es MTG-Displays? (wird wieder entfernt)"""
import os, re, json, requests
DOMAINS = ['genkicorp.ch','la-guilde.ch','spielstatt.ch','miracoolix.ch','drachenaescht.ch','xenomorph.ch','lespecialiste.ch',
  'sognidicarta.ch','atoidejouer.ch','molo13.ch','lemaitredejeux.ch','spielkiste.ch','tulispiele.ch','tuli.ch','spikus.ch',
  'wild-cards.ch','wildcards.ch','garagentroll.ch','drachechaeller.ch','graffiti-spiel.ch','stauffacher.ch','spiel-laeselade.ch',
  'stocker-stadel.ch','kaufparadies.ch','aupardisdujeu.ch','auparadisdujeu.ch','spielwerk.ch','spieleladen.ch','wartavern.ch','mediamarkt.ch']
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', 'Accept-Language': 'de-CH,de;q=0.9,fr;q=0.8'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'probe'); os.makedirs(out, exist_ok=True)
res = []
def g(u):
    return requests.get(u, headers=H, timeout=25, allow_redirects=True)
for d in DOMAINS:
    info = {'domain': d}
    try:
        r = g(f'https://www.{d}/') if not d.startswith('www') else g(f'https://{d}/')
        t = r.text; info.update(status=r.status_code, final=r.url, title=(re.search(r'<title>(.*?)</title>', t, re.S|re.I) or [0,''])[1].strip()[:80])
        low = t.lower()
        info['plat'] = [k for k in ['cdn.shopify','woocommerce','prestashop','webshopapp','shopware','wix','jimdo','magento','squarespace','odoo','ecwid'] if k in low]
        info['mtg'] = low.count('magic')
        base = r.url.split('/')[0] + '//' + r.url.split('/')[2]
        try:
            p = g(base + '/products.json?limit=250'); 
            if p.ok and p.text.strip().startswith('{'):
                prods = p.json().get('products', []); info['shopify_n'] = len(prods)
                info['shopify_disp'] = [x['title'] for x in prods if re.search('magic|mtg', x['title']+x.get('vendor',''), re.I) and re.search('display|booster ?box', x['title'], re.I)][:5]
        except Exception as e: info['shopify_err'] = str(e)[:60]
        try:
            w = g(base + '/wp-json/wc/store/v1/products?search=display&per_page=50')
            if w.ok and w.text.strip().startswith('['):
                j = w.json(); info['wc_n'] = len(j); info['wc_disp'] = [x['name'] for x in j if re.search('magic|mtg', x['name'], re.I)][:5]
        except Exception as e: info['wc_err'] = str(e)[:60]
    except Exception as e:
        info['error'] = str(e)[:100]
    res.append(info)
open(os.path.join(out, 'result.json'), 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
