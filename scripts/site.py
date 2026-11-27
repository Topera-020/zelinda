"""Gera um site estatico simples (prototipo) em build/site a partir de build/content."""
import os, re, html, json, shutil, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'build'); S = os.path.join(ROOT, 'docs')   # docs/ = pasta publicada pelo GitHub Pages
shutil.rmtree(S, ignore_errors=True); os.makedirs(S)
shutil.copytree(B + '/img', S + '/img')
if os.path.isdir(B + '/colorido'):
    shutil.copytree(B + '/colorido', S + '/colorido', ignore=shutil.ignore_patterns('*_comparacao.png'))
shutil.copy(ROOT + '/zelinda.jpeg', S + '/capa.jpg')   # capa do livro
# livro para baixar: capa como 1a pagina + livro.pdf (o livro.pdf original nao e alterado)
PDF = None
if os.path.exists(ROOT + '/livro.pdf'):
    import pymupdf
    doc = pymupdf.open(ROOT + '/livro.pdf'); r = doc[0].rect
    capa = pymupdf.Pixmap(ROOT + '/zelinda.jpeg')
    alt = r.width * capa.height / capa.width          # capa na largura da pagina; o que sobra em cima/embaixo e cortado
    doc.new_page(0, width=r.width, height=r.height).insert_image(
        pymupdf.Rect(0, (r.height - alt) / 2, r.width, (r.height + alt) / 2), filename=ROOT + '/zelinda.jpeg')
    m = doc.metadata
    doc.set_metadata({k: m.get(k) or '' for k in ('author', 'subject', 'keywords', 'creator', 'producer', 'creationDate', 'modDate')}
                     | {'title': 'Memórias e Receitas de Dona Zelinda'})
    doc.save(S + '/livro.pdf', garbage=3, deflate=True, no_new_id=True)
    PDF = (doc.page_count, os.path.getsize(S + '/livro.pdf') / 1e6)
    doc.close()
BAIXAR = 'href="livro.pdf" download="Memorias-e-Receitas-de-Dona-Zelinda.pdf"' if PDF else 'href="livro.html"'
open(S + '/.nojekyll', 'w').close()
E = html.escape


def inline(t):
    t = E(t)
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)


def parse(path):
    raw = open(path, encoding='utf-8').read()
    fm, corpo = raw.split('---\n', 2)[1:]
    meta = {}
    for l in fm.strip().splitlines():
        k, v = l.split(': ', 1)
        meta[k] = v
    meta['titulo'] = meta['titulo'].strip('"')
    meta['parte'] = meta['parte'].strip('"')
    meta['familiar'] = re.findall(r'"([^"]+)"', meta['familiar'])
    return meta, corpo


def corpo_html(corpo):
    out, blocos = [], [b.strip() for b in re.split(r'\n\s*\n', corpo) if b.strip()]
    i = 0
    while i < len(blocos):
        b = blocos[i]
        m = re.match(r'!\[\]\(/img/(img\d+)\.(\w+)\)', b)
        if m:
            nome, ext = m.groups()
            leg = ''
            if i + 1 < len(blocos) and blocos[i + 1].startswith('*Figura'):
                leg = f'<figcaption>{inline(blocos[i + 1].strip("*"))}</figcaption>'
                i += 1
            cor = f'colorido/{nome}.png'
            col = f'<img class="cor" src="{cor}" alt="" loading="lazy">' if os.path.exists(f'{S}/{cor}') else ''
            cls = ' colorir' if col else ''
            out.append(f'<figure class="ilus{cls}"><div class="moldura"><img class="traco" src="img/{nome}.{ext}" alt="" loading="lazy">{col}</div>{leg}</figure>')
        elif b.startswith('### '):
            out.append(f'<h3>{inline(b[4:])}</h3>')
        elif b.startswith('> '):
            out.append(f'<blockquote>{inline(b[2:])}</blockquote>')
        elif b.startswith('- '):
            out.append('<ul>' + ''.join(f'<li>{inline(l[2:])}</li>' for l in b.splitlines()) + '</ul>')
        elif b.startswith('*') and b.endswith('*'):
            out.append(f'<p class="leg">{inline(b)}</p>')
        else:
            out.append(f'<p>{inline(b)}</p>')
        i += 1
    return '\n'.join(out)


def poema_html(corpo):
    """Meus Netos: a legenda vira texto comum e o poema ganha formatacao propria."""
    blocos = [b.strip() for b in re.split(r'\n\s*\n', corpo) if b.strip()]
    intro = blocos[0].lstrip('> ').strip()
    out = [f'<p class="intro-poema"><em>{inline(intro)}</em></p><div class="poema">']
    assin = ''
    for b in blocos[1:]:
        if b.startswith('### '):
            assin = b[4:]
            continue
        tit = ''
        if b.startswith('A volta dos meus netos '):
            tit = '<h3 class="poema-tit">A volta dos meus netos</h3>'
            b = b[len('A volta dos meus netos '):]
        linhas = re.split(r'(?<=[,.?!])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕ])', b)
        out.append(tit + '<p class="estrofe">' + '<br>'.join(E(l) for l in linhas) + '</p>')
    out.append('</div>')
    if assin:
        out.append(f'<p class="assina">— {E(assin)}</p>')
    return '\n'.join(out)



FONTES = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Playball&display=swap" rel="stylesheet">'


