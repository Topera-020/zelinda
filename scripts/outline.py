import docx,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
d=docx.Document('livro.docx')
for i,p in enumerate(d.paragraphs):
    img=len(p._p.xpath('.//a:blip'))
    t=p.text.strip()
    if p.style.name.startswith('Heading') or p.style.name=='Title' or img:
        print(i,p.style.name,('[IMG%d]'%img if img else ''),t[:60])
