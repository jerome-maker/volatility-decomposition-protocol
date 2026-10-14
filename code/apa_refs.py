"""Rebuild the reference list in APA style, which is what Journal of Forecasting uses.

Authors, volume, issue and pages come from Crossref (crossref_apa.json) rather than from the
draft, because the draft abbreviated several author lists with "et al." and carried no issue
numbers; APA wants every author up to twenty and the issue in parentheses. Titles are taken
from the draft, where they were already checked against Crossref earlier, and the script
reports any that disagree with the Crossref record so the difference is a decision rather
than a silent overwrite.
"""
import json, re, unicodedata

SRC = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_全文_精簡.md'
OUT = r'J:/我的雲端硬碟/2026工作區/指導學生/柳宇軒/論文草稿_參考文獻_APA.md'
META = 'crossref_apa.json'

# the three entries Crossref does not cover (conference proceedings without a DOI)
MANUAL = {
 'Kumar': 'Kumar, I. E., Venkatasubramanian, S., Scheidegger, C., & Friedler, S. (2020). Problems with '
          'Shapley-value-based explanations as feature importance measures. In H. Daumé III & A. Singh (Eds.), '
          '*Proceedings of the 37th International Conference on Machine Learning* (Vol. 119, pp. 5491–5500). PMLR.',
 'Lundberg': 'Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. '
             'In I. Guyon, U. von Luxburg, S. Bengio, H. Wallach, R. Fergus, S. Vishwanathan, & R. Garnett (Eds.), '
             '*Advances in Neural Information Processing Systems* (Vol. 30, pp. 4765–4774). Curran Associates.',
 'Vaswani': 'Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & '
            'Polosukhin, I. (2017). Attention is all you need. In I. Guyon, U. von Luxburg, S. Bengio, H. Wallach, '
            'R. Fergus, S. Vishwanathan, & R. Garnett (Eds.), *Advances in Neural Information Processing Systems* '
            '(Vol. 30, pp. 5998–6008). Curran Associates.',
}


def initials(given):
    """'Tim Bollerslev' -> 'T.'; 'Jean-Marie' -> 'J.-M.'; 'S.Ö.' -> 'S. Ö.'"""
    parts = [p for p in re.split(r'[\s]+', given.strip()) if p]
    out = []
    for p in parts:
        if '-' in p and not p.endswith('.'):
            out.append('-'.join(q[0] + '.' for q in p.split('-') if q))
        elif p.endswith('.') and len(p) <= 3:
            out.append(p)
        elif re.fullmatch(r'(?:[A-ZÀ-ÿĀ-ž]\.){2,}', p):      # already 'T.G.'
            out.append(' '.join(x + '.' for x in p.replace('.', '')))
        else:
            out.append(p[0] + '.')
    return ' '.join(out)


def tidy_name(n):
    """Crossref returns some names in capitals (Journal of Finance records)."""
    if n.isupper() and len(n) > 2:
        return '-'.join(w.capitalize() for w in n.split('-'))
    return n


def author_string(authors):
    authors = [(tidy_name(fam), giv) for fam, giv in authors if fam.strip()]   # initials stay as given
    names = [f'{fam}, {initials(giv)}' if giv else fam for fam, giv in authors]
    if len(names) == 1:
        return names[0]
    if len(names) <= 20:
        return ', '.join(names[:-1]) + ', & ' + names[-1]
    return ', '.join(names[:19]) + ', ... ' + names[-1]          # APA: first 19, ellipsis, last


def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '', s)


def main():
    md = open(SRC, encoding='utf-8').read()
    draft = [l.strip() for l in md[md.index('# References'):].split('\n')
             if l.strip() and not l.startswith('#') and l.strip() != '---']
    meta = json.load(open(META, encoding='utf-8'))
    out, notes = [], []
    for line in draft:
        doi = (re.search(r'https://doi\.org/(\S+)', line) or [None, None])[1]
        key = line.split(',')[0]
        if doi is None:
            hit = next((v for k, v in MANUAL.items() if line.startswith(k)), None)
            if hit is None:
                raise SystemExit('no DOI and no manual entry: ' + line[:60])
            out.append(hit)
            continue
        m = meta[doi]
        # Crossref records are sometimes short of authors (ECTA5771 has none, nbh001 has one),
        # while the draft abbreviated others; take whichever list is longer and say which.
        head = line.split('(')[0]
        draft_authors = [(p.split(',')[0].strip(), p.split(',', 1)[1].strip())
                         for p in re.findall(r"[A-ZA-ÿÀ-ɏ][\w’'-]*,\s*(?:[A-ZÀ-ɏ]\.-?)+", head)]
        if len(draft_authors) == len(m['authors']):      # same people: keep the draft's diacritics
            fixed = []
            for (cf, cg), (df, dg) in zip(m['authors'], draft_authors):
                fixed.append((df if norm(df) == norm(cf) and df != cf else cf, cg))
            changed = [f for (f, _), (cf, _) in zip(fixed, m['authors']) if f != cf]
            if changed:
                notes.append(f'改用草稿的變音拼法: {changed}')
            m = dict(m, authors=fixed)
        if len(draft_authors) > len(m['authors']) and 'et al.' not in head:
            notes.append(f"Crossref 作者不全（改用草稿 {len(draft_authors)} 位）: {head.strip()}")
            m = dict(m, authors=draft_authors)
        elif len(m['authors']) > len(draft_authors) and 'et al.' not in head:
            notes.append(f"草稿漏列作者（改用 Crossref {len(m['authors'])} 位）: {head.strip()}")
        if not m['authors']:                       # Crossref record without authors (ECTA5771)
            m = dict(m, authors=[(p.split(',')[0].strip(), p.split(',')[1].strip())
                                 for p in re.findall(r'[A-ZÀ-ÿ][^,]*,\s*(?:[A-ZÀ-ÿ]\.-?)+',
                                                     line.split('(')[0])])
        title = re.search(r'\(\d{4}\)\.\s*(.+?)([.?])\s*\*', line)   # some titles end in a question mark
        if not title:
            raise SystemExit('cannot read title: ' + line[:70])
        title = title.group(1).strip() + ('?' if title.group(2) == '?' else '')
        if norm(title) != norm(m['title']):
            notes.append(f"標題與 Crossref 不同（保留草稿版）\n      草稿: {title}\n      Crossref: {m['title']}")
        journal = m['journal'] or re.search(r'\*([^*]+)\*', line).group(1)
        vol, iss, pg = m['volume'], m['issue'], (m['page'] or '').replace('-', '–')
        # Crossref's "issued" date can be the online-first year; the issue year is what APA wants,
        # and where Crossref has no print date the draft's year was checked against the journal.
        draft_year = int(re.search(r'\((\d{4})\)', line).group(1))
        year = m.get('print_year') or draft_year
        if year != draft_year:
            notes.append(f'年份改用卷期年 {year}（草稿 {draft_year}、Crossref issued {m["year"]}）: {title[:50]}')
        bits = f"{author_string(m['authors'])} ({year}). {title}. *{journal}*"
        if vol:
            bits += f", *{vol}*" + (f"({iss})" if iss else '')
        if pg:
            bits += f", {pg}"
        out.append(bits + f". https://doi.org/{doi}")
    out.sort(key=lambda s: norm(s))
    open(OUT, 'w', encoding='utf-8').write('# References\n\n' + '\n\n'.join(out) + '\n')
    print(f'wrote {OUT}\n  {len(out)} entries in APA style')
    for n in notes:
        print('  ·', n)
    for s in out[:3]:
        print('\n   ', s[:190])


if __name__ == '__main__':
    main()
