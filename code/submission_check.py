"""Pre-submission check against the journal's stated requirements and internal consistency."""
import re, sys
from docx import Document
from docx.shared import Pt

D = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/'
MAIN = D + 'Chou_2026_information_or_architecture.docx'
ANON = D + 'Chou_2026_anonymised_manuscript.docx'
TITLE = D + 'Chou_2026_title_page.docx'
ok, warn, fail = [], [], []

def text_of(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            for c in r.cells: parts.append(c.text)
    return d, '\n'.join(parts), '\n'.join(p.text for p in d.paragraphs)

doc, full, body = text_of(MAIN)

# --- journal formatting rules
abstract = re.search(r'Abstract:?\s*(.+?)\nKeywords', body, re.S)   # the template puts the label inline
aw = len(abstract.group(1).split()) if abstract else 0
(ok if 0 < aw < 300 else fail).append(f'摘要字數 {aw}（規定 < 300）')
kw = re.search(r'Keywords:(.+)', body)
nk = len([k for k in kw.group(1).split(';') if k.strip()]) if kw else 0
(ok if 5 <= nk <= 10 else fail).append(f'關鍵詞 {nk} 個（規定 5–10）')
words = len(re.findall(r"[A-Za-z][A-Za-z'’-]+", body))
(ok if words >= 6000 else warn).append(f'正文英文字數 約 {words:,}（建議 ≥ 6,000）')
fonts = {r.font.name for p in doc.paragraphs for r in p.runs if r.font.name}
(ok if fonts <= {'Times New Roman'} else fail).append(f'字型 {sorted(fonts) or "繼承預設"}')
ls = [p.paragraph_format.line_spacing for p in doc.paragraphs if p.paragraph_format.line_spacing]
bad_ls = [x for x in ls if isinstance(x, Pt(1).__class__) and x.pt < 15]
(ok if not bad_ls else fail).append(f'行距：{len(ls)} 段設定，低於 15 點者 {len(bad_ls)} 段')
(ok if doc.part.element.xpath('.//m:oMath') else fail).append(
    f'方程式物件 {len(doc.part.element.xpath(".//m:oMath"))} 個（須為可編輯物件）')
(ok if not re.search(r'[\u4e00-\u9fff]', full) else fail).append('中文殘留 0 處' if not re.search(r'[\u4e00-\u9fff]', full) else '仍有中文殘留')
(ok if not re.search(r'\\[a-zA-Z]+\{|\$\w', full) else fail).append('LaTeX 標記殘留 0 處')
caps = [p.text for p in doc.paragraphs if p.text.strip().startswith(('Table ', 'Figure '))]
stray = [c for c in caps if '*' in c or '_' in c.split('.')[0]]
(ok if not stray else fail).append(f'表圖標題殘留 markdown 標記 {len(stray)} 處')

# --- numbering and cross-references
tab_caps = sorted(int(m) for m in re.findall(r'^Table (\d+)\.', body, re.M))
fig_caps = sorted(int(m) for m in re.findall(r'^Figure (\d+)\.', body, re.M))
(ok if tab_caps == list(range(1, len(tab_caps) + 1)) else fail).append(f'表標題連號 1–{len(tab_caps)}')
(ok if fig_caps == list(range(1, len(fig_caps) + 1)) else fail).append(f'圖標題連號 1–{len(fig_caps)}')
refs_t = {int(m) for m in re.findall(r'Table (\d+)\b', body)}
refs_f = {int(m) for m in re.findall(r'Figure (\d+)\b', body)}
miss_t = sorted(set(tab_caps) - refs_t); miss_f = sorted(set(fig_caps) - refs_f)
(ok if not miss_t else fail).append('每張表都有在正文被引用' if not miss_t else f'未被引用的表：{miss_t}')
(ok if not miss_f else fail).append('每張圖都有在正文被引用' if not miss_f else f'未被引用的圖：{miss_f}')
heads = re.findall(r'^(\d+(?:\.\d+)*)\.?\s+[A-Z]', body, re.M)
sec_refs = {m for m in re.findall(r'Section (\d+(?:\.\d+)?)', body)}
heads_set = set(heads)
dangling = sorted(s for s in sec_refs if s not in heads_set)
(ok if not dangling else fail).append('章節交互引用皆存在' if not dangling else f'指向不存在的章節：{dangling}')

# --- references: see refcross.py (run separately)

# --- anonymised version
_, afull, _ = text_of(ANON)
leaks = [k for k in ('Jerome', 'Chou', 'ntust', 'Graduate Institute', 'Taiwan University of Science') if k in afull]
(ok if not leaks else fail).append('匿名版無識別資訊' if not leaks else f'匿名版殘留：{leaks}')
_, tfull, _ = text_of(TITLE)
need = ['Funding', 'Conflicts of interest', 'Data availability', 'generative AI', 'Corresponding author']
miss_decl = [n for n in need if n.lower() not in tfull.lower()]
(ok if not miss_decl else fail).append('題名頁聲明齊全' if not miss_decl else f'題名頁缺：{miss_decl}')

print('=' * 64)
for s in ok:   print('  [通過]', s)
for s in warn: print('  [注意]', s)
for s in fail: print('  [問題]', s)
print('=' * 64)
print(f'通過 {len(ok)}、注意 {len(warn)}、問題 {len(fail)}')
