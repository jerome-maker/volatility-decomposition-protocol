"""Produce the anonymized manuscript required for double-blind review, plus a separate title page."""
import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import md2docx as M

OUT_ANON = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/Chou_2026_anonymised_manuscript.docx'
OUT_TITLE = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/Chou_2026_title_page.docx'

# 1) anonymised body: same converter, author block replaced, identifying links removed
M.OUT = OUT_ANON
orig_main = M.main
def anon_main():
    orig_main()
    d = Document(OUT_ANON)
    kill = ('Jerome Chih-Lung Chou', 'Graduate Institute of Finance', 'jerome.chou@', 'Corresponding author')
    for p in list(d.paragraphs):
        if any(k in p.text for k in kill):
            p._element.getparent().remove(p._element)
    for p in d.paragraphs:                      # replace any repository or environment link
        if 'anonymous' in p.text.lower() or 'github' in p.text.lower():
            for r in p.runs: r.text = r.text.replace('github.com', '[anonymised repository]')
    d.save(OUT_ANON)
anon_main()

# 2) title page
t = Document()
st = t.styles['Normal']; st.font.name = M.FONT; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), M.FONT)
sec = t.sections[0]
for a in ('left_margin','right_margin','top_margin','bottom_margin'): setattr(sec, a, Cm(2.5))
def para(txt, size=12, bold=False, align='center', after=8):
    p = t.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER if align=='center' else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(after)
    M.setfont(p.add_run(txt), size, bold=bold); return p
para('Title page', 11, align='left', after=18)
para('Information or architecture? A decomposition protocol for evaluating deep learning gains in volatility forecasting', 15, bold=True, after=16)
para('Jerome Chih-Lung Chou', 12, after=4)
para('Graduate Institute of Finance, National Taiwan University of Science and Technology, Taipei, Taiwan', 11, after=4)
para('E-mail: jerome.chou@mail.ntust.edu.tw', 11, after=20)
for line in ['Corresponding author: Jerome Chih-Lung Chou.',
             'Funding: This research received no external funding.',
             'Conflicts of interest: The author declares no conflicts of interest.',
             'Data availability: The daily derived series and all code required to reproduce the results are available at the repository cited in the manuscript. The one-minute bars were obtained from the HF Data Library; the portion from March 2022 onward derives from IEX Exchange HIST and is freely redistributable, while the earlier portion comes from a commercial feed and cannot be redistributed.',
             'Declaration of generative AI use: Generative AI tools were used for code drafting, language editing and manuscript preparation. The author reviewed and verified all analyses, numbers and claims and takes full responsibility for the content.']:
    para(line, 11, align='left', after=10)
t.save(OUT_TITLE)
print('saved anonymised manuscript and title page')
