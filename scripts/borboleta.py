"""borboleta.gif (azul) -> assets/borboleta.webp (vermelha, animada, recortada)."""
import os, numpy as np
from PIL import Image, ImageSequence
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIRO = 120 / 360          # azul (~235 graus) -> vermelho (~355 graus)
ALTURA = 200
im = Image.open(os.path.join(ROOT, 'borboleta.gif'))
quadros, durs = [], []
for f in ImageSequence.Iterator(im):
    durs.append(f.info.get('duration', 60))
    quadros.append(f.convert('RGBA'))
# caixa comum a todos os quadros
caixa = None
for q in quadros:
    b = q.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    if b: caixa = b if caixa is None else (min(caixa[0], b[0]), min(caixa[1], b[1]), max(caixa[2], b[2]), max(caixa[3], b[3]))
out = []
for q in quadros:
    q = q.crop(caixa)
    a = q.getchannel('A')
    hsv = np.array(q.convert('RGB').convert('HSV')).astype(np.int32)
    mask = hsv[:, :, 1] > 40                      # so gira o que tem cor (preto do contorno fica)
    hsv[:, :, 0] = np.where(mask, (hsv[:, :, 0] + int(GIRO * 255)) % 256, hsv[:, :, 0])
    rgb = Image.fromarray(hsv.astype(np.uint8), 'HSV').convert('RGB')
    r = Image.merge('RGBA', (*rgb.split(), a))
    w = round(r.width * ALTURA / r.height)
    out.append(r.resize((w, ALTURA), Image.LANCZOS))
out[0].save(os.path.join(ROOT, 'assets', 'borboleta.webp'), save_all=True, append_images=out[1:], duration=durs, loop=0, lossless=False, quality=80, method=6)
print(len(out), 'quadros', out[0].size, durs[:3], os.path.getsize(os.path.join(ROOT, 'assets', 'borboleta.webp')) // 1024, 'KB')
# folha de contato para conferir
folha = Image.new('RGBA', (out[0].width * 5 + 20, ALTURA), (249, 235, 205, 255))
for k, i in enumerate((0, 4, 9, 14, 18)): folha.alpha_composite(out[min(i, len(out) - 1)], (k * (out[0].width + 5), 0))
folha.convert('RGB').save(os.path.join(ROOT, 'build', 'borboleta_teste.png'))
