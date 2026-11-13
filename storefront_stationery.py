"""The client demo catalogue, independent of ERP products and stock."""
from functools import lru_cache
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlencode

STATIONERY = '/shop/stationery'
KALAM = '/shop/kalam'
ASSETS = '/storefront/stationery'
KALAM_ASSETS = '/storefront/kalam'
SEARCH = '/api/storefront/stationery-search'
KALAM_SEARCH = '/api/storefront/kalam-search'
GROUPS = {
    'writing-marking': ('Writing & Marking', 'Pens, pencils, markers and highlighters for the things you write every day.'),
    'paper-planning': ('Paper & Planning', 'Notebooks, planners and paper goods for ideas, notes and dates.'),
    'office-tools': ('Office Tools', 'Staplers, scissors and the small tools that earn their place on a desk.'),
    'files-desk-organization': ('Files & Desk Organization', 'Give paperwork and desk essentials a place of their own.'),
    'adhesives-office-supplies': ('Adhesives & Office Supplies', 'Glues, tapes and everyday supplies to keep the work moving.'),
    'school-geometry': ('School & Geometry', 'Measuring tools and classroom essentials.'),
}
COLLECTIONS = {
    'premium-pens': ('Premium Kalams', 'Contemporary fountain pens with distinctive finishes and nibs.'),
    'grandfathers-collection': ('Grandfather’s Collection', 'A demo selection inspired by pens worth passing down.'),
}
BRANDS = (('LAMY', 'lamy.svg'), ('Penlux', 'penlux.png'), ('YSTUDIO', 'ystudio.png'),
          ('Waterman', 'waterman.svg'), ('Pelikan', 'pelikan.svg'), ('Platinum', 'platinum.svg'))
CART_ID = r'stationery:[a-z0-9-]{1,120}'

# Hand-traced silhouettes on the approved scene keep the shelves still on hover.
DISPLAYS = (
    (117, '21,440,192,176', '33,502 42,498 54,527 51,488 67,481 80,477 85,503 90,487 113,485 134,491 139,509 195,513 196,531 189,623 202,637 187,654 126,669 42,651 40,567 49,556'),
    (314, '218,414,192,202', '220,514 225,497 243,498 244,455 361,446 385,450 390,544 401,546 406,642 390,654 316,667 239,663 236,640 221,635'),
    (510, '413,434,192,182', '431,530 493,505 517,509 513,480 529,471 546,476 558,471 576,486 568,533 582,538 583,584 601,605 600,626 541,671 472,665 421,649 417,622 431,603 420,585 426,571'),
    (708, '608,412,197,204', '607,464 612,454 719,449 741,458 743,468 765,470 767,516 800,518 803,620 795,642 782,662 641,665 635,638 610,636'),
    (903, '811,438,184,178', '822,559 825,541 871,540 870,524 883,514 888,484 896,483 902,512 913,525 913,536 945,529 978,536 981,592 976,639 979,652 929,667 827,658 818,642'),
    (1092, '996,408,189,208', '1003,501 1014,489 1105,488 1106,444 1136,443 1138,529 1167,531 1176,541 1164,632 1171,651 1149,666 1024,667 1019,646 1004,626'),
    (1297, '1187,433,223,183', '1192,615 1203,607 1202,570 1240,540 1228,473 1237,467 1391,489 1397,507 1400,580 1392,599 1374,612 1386,638 1374,660 1280,669 1207,650'),
    (1533, '1411,433,240,183', '1421,568 1445,546 1447,479 1461,470 1534,475 1538,468 1552,468 1554,481 1647,486 1642,572 1635,614 1621,655 1557,675 1446,654 1432,635 1420,631'),
)


