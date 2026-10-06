"""Convert the manuscript to the house style of the DSFE Word template.

Two changes the journal's own template requires and our draft style does not follow:
  * in-text citations with three or more authors are given as "First et al. (year)";
  * reference entries read "Surname AB, Surname C, et al. (year) Title. J Abbrev vol: pages. doi",
    with initials run together, no period after the year, and ISO-4 journal abbreviations.
Input is the assembled manuscript; output is the version the document build reads.
"""
import re

SRC = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_全文_精簡.md'
OUT = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_投稿版.md'

# ---- in-text: three or more authors become "First et al."
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

# ---- ISO-4 abbreviations, as the template's own reference list writes them
JOURNALS = {
    'Advances in Neural Information Processing Systems': 'Adv Neural Inf Process Syst',
    'Annals of Statistics': 'Ann Stat',
    'Artificial Intelligence': 'Artif Intell',
    'Data Science in Finance and Economics': 'Data Sci Financ Econ',
    'Econometric Reviews': 'Econom Rev',
    'Econometrica': 'Econometrica',
    'Financial Innovation': 'Financ Innov',
    'International Economic Review': 'Int Econ Rev',
    'International Journal of Forecasting': 'Int J Forecast',
    'Journal of Applied Econometrics': 'J Appl Econom',
    'Journal of Business & Economic Statistics': 'J Bus Econ Stat',
    'Journal of Derivatives': 'J Deriv',
    'Journal of Econometrics': 'J Econom',
    'Journal of Empirical Finance': 'J Empir Financ',
    'Journal of Finance': 'J Financ',
    'Journal of Financial Econometrics': 'J Financ Econom',
    'Journal of Financial Economics': 'J Financ Econ',
    'Nature Machine Intelligence': 'Nat Mach Intell',
    'Neural Computation': 'Neural Comput',
    'Patterns': 'Patterns',
    'Proceedings of the 2019 Conference of the North American Chapter of the Association for '
    'Computational Linguistics': 'Proc 2019 Conf North Am Chapter Assoc Comput Linguist',
    'Proceedings of the 37th International Conference on Machine Learning': 'Proc 37th Int Conf Mach Learn',
    'Proceedings of the AAAI Conference on Artificial Intelligence': 'Proc AAAI Conf Artif Intell',
    'Review of Economics and Statistics': 'Rev Econ Stat',
    'Review of Financial Studies': 'Rev Financ Stud',
}


def authors(block):
    """'Aas, K., Jullum, M., Løland, A.' -> 'Aas K, Jullum M, Løland A'."""
    toks = [t.strip() for t in block.split(', ') if t.strip()]
    out, i = [], 0
    while i < len(toks):
        if toks[i].lower().startswith('et al'):
            out.append('et al.'); i += 1; continue
        if i + 1 < len(toks) and re.fullmatch(r'(?:[A-ZÀ-ÿĀ-ž]\.-?)+', toks[i + 1]):
            out.append(toks[i] + ' ' + toks[i + 1].replace('.', '').replace('-', ''))
            i += 2
        else:                                   # single-name entity (a committee, say)
            out.append(toks[i]); i += 1
    return ', '.join(out)


def reference(line):
    m = re.match(r'^(.*?)\((\d{4})\)\.\s*(.*)$', line)
    if not m:
        raise ValueError('unparsed reference: ' + line[:70])
    auth, year, rest = m.group(1).rstrip().rstrip(','), m.group(2), m.group(3)
    for full, abbr in sorted(JOURNALS.items(), key=lambda kv: -len(kv[0])):
        if '*' + full + '*' in rest:
            rest = rest.replace('*' + full + '*', abbr)
            break
    else:
        raise ValueError('unknown journal: ' + line[:90])
    return f'{authors(auth)} ({year}) {rest}'


def main():
    md = open(SRC, encoding='utf-8').read()
    head, refs = md.split('# References\n', 1)
    for a, b in CITES:
        if a not in head:
            raise SystemExit('citation not found: ' + a)
        head = head.replace(a, b)
    left = [a for a, _ in CITES if a in head]
    if left:
        raise SystemExit('citation left unconverted: %s' % left)
    done = []
    for ln in refs.split('\n'):
        s = ln.strip()
        done.append('' if (not s or s == '---') else reference(s))
    out = head + '# References\n' + '\n'.join(done).strip() + '\n'
    open(OUT, 'w', encoding='utf-8').write(out)
    n = sum(1 for l in done if l)
    print(f'wrote {OUT}\n  references converted: {n}')
    for l in [x for x in done if x][:4]:
        print('   ', l[:120])


if __name__ == '__main__':
    main()
