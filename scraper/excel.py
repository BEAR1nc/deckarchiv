"""Excel-Preisvergleich (nur englische Displays) aus offers.json erzeugen."""
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TYPE_ORDER = {'Play': 0, 'Set': 1, 'Collector': 2}
ARIAL = 'Arial'
F = Font(name=ARIAL, size=10)
FB = Font(name=ARIAL, size=10, bold=True)
FH = Font(name=ARIAL, size=10, bold=True, color='FFFFFF')
FHL = Font(name=ARIAL, size=10, bold=True, color='FFFFFF', underline='single')
FGREY = Font(name=ARIAL, size=10, italic=True, color='999999')
HFILL = PatternFill('solid', fgColor='1F3864')
SIDE = PatternFill('solid', fgColor='EEF2F8')
GREEN = PatternFill('solid', fgColor='C6EFCE')
BORDER = Border(bottom=Side(style='thin', color='D9D9D9'))
NUM = '#,##0.00'


def _sortkey(c):
    return (-int(c[1].replace('-', '')[:6] or 0), c[0], TYPE_ORDER[c[2]])


def _matrix(ws, data, shops, links, include_soldout):
    hdr = ['Edition', 'Display'] + shops + ['Günstigster Preis (CHF)', 'Günstigster Shop', 'Display', 'Edition']
    ws.append(hdr)
    for i in range(1, len(hdr) + 1):
        c = ws.cell(row=1, column=i)
        c.font = FH
        c.fill = HFILL
        c.alignment = Alignment(wrap_text=True, vertical='center', horizontal='left' if i <= 2 else 'center')
    for j, s in enumerate(shops):
        c = ws.cell(row=1, column=3 + j)
        if links.get(s):
            c.hyperlink = links[s]
            c.font = FHL
    ws.row_dimensions[1].height = 48
    first, last = 3, 2 + len(shops)
    fL, lL = get_column_letter(first), get_column_letter(last)
    cmin, cshop, cdisp, ced = last + 1, last + 2, last + 3, last + 4
    mL = get_column_letter(cmin)
    combos = sorted(data, key=_sortkey)
    for r, c in enumerate(combos, start=2):
        setname, rel, ty = c
        ws.cell(row=r, column=1, value=setname).font = FB
        ws.cell(row=r, column=2, value=f'{ty} Booster Display').font = F
        for j, s in enumerate(shops):
            v = data[c].get(s)
            if v is None:
                continue
            cell = ws.cell(row=r, column=first + j, value=v[0])
            cell.font = F
            if include_soldout and not v[1]:
                cell.font = FGREY
                cell.comment = Comment('ausverkauft / nicht lieferbar', 'Preisvergleich')
        ws.cell(row=r, column=cmin, value=f'=IF(COUNT({fL}{r}:{lL}{r})=0,"",MIN({fL}{r}:{lL}{r}))').font = FB
        ws.cell(row=r, column=cshop, value=f'=IF({mL}{r}="","",INDEX(${fL}$1:${lL}$1,MATCH({mL}{r},{fL}{r}:{lL}{r},0)))').font = FB
        ws.cell(row=r, column=cdisp, value=f'=B{r}').font = F
        ws.cell(row=r, column=ced, value=f'=A{r}').font = F
        for col in range(1, ced + 1):
            cell = ws.cell(row=r, column=col)
            cell.border = BORDER
            if first <= col <= cmin:
                cell.number_format = NUM
            if col <= 2 or col >= cmin:
                cell.fill = SIDE
    n = len(combos) + 1
    if n > 1:
        ws.conditional_formatting.add(f'{fL}2:{lL}{n}', FormulaRule(
            formula=[f'AND({fL}2<>"",{fL}2=${mL}2)'], fill=GREEN, font=Font(name=ARIAL, bold=True, color='006100')))
    widths = [34, 24] + [11] * len(shops) + [13, 20, 24, 34]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:{get_column_letter(ced)}{max(n, 2)}'
    ws.sheet_view.zoomScale = 90


