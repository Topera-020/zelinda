"""Prototipo: livro.docx -> markdown por item + imagens + pagina de revisao."""
import docx, re, os, html, unicodedata, shutil, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build')
# marcacoes ja revisadas a mao (revisado: true) sobrevivem a novas extracoes
REVISADOS = {}
if os.path.isdir(OUT + '/content'):
    for f in os.listdir(OUT + '/content'):
        txt = open(os.path.join(OUT, 'content', f), encoding='utf-8').read()
        if re.search(r'^revisado: true', txt, re.M):
            REVISADOS[f[:-3]] = re.search(r'^familiar: .*$', txt, re.M).group(0)
for sub in ('content', 'img'): shutil.rmtree(OUT + '/' + sub, ignore_errors=True)
os.makedirs(OUT + '/content'); os.makedirs(OUT + '/img')
d = docx.Document(os.path.join(ROOT, 'livro.docx'))

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60] or 'item'

import json
PESSOAS = {k: v for k, v in json.load(open(os.path.join(ROOT, 'familia.json'), encoding='utf-8')).items() if not k.startswith('_')}
def sem_acento(t): return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
def familiar(texto):
    """pessoas de familia.json citadas no titulo ou no texto, na ordem em que aparecem (Zelinda nunca entra)"""
    t = sem_acento(texto); achados = []
    for nome, apelidos in PESSOAS.items():
        pos = [m.start() for a in apelidos for m in re.finditer(r'\b' + re.escape(sem_acento(a)) + r'\b', t)]
        if pos: achados.append((min(pos), nome))
    return [n for _, n in sorted(achados)]

from PIL import Image
import numpy as np
vazias = []
def em_branco(caminho):
    x = np.array(Image.open(caminho).convert('RGBA')); op = x[..., 3] > 10
    return not (((x[..., :3].mean(axis=2) < 200) & op).mean() > 0.003)

# --- imagens: salvar na ordem do documento
img_n = 0
def salvar_imgs(p):
    global img_n
    nomes = []
    for rid in p._p.xpath('.//a:blip/@r:embed'):
        part = d.part.related_parts[rid]
        img_n += 1
        ext = os.path.splitext(part.partname)[1] or '.bin'
        nome = f'img{img_n:03d}{ext}'
        caminho = os.path.join(OUT, 'img', nome)
        open(caminho, 'wb').write(part.blob)
        if em_branco(caminho):          # imagem toda branca/vazia: nao entra no site
            os.remove(caminho); vazias.append(nome); continue
        nomes.append(nome)
    return nomes

itens, atual, parte = [], None, ''
ps = d.paragraphs
i = 0
def novo(titulo):
    global atual
    atual = dict(titulo=titulo, parte=parte, corpo=[], imgs=[], tem_ing=False, legendas=[])
    itens.append(atual)

while i < len(ps):
    p = ps[i]; st = p.style.name; t = p.text.strip()
    imgs = salvar_imgs(p)
    if st == 'Heading 2' and t: parte = t; i += 1; continue
    if st in ('Heading 1', 'Heading 4') and t:
        # continuacao do titulo quebrado em outro paragrafo
        while i + 1 < len(ps):
            n = ps[i + 1]; nt = n.text.strip()
            if n.style.name == 'Normal' and nt and len(nt.split()) <= 8 and not nt.startswith('Figura') and not re.search(r'[.!?:]$', nt) and not n._p.xpath('.//a:blip'):
                t += ' ' + nt; i += 1
            else: break
        novo(t); i += 1; continue
    if atual is None: i += 1; continue
    for im in imgs:
        atual['imgs'].append(im); atual['corpo'].append(f'![](/img/{im})')
    if t:
        if st in ('Heading 6', 'Heading 7') and re.search(r'[!?]$|\.\.\.$', t):
            atual['corpo'].append('> ' + t)   # frase de efeito/citacao, nao subtopico
        elif st == 'Heading 7' or st == 'Heading 6' and not t.startswith('—'):
            atual['corpo'].append('### ' + t)
            if t.lower().startswith('ingredientes'): atual['tem_ing'] = True
        elif st == 'Heading 6': atual['corpo'].append('*' + t + '*')
        elif st == 'Heading 5': atual['corpo'].append('> ' + t)
        elif st == 'List Paragraph': atual['corpo'].append('- ' + t)
        elif t.startswith('Figura'): atual['legendas'].append(t); atual['corpo'].append('*' + t + '*')
        else:
            if t.lower().startswith('ingredientes'): atual['tem_ing'] = True
            atual['corpo'].append(t)
    i += 1

