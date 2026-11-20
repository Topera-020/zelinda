"""screenshot da home: python scripts/foto.py [pagina.html] [largura]"""
import pathlib
import sys, os
from playwright.sync_api import sync_playwright
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pg = sys.argv[1] if len(sys.argv) > 1 else 'index.html'; w = int(sys.argv[2]) if len(sys.argv) > 2 else 1280
with sync_playwright() as p:
    b = p.chromium.launch(); pa = b.new_page(viewport={'width': w, 'height': 900})
    pa.goto(pathlib.Path(R, 'docs', pg).as_uri()); pa.wait_for_timeout(1200)
    pa.screenshot(path=R + '/build/foto.png', full_page=True); b.close()