def build(offers, status, path):
    meta = status.get('_meta', {})
    order = [s['name'] for s in meta.get('shops', [])]
    links = {s['name']: s['link'] for s in meta.get('shops', [])}
    en = [o for o in offers if o['lang'] == 'EN']

    av, alld = defaultdict(dict), defaultdict(dict)
    for o in en:
        c = (o['set'], o['release'], o['type'])
        s = o['shop']
        if o['avail'] and (s not in av[c] or o['price'] < av[c][s][0]):
            av[c][s] = (o['price'], True)
        cur = alld[c].get(s)
        cand = (o['price'], o['avail'])
        if cur is None or (cand[1] and not cur[1]) or (cand[1] == cur[1] and cand[0] < cur[0]):
            alld[c][s] = cand

    def shops_of(d):
        used = {s for c in d for s in d[c]}
        return [s for s in order if s in used] + sorted(used - set(order))

    wb = Workbook()
    ws = wb.active
    ws.title = 'Vergleich (lieferbar)'
    _matrix(ws, av, shops_of(av), links, False)
    ws2 = wb.create_sheet('Vergleich (alle)')
    _matrix(ws2, alld, shops_of(alld), links, True)

    ws3 = wb.create_sheet('Alle Angebote')
    hdr = ['Händler', 'Edition', 'Display', 'Preis (CHF)', 'Lieferbar', 'Stand', 'Produkttitel beim Händler']
    ws3.append(hdr)
    for i in range(1, len(hdr) + 1):
        ws3.cell(row=1, column=i).font = FH
        ws3.cell(row=1, column=i).fill = HFILL
    for o in sorted(en, key=lambda o: (o['shop'], _sortkey((o['set'], o['release'], o['type'])))):
        ws3.append([o['shop'], o['set'], o['type'] + ' Booster Display', o['price'], 'ja' if o['avail'] else 'nein', o.get('stand', ''), o['title']])
        rr = ws3.max_row
        for c in ws3[rr]:
            c.font = F if o['avail'] else FGREY
        ws3.cell(row=rr, column=4).number_format = NUM
    for i, w in enumerate([22, 38, 24, 11, 9, 11, 80], 1):
        ws3.column_dimensions[get_column_letter(i)].width = w
    ws3.freeze_panes = 'A2'
    ws3.auto_filter.ref = f'A1:G{max(ws3.max_row, 2)}'

    ws4 = wb.create_sheet('Händler & Stand')
    hdr = ['Händler', 'Shop', 'Letzte erfolgreiche Abfrage', 'Status', 'EN-Angebote', 'Hinweis']
    ws4.append(hdr)
    for i in range(1, len(hdr) + 1):
        ws4.cell(row=1, column=i).font = FH
        ws4.cell(row=1, column=i).fill = HFILL
    for s in order:
        st = status.get(s, {})
        state = {True: 'OK', False: 'Fehler', None: 'manuell'}.get(st.get('ok'), '–')
        ws4.append([s, links.get(s, ''), st.get('last_ok', '2026-11-21'), state,
                    f"=COUNTIF('Alle Angebote'!$A:$A,\"{s}\")", st.get('error') or st.get('note') or ''])
        rr = ws4.max_row
        for c in ws4[rr]:
            c.font = F
        if links.get(s):
            ws4.cell(row=rr, column=2).hyperlink = links[s]
    r0 = ws4.max_row + 2
    notes = [
        f"Aktualisiert: {meta.get('updated', '')} (UTC). Preise in CHF inkl. MwSt., ohne Versand. Nur englische Displays.",
        'Grün = günstigster Preis der Zeile. Rechts stehen günstigster Preis, Shop, Display und Edition zusammen.',
        'Fehlt eine Abfrage, bleiben die letzten bekannten Preise des Shops stehen (Spalte «Stand» im Blatt «Alle Angebote»).',
        'The Mana Shop zeigt oft «ab»-Preise; dieser kann für eine andere Sprachversion gelten.',
        'Spieltreff Tonazzi (magickarten.ch) leitet auf CardCollectors weiter. ManaBase ist nicht erreichbar.',
    ]
    ws4.cell(row=r0, column=1, value='Hinweise').font = FB
    for i, t in enumerate(notes):
        ws4.cell(row=r0 + 1 + i, column=1, value=t).font = F
    for i, w in enumerate([22, 48, 22, 10, 12, 80], 1):
        ws4.column_dimensions[get_column_letter(i)].width = w
    try:
        from openpyxl.workbook.properties import CalcProperties
        wb.calculation = CalcProperties(fullCalcOnLoad=True)
    except Exception:
        pass
    wb.save(path)
