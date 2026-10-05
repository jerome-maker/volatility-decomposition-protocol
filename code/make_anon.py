"""Produce the anonymized manuscript required for double-blind review, plus a separate title page."""
import re
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import md2docx as M

OUT_ANON = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/Chou_2026_anonymised_manuscript.docx'
ANON = 'https://anonymous.4open.science/r/volatility-decomposition-protocol-E6EC'
GH = 'https://github.com/jerome-maker/volatility-decomposition-protocol'
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
    for p in d.paragraphs:                      # the review copy points at the anonymised mirror
        for r in p.runs:
            if 'github.com' in r.text:
                r.text = r.text.replace(GH, ANON)
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
             'Data availability: All code and the daily derived series are available at ' + GH + '. For double-blind review an anonymised mirror is provided at ' + ANON + ', which is the link given in the review copy of the manuscript. The one-minute bars were obtained from the HF Data Library; the portion from March 2022 onward derives from IEX Exchange HIST and is freely redistributable, while the earlier portion comes from a commercial feed and cannot be redistributed.',
             'Declaration of generative AI use: Generative AI tools (Claude, Anthropic) were used for code drafting, data processing, drafting of the manuscript text, language editing and document preparation, and in discussing analytical choices. All research decisions, analyses and interpretations were made and verified by the author, who takes full responsibility for the content.']:
    para(line, 11, align='left', after=10)
t.save(OUT_TITLE)
print('saved anonymised manuscript and title page')