usados = set()
for ordem, it in enumerate(itens, 1):
    s = slug(it['titulo']); b = s; k = 2
    while s in usados: s = f'{b}-{k}'; k += 1
    usados.add(s); it['slug'] = s
    it['tipo'] = 'receita' if it['tem_ing'] else 'memoria'
    it['familiares'] = familiar(it['titulo'] + ' ' + ' '.join(it['corpo']))
    # junta listas consecutivas com linha em branco entre blocos
    fm = ['---', f'titulo: "{it["titulo"]}"', f'ordem: {ordem}', f'tipo: {it["tipo"]}',
          'familiar: [' + ', '.join(f'"{f}"' for f in it['familiares']) + ']',
          f'parte: "{it["parte"]}"', 'revisado: false', '---', '']
    if s in REVISADOS:
        fm[4] = REVISADOS[s]; fm[6] = 'revisado: true'
    corpo, prev = [], ''
    for l in it['corpo']:
        if prev.startswith('- ') and l.startswith('- '): corpo.append(l)
        else: corpo.append('\n' + l if corpo else l)
        prev = l
    open(f'{OUT}/content/{s}.md', 'w', encoding='utf-8').write('\n'.join(fm) + '\n'.join(corpo) + '\n')

# --- pagina de revisao
E = html.escape
linhas = []
for n, it in enumerate(itens, 1):
    th = ''.join(f'<img src="img/{im}" loading="lazy">' for im in it['imgs'][:3])
    prev = E(next((l for l in it['corpo'] if not l.startswith(('!', '#', '*', '-', '>'))), '')[:140])
    linhas.append(f'<tr data-t="{it["tipo"]}"><td>{n}</td><td><b>{E(it["titulo"])}</b><br><small>{E(it["parte"])}</small><br><small>{prev}</small></td>'
                  f'<td>{it["tipo"]}</td><td>{E(", ".join(it["familiares"]) or "—")}</td><td>{th}</td>'
                  f'<td><a href="content/{it["slug"]}.md">{it["slug"]}.md</a></td></tr>')
pg = f'''<!doctype html><meta charset="utf-8"><title>Revisão — Zelinda</title>
<style>body{{font:15px/1.4 Georgia,serif;background:#f6efe0;color:#3a2e22;margin:24px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cdbf9f;padding:6px 8px;vertical-align:top;background:#fffaf0}}
th{{background:#e8dcc0;text-align:left}}img{{height:70px;margin:2px;border:1px solid #cdbf9f}}small{{color:#6b5a45}}
tr[data-t=memoria] td:nth-child(3){{color:#7a5a1e}}</style>
<h1>Revisão do protótipo</h1><p>{len(itens)} itens ({sum(i["tipo"]=="receita" for i in itens)} receitas, {sum(i["tipo"]=="memoria" for i in itens)} memórias), {img_n} imagens. Confira tipo e familiar; me diga o que consertar.</p>
<table><tr><th>#</th><th>Título</th><th>Tipo</th><th>Familiar detectado</th><th>Imagens</th><th>Arquivo</th></tr>{''.join(linhas)}</table>'''
open(OUT + '/revisao.html', 'w', encoding='utf-8').write(pg)
print(len(itens), 'itens;', img_n - len(vazias), 'imagens;', len(vazias), 'em branco ignoradas:', vazias)
