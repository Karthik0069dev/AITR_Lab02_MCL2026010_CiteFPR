"""Write adjudication labels into results/adjudication_sample.csv (13 Nov 2026).

Labels were produced with AI assistance (Claude) from recorded evidence and accepted by the author:
  * rule (90 rows): independent OpenAlex / Semantic Scholar record (results/adjudication_evidence.csv)
    with title similarity >= 0.9, author overlap >= 0.5 and |year difference| <= 1 -> genuine
  * manual (33 rows): listed below with the evidence used (web search of the primary source)
"""
from __future__ import annotations

import csv

E = "web search, primary source"
MANUAL = {
    # ---- genuine: paper exists and the .bib entry matches it
    "2001.06626:DBLP:journals/corr/KingmaW13": ("genuine", "arXiv:1312.6114, ICLR 2014; registries returned a 2024 title twin"),
    "2002.11893:eric2019multiwoz21": ("genuine", "arXiv:1907.01669, authors match"),
    "2003.11522:zhang2015character": ("genuine", "NIPS 2015 proceedings; arXiv:1509.01626"),
    "2003.03239:wu2012probase": ("genuine", "SIGMOD 2012, DOI 10.1145/2213836.2213891"),
    "2002.02562:graves:06": ("genuine", "ICML 2006, DOI 10.1145/1143844.1143891"),
    "2002.08909:mips_alsh": ("genuine", "NIPS 2014; arXiv:1405.5869"),
    "2001.06626:DBLP:journals/corr/HaDL16": ("genuine", "arXiv:1609.09106, ICLR 2017"),
    "2003.04970:Reed:08a": ("genuine", "COMMA 2008, FAIA vol. 172 pp. 311-323"),
    "2003.04970:Erhan:10": ("genuine", "JMLR 11 (2010) 625-660"),
    "2002.07339:Rahul2017BiomedicalET": ("genuine", "BioNLP 2017, DOI 10.18653/v1/W17-2340"),
    "2003.02301:vaidya2015cocaine": ("genuine", "USENIX WOOT 2015"),
    "2002.11768:gpt-2": ("genuine", "OpenAI 2019 report; authors match"),
    "2002.11910:emerson2005second": ("genuine", "SIGHAN 2005, ACL Anthology I05-3017"),
    "2002.11910:peng2017Sup4improving": ("genuine", "authors' supplement PDF (golden-horse repo); CoRR venue not confirmed"),
    "2003.02301:povey2011kaldi": ("genuine", "OpenAlex: repository copy of the Kaldi ASRU 2011 paper, first author matches"),
    "2001.09907:hunalign": ("genuine", "OpenAlex: 2007 republication of the RANLP 2005 paper, authors match"),
    "2002.10829:Avt2007sub": ("genuine", "OpenAlex: Routledge 2014 reissue of the 2007 book, authors match"),
    "2003.11522:drugsurvey": ("genuine", "OpenAlex: ICPSR record with identical title; report by SAMHSA"),
    "2003.04987:Guo_2017": ("genuine", "OpenAlex: exact title and year; .bib lists 'C. Guo et al.'"),
    # ---- genuine_erroneous: the work exists but the .bib entry contains a real error
    "2003.02301:christophe2016cstr": ("genuine_erroneous", "given/family names swapped ('Christophe, Veaux') and 'Yarnagishi' misspelt; OpenAlex record"),
    "2003.04987:Ghavamzadeh_2016": ("genuine_erroneous", "title lacks ': A Survey'; FnT ML 8(5-6) 2015, DOI 10.1561/2200000049"),
    "2002.08909:gpt": ("genuine_erroneous", "report title is 'Improving Language Understanding by Generative Pre-Training' (OpenAI 2018)"),
    # ---- unresolvable: non-scholarly resource or unpublished; not checkable in scholarly sources
    "2003.11522:deauseterms": ("unresolvable", "government guide; evidence found only the 2011 edition"),
    "2003.11522:deaslangterms": ("unresolvable", "government guide; no scholarly record"),
    "2003.04987:Huggingface2017": ("unresolvable", "GitHub repository"),
    "2003.02301:chase": ("unresolvable", "company web page"),
    "2003.04987:2019bots": ("unresolvable", "blog article"),
    "2003.04987:Zo": ("unresolvable", "product web page"),
    "2003.04987:deeptextcorrector2017": ("unresolvable", "GitHub repository"),
    "2003.02301:voice_match": ("unresolvable", "product web page"),
    "2003.11522:twitterdevagree": ("unresolvable", "policy web page"),
    "2003.04987:Mitsuku": ("unresolvable", "product web page"),
    "2003.03239:honnibal2017spacy": ("unresolvable", "cited as 'to appear'; no formal publication found"),
}


def main():
    ev = {r["ref_id"]: r for r in csv.DictReader(open("results/adjudication_evidence.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open("results/adjudication_sample.csv", encoding="utf-8")))
    n_rule = 0
    for r in rows:
        rid = r["ref_id"]
        if rid in MANUAL:
            lab, note = MANUAL[rid]
            r["adjudicated"], r["note"] = lab, f"manual ({E if 'OpenAlex' not in note else 'evidence file'}): {note}"
        else:
            e = ev[rid]
            t = float(e["ev_title_sim"]); a = e["ev_author_overlap"]
            dy = abs(int(e["ev_year"]) - int(float(e["cited_year"]))) if e["ev_year"] and e["cited_year"] else 0
            assert t >= 0.9 and (not a or float(a) >= 0.5) and dy <= 1, rid
            r["adjudicated"] = "genuine"
            r["note"] = f"rule: {e['evidence_source']} record t={t} a={a or 'n/a'} dyear={dy}"
            n_rule += 1
        r["labelled_by"] = "Claude (AI-assisted from evidence); accepted by author 13 Nov 2026"
    fields = list(rows[0].keys())
    with open("results/adjudication_sample.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(f"rule-labelled {n_rule}, manual {len(rows) - n_rule};", Counter(r["adjudicated"] for r in rows))


if __name__ == "__main__":
    main()