@lru_cache(maxsize=1)
def catalogue():
    file = Path(__file__).resolve().parent / 'reference' / 'stationery-demo.json'
    return json.loads(file.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def kalams():
    file = Path(__file__).resolve().parent / 'reference' / 'kalam-demo.json'
    return json.loads(file.read_text(encoding='utf-8')) + [p for p in catalogue() if p['group'] in COLLECTIONS]


def is_kalam(path):
    return path == KALAM or path.startswith(KALAM + '/')


@lru_cache(maxsize=1)
def kalam_signature():
    file = Path(__file__).resolve().parent / 'public/storefront/kalam/signature.svg'
    return '<span class="sr-only">Kalam</span>' + file.read_text(encoding='utf-8')


def product_url(p):
    root = KALAM if p['group'] in COLLECTIONS else STATIONERY
    return f'{root}/product/{p["id"]}'


def product_image(p):
    root = KALAM_ASSETS if p.get('concept') else ASSETS
    extension = 'svg' if p.get('concept') else 'webp'
    return f'{root}/products/{p["id"]}.{extension}'


def public_product(p):
    return {
        'id': 'stationery:' + p['id'], 'name': p['name'], 'url': product_url(p), 'image': product_image(p),
        'price': p['price'], 'mrp': p['mrp'], 'discount': (p['mrp'] - p['price']) * 100 // p['mrp'],
        'demo_stationery': True,
    }


def saved_products(ids):
    products = [p for p in catalogue() if p['group'] in GROUPS] + kalams()
    return [item for item in map(public_product, products) if item['id'] in ids]


def search_products(query, products=None):
    tokens = set(re.findall(r'[^\W_]+', query.casefold()))
    products = [p for p in catalogue() if p['group'] in GROUPS] if products is None else products
    if not tokens:
        return products
    matches = []
    for p in products:
        title = re.findall(r'[^\W_]+', p['name'].casefold())
        group = (GROUPS.get(p['group']) or COLLECTIONS[p['group']])[0]
        facets = re.findall(r'[^\W_]+', (p['type'] + ' ' + group).casefold())
        if all(any(term.startswith(token) for term in title + facets) for token in tokens):
            score = sum(any(term.startswith(token) for term in title) for token in tokens)
            matches.append((score, p))
    return [p for _, p in sorted(matches, key=lambda match: match[0], reverse=True)]


def suggestions(query, *, kalam=False):
    return {'products': [
        {'id': p['id'], 'name': p['name'], 'image': product_image(p), 'url': product_url(p)}
        for p in search_products(query, kalams() if kalam else None)[:8]
    ] if query.strip() else []}


def group_url(group):
    return f'{KALAM if group in COLLECTIONS else STATIONERY}/{group}'


def nav_links(path, *, kalam=False):
    def link(url, label):
        current = ' aria-current="page"' if path.rstrip('/') == url else ''
        return f'<a href="{escape(url)}"{current}>{escape(label)}</a>'

    if kalam:
        return ''.join([link(KALAM, 'Kalam studio'), *(link(group_url(key), label) for key, (label, _) in COLLECTIONS.items())])
    links = [link(STATIONERY + '/catalogue', 'All stationery')]
    for key, (label, _) in GROUPS.items():
        url = group_url(key)
        types = sorted({p['type'] for p in catalogue() if p['group'] == key})
        options = [(url, f'All {label}')] + [
            (url + '?' + urlencode({'type': kind}) + '#stationery-products', kind) for kind in types
        ]
        branches = ''.join(f'<div class="nav-branch"><a class="nav-group-link" href="{escape(href)}">'
                           f'{escape(name)}</a></div>' for href, name in options)
        links.append(
            f'<details class="nav-dropdown" data-nav-key="{key}" data-nav-href="{url}">'
            f'<summary>{escape(label)}</summary><div>{branches}</div></details>'
        )
    return ''.join(links)


def base_glow(index):
    x, y, rx, ry = (
        (117, 660, 93, 30), (314, 661, 91, 30), (511, 663, 91, 28), (708, 663, 94, 28),
        (903, 661, 88, 30), (1092, 661, 89, 30), (1297, 660, 106, 32), (1533, 662, 113, 31),
    )[index]
    return (f'<g class="stationery-base-glow"><ellipse cx="{x}" cy="{y + ry}" rx="{rx * .86}" ry="8"/>'
            f'<path d="M{x - rx} {y}a{rx} {ry} 0 0 0 {2 * rx} 0"/></g>')


def thumbnail(index):
    _, box, _ = DISPLAYS[index]
    x, y, width, _ = map(int, box.split(','))
    return (f'<svg class="stationery-thumb" viewBox="{x} {y} {width} {710 - y}" '
            f'preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<image href="{ASSETS}/shop-unlit.webp" width="1672" height="941"/>{base_glow(index)}</svg>')


def hero(group):
    scene, objects = [], []
    attrs, selected = '', ''
    copy = ('<h1>The Art of Writing, Beautifully</h1>'
            '<p>Everyday essentials and pieces worth passing down.</p>')
    for index, (key, (name, _)) in enumerate(GROUPS.items()):
        x, _, points = DISPLAYS[index]
        target = x / 1187 * 100
        side = 'left' if target < 50 else 'right'
        pan = max(-70, min(70, (25 if side == 'left' else 75) - (50 + (target - 50) * 2.4)))
        scene.append(f'<clipPath id="stationery-cut-{key}"><polygon points="{points}"/></clipPath>'
                     f'<g class="stationery-lift" data-lift="{key}">'
                     f'<g class="stationery-cutout" style="transform-origin:{x}px 555px">'
                     f'<use href="#stationery-photo" clip-path="url(#stationery-cut-{key})"/></g>'
                     f'{base_glow(index)}</g>')
        objects.append(f'<a href="{group_url(key)}" class="stationery-object" data-stationery-object="{key}" '
                       f'data-pan="{pan:.2f}%" data-side="{side}" '
                       f'style="--item-x:{target:.2f}%">{thumbnail(index)}<span>{escape(name)}</span></a>')
        if key == group:
            attrs = f'data-side="{side}" style="--camera-pan:{pan:.2f}%"'
            copy = (f'<a class="button outline stationery-back" data-stationery-back href="{STATIONERY}">← All stationery</a>'
                    f'<p class="stationery-kicker">Stationery</p><h1>{escape(name)}</h1>'
                    f'<p>{escape(GROUPS[key][1])}</p>')
            selected = thumbnail(index)
    return f'''
<section class="stationery-hero" data-stationery-hero data-group="{group}" {attrs} aria-label="Stationery displays">
  <div class="stationery-camera">
    <svg class="stationery-scene" viewBox="0 190 1187 560" aria-hidden="true">
      <image id="stationery-photo" href="{ASSETS}/shop-unlit.webp" width="1672" height="941"/>
      {''.join(scene)}
    </svg>
  </div>
  <div class="stationery-copy">{copy}</div>
  <div class="stationery-selected">{selected}</div>
  <nav class="stationery-objects" aria-label="Stationery categories">{''.join(objects)}</nav>
</section>'''


def prices(p, price):
    return (f'<p class="stationery-prices"><strong>{price(p["price"])}</strong> '
            f'<del>{price(p["mrp"])}</del></p>')


def discount_flag(item):
    discount = item['discount']
    return f'<span class="discount-badge" data-discount-band="{min(discount // 10, 4) * 10}">{discount}% off</span>' if discount else ''


def add_button(p):
    return f'''<form class="stationery-add" data-add="{p["id"]}" method="post">
      <button class="button" type="submit">Add to cart</button>
      <p class="cart-note" data-add-message role="status"></p>
    </form>'''


def card(p, price, save_button):
    item = public_product(p)
    return f'''
<article class="stationery-product">
  <a href="{product_url(p)}" class="stationery-product-link">
    <img src="{product_image(p)}" alt="" width="560" height="560" loading="lazy" decoding="async" data-product-image>
    <div><p>{escape(p['type'])}</p><h3>{escape(p['name'])}</h3></div>
  </a>
  {discount_flag(item)}
  {save_button(item)}
  <div class="stationery-product-purchase">{prices(item, price)}{add_button(item)}</div>
</article>'''


def listing(price, save_button, group='', query='', kind='', *, kalam=False):
    products = [p for p in (kalams() if kalam else catalogue())
                if (kalam or p['group'] in GROUPS) and (not group or p['group'] == group)]
    types = sorted({p['type'] for p in products})
    if kind:
        products = [p for p in products if p['type'] == kind]
    products = search_products(query, products)
    heading = (f'Results for “{query}”' if query else kind or
               ('In this collection' if group else 'Browse Kalam' if kalam else 'Browse stationery'))
    path = group_url(group) if group else (KALAM if kalam else STATIONERY) + '/catalogue'
    filters = ''
    if group and len(types) > 1:
        links = []
        for name in ['', *types]:
            href = path + ('?' + urlencode({'type': name}) if name else '') + '#stationery-products'
            current = ' aria-current="true"' if name == kind else ''
            links.append(f'<a href="{escape(href)}"{current}>{escape(name or "All types")}</a>')
        filters = '<nav class="stationery-filters" aria-label="Product types">' + ''.join(links) + '</nav>'
    items = ''.join(card(p, price, save_button) for p in products) or '<p>No matching products. Try another search.</p>'
    return f'''
<section class="wrap stationery-catalogue" id="stationery-products">
  <div class="stationery-section-title">
    <div><p class="stationery-kicker">Demo catalogue</p><h2>{escape(heading)}</h2></div>
    <span>{len(products)} {'item' if len(products) == 1 else 'items'}</span>
  </div>
  {filters}
  <div class="stationery-products">{items}</div>
</section>'''


def home_sections(price, save_button, membership):
    deals = sorted((p for p in catalogue() if p['group'] in GROUPS),
                   key=lambda p: public_product(p)['discount'], reverse=True)[:4]
    return f'''
<div id="stationery-products">
  {membership}
  <section class="wrap stationery-catalogue" aria-labelledby="stationery-deals-heading">
    <div class="stationery-section-title"><h2 id="stationery-deals-heading">Featured stationery discounts</h2>
      <a class="button outline" href="{STATIONERY}/catalogue">Browse stationery</a></div>
    <div class="stationery-products">{''.join(card(p, price, save_button) for p in deals)}</div>
  </section>
</div>'''


def pen_gallery(group, price, save_button, kind):
    products = [p for p in kalams() if p['group'] == group]
    items = []
    for p in products:
        product = public_product(p)
        views = p.get('rail') or [{'src': product['image'], 'label': 'Full pen',
                                  'clip': 'none', 'transform': 'none', **p.get('shelf', {})}]
        if p.get('concept'):
            views = [*views, {'src': product['image'].replace('.svg', '-nib.svg'),
                              'label': 'Nib detail', 'clip': 'none', 'transform': 'none'}]
        items.append({
            **product, 'description': p['description'], 'type': p['type'],
            'onRail': len(items) < 3, 'views': views,
            'saleLabel': price(p['price']), 'originalLabel': price(p['mrp']),
        })
    title = COLLECTIONS[group][0]
    data = json.dumps({'title': title, 'items': items, 'kind': kind}, ensure_ascii=False).replace('<', r'\u003c')
    fallback = listing(price, save_button, group, kind=kind, kalam=True)
    return (f'<div data-pen-gallery>{fallback}</div>'
            f'<script type="application/json" id="pen-gallery-data">{data}</script>'
            '<script type="module" src="/storefront/vendor/pen-gallery.js"></script>')


def grandfather_story():
    return '''
<section class="grandfather-story" aria-labelledby="grandfather-story-heading">
  <div class="wrap grandfather-story-inner">
    <figure class="grandfather-story-portrait">
      <span class="grandfather-story-portrait-note">Representative portrait</span>
      <img src="/storefront/kalam/representative-portrait.webp"
           alt="Illustrative black-and-white portrait of an elderly bookseller reading."
           loading="lazy" decoding="async" width="760" height="950">
    </figure>
    <div class="grandfather-story-copy">
      <h2 id="grandfather-story-heading">Gupta since 1916</h2>
      <p>Gupta Brothers Books was established in 1916 by Mr. V.J. Gupta. It has grown from humble beginnings and has now become a household name for books. Taken over by the children of Mr. V.J. Gupta, Gupta Brothers Books have opened up three branches that are strategically located in various parts of the city, in order to cater to the burgeoning requirements of students, teachers, academicians and connoisseurs of literature.</p>
      <p>There are many who just drop by to spend a few hours in the shop, just to browse around. Culture and tradition continue to be the hallmark of Gupta Brothers Books. Gupta Brothers Books has always been more than just a book shop. Many distinguished writers including Manepalli Ramachandra Sastry, Cetti Laksminarasimham and others…</p>
    </div>
  </div>
</section>'''


def kalam_display(key, *, lamp=False):
    lighting = (f'<span class="kalam-light"></span>'
                f'<img class="kalam-lamp" src="{ASSETS}/pendant.webp" alt="" width="480" height="480">') if lamp else ''
    return f'''<span class="kalam-display" data-kalam-display="{key}" aria-hidden="true">
      <img class="kalam-scene" src="{KALAM_ASSETS}/{key}.webp" alt="" width="887" height="887" fetchpriority="high">
      {lighting}
    </span>'''


def kalam_hero(group):
    if group:
        title, description = COLLECTIONS[group]
        return f'''<section class="kalam-collection-hero wrap" data-kalam-group="{group}">
  <div class="kalam-collection-copy">
    <a class="button outline kalam-back" href="{KALAM}">← Back to Kalam</a>
    <h1>{escape(title)}</h1>
    <p>{escape(description)}</p>
    <a class="button kalam-action" href="#stationery-products">Browse pens</a>
  </div>
  <div class="kalam-collection-photo">{kalam_display(group)}</div>
</section>'''
    panels = ''.join(
        f'<a class="kalam-tile" href="{group_url(key)}">{kalam_display(key, lamp=True)}'
        f'<span class="kalam-tile-title">{escape(title)}<span aria-hidden="true">↗</span></span></a>'
        for key, (title, _) in COLLECTIONS.items())
    return f'''<section class="kalam-landing wrap" data-kalam-landing>
  <h1>{kalam_signature()}</h1>
  <nav class="kalam-panels" aria-label="Kalam collections">{panels}</nav>
</section>'''


def legacy_kalam_path(path):
    if not path.startswith(STATIONERY + '/'):
        return None
    suffix = path.removeprefix(STATIONERY + '/').rstrip('/')
    if suffix in COLLECTIONS or (suffix.startswith('product/') and any(
            suffix == 'product/' + p['id'] for p in kalams())):
        return f'{KALAM}/{suffix}'
    return None


def page(path, params, price, save_button, membership):
    kalam = is_kalam(path)
    root = KALAM if kalam else STATIONERY
    name = 'Kalam' if kalam else 'Stationery'
    groups = COLLECTIONS if kalam else GROUPS
    suffix = path.removeprefix(root).strip('/')
    if not suffix:
        if not kalam:
            return 200, name, hero('') + home_sections(price, save_button, membership)
        logos = ''.join(f'<a href="{KALAM}/catalogue?{urlencode({"q": brand})}">'
                        f'<img src="{ASSETS}/{asset}" alt="{brand}" loading="lazy" decoding="async"></a>'
                        for brand, asset in BRANDS)
        return 200, name, (kalam_hero('') + '<section class="kalam-brands wrap">'
                           '<h2>Brands we provide</h2><div class="stationery-brand-logos">' + logos + '</div></section>')
    if suffix in groups:
        kind = params.get('type', [''])[0][:60]
        if kalam:
            content = kalam_hero(suffix) + pen_gallery(suffix, price, save_button, kind)
            if suffix == 'grandfathers-collection':
                content += grandfather_story()
        else:
            content = hero(suffix) + listing(price, save_button, suffix, kind=kind)
        return 200, groups[suffix][0], content
    if suffix == 'catalogue':
        query = params.get('q', [''])[0].strip()[:100]
        return 200, f'{name} catalogue', ('<div class="wrap stationery-catalogue-top">'
                                         f'<a class="button outline" href="{root}">← Back to {name}</a><h1>{name} catalogue</h1></div>'
                                         + listing(price, save_button, query=query, kalam=kalam))
    product_id = suffix.removeprefix('product/')
    if suffix.startswith('product/') and (p := next((p for p in (kalams() if kalam else catalogue())
                                                      if p['id'] == product_id and p['group'] in groups), None)):
        title, group, item = escape(p['name']), p['group'], public_product(p)
        front = p['rail'][0].get('detailSrc') if p.get('rail') else None
        resolution = f' srcset="{escape(front)}"' if front else ''
        return 200, p['name'], f'''
<section class="wrap stationery-detail">
  <a class="button outline stationery-product-back" data-stationery-product-back href="{group_url(group)}#stationery-products">← Back to {escape(groups[group][0])}</a>
  <nav class="stationery-trail" aria-label="Breadcrumb"><a href="{root}">{name}</a>
    <span aria-hidden="true">/</span><a href="{group_url(group)}">{escape(groups[group][0])}</a></nav>
  <div class="stationery-detail-grid">
    <div class="stationery-detail-image">
      <img src="{product_image(p)}"{resolution} alt="{title}" width="560" height="560" data-product-image>
      {discount_flag(item)}{save_button(item)}
    </div>
    <div><p class="stationery-kicker">{escape(p['type'])} · Demo catalogue</p><h1>{title}</h1>
      <p>{escape(p['description'])}</p>
      {prices(item, price)}
      <div class="stationery-detail-actions">{add_button(item)}</div>
    </div>
  </div>
</section>'''
    return 404, f'{name} page not found', (f'<section class="wrap page"><h1>{name} page not found</h1>'
                                         f'<a class="button outline" href="{root}">← Back to {name}</a></section>')
