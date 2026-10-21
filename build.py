"""
Builds the profile graphics.  python3 build.py
Idea: a Kurdish kilim woven row by row, the way a Jacquard loom (grandparent of the
punch card) works. Text is set in Schibsted Grotesk, a typeface from Oslo.
"""
import os, io, base64, random
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
os.makedirs(f"{HERE}/assets/projects", exist_ok=True)

# kilim palette
INDIGO, DEEP, MADDER, SAFFRON, WOOL, TEAL, PLUM = "#1D2650", "#141A38", "#A63329", "#E2A62E", "#ECE4D4", "#2C7A6C", "#6E3A5E"

def font_face(text, weight):
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga"]
    f = TTFont(f"{FONTS}/SchibstedGrotesk-{weight}.ttf")
    s = subset.Subsetter(opts); s.populate(text=text + " "); s.subset(f)
    buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:SG{weight};src:url(data:font/woff2;base64,{b64}) format('woff2');}}"

def styles(texts, extra=""):
    faces = "".join(font_face(t, w) for w, t in texts.items() if t)
    return f"<style>{faces}{extra}</style>"

# ------------------------------------------------------------- pixel lettering
GLYPHS = {
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}
def word_bitmap(word):
    rows = [""] * 7
    for i, ch in enumerate(word):
        for r in range(7):
            rows[r] += GLYPHS[ch][r] + ("." if i < len(word) - 1 else "")
    return rows