def pagina(titulo, corpo, ativo=''):
    def nav(h, t, k):
        c = 'on' if ativo == k else ''
        return f'<a href="{h}" class="{c}">{t}</a>'
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(titulo)} — Zelinda</title>{FONTES}<link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="icon" href="favicon.ico" sizes="any"><link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="stylesheet" href="estilo.css"></head><body>
<div class="xadrez"></div>
<div class="topo"><header><a class="logo" href="index.html">Zelinda</a><button class="menu-btn" type="button" aria-label="Abrir menu" aria-expanded="false" aria-controls="menu"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#c8283a" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button><nav id="menu">{nav("receitas.html?t=receita","Receitas","r")}{nav("receitas.html?t=memoria","Memórias","m")}{nav("familiares.html","Por familiar","f")}{nav("musicas.html","Músicas","u")}{nav("fotos.html","Fotos","o")}{nav("livro.html","O livro","l")}</nav></header></div>
<main>{corpo}</main>
<footer><span class="coracao">♥</span> Memórias e Receitas de Dona Zelinda</footer><script src="app.js"></script></body></html>'''


itens = []
for p in sorted(glob.glob(B + '/content/*.md')):
    meta, corpo = parse(p)
    slug = os.path.basename(p)[:-3]
    texto = re.sub(r'[#>*!\[\]\-]|\(/img/[^)]*\)', ' ', corpo)
    itens.append(dict(slug=slug, texto=texto, corpo=corpo, **meta))
# pares memoria <-> receita: a receita fica ligada a memoria que vem antes dela no livro
por_ordem = sorted(itens, key=lambda x: int(x['ordem']))
atual = None
for it in por_ordem:
    it['liga'] = []
    if it['tipo'] == 'memoria':
        atual = it
    elif atual is not None:
        it['liga'].append(atual)
        atual['liga'].append(it)
for k, it in enumerate(por_ordem):
    it['ant'] = por_ordem[k - 1] if k > 0 else None
    it['prox'] = por_ordem[k + 1] if k + 1 < len(por_ordem) else None
itens.sort(key=lambda x: x['titulo'].lower())


def navegacao(it):
    a = f'<a class="nav-a" href="r-{it["ant"]["slug"]}.html"><small>← Anterior</small>{E(it["ant"]["titulo"])}</a>' if it['ant'] else '<span></span>'
    n = f'<a class="nav-p" href="r-{it["prox"]["slug"]}.html"><small>Próxima →</small>{E(it["prox"]["titulo"])}</a>' if it['prox'] else '<span></span>'
    return f'<nav class="passos">{a}{n}</nav>'


def botoes(it):
    if not it['liga']:
        return ''
    if it['tipo'] == 'receita':
        return ''.join(f'<a class="par" href="r-{o["slug"]}.html">Ler a história: {E(o["titulo"])}</a>' for o in it['liga'])
    return ''.join(f'<a class="par" href="r-{o["slug"]}.html">Ver a receita: {E(o["titulo"])}</a>' for o in it['liga'])


# musicas de Zelinda Gomes no YouTube: (titulo, id do video, capa em assets/musicas, historia do livro ligada)
MUSICAS = [
    ('Sorriso e um Abraço', 'S1gIQM2viv4', 'sorriso-e-um-abraco', None),
    ('Na Tesoura e no Canto', 'gtaIPdJ2Stc', 'na-tesoura-e-no-canto', None),
    ('A Lida do Nosso Chão', 'x5WvdiWxH5w', 'a-lida-do-nosso-chao', None),
    ('Festa no Jardim da Vovó', '0xmnJoMOeng', 'festa-no-jardim-da-vovo', None),
    ('A Nossa Zelinda Chegou', 'ZEE9Vb4bBRM', 'a-nossa-zelinda-chegou', None),
    ('Alho no Café', 'dNT0nZ7qB0E', 'alho-no-cafe', 'o-famoso-cafe-com-alho-servido-as-irmas'),
    ('Noite do Autógrafo', 'dSn8dAIi0AU', 'noite-do-autografo', None),
    ('O Sim de José Arnaldo', '3sbg6jiN7_c', 'o-sim-de-jose-arnaldo', 'o-doce-oficio-da-noiva-o-casamento-de-zelinda-e-jose-arnaldo'),
]
shutil.copytree(ROOT + '/assets/musicas', S + '/musicas')
POR_SLUG = {i['slug']: i for i in itens}


def player(t, vid, capa):
    """capa da musica; o video do YouTube so carrega quando a pessoa aperta o play"""
    return (f'<button class="yt" type="button" data-id="{vid}" aria-label="Tocar {E(t)}"><img src="musicas/{capa}.jpg" alt="" loading="lazy">'
            f'<span class="play"><svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true"><path d="M8 5v14l11-7z" fill="#fff"/></svg></span></button>')


def musica_card(m, com_historia=True):
    t, vid, capa, hist = m
    h = POR_SLUG.get(hist) if com_historia else None
    liga = f'<a href="r-{hist}.html">Da história: {E(h["titulo"])}</a> · ' if h else ''
    return (f'<div class="musica">{player(t, vid, capa)}<h2>{E(t)}</h2>'
            f'<p class="leg">{liga}<a href="https://youtu.be/{vid}" target="_blank" rel="noopener">ouvir no YouTube</a></p></div>')


def musica_da_historia(it):
    ms = [m for m in MUSICAS if m[3] == it['slug']]
    if not ms:
        return ''
    return '<section class="musica-hist"><h2 class="script">♪ A música desta história</h2>' + ''.join(musica_card(m, False) for m in ms) + '</section>'


def cap(it):
    if not it['parte']:
        return ''
    return f'<span class="parte">Capítulo: {E(it["parte"].rstrip(":"))}</span>'


for it in itens:
    fam = ''.join(f'<a class="selo" href="familiares.html#{E(f)}">♥ {E(f)}</a>' for f in it['familiar'])
    tag = 'Receita' if it['tipo'] == 'receita' else 'Memória'
    corpo = f'''<article class="item"><p class="trilha"><a href="index.html">Início</a> › <a href="receitas.html?t={it["tipo"]}">{tag}s</a></p>
