"""Prepare the manuscript for Journal of Forecasting (Wiley).

Three differences from the version prepared for DSFE:
  * citations follow APA — "et al." from three authors, and an ampersand inside parentheses;
  * the reference list is the APA one rebuilt from Crossref;
  * the sentence that called two papers "recent work in this journal" was true only while DSFE
    was the target, and the reference it was carrying for venue fit alone is dropped because
    nothing in the text cites it.
Review at Journal of Forecasting is single-blind, so no anonymised version is produced.
"""
import re

SRC = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_精簡版.md'
REFS = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_參考文獻_APA.md'
OUT = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_JOF.md'

# narrative citations: three or more authors become "First et al." (APA 7)
CITES = [
    ('Andersen, Bollerslev, Diebold and Labys (2003)', 'Andersen et al. (2003)'),
    ('Glosten, Jagannathan and Runkle (1993)', 'Glosten et al. (1993)'),
    ('Harvey, Leybourne and Newbold (1997)', 'Harvey et al. (1997)'),
    ('Hansen, Lunde and Nason (2011)', 'Hansen et al. (2011)'),
    ('Busch, Christensen and Nielsen (2011)', 'Busch et al. (2011)'),
    ('Gu, Kelly and Xiu (2020)', 'Gu et al. (2020)'),
    ('Fleming, Kirby and Ostdiek (2003)', 'Fleming et al. (2003)'),
    ('Aas, Jullum and Løland (2021)', 'Aas et al. (2021)'),
    ('Christensen, Siggaard and Veliyev (2023)', 'Christensen et al. (2023)'),
]

# the DSFE framing, and the section heading Wiley expects to see
EDITS = [
    ('Recent work in this journal illustrates both the promise and the difficulty.',
     'Two recent studies illustrate both the promise and the difficulty.'),
    ('# Data and code availability', '# Data availability statement'),
]

UNCITED = '10.3934/DSFE.2026010'   # carried for venue fit only; no sentence cites it


def ampersands(text):
    """Inside a parenthetical citation, APA writes '&' rather than 'and'."""
    def fix(m):
        inner = m.group(1)
        if not re.search(r'\b(?:19|20)\d{2}\b', inner):      # not a citation
            return m.group(0)
        return '(' + re.sub(r'(?<=[a-zç])\s+and\s+(?=[A-ZÀ-ÿ])', ' & ', inner) + ')'
    return re.sub(r'\(([^()]*)\)', fix, text)


def main():
    md = open(SRC, encoding='utf-8').read()
    for a, b in CITES + EDITS:
        if a not in md:
            raise SystemExit('not found: ' + a[:60])
        md = md.replace(a, b)
    before = md
    md = ampersands(md)
    n_amp = len(re.findall(r' & ', md)) - len(re.findall(r' & ', before))

    refs = open(REFS, encoding='utf-8').read()
    keep, dropped = [], 0
    for para in refs.split('\n\n'):
        if UNCITED in para:
            dropped += 1; continue
        keep.append(para)
    refs = '\n\n'.join(keep)

    open(OUT, 'w', encoding='utf-8').write(md.rstrip() + '\n\n' + refs.strip() + '\n')
    body = re.sub(r'^\|.*$', '', md, flags=re.M)
    n_refs = len([p for p in refs.split('\n\n') if p.strip() and not p.startswith('#')])
    print(f'wrote {OUT}')
    print(f'  narrative citations converted: {len(CITES)}')
    print(f'  parenthetical "and" -> "&": {n_amp}')
    print(f'  uncited references dropped: {dropped}')
    print(f'  references: {n_refs}')
    print(f'  body words (excluding tables): {len(re.findall(r"[A-Za-z][A-Za-z’-]+", body)):,}')


if __name__ == '__main__':
    main()
