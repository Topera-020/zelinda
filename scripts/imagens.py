"""Gera build/imagens.md: imagem, item, legenda, pessoas (a preencher)."""
import docx, os, re, sys, io, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = docx.Document(os.path.join(ROOT, 'livro.docx'))
ps = d.paragraphs
linhas, vistos, titulo, n = [], set(), '(antes do 1º item)', 0
for i, p in enumerate(ps):
    if p.style.name in ('Heading 1', 'Heading 4') and p.text.strip(): titulo = p.text.strip()
    for rid in p._p.xpath('.//a:blip/@r:embed'):
        nome = os.path.basename(d.part.related_parts[rid].partname)
        leg = ''
        for j in (i, i + 1, i + 2, i - 1):
            if 0 <= j < len(ps) and ps[j].text.strip().startswith('Figura'):
                leg = ps[j].text.strip(); break
        n += 1; vistos.add(nome)
        linhas.append((n, nome, titulo, leg))
todas = sorted(f for f in os.listdir(os.path.join(ROOT, 'build/img_todas')))
sobra = [f for f in todas if f not in vistos]
out = ['# Imagens do livro', '',
       'Preencha a coluna **Pessoas** (nomes separados por vírgula). Arquivos em `img_todas/`.', '',
       '| # | Arquivo | Item onde aparece | Legenda do livro | Pessoas |', '| --- | --- | --- | --- | --- |']
for n, nome, t, l in linhas:
    out.append(f'| {n} | {nome} | {t.replace("|","/")} | {l.replace("|","/")} |  |')
out += ['', '## Imagens que não aparecem no corpo do texto', '', '| Arquivo | Pessoas |', '| --- | --- |']
out += [f'| {f} |  |' for f in sobra]
open(os.path.join(ROOT, 'build/imagens.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(linhas), 'no texto;', len(sobra), 'fora;', sum(1 for l in linhas if l[3]), 'com legenda')