<h1>{E(it["titulo"])}</h1><p class="meta">{cap(it)}{fam}</p>
{poema_html(it["corpo"]) if it["slug"] == "meus-netos" else corpo_html(it["corpo"])}{musica_da_historia(it)}<div class="pares">{botoes(it)}</div>{navegacao(it)}</article>'''
    open(f'{S}/r-{it["slug"]}.html', 'w', encoding='utf-8').write(pagina(it['titulo'], corpo))

idx = [dict(s=i['slug'], t=i['titulo'], k=i['tipo'], f=i['familiar'], x=re.sub(r'\s+', ' ', i['texto'])[:6000].lower()) for i in itens]
open(S + '/indice.js', 'w', encoding='utf-8').write('window.INDICE=' + json.dumps(idx, ensure_ascii=False) + ';')
nrec = sum(i['tipo'] == 'receita' for i in itens)
nmem = len(itens) - nrec


def primeira_img(i):
    m = re.search(r'!\[\]\(/img/(img\d+)\.(\w+)\)', i['corpo'])
    return f'img/{m.group(1)}.{m.group(2)}' if m else ''


def card(i):
    t = 'Receita' if i['tipo'] == 'receita' else 'Memória'
    im = primeira_img(i)
    foto = f'<span class="foto"><img src="{im}" alt="" loading="lazy"></span>' if im else '<span class="foto vazio">♥</span>'
    return f'<a class="card" href="r-{i["slug"]}.html">{foto}<span class="tipo">{t}</span><b>{E(i["titulo"])}</b></a>'


DIV = '<div class="div"><svg viewBox="0 0 320 32" width="320" height="32" aria-hidden="true"><path d="M4 16h122M194 16h122" stroke="#c9a24a" stroke-width="2" stroke-linecap="round"/><circle cx="134" cy="16" r="3" fill="#c9a24a"/><circle cx="186" cy="16" r="3" fill="#c9a24a"/><g transform="translate(147.2 3.6) scale(.8)"><path d="M16 28.5C4 20.5 1.5 14 1.5 9.8 1.5 5.4 4.8 2.5 8.6 2.5c3 0 5.6 1.7 7.4 4.6 1.8-2.9 4.4-4.6 7.4-4.6 3.8 0 7.1 2.9 7.1 7.3 0 4.2-2.5 10.7-14.5 18.7z" fill="#c8283a"/></g></svg></div>'

# destaques: itens com ilustracao, alternando memoria/receita, na ordem do livro
com_img = [i for i in por_ordem if primeira_img(i)]
destaque = []
for tipo in ('memoria', 'receita'):
    destaque += [i for i in com_img if i['tipo'] == tipo][:3]
destaque = sorted(destaque, key=lambda x: int(x['ordem']))

# frase do livro: primeira citacao de tamanho agradavel
frase = frase_de = ''
for i in por_ordem:
    for b in re.findall(r'^> (.+)$', i['corpo'], re.M):
        b = b.strip('“”" ')
        if 60 <= len(b) <= 170 and not frase:
            frase, frase_de = b, i['titulo']

# familiares com mais itens
cont = {}
for i in itens:
    for f in i['familiar']:
        cont[f] = cont.get(f, 0) + 1
chips = ''.join(f'<a class="chip" href="familiares.html#{E(f)}">♥ {E(f)} <small>{n}</small></a>' for f, n in sorted(cont.items(), key=lambda kv: (-kv[1], kv[0]))[:14])

home = f'''<section class="hero"><div class="hero-txt"><p class="script">Memórias e Receitas de</p><h1>Dona Zelinda</h1>
<p class="lead">Receitas de família, histórias da cozinha e os desenhos de quem viveu tudo isso.</p>
<form class="busca" action="receitas.html" method="get"><span class="campo"><input name="q" placeholder="Receita, ingrediente ou nome…" autocomplete="off" aria-label="Buscar receitas e memórias"></span><button>Buscar</button></form>
<p class="numeros"><a href="receitas.html?t=receita"><b>{nrec}</b> receitas</a><a href="receitas.html?t=memoria"><b>{nmem}</b> memórias</a><a href="familiares.html"><b>{len(cont)}</b> familiares</a><a href="musicas.html"><b>{len(MUSICAS)}</b> músicas</a></p></div>
<div class="hero-img"><img src="capa.jpg" alt="Capa do livro"><span class="selo-hero">♥ feito com amor</span></div></section>
{DIV}
<section><h2 class="script sec">Para começar</h2><div class="cards">{''.join(card(i) for i in destaque)}</div>
<p class="mais"><a class="botao" href="receitas.html">Ver todas as receitas e memórias</a></p></section>
{DIV}
<section><h2 class="script sec sub">Quem aparece nas histórias</h2><p class="chips">{chips}<a class="chip todos" href="familiares.html">ver todos os {len(cont)} →</a></p></section>
<section class="faixa"><blockquote class="frase">“{E(frase)}”<cite>do capítulo “{E(frase_de)}”</cite></blockquote></section>
<section class="livro-cta"><img src="capa.jpg" alt="" class="mini"><div><h2 class="script">Leve o livro com você</h2><p>Todas as histórias e receitas em um só arquivo, para ler no sofá ou imprimir para a cozinha.</p><a class="botao" {BAIXAR}>Baixar o livro (PDF)</a></div></section>'''
open(S + '/index.html', 'w', encoding='utf-8').write(pagina('Início', home))

lista = '''<h1 class="script">Receitas e memórias</h1><form class="busca" onsubmit="return false"><input id="q" placeholder="Buscar…" autocomplete="off"></form>
<p class="filtros"><button data-t="">Tudo</button><button data-t="receita">Receitas</button><button data-t="memoria">Memórias</button></p><p id="cont" class="leg"></p><ul id="lista" class="lista"></ul>'''
open(S + '/receitas.html', 'w', encoding='utf-8').write(pagina('Receitas', '<script src="indice.js"></script><div class="item largo">' + lista + '</div>', 'r'))

fams = {}
for i in itens:
    for f in (i['familiar'] or ['Sem marcação']):
        fams.setdefault(f, []).append(i)


def secao(f, v):
    li = ''.join(f'<li><a href="r-{i["slug"]}.html">{E(i["titulo"])}</a></li>' for i in v)
    return f'<section id="{E(f)}"><h2>♥ {E(f)} <small>({len(v)})</small></h2><ul class="lista">{li}</ul></section>'


corpo = '<h1 class="script">Por familiar</h1>' + ''.join(
    secao(f, v) for f, v in sorted(fams.items(), key=lambda kv: (kv[0] == 'Sem marcação', kv[0])))
open(S + '/familiares.html', 'w', encoding='utf-8').write(pagina('Por familiar', '<div class="item largo">' + corpo + '</div>', 'f'))
if PDF:
    mb = f'{PDF[1]:.1f}'.replace('.', ',')
    livro = (f'<h1 class="script" style="text-align:center">O livro</h1><section class="livro-cta"><img src="capa.jpg" alt="Capa do livro" class="mini"><div>'
             f'<h2 class="script">Leve o livro com você</h2><p>Todas as histórias e receitas de Dona Zelinda em um só arquivo, para ler no sofá ou imprimir para a cozinha.</p>'
             f'<p class="leg">PDF · {PDF[0]} páginas · {mb} MB</p>'
             f'<p><a class="botao" {BAIXAR}>Baixar o livro (PDF)</a></p><p><a href="livro.pdf" target="_blank" rel="noopener">ou ler no navegador</a></p></div></section>')
else:
    livro = '<div class="item"><h1 class="script">O livro</h1><p>Aqui ficará o botão para baixar o livro completo em PDF.</p><p><a class="botao" href="#">Baixar PDF (em breve)</a></p></div>'
open(S + '/livro.html', 'w', encoding='utf-8').write(pagina('O livro', livro, 'l'))

musicas = (f'<h1 class="script" style="text-align:center">Músicas</h1><p class="lead" style="text-align:center">As músicas de Zelinda Gomes. Aperte o play na capa para ouvir.</p>'
           f'<p style="text-align:center;margin:18px 0 34px"><a class="botao" style="display:inline-block" href="fotos.html">▶ Ouvir todas com as fotos do livro</a></p>'
           f'<div class="musicas">{"".join(musica_card(m) for m in MUSICAS)}</div>')
open(S + '/musicas.html', 'w', encoding='utf-8').write(pagina('Músicas', musicas, 'u'))

# pagina Fotos: desenhos do livro passando em loop, com as musicas tocando uma atras da outra
fotos = [dict(src='capa.jpg', t='Memórias e Receitas de Dona Zelinda', s='')]
for it in por_ordem:
    for nome, ext in re.findall(r'!\[\]\(/img/(img\d+)\.(\w+)\)', it['corpo']):
        if os.path.exists(f'{S}/img/{nome}.{ext}'):
            fotos.append(dict(src=f'img/{nome}.{ext}', t=it['titulo'], s=it['slug']))
show = dict(fotos=fotos, musicas=[dict(src=f'musicas/{c}.mp3', t=t, capa=f'musicas/{c}.jpg') for t, _, c, _ in MUSICAS])
IC = lambda d, extra='', t=22: f'<svg viewBox="0 0 24 24" width="{t}" height="{t}" aria-hidden="true" {extra}><path d="{d}"/></svg>'
fotos_html = f'''<h1 class="script" style="text-align:center">Fotos e músicas</h1>
<div class="show" id="show"><div class="tela">
<figure class="slide on"><img src="capa.jpg" alt=""><figcaption>{E(fotos[0]["t"])}</figcaption></figure><figure class="slide"><img alt=""><figcaption></figcaption></figure>
<button class="comecar" type="button"><span class="play">{IC("M8 5v14l11-7z", 'fill="#fff"', 40)}</span>Começar</button></div>
<div class="barra"><img class="disco" src="{show["musicas"][0]["capa"]}" alt=""><div class="agora"><small>Tocando</small><b id="show-musica">{E(MUSICAS[0][0])}</b></div>
<button type="button" data-acao="ant" aria-label="Música anterior">{IC("M6 5h2v14H6zM9.5 12 19 5v14z")}</button>
<button type="button" data-acao="play" aria-label="Tocar">{IC("M8 5v14l11-7z", 'class="i-play"')}{IC("M7 5h4v14H7zM13 5h4v14h-4z", 'class="i-pausa"')}</button>
<button type="button" data-acao="prox" aria-label="Próxima música">{IC("M16 5h2v14h-2zM14.5 12 5 5v14z")}</button>
<button type="button" data-acao="tela" aria-label="Tela cheia">{IC("M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5", 'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"')}</button></div>
<audio id="som" preload="none"></audio></div>
<p class="leg" style="text-align:center;margin-top:16px">{len(fotos)} desenhos do livro e {len(MUSICAS)} músicas, em loop. Dica: na TV ou no computador, use a tela cheia.</p>
<script>window.SHOW={json.dumps(show, ensure_ascii=False).replace("</", "<\\/")}</script>'''
open(S + '/fotos.html', 'w', encoding='utf-8').write(pagina('Fotos e músicas', fotos_html, 'o'))


# icone do site: coracao vermelho
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><path d="M16 28.5C4 20.5 1.5 14 1.5 9.8 1.5 5.4 4.8 2.5 8.6 2.5c3 0 5.6 1.7 7.4 4.6 1.8-2.9 4.4-4.6 7.4-4.6 3.8 0 7.1 2.9 7.1 7.3 0 4.2-2.5 10.7-14.5 18.7z" fill="#d6283b"/><ellipse cx="9.2" cy="9" rx="3.2" ry="2" transform="rotate(-35 9.2 9)" fill="#fff" opacity=".55"/></svg>'
open(S + '/favicon.svg', 'w', encoding='utf-8').write(SVG)
from PIL import Image, ImageDraw
import math
def coracao(n):
    g = 8 * n; im = Image.new('RGBA', (g, g), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = []
    for k in range(720):
        t = k / 720 * 2 * math.pi
        x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((g / 2 + x * g / 36, g * 0.46 - y * g / 36))
    d.polygon(pts, fill=(214, 40, 59, 255))
    d.ellipse([g * .22, g * .2, g * .36, g * .3], fill=(255, 255, 255, 140))
    return im.resize((n, n), Image.LANCZOS)
coracao(256).save(S + '/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
fundo = Image.new('RGBA', (180, 180), (249, 235, 205, 255)); fundo.alpha_composite(coracao(140), (20, 24)); fundo.convert('RGB').save(S + '/apple-touch-icon.png')

CSS = '''
:root{--creme:#f9ebcd;--papel:#fdf4df;--verm:#c8283a;--vermesc:#9e1d2c;--ouro:#c9a24a;--tinta:#2b211c;--suave:#6b5a45}
*{box-sizing:border-box}body{margin:0;overflow-x:hidden;background:var(--creme);color:var(--tinta);font:18px/1.45 Lora,Georgia,serif}p{margin:0 0 .65em}li{margin:0}ul{margin:.4em 0 .8em;padding-left:1.3em}
.xadrez{height:22px;background:repeating-conic-gradient(var(--verm) 0 25%,#fff 0 50%) 0 0/22px 22px;border-bottom:3px solid var(--ouro)}
.menu-btn{display:none;background:var(--papel);border:2px solid var(--verm);border-radius:10px;padding:6px 8px;cursor:pointer;line-height:0}.topo{background:var(--papel);border-bottom:2px solid var(--ouro)}header{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center;justify-content:space-between;max-width:1080px;margin:0 auto;padding:18px 20px}
.logo{font:44px Playball,cursive;color:var(--verm);text-decoration:none}nav a{margin-left:20px;color:var(--tinta);text-decoration:none;border-bottom:2px solid transparent}nav a:hover,nav a.on{border-color:var(--verm);color:var(--verm)}
main{max-width:1080px;margin:0 auto;padding:30px 20px 50px}a{color:var(--vermesc)}
.script{font-family:Playball,cursive;color:var(--verm);font-weight:400}h1.script{font-size:46px;margin:.3em 0}
h1{font:400 44px/1.15 Lora,serif;margin:.2em 0}h2{font-size:26px}h3{font-size:20px;color:var(--vermesc);margin:1.4em 0 .3em;border-bottom:2px dotted var(--ouro);padding-bottom:4px}
.hero{display:grid;grid-template-columns:1.5fr .7fr;gap:30px;align-items:center;margin:0 0 34px;padding:38px 42px;background:var(--papel);border:2px solid var(--verm);border-radius:18px;outline:4px solid var(--creme);box-shadow:0 0 0 6px var(--ouro),0 14px 30px rgba(43,33,28,.18)}
.hero .script{font-size:34px;margin:0}.hero h1{font:400 88px/1 Playball,cursive;color:var(--verm);margin:0 0 .2em}
.hero-img img{display:block;width:100%;height:auto;border:3px solid var(--ouro);border-radius:14px;outline:6px solid var(--creme);box-shadow:0 0 0 8px var(--verm)}
.busca{display:flex;gap:8px;margin:18px 0}.busca input{flex:1;padding:12px 16px;font:inherit;border:2px solid var(--verm);border-radius:999px;background:var(--papel)}
.busca button,.botao{background:var(--verm);color:#fff;border:0;border-radius:999px;padding:12px 22px;font:inherit;text-decoration:none;cursor:pointer}.botao:hover,.busca button:hover{background:var(--vermesc)}
.atalhos a{margin-right:16px}.atalhos .botao{margin:0}
form.busca{position:relative}.musicas{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:22px;margin-top:20px}
.musica{background:var(--papel);border:2px solid var(--verm);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:6px}.musica h2{font:400 28px/1.15 Playball,cursive;color:var(--verm);margin:6px 0 0}.musica .leg{margin:0;font-size:14px}
.yt{position:relative;display:block;width:100%;aspect-ratio:1;padding:0;border:0;border-radius:10px;overflow:hidden;cursor:pointer;background:#2b211c}.yt img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .4s}.yt:hover img{transform:scale(1.03)}
.yt .play{position:absolute;left:50%;top:50%;width:66px;height:66px;margin:-33px 0 0 -33px;border-radius:50%;background:var(--verm);box-shadow:0 3px 0 var(--vermesc),0 0 0 4px rgba(255,255,255,.85);display:flex;align-items:center;justify-content:center;padding-left:4px;transition:transform .2s}.yt:hover .play,.yt:focus-visible .play{transform:scale(1.08)}
.yt iframe{display:block;width:100%;height:100%;border:0}
.musica-hist{margin:30px 0 6px;padding-top:18px;border-top:3px dotted var(--ouro)}.musica-hist>h2{font-size:30px;margin:0 0 12px;color:var(--verm)}.musica-hist .musica{max-width:360px}
.show{max-width:980px;margin:0 auto;background:var(--papel);border:2px solid var(--verm);border-radius:18px;outline:4px solid var(--creme);box-shadow:0 0 0 6px var(--ouro);overflow:hidden}
.tela{position:relative;height:min(68vh,640px);background:#fffdf8}
.slide{position:absolute;inset:0;margin:0;display:flex;flex-direction:column;align-items:center;padding:18px 18px 12px;opacity:0;transition:opacity 1.2s ease}.slide.on{opacity:1}
.slide img{flex:1;min-height:0;width:100%;object-fit:contain;mix-blend-mode:multiply}.slide figcaption{margin-top:10px;font:italic 17px/1.3 Lora,serif;color:var(--suave);text-align:center}.slide figcaption a{color:var(--verm)}
.comecar{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;background:rgba(253,248,238,.6);border:0;font:400 40px Playball,cursive;color:var(--verm);cursor:pointer}
.comecar .play{width:96px;height:96px;border-radius:50%;background:var(--verm);display:flex;align-items:center;justify-content:center;padding-left:6px;box-shadow:0 4px 0 var(--vermesc),0 0 0 6px rgba(255,255,255,.9);transition:transform .2s}.comecar:hover .play{transform:scale(1.07)}.show.iniciado .comecar{display:none}
.barra{display:flex;align-items:center;gap:10px;padding:10px 14px;border-top:2px dotted var(--ouro)}.disco{width:50px;height:50px;border-radius:8px;object-fit:cover;flex:none}
.agora{flex:1;min-width:0}.agora small{display:block;font-size:12px;color:var(--suave);text-transform:uppercase;letter-spacing:.08em}.agora b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--verm);font-weight:600}
.barra button{flex:none;width:44px;height:44px;border-radius:50%;border:2px solid var(--verm);background:var(--papel);color:var(--verm);fill:currentColor;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0}.barra button:hover{background:var(--creme)}
.barra button[data-acao=play]{width:50px;height:50px;background:var(--verm);color:#fff}.barra button[data-acao=play]:hover{background:var(--vermesc)}
.i-pausa{display:none}.show.tocando .i-pausa{display:block}.show.tocando .i-play{display:none}
.show:fullscreen{max-width:none;border:0;border-radius:0;outline:0;box-shadow:none;display:flex;flex-direction:column}.show:fullscreen .tela{height:auto;flex:1}.show:fullscreen .slide figcaption{font-size:22px}
.campo{flex:1;min-width:0;display:flex}.campo input{width:100%}
.sugest{position:absolute;z-index:20;top:calc(100% + 6px);left:0;right:0;margin:0;padding:6px;list-style:none;background:var(--papel);border:2px solid var(--verm);border-radius:14px;box-shadow:0 12px 26px rgba(43,33,28,.2);max-height:min(60vh,430px);overflow:auto;text-align:left}
.sugest a{display:block;padding:7px 12px;border-radius:10px;text-decoration:none;color:var(--tinta);font-size:16px;line-height:1.3}
.sugest small{color:var(--suave);font-size:13px}.sg-tipo{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--suave)}
.sugest li.on a,.sugest a:hover{background:var(--verm);color:#fff}.sugest li.on small,.sugest a:hover small,.sugest li.on .sg-tipo,.sugest a:hover .sg-tipo{color:#fff}
.sg-todos{border-top:1px dotted var(--ouro);margin-top:4px;padding-top:4px}.sg-todos a{color:var(--verm);font-weight:600}.sg-vazio{padding:8px 12px;color:var(--suave);font-size:16px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}@media(max-width:900px){.cards{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.cards{grid-template-columns:1fr}}.card{background:var(--papel);border:2px solid var(--verm);border-radius:12px;padding:16px;text-decoration:none;color:var(--tinta);display:flex;flex-direction:column;gap:6px}.card:hover{border-color:var(--ouro);transform:translateY(-2px)}
.tipo{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--suave)}.leg{color:var(--suave);font-size:15px}
.item{max-width:760px;margin:0 auto;background:var(--papel);border:2px solid var(--verm);border-radius:14px;padding:10px 40px 40px;outline:4px solid var(--creme);box-shadow:0 0 0 6px var(--ouro)}
.item.largo{max-width:960px}.item h2{margin-bottom:.2em}
.item h1{font-family:Playball,cursive;color:var(--verm);font-size:50px}.trilha{font-size:14px;color:var(--suave)}.meta{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.selo{background:var(--verm);color:#fff;border-radius:999px;padding:2px 14px;font-size:15px;text-decoration:none}.parte{color:var(--suave);font-size:14px;font-style:italic}
a.par{display:block;margin:10px 0 0;padding:12px 18px;border:2px solid var(--verm);background:var(--verm);color:#fff;border-radius:12px;text-decoration:none;font-weight:600}a.par:hover{background:var(--vermesc)}a.par::after{content:' →'}
.pares{margin-top:28px}.passos{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;padding-top:14px;border-top:3px dotted var(--ouro)}.passos a{margin:0;display:block;padding:12px 16px;border:2px solid var(--verm);border-radius:12px;text-decoration:none;color:var(--tinta);background:var(--papel)}.passos a:hover{background:var(--verm);color:#fff}.passos small{display:block;color:var(--suave);font-size:13px}.passos a:hover small{color:#fff}.nav-p{text-align:right}
blockquote{margin:1em 0;padding:6px 18px;border-left:4px solid var(--verm);font-style:italic;background:var(--creme)}
.ilus{margin:24px 0;text-align:center}.moldura{position:relative;display:inline-block;max-width:100%;border:2px solid var(--verm);border-radius:12px;padding:10px;background:var(--papel)}
.ilus img{display:block;max-width:100%;max-height:520px;mix-blend-mode:multiply}.cor{position:absolute;inset:10px;width:calc(100% - 20px);height:calc(100% - 20px);object-fit:contain;opacity:0;transition:opacity .9s ease}
.colorir:hover .cor,.colorir.ativo .cor{opacity:1}figcaption{color:var(--suave);font-size:14px;margin-top:6px;font-style:italic}
.lista{list-style:none;padding:0;columns:2 280px;column-gap:30px}.lista li{padding:6px 0;border-bottom:1px dotted var(--ouro);break-inside:avoid}.lista small{color:var(--suave)}
.filtros button{background:var(--papel);border:2px solid var(--verm);color:var(--verm);border-radius:999px;padding:4px 16px;font:inherit;cursor:pointer;margin-right:6px}.filtros button.on{background:var(--verm);color:#fff}
.lead{font-size:20px;color:var(--suave)}.numeros{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}.numeros a{background:var(--papel);border:2px solid var(--verm);border-radius:999px;padding:6px 16px;text-decoration:none;color:var(--tinta)}.numeros b{color:var(--verm);font-size:22px}.numeros a:hover{background:var(--verm);color:#fff}.numeros a:hover b{color:#fff}
.hero-img{position:relative;max-width:300px;width:100%;justify-self:center;transform:rotate(2.5deg)}.selo-hero{position:absolute;left:-14px;bottom:26px;background:var(--verm);color:#fff;font:22px Playball,cursive;padding:6px 18px;border-radius:999px;transform:rotate(-5deg);box-shadow:0 3px 0 var(--vermesc)}
.sec{font-size:40px;text-align:center;margin:.2em 0 .6em}.chips{justify-content:center}.chip.todos{background:var(--verm);color:#fff}.sub{text-decoration:underline solid var(--verm) 3px;text-underline-offset:9px}
.div{text-align:center;margin:8px 0 22px}
.mais{text-align:center;margin:26px 0 34px}
.card .foto{display:flex;align-items:center;justify-content:center;height:170px;background:var(--papel);border-radius:8px;overflow:hidden}.card .foto img{max-height:100%;max-width:100%;object-fit:contain;mix-blend-mode:multiply;transition:transform .5s}.card:hover .foto img{transform:scale(1.05)}.card .vazio{font-size:46px;color:var(--verm)}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:var(--papel);border:2px solid var(--verm);border-radius:999px;padding:4px 14px;text-decoration:none;color:var(--tinta)}.chip small{color:var(--suave)}.chip:hover{background:var(--verm);color:#fff}.chip:hover small{color:#fff}
.faixa{margin:44px calc(50% - 50vw);padding:50px 20px;background:var(--verm) repeating-conic-gradient(rgba(255,255,255,.12) 0 25%,transparent 0 50%) 0 0/36px 36px;text-align:center;border-top:3px solid var(--ouro);border-bottom:3px solid var(--ouro)}
.frase{max-width:760px;margin:0 auto;padding:26px 30px;background:var(--papel);border:3px double var(--ouro);border-radius:12px;font:italic 26px/1.4 Lora,serif;color:var(--vermesc)}.frase cite{display:block;margin-top:12px;font:15px Lora,serif;color:var(--suave)}
.livro-cta{display:grid;grid-template-columns:200px 1fr;gap:34px;align-items:center;max-width:820px;margin:0 auto;padding:30px 36px;background:var(--papel);border:2px solid var(--verm);border-radius:18px;outline:4px solid var(--creme);box-shadow:0 0 0 6px var(--ouro)}.livro-cta h2{font-size:38px;margin:0 0 .2em}.livro-cta .mini{display:block;width:200px;height:auto;border:2px solid var(--ouro);border-radius:10px;box-shadow:0 0 0 5px var(--verm)}
@media(max-width:700px){.hero{padding:22px 20px}.hero h1{font-size:60px}.hero-img{transform:none}}@media(max-width:600px){.livro-cta{grid-template-columns:100px 1fr;padding:18px}.livro-cta .mini{width:100px}.selo-hero{left:8px}}
footer{text-align:center;color:var(--suave);padding:24px;border-top:3px solid var(--ouro)}.coracao{color:var(--verm)}
@media(max-width:760px){.hero{grid-template-columns:1fr}.hero h1{font-size:56px}.item{padding:6px 18px 28px}.item h1{font-size:38px}h1{font-size:34px}}
.intro-poema{color:var(--suave);text-align:center;margin:18px 0 6px}.poema{margin:10px auto 0;max-width:460px;text-align:center;font:italic 20px/1.55 Lora,serif;color:var(--vermesc);padding:10px 0 4px;border-top:2px dotted var(--ouro);border-bottom:2px dotted var(--ouro)}.estrofe{margin:0 0 1.1em}.poema-tit{font:400 32px Playball,cursive;color:var(--verm);border:0;margin:1.2em 0 .4em}.assina{text-align:right;font:26px Playball,cursive;color:var(--verm);margin:10px 0 0}
/* ---- mobile ---- */
@media(max-width:700px){
header{padding:12px 16px;gap:2px}.logo{font-size:36px}
header{flex-wrap:wrap}.menu-btn{display:block}header nav{display:none;flex-direction:column;width:100%;gap:0;border-top:2px dotted var(--ouro);margin-top:8px}header.aberto nav{display:flex}header nav a{margin:0;padding:12px 4px;font-size:18px;border-bottom:1px dotted var(--ouro)}header nav a:last-child{border-bottom:0}
main{padding:20px 14px 40px}
.hero{grid-template-columns:minmax(0,1fr);gap:22px;padding:22px 18px}.hero>*{min-width:0}
.hero-img{max-width:210px}
.busca{gap:6px}.busca input{min-width:0;padding:11px 14px}.busca button{padding:11px 16px}
.hero h1{font-size:56px}.hero .script{font-size:26px}.lead{font-size:17px}.numeros a{padding:4px 12px}
.sec{font-size:32px}
.cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.card{padding:10px}.card .foto{height:110px}.card b{font-size:15px;line-height:1.3}
.frase{font-size:19px;padding:18px}
.livro-cta{grid-template-columns:1fr;text-align:center;justify-items:center;padding:22px 18px;gap:16px}.livro-cta .mini{width:120px}.livro-cta h2{font-size:32px;line-height:1.2}
.botao{white-space:nowrap}
.item{padding:6px 16px 26px}.item h1{font-size:34px}
.passos{grid-template-columns:1fr}.nav-p{text-align:left}
.lista{columns:1}
.tela{height:60vh}.slide{padding:12px 10px 8px}.slide figcaption{font-size:15px}.barra{gap:6px;padding:8px 10px}.disco{width:40px;height:40px}.barra button{width:38px;height:38px}.barra button[data-acao=play]{width:44px;height:44px}.comecar{font-size:32px}
.musicas{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.musica{padding:8px}.musica h2{font-size:21px}.yt .play{width:48px;height:48px;margin:-24px 0 0 -24px}.yt .play svg{width:22px;height:22px}
.hero-img{transform:none}
}
@media(prefers-reduced-motion:reduce){.cor{transition:none}}
'''
open(S + '/estilo.css', 'w', encoding='utf-8').write(CSS)

JS = r'''
(function(){
var mb=document.querySelector('.menu-btn');if(mb){mb.addEventListener('click',function(){var h=mb.closest('header'),a=h.classList.toggle('aberto');mb.setAttribute('aria-expanded',a);mb.setAttribute('aria-label',a?'Fechar menu':'Abrir menu')})}
var fs=document.querySelectorAll('.colorir');
if('IntersectionObserver' in window&&fs.length){var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&matchMedia('(hover:none)').matches)e.target.classList.add('ativo')})},{threshold:.6});fs.forEach(function(f){o.observe(f);f.addEventListener('click',function(){f.classList.toggle('ativo')})})}
document.querySelectorAll('.yt').forEach(function(b){b.addEventListener('click',function(){
var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0';
f.title=b.getAttribute('aria-label');f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;
var d=document.createElement('div');d.className='yt';d.appendChild(f);b.replaceWith(d)})});
var sh=document.getElementById('show');
if(sh&&window.SHOW){var F=SHOW.fotos,M=SHOW.musicas,som=document.getElementById('som'),sl=sh.querySelectorAll('.slide'),fi=0,mi=0,cam=0,timer=null,toca=false,trava=null;
var mostra=function(k){fi=(k+F.length)%F.length;var a=sl[cam],b=sl[1-cam],f=F[fi],im=b.querySelector('img');
im.onload=function(){a.classList.remove('on');b.classList.add('on');cam=1-cam};im.src=f.src;
b.querySelector('figcaption').innerHTML=f.s?'<a href="r-'+f.s+'.html">'+esc(f.t)+'</a>':esc(f.t);
(new Image()).src=F[(fi+1)%F.length].src};
var relogio=function(){clearInterval(timer);if(toca)timer=setInterval(function(){mostra(fi+1)},7000)};
var musica=function(k){mi=(k+M.length)%M.length;som.src=M[mi].src;document.getElementById('show-musica').textContent=M[mi].t;sh.querySelector('.disco').src=M[mi].capa;if(toca)som.play().catch(function(){})};
var tocar=function(){toca=true;sh.classList.add('tocando','iniciado');if(!som.src)musica(mi);som.play().catch(function(){});relogio();
sh.querySelector('[data-acao=play]').setAttribute('aria-label','Pausar');if(navigator.wakeLock)navigator.wakeLock.request('screen').then(function(l){trava=l}).catch(function(){})};
var pausar=function(){toca=false;sh.classList.remove('tocando');som.pause();relogio();sh.querySelector('[data-acao=play]').setAttribute('aria-label','Tocar');if(trava){trava.release();trava=null}};
som.addEventListener('ended',function(){musica(mi+1)});
sh.querySelector('.comecar').addEventListener('click',tocar);
sh.querySelectorAll('.barra button').forEach(function(b){b.addEventListener('click',function(){var a=b.dataset.acao;
if(a==='play')toca?pausar():tocar();else if(a==='ant')musica(mi-1);else if(a==='prox')musica(mi+1);
else if(a==='tela'){if(document.fullscreenElement)document.exitFullscreen();else if(sh.requestFullscreen)sh.requestFullscreen()}})});
if(!sh.requestFullscreen)sh.querySelector('[data-acao=tela]').hidden=true;
document.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT')return;if(e.key==='ArrowRight'){mostra(fi+1);relogio()}else if(e.key==='ArrowLeft'){mostra(fi-1);relogio()}});
document.addEventListener('visibilitychange',function(){if(toca&&!trava&&document.visibilityState==='visible'&&navigator.wakeLock)navigator.wakeLock.request('screen').then(function(l){trava=l}).catch(function(){})})}
var bi=document.querySelector('form.busca[action] input');
if(bi){var bf=bi.form,box=document.createElement('ul'),sel=-1,opts=[],pedido=false;
box.className='sugest';box.id='sugest';box.setAttribute('role','listbox');box.hidden=true;bi.parentNode.appendChild(box);
bi.setAttribute('role','combobox');bi.setAttribute('aria-autocomplete','list');bi.setAttribute('aria-controls','sugest');bi.setAttribute('aria-expanded','false');
var carregar=function(){if(window.INDICE||pedido)return;pedido=true;var s=document.createElement('script');s.src='indice.js';s.onload=sugerir;document.head.appendChild(s)};
var fechar=function(){box.hidden=true;sel=-1;bi.setAttribute('aria-expanded','false');bi.removeAttribute('aria-activedescendant')};
var marcar=function(){opts.forEach(function(a,k){a.parentNode.classList.toggle('on',k===sel);a.parentNode.setAttribute('aria-selected',k===sel)});
if(sel>-1){bi.setAttribute('aria-activedescendant',opts[sel].parentNode.id);opts[sel].scrollIntoView({block:'nearest'})}else bi.removeAttribute('aria-activedescendant')};
var sugerir=function(){var v=bi.value.trim(),t=norm(v);if(!t||!window.INDICE){fechar();return}
var r=window.INDICE.map(function(i){var a=norm(i.t),p=a.indexOf(t),n=p===0?0:p>-1?1:norm(i.f.join(' ')).indexOf(t)>-1?2:norm(i.x).indexOf(t)>-1?3:-1;return{i:i,n:n}}).filter(function(o){return o.n>-1});
r.sort(function(a,b){return a.n-b.n});
box.innerHTML=r.length?r.slice(0,8).map(function(o,k){var i=o.i;return'<li id="sg'+k+'" role="option"><a href="r-'+i.s+'.html"><span class="sg-tipo">'+(i.k==='receita'?'Receita':'Memória')+'</span>'+esc(i.t)+(i.f.length?' <small>♥ '+esc(i.f.join(', '))+'</small>':'')+'</a></li>'}).join('')
+'<li id="sgt" class="sg-todos" role="option"><a href="receitas.html?q='+encodeURIComponent(v)+'">Ver '+(r.length===1?'o resultado':'todos os '+r.length+' resultados')+' →</a></li>'
:'<li class="sg-vazio">Nada encontrado para “'+esc(v)+'”</li>';
opts=[].slice.call(box.querySelectorAll('a'));sel=-1;marcar();box.hidden=false;bi.setAttribute('aria-expanded','true')};
bi.addEventListener('input',function(){carregar();sugerir()});
bi.addEventListener('focus',function(){carregar();if(bi.value.trim())sugerir()});
bi.addEventListener('keydown',function(e){if(e.key==='Escape'){fechar();return}
if(box.hidden||!opts.length)return;
if(e.key==='ArrowDown'){e.preventDefault();sel=sel+1<opts.length?sel+1:0;marcar()}
else if(e.key==='ArrowUp'){e.preventDefault();sel=sel>0?sel-1:opts.length-1;marcar()}
else if(e.key==='Enter'&&sel>-1){e.preventDefault();location.href=opts[sel].href}});
document.addEventListener('click',function(e){if(!bf.contains(e.target))fechar()})}
var L=document.getElementById('lista');if(!L||!window.INDICE)return;
var q=document.getElementById('q'),cont=document.getElementById('cont'),tipo='';
var p=new URLSearchParams(location.search);q.value=p.get('q')||'';tipo=p.get('t')||'';
function norm(s){return s.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase()}
function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function render(){var t=norm(q.value.trim()),r=window.INDICE.filter(function(i){return(!tipo||i.k===tipo)&&(!t||norm(i.t+' '+i.f.join(' ')+' '+i.x).indexOf(t)>-1)});
L.innerHTML=r.map(function(i){return'<li><a href="r-'+i.s+'.html">'+esc(i.t)+'</a>'+(i.f.length?' <small>♥ '+esc(i.f.join(', '))+'</small>':'')+'</li>'}).join('');
cont.textContent=r.length+' resultado'+(r.length===1?'':'s');
document.querySelectorAll('.filtros button').forEach(function(b){b.classList.toggle('on',b.dataset.t===tipo)})}
q.addEventListener('input',render);document.querySelectorAll('.filtros button').forEach(function(b){b.addEventListener('click',function(){tipo=b.dataset.t;render()})});render();
})();
'''
open(S + '/app.js', 'w', encoding='utf-8').write(JS)
print(len(itens), 'paginas em', S)