# ------------------------------------------------------------- kilim band
def band_color(x, y, h, phase=0):
    c = h // 2
    if y == 0 or y == h - 1:
        return MADDER if (x // 2) % 2 == 0 else DEEP
    xx = (x + phase) % 18
    d = abs(xx - 9) + abs(y - c)
    if d <= 1: return SAFFRON
    if d == 3: return WOOL
    if d in (5, 6): return MADDER
    # small crosses between diamonds
    if xx in (0, 17) and abs(y - c) <= 1: return TEAL
    if (xx == 0 or xx == 17) and abs(y - c) == 0: return TEAL
    return None

def stitch(x, y, s, col):
    # a cell drawn as a slightly inset stitch so the weave shows
    return f'<rect x="{x+.6:.1f}" y="{y+.6:.1f}" width="{s-1.2:.1f}" height="{s-1.2:.1f}" rx="1.4" fill="{col}"/>'

def fringe(x0, x1, y, down, seed):
    rnd = random.Random(seed); out = []
    x = x0 + 4
    while x < x1 - 2:
        ln = rnd.uniform(12, 22); dx = rnd.uniform(-2.5, 2.5)
        y2 = y + ln if down else y - ln
        out.append(f'<path d="M{x:.1f} {y} q {dx:.1f} {(y2-y)/2:.1f} {dx*1.6:.1f} {y2-y:.1f}" stroke="#CDBFA6" stroke-width="2.2" stroke-linecap="round" fill="none"/>')
        x += rnd.uniform(5, 8)
    return "".join(out)

# ------------------------------------------------------------- header
def header():
    S = 10                      # cell size
    COLS = 116
    X0, FR = 20, 24             # rug x offset, fringe room
    BAND = 9
    NAME_S = 15
    name = word_bitmap("SHAHI FTAH")
    name_w = len(name[0]) * NAME_S
    body_h = 270
    rug_w = COLS * S
    rug_h = BAND * S * 2 + body_h
    W, H = rug_w + X0 * 2, rug_h + FR * 2
    top, bot = FR, FR + rug_h

    rows = []   # (y_of_row, svg) woven bottom -> top
    # bottom band
    for r in range(BAND):
        y = bot - (r + 1) * S
        cells = [stitch(X0 + c * S, y, S, col) for c in range(COLS) if (col := band_color(c, BAND - 1 - r, BAND, 9))]
        rows.append(cells)
    # body rows: ground + side borders + lettering
    body_rows = body_h // S
    ny0 = (body_rows - 7) // 2 - 3
    nx = X0 + 48
    for r in range(body_rows):
        y = bot - BAND * S - (r + 1) * S
        rr = body_rows - 1 - r          # row index from top of body
        cells = []
        for c in (0, 1, COLS - 2, COLS - 1):   # selvedge
            cells.append(stitch(X0 + c * S, y, S, MADDER if (rr + c) % 2 else SAFFRON))
        # lettering: map name rows that overlap this body row
        if ny0 <= rr < ny0 + 7:
            pass
        rows.append(cells)
    # top band
    for r in range(BAND):
        y = top + (BAND - 1 - r) * S
        cells = [stitch(X0 + c * S, y, S, col) for c in range(COLS) if (col := band_color(c, r, BAND))]
        rows.append(cells)
    rows_svg = []
    n = len(rows)
    for i, cells in enumerate(rows):
        rows_svg.append(f'<g class="r" style="animation-delay:{i*0.07:.2f}s">{"".join(cells)}</g>')
    weave_end = n * 0.07

    # name lettering, woven row by row in its own sequence
    name_top = top + BAND * S + 50
    letters = []
    for r in range(7):
        y = name_top + r * NAME_S
        cells = [stitch(nx + c * NAME_S, y, NAME_S, WOOL) for c, ch in enumerate(name[r]) if ch == "#"]
        delay = ((bot - y - NAME_S) / S) * 0.07
        letters.append(f'<g class="r" style="animation-delay:{delay:.2f}s">{"".join(cells)}</g>')
    # saffron underline stitch under the name
    ul_y = name_top + 7 * NAME_S + 14
    ul = "".join(stitch(nx + c * 8, ul_y, 8, SAFFRON if c % 2 == 0 else MADDER) for c in range(16))

    t1 = "Computer science, University of Oslo."
    t2 = "Now a master's in entrepreneurship & innovation."
    tx = nx + 2
    texts = {600: "", 400: t1 + t2 + "Hei Silav Hola Hello,"}
    greet = ["Hei", "Silav", "Hola", "Hello", "Hei"]
    gl = []
    period = 2.2 * 4
    for i, g in enumerate(greet[:4]):
        gl.append(f'<text class="g" style="animation-delay:{weave_end + i*2.2:.2f}s" x="{nx}" y="{name_top - 18}" font-family="SG400" font-size="22" fill="{SAFFRON}">{g},</text>')

    css = f"""
    .r {{ opacity:0; animation: weave .35s steps(3) forwards; }}
    @keyframes weave {{ from {{ opacity:0; transform: translateX(-6px) }} to {{ opacity:1; transform:none }} }}
    .shuttle {{ animation: shuttle {weave_end:.2f}s linear forwards; }}
    @keyframes shuttle {{ 0% {{ transform: translateY(0); opacity:1 }} 96% {{ opacity:1 }} 100% {{ transform: translateY(-{rug_h}px); opacity:0 }} }}
    .fade {{ opacity:0; animation: fade 1s {weave_end*0.55:.2f}s ease-out forwards; }}
    @keyframes fade {{ to {{ opacity:1 }} }}
    .g {{ opacity:0; animation: gr {period}s infinite; }}
    @keyframes gr {{ 0%{{opacity:0}} 6%{{opacity:1}} 22%{{opacity:1}} 26%{{opacity:0}} 100%{{opacity:0}} }}
    .glint {{ animation: glint 7s {weave_end+1:.2f}s ease-in-out infinite; opacity:0 }}
    @keyframes glint {{ 0%{{opacity:0; transform:translateX(0)}} 10%{{opacity:.55}} 40%{{opacity:0; transform:translateX({rug_w}px)}} 100%{{opacity:0; transform:translateX({rug_w}px)}} }}
    @media (prefers-reduced-motion: reduce) {{ .r,.fade{{animation:none;opacity:1}} .shuttle,.glint{{display:none}} .g{{animation:none}} .g:first-of-type{{opacity:1}} }}
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Shahi Ftah. Software engineer from the University of Oslo, now doing a master's in entrepreneurship and innovation.">
{styles(texts, css)}
<defs>
  <filter id="wool" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".9 .35" numOctaves="2" seed="4" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .09 0"/>
  </filter>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="rug"><rect x="{X0}" y="{top}" width="{rug_w}" height="{rug_h}"/></clipPath>
</defs>
{fringe(X0, X0 + rug_w, top, False, 1)}
{fringe(X0, X0 + rug_w, bot, True, 2)}
<rect x="{X0}" y="{top}" width="{rug_w}" height="{rug_h}" fill="{INDIGO}"/>
<g clip-path="url(#rug)">
  {''.join(rows_svg)}
  {''.join(letters)}
  <g class="r" style="animation-delay:{((bot-ul_y-8)/S)*0.07:.2f}s">{ul}</g>
  <g class="fade" font-family="SG400" font-size="21" fill="{WOOL}" opacity=".9">
    <text x="{tx}" y="{name_top + 7*NAME_S + 62}">{t1}</text>
    <text x="{tx}" y="{name_top + 7*NAME_S + 90}">{t2.replace("&","&amp;")}</text>
  </g>
  {''.join(gl)}
  <rect class="shuttle" x="{X0}" y="{bot-3}" width="{rug_w}" height="3" fill="{SAFFRON}"/>
  <rect class="glint" x="{X0-260}" y="{top}" width="260" height="{rug_h}" fill="url(#gl)"/>
  <rect x="{X0}" y="{top}" width="{rug_w}" height="{rug_h}" filter="url(#wool)"/>
</g>
</svg>'''

# ------------------------------------------------------------- project strips
ICONS = {
    "sun":   ["....#....", ".#.....#.", "...###...", "..#####..", "#.#####.#", "..#####..", "...###...", ".#.....#.", "....#...."],
    "wave":  [".........", ".##...##.", "#..#.#..#", "....#....", ".........", ".##...##.", "#..#.#..#", "....#....", "........."],
    "bird":  ["##.....##", "##.....##", "##.....##", ".........", "...##....", "...##....", "##.....##", "##.....##", "##.....##"],
    "note":  ["######...", "#....##..", "#.###.#..", "#......#.", "#.####.#.", "#......#.", "#.###..#.", "#......#.", "########."],
    "bars":  ["........#", "......#.#", "......#.#", "....#.#.#", "....#.#.#", "..#.#.#.#", "..#.#.#.#", "#.#.#.#.#", "#.#.#.#.#"],
}
THEME = {"dark": dict(text="#ECE4D4", muted="#9EA6BC", stitch="#3A4466"),
         "light": dict(text="#1D2650", muted="#5D6580", stitch="#C9C2B4")}

def strip(p, mode, i):
    t = THEME[mode]; S = 10; W, H = 1200, 158
    ground = p["color"]
    sw = []
    for r in range(11):
        for c in range(11):
            if r in (0, 10) or c in (0, 10):
                col = SAFFRON if (r + c) % 2 == 0 else ground
            elif ICONS[p["icon"]][r - 1][c - 1] == "#":
                col = WOOL
            else:
                col = ground
            sw.append((r, stitch(14 + c * S, 18 + r * S, S, col)))
    # icon weaves bottom-up
    rows = {}
    for r, s in sw: rows.setdefault(r, []).append(s)
    sw_svg = "".join(f'<g class="r" style="animation-delay:{(10-r)*0.06 + i*0.15:.2f}s">{"".join(v)}</g>' for r, v in rows.items())
    texts = {600: p["name"], 400: p["desc"] + p["tech"]}
    css = """.r{opacity:0;animation:w .3s steps(2) forwards}@keyframes w{to{opacity:1}}
    @media (prefers-reduced-motion: reduce){.r{animation:none;opacity:1}}"""
    dash = f'<line x1="160" y1="{H-2}" x2="{W-10}" y2="{H-2}" stroke="{t["stitch"]}" stroke-width="2" stroke-dasharray="7 6"/>' if p.get("sep", True) else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{p['name']}. {p['desc']}">
{styles(texts, css)}
{sw_svg}
<text x="160" y="56" font-family="SG600" font-size="34" fill="{t['text']}" letter-spacing="-.4">{p['name']}</text>
<text x="160" y="93" font-family="SG400" font-size="22" fill="{t['text']}" opacity=".85">{p['desc']}</text>
<text x="160" y="124" font-family="SG400" font-size="18" fill="{t['muted']}">{p['tech']}</text>
{dash}
</svg>'''

PROJECTS = [
    dict(slug="sunify", name="Sunify", icon="sun", color="#B07A12",
         desc="An Android app that shows what your solar panels produce, in real time.", tech="Kotlin, Android"),
    dict(slug="aquaflow", name="AquaFlow", icon="wave", color=TEAL,
         desc="Water data turned into interactive charts.", tech="TypeScript, Node.js"),
    dict(slug="flappy", name="MyOwnFlappyBird", icon="bird", color="#3A4A8C",
         desc="My take on Flappy Bird, with physics I tuned by hand.", tech="TypeScript, HTML, CSS"),
    dict(slug="notes", name="Note-app", icon="note", color=PLUM,
         desc="A small notes app that keeps everything in your browser.", tech="TypeScript, HTML, CSS"),
    dict(slug="sorting", name="Sorting-Algorithm", icon="bars", color=MADDER, sep=False,
         desc="Classic sorting algorithms, written so you can follow them.", tech="Python"),
]

# ------------------------------------------------------------- footer band
def footer():
    S, COLS, BAND = 8, 145, 9
    rug_w = COLS * S; X0, FR = 20, 22
    W, H = rug_w + 2 * X0, BAND * S + 2 * FR
    cells = [stitch(X0 + c * S, FR + r * S, S, col) for r in range(BAND) for c in range(COLS) if (col := band_color(c, r, BAND, 4))]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Woven band">
{fringe(X0, X0+rug_w, FR, False, 3)}{fringe(X0, X0+rug_w, FR+BAND*S, True, 4)}
<rect x="{X0}" y="{FR}" width="{rug_w}" height="{BAND*S}" fill="{INDIGO}"/>{''.join(cells)}
</svg>'''


# ------------------------------------------------------------- text metrics
_fm = {}
def text_w(text, size, weight=400):
    if weight not in _fm:
        f = TTFont(f"{FONTS}/SchibstedGrotesk-{weight}.ttf")
        _fm[weight] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hm, upm = _fm[weight]
    return sum(hm[cmap.get(ord(ch), cmap[32])][0] for ch in text) * size / upm

def diamond(x, y, S, ground=None):
    out = []
    for r in range(7):
        for c in range(7):
            d = abs(r - 3) + abs(c - 3)
            col = SAFFRON if d == 0 else WOOL if d == 1 else MADDER if d == 3 else (ground if ground else None)
            if col: out.append(stitch(x + c * S, y + r * S, S, col))
    return "".join(out)

# ------------------------------------------------------------- section headings
def heading(text, mode):
    t = THEME[mode]; W, H = 1200, 76
    css = ".r{opacity:0;animation:w .3s steps(2) forwards}@keyframes w{to{opacity:1}}@media (prefers-reduced-motion: reduce){.r{animation:none;opacity:1}}"
    tw = text_w(text, 34, 600)
    lx = 64 + tw + 28
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{text}">
{styles({600: text}, css)}
<g class="r">{diamond(14, 17, 6)}</g>
<text x="66" y="50" font-family="SG600" font-size="34" letter-spacing="-.5" fill="{t['text']}">{text.replace("&","&amp;")}</text>
<line x1="{lx:.0f}" y1="38" x2="{W-10}" y2="38" stroke="{t['stitch']}" stroke-width="2" stroke-dasharray="7 6"/>
</svg>"""

# ------------------------------------------------------------- toolbox
TOOLS = [
    ("Languages", SAFFRON, ["Java", "Kotlin", "Python", "C", "TypeScript", "JavaScript"]),
    ("Web & data", TEAL, ["Node.js", "HTML", "CSS", "MySQL"]),
    ("Mobile & cloud", MADDER, ["Android", "Google Cloud", "JWT"]),
    ("Tools & design", PLUM, ["Git", "GitHub", "VS Code", "Photoshop", "Illustrator", "Canva"]),
]
def toolbox(mode):
    t = THEME[mode]; W = 1200; RH = 66; S = 9
    rows_svg = []; all_txt = ""; lab_txt = ""
    for i, (label, col, items) in enumerate(TOOLS):
        y = 20 + i * RH
        lab_txt += label
        parts = [f'<text x="14" y="{y+23}" font-family="SG400" font-size="20" fill="{t["muted"]}">{label.replace("&","&amp;")}</text>']
        x = 250
        for j, name in enumerate(items):
            all_txt += name
            # 3x3 woven swatch: group colour with a wool centre
            sw = "".join(stitch(x + c * S, y + 4 + r * S, S, WOOL if (r, c) == (1, 1) else col) for r in range(3) for c in range(3))
            parts.append(f'<g class="r" style="animation-delay:{i*0.12 + j*0.06:.2f}s">{sw}</g>')
            parts.append(f'<text x="{x+38}" y="{y+25}" font-family="SG600" font-size="23" fill="{t["text"]}">{name}</text>')
            x += 34 + text_w(name, 23, 600) + 32
        rows_svg.append("".join(parts))
        if i < len(TOOLS) - 1:
            rows_svg.append(f'<line x1="14" y1="{y+RH-12}" x2="{W-10}" y2="{y+RH-12}" stroke="{t["stitch"]}" stroke-width="1.5" stroke-dasharray="3 7" opacity=".7"/>')
    H = 20 + len(TOOLS) * RH - 10
    css = ".r{opacity:0;animation:w .3s steps(2) forwards}@keyframes w{to{opacity:1}}@media (prefers-reduced-motion: reduce){.r{animation:none;opacity:1}}"
    alt = "; ".join(f"{l}: {', '.join(it)}" for l, _, it in TOOLS)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{alt.replace('&','&amp;')}">
{styles({400: lab_txt, 600: all_txt}, css)}
{''.join(rows_svg)}
</svg>"""

# ------------------------------------------------------------- the year, woven
USER = "ShahiFtah"
def fetch_year(user=USER):
    import re, urllib.request, datetime as dt
    html = urllib.request.urlopen(urllib.request.Request(
        f"https://github.com/users/{user}/contributions", headers={"User-Agent": "profile-build"}), timeout=30).read().decode()
    days = {}
    for m in re.finditer(r'data-date="([\d-]+)"\s+id="contribution-day-component-(\d+)-(\d+)"\s+data-level="(\d)"', html):
        days[(int(m[2]), int(m[3]))] = [dt.date.fromisoformat(m[1]), int(m[4]), 0]
    for m in re.finditer(r'for="contribution-day-component-(\d+)-(\d+)"[^>]*>\s*(\d+|No) contributions?', html):
        k = (int(m[1]), int(m[2]))
        if k in days: days[k][2] = 0 if m[3] == "No" else int(m[3])
    if not days: raise RuntimeError("no contribution data found")
    return days

LEVEL = {0: "#2A3466", 1: "#7A3A55", 2: MADDER, 3: SAFFRON, 4: WOOL}
def year(mode, days):
    t = THEME[mode]; S = 20
    cols = max(c for _, c in days) + 1
    X0, FR = 20, 22
    rug_w = (cols + 4) * S; rug_h = (7 + 4) * S
    W = max(1200, rug_w + 2 * X0); X0 = (W - rug_w) // 2
    top = FR; H = FR + rug_h + FR + 64
    gx, gy = X0 + 2 * S, top + 2 * S
    cells = []
    by_col = {}
    for (r, c), (d, lvl, n) in days.items():
        by_col.setdefault(c, []).append(stitch(gx + c * S, gy + r * S, S, LEVEL[lvl]))
    for c in sorted(by_col):
        cells.append(f'<g class="r" style="animation-delay:{c*0.035:.2f}s">{"".join(by_col[c])}</g>')
    # selvedge: checker frame
    frame = []
    for c in range(cols + 4):
        for r in (0, 10):
            frame.append(stitch(X0 + c * S, top + r * S, S, MADDER if c % 2 else SAFFRON))
    for r in range(1, 10):
        for c in (0, cols + 3):
            frame.append(stitch(X0 + c * S, top + r * S, S, MADDER if r % 2 else SAFFRON))
    # today
    last = max(days.items(), key=lambda kv: kv[1][0])
    (lr, lc), _ = last
    today = f'<rect class="today" x="{gx+lc*S+.6}" y="{gy+lr*S+.6}" width="{S-1.2}" height="{S-1.2}" rx="1.4" fill="none" stroke="{SAFFRON}" stroke-width="2.5"/>'
    # month labels
    labels = []; seen = set(); txt = ""
    for (r, c), (d, *_ ) in sorted(days.items(), key=lambda kv: kv[1][0]):
        if d.day <= 7 and r == 0 or (d.day == 1):
            key = (d.year, d.month)
            if key in seen or c > cols - 3: continue
            seen.add(key); name = d.strftime("%b"); txt += name
            labels.append(f'<text x="{gx + c*S}" y="{top + rug_h + 46}" font-family="SG400" font-size="18" fill="{t["muted"]}">{name}</text>')
    total = sum(v[2] for v in days.values()); active = sum(1 for v in days.values() if v[2] > 0)
    cap = f"{total} contributions over {active} days in the past year"
    weave_end = cols * 0.035
    css = f""".r{{opacity:0;animation:w .3s steps(2) forwards}}@keyframes w{{to{{opacity:1}}}}
    .today{{opacity:0;animation:p 2.4s {weave_end:.2f}s ease-in-out infinite}}@keyframes p{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
    @media (prefers-reduced-motion: reduce){{.r{{animation:none;opacity:1}}.today{{animation:none;opacity:1}}}}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution calendar woven as a rug. {cap}.">
{styles({400: txt + cap + "0123456789"}, css)}
{fringe(X0, X0 + rug_w, top, False, 5)}{fringe(X0, X0 + rug_w, top + rug_h, True, 6)}
<rect x="{X0}" y="{top}" width="{rug_w}" height="{rug_h}" fill="{INDIGO}"/>
{''.join(frame)}{''.join(cells)}{today}
{''.join(labels)}
<text x="{gx}" y="{top + rug_h + 76}" font-family="SG400" font-size="19" fill="{t['text']}" opacity=".85">{cap}</text>
</svg>"""

def build_year():
    try:
        days = fetch_year()
    except Exception as e:
        print("year: skipped,", e); return
    for mode in THEME:
        open(f"{HERE}/assets/year-{mode}.svg", "w").write(year(mode, days))
    print("year: built")

HEADINGS = {"built": "Things I've built", "tools": "What I work with", "year": "My year, woven"}

if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["year"]:
        build_year(); raise SystemExit
    open(f"{HERE}/assets/header.svg", "w").write(header())
    open(f"{HERE}/assets/footer.svg", "w").write(footer())
    for i, p in enumerate(PROJECTS):
        for mode in THEME:
            open(f"{HERE}/assets/projects/{p['slug']}-{mode}.svg", "w").write(strip(p, mode, i))
    for mode in THEME:
        open(f"{HERE}/assets/tools-{mode}.svg", "w").write(toolbox(mode))
        for k, v in HEADINGS.items():
            open(f"{HERE}/assets/h-{k}-{mode}.svg", "w").write(heading(v, mode))
    build_year()
    print("built")
