from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
FONT='Microsoft JhengHei'
# CT_TblPrBase (ECMA-376 Part 1, 17.4.60) allows each tblPr child at most once
# and fixes their order. python-docx enforces neither when you append, and Word,
# python-docx and mammoth all read violations without complaint -- the IAJ
# submission was returned three times over tables that opened fine everywhere
# locally. Note t.autofit=False already writes a tblLayout, so appending another
# is how the duplicate arose. Set children through the helper below instead.
_TBLPR_ORDER=['tblStyle','tblpPr','tblOverlap','bidiVisual','tblStyleRowBandSize',
    'tblStyleColBandSize','tblW','jc','tblCellSpacing','tblInd','tblBorders',
    'shd','tblLayout','tblCellMar','tblLook','tblCaption','tblDescription']
def set_tblPr_child(tblPr,tag,attrs):
    """Set one tblPr child exactly once, in its schema position."""
    for e in tblPr.findall(qn(tag)): tblPr.remove(e)
    el=OxmlElement(tag)
    for k,v in attrs.items(): el.set(qn(k),v)
    tblPr.append(el)
    rank=lambda c:(_TBLPR_ORDER.index(c.tag.split('}')[-1])
                   if c.tag.split('}')[-1] in _TBLPR_ORDER else len(_TBLPR_ORDER))
    for child in sorted(list(tblPr),key=rank): tblPr.append(child)
    return el
def setfont(run,size=None,bold=None,color=None):
    run.font.name=FONT; run._element.rPr.rFonts.set(qn('w:eastAsia'),FONT)
    if size: run.font.size=Pt(size)
    if bold is not None: run.bold=bold
    if color: run.font.color.rgb=RGBColor.from_string(color)
def new_doc():
    d=Document()
    sec=d.sections[0]; sec.page_width=Cm(21); sec.page_height=Cm(29.7)
    for a in ('left_margin','right_margin'): setattr(sec,a,Cm(2.2))
    sec.top_margin=Cm(2.2); sec.bottom_margin=Cm(2.2)
    for st in ['Normal','Heading 1','Heading 2','Heading 3','Title','Caption','List Bullet','List Number']:
        s=d.styles[st]; s.font.name=FONT; s.element.rPr.rFonts.set(qn('w:eastAsia'),FONT)
    d.styles['Normal'].font.size=Pt(10.5)
    d.styles['Normal'].paragraph_format.line_spacing=1.35
    d.styles['Normal'].paragraph_format.space_after=Pt(4)
    for st,sz,col in [('Heading 1',16,'1F3A5F'),('Heading 2',13,'1F3A5F'),('Heading 3',11.5,'2A5A8A'),('Title',22,'1F3A5F')]:
        d.styles[st].font.size=Pt(sz); d.styles[st].font.color.rgb=RGBColor.from_string(col)
    # page number footer
    p=sec.footer.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(); f1=OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'),'begin')
    it=OxmlElement('w:instrText'); it.set(qn('xml:space'),'preserve'); it.text='PAGE'
    f2=OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'),'end')
    r._r.append(f1); r._r.append(it); r._r.append(f2); setfont(r,9)
    return d
def para(d,text,bold_prefix=None,size=None,style=None,align=None):
    p=d.add_paragraph(style=style)
    if bold_prefix: setfont(p.add_run(bold_prefix),size,True)
    # simple **bold** markup
    parts=text.split('**')
    for i,t in enumerate(parts):
        if t: setfont(p.add_run(t),size,i%2==1)
    if align=='center': p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    return p
def bullet(d,text): return para(d,text,style='List Bullet')
def numbered(d,text): return para(d,text,style='List Number')
def shade(cell,hexcol):
    tcPr=cell._tc.get_or_add_tcPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:color'),'auto'); sh.set(qn('w:fill'),hexcol); tcPr.append(sh)
def table(d,header,rows,widths=None,size=9,highlight_rows=()):
    t=d.add_table(rows=1+len(rows),cols=len(header)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for j,h in enumerate(header):
        c=t.rows[0].cells[j]; c.text=''; setfont(c.paragraphs[0].add_run(str(h)),size,True); shade(c,'DCE8F5')
        c.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.rows[i+1].cells[j]; c.text=''
            txt=str(v); b=txt.startswith('**'); txt=txt.strip('*')
            setfont(c.paragraphs[0].add_run(txt),size,b)
            c.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
            if i in highlight_rows: shade(c,'FFF4E0')
    if widths:
        t.autofit=False                       # python-docx writes a tblLayout here
        tblPr=t._tbl.tblPr
        set_tblPr_child(tblPr,'w:tblLayout',{'w:type':'fixed'})
        set_tblPr_child(tblPr,'w:tblW',{'w:w':str(int(sum(widths)*567)),'w:type':'dxa'})
        grid=t._tbl.tblGrid
        for j,gc in enumerate(grid.findall(qn('w:gridCol'))): gc.set(qn('w:w'),str(int(widths[j]*567)))
        for row in t.rows:
            for j,w in enumerate(widths): row.cells[j].width=Cm(w)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.line_spacing=1.1; p.paragraph_format.space_after=Pt(1); p.paragraph_format.space_before=Pt(1)
    d.add_paragraph().paragraph_format.space_after=Pt(2)
    return t
def caption(d,text):
    p=d.add_paragraph(); setfont(p.add_run(text),9,False,'52514E'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; return p
def figure(d,path,cap,width=16):
    d.add_picture(path,width=Cm(width)); d.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER; caption(d,cap)
