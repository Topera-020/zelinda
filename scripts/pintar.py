"""Pinta desenhos de linha por regioes fechadas (balde automatico).
uso: python scripts/pintar.py build/img/img030.jpeg [mais arquivos...]
saida: build/colorido/<nome>.png  e  build/colorido/<nome>_comparacao.png"""
import cv2, numpy as np, sys, os, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'colorido'); os.makedirs(OUT, exist_ok=True)

# paleta do livro (RGB): creme, vermelho, amarelo-manteiga, verde-salvia, madeira, rosa, azul-poeira, terracota
PALETA = [(250, 226, 160), (214, 90, 90), (240, 190, 90), (150, 185, 140),
          (214, 165, 110), (240, 170, 170), (140, 175, 200), (200, 120, 80)]
PELE = (245, 205, 175)

def pintar(caminho):
    img = cv2.imread(caminho, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    linha = (g < 150).astype(np.uint8)
    linha = cv2.dilate(linha, np.ones((3, 3), np.uint8))          # fecha pequenas falhas
    livre = (1 - linha).astype(np.uint8)
    n, rot, stats, cent = cv2.connectedComponentsWithStats(livre, connectivity=4)
    rnd = random.Random(os.path.basename(caminho))
    cor = np.full((h, w, 3), 255, np.uint8)
    # regioes que encostam na borda = fundo, ficam brancas
    borda = set(rot[0, :]) | set(rot[-1, :]) | set(rot[:, 0]) | set(rot[:, -1])
    pele_usada = False
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if i in borda or area < 60: continue
        # a maior regiao no terco superior central costuma ser rosto: pele (heuristica simples)
        cx, cy = cent[i]
        if not pele_usada and area > 0.01 * h * w and cy < 0.45 * h and 0.25 * w < cx < 0.75 * w:
            c = PELE; pele_usada = True
        else:
            c = rnd.choice(PALETA)
        cor[rot == i] = c
    # fundo atras das linhas: pixels de linha ficam pretos por multiplicacao com o original
    cor_bgr = cor[:, :, ::-1].astype(np.float32) / 255
    orig = img.astype(np.float32) / 255
    out = (cor_bgr * orig * 255).clip(0, 255).astype(np.uint8)     # multiply: mantem o traco
    nome = os.path.splitext(os.path.basename(caminho))[0]
    cv2.imwrite(f'{OUT}/{nome}.png', out)
    lado = np.hstack([img, out])
    cv2.imwrite(f'{OUT}/{nome}_comparacao.png', lado)
    print(nome, f'{n} regioes ->', f'{OUT}/{nome}.png')

for c in sys.argv[1:]: pintar(c)
