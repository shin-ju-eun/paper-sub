"""OpenAlex에서 저널별 최신 논문(제목/저자/초록)을 수집. 키 불필요."""
import time
from datetime import datetime, timedelta

import requests

OPENALEX = "https://api.openalex.org/works"


def reconstruct_abstract(inverted):
    """OpenAlex의 abstract_inverted_index를 일반 텍스트로 복원."""
    if not inverted:
        return ""
    positions = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def fetch_journal(journal_name, issn, days_back, max_rows, mailto, include_no_abstract):
    """단일 저널( ISSN )의 최신 논문 목록을 반환."""
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "filter": f"primary_location.source.issn:{issn},from_publication_date:{since},type:article",
        "per-page": min(max_rows, 200),
        "select": "id,doi,title,publication_date,authorships,abstract_inverted_index,primary_location",
        "mailto": mailto,
    }
    headers = {"User-Agent": "PaperSub/1.0"}
    r = requests.get(OPENALEX, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    papers = []
    for w in r.json().get("results", []):
        title = (w.get("title") or "").strip()
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
        if not abstract and not include_no_abstract:
            continue
        doi = w.get("doi") or ""
        authors_list = [a["author"]["display_name"] for a in (w.get("authorships") or [])]
        authors = ", ".join(authors_list[:5]) + (" et al." if len(authors_list) > 5 else "")
        link = doi if doi else (w.get("primary_location") or {}).get("landing_page_url") or ""
        papers.append({
            "journal": journal_name,
            "title": title,
            "authors": authors,
            "date": w.get("publication_date", ""),
            "doi": doi,
            "link": link,
            "abstract": abstract,
        })
    return papers


def fetch_all(config):
    """config의 모든 저널을 순회하며 논문 수집."""
    mailto = config["mailto"]
    days_back = config["days_back"]
    max_rows = config["max_per_journal"]
    include_no_abstract = config.get("include_no_abstract", True)
    all_papers = []
    for name, issn in config["journals"].items():
        try:
            papers = fetch_journal(name, issn, days_back, max_rows, mailto, include_no_abstract)
            all_papers.extend(papers)
            print(f"[{name}] {len(papers)}건")
        except Exception as e:
            print(f"[{name}] 수집 실패: {e}")
        time.sleep(1)  # OpenAlex polite
    return all_papers
