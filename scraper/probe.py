"""Einmaliger Test 2 (wird wieder entfernt)"""
import os, re, json, requests
from bs4 import BeautifulSoup
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'probe'); os.makedirs(out, exist_ok=True)
URLS = ['https://www.genkicorp.ch/de/', 'https://www.genkicorp.ch/de/suche?controller=search&s=magic+display',
  'https://molo13.ch/de', 'https://molo13.ch/de/search?q=magic+display', 'https://fatamorgana.ch/',
  'https://shop.spielkiste.ch', 'https://www.spielstatt.ch/', 'https://www.miracoolix.ch/', 'https://www.la-guilde.ch/']
res = []
for u in URLS:
    try:
        r = requests.get(u, headers=H, timeout=25)
        sp = BeautifulSoup(r.text, 'html.parser')
        links = sorted({(a.get('href') or '')[:120] for a in sp.find_all('a') if re.search(r'magic|mtg|display|shop|boutique', (a.get('href') or '') + a.get_text(), re.I)})[:40]
        gen = [m.get('content') for m in sp.find_all('meta', attrs={'name': 'generator'})]
        txt = re.sub(r'\s+', ' ', sp.get_text(' '))
        disp = re.findall(r'[^.]{0,80}(?:Display|Booster Box)[^.]{0,60}', txt)[:10]
        res.append({'u': u, 'st': r.status_code, 'final': r.url, 'gen': gen, 'links': links, 'disp': disp})
    except Exception as e:
        res.append({'u': u, 'err': str(e)[:100]})
open(os.path.join(out, 'result.json'), 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
