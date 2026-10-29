import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

TERMS = [
    "coronary intervention", "percutaneous coronary intervention", "coronary stent",
    "intravascular imaging", "IVUS", "OCT", "atherectomy", "intravascular lithotripsy",
    "chronic total occlusion", "bifurcation PCI", "coronary guidewire"
]


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "coronary-intervention-book/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    query = 'FIRST_PDATE:[NOW-3DAYS TO NOW] AND (coronary OR percutaneous OR stent OR atherectomy OR lithotripsy)'
    params = urllib.parse.urlencode({"query": query, "format": "json", "pageSize": 50, "resultType": "core"})
    data = fetch_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + params)
    results = []
    for item in data.get("resultList", {}).get("result", []):
        text = " ".join(str(item.get(k, "")) for k in ("title", "abstractText", "journalTitle")).lower()
        if any(term.lower() in text for term in TERMS):
            results.append(item)
    results = results[:12]

    out = Path("drafts/news")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{today.isoformat()}-daily-research-draft.md"
    lines = [
        f"# Daily Coronary Intervention Research Draft — {today.isoformat()}", "",
        "> **Draft — review required.** This automated collection is not medically reviewed and must not be treated as clinical guidance.", "",
        "## Editorial summary", "",
        "This draft collects potentially relevant recent records from Europe PMC for editorial review. Each item must be checked against the original publication before inclusion in the public book or news archive.", "",
        "## Candidate updates", ""
    ]
    if not results:
        lines += ["No relevant records were returned in the current three-day search window.", ""]
    else:
        for index, item in enumerate(results, 1):
            title = re.sub(r"\s+", " ", item.get("title", "Untitled")).strip()
            authors = item.get("authorString", "Authors not listed")
            journal = item.get("journalTitle", "Journal not listed")
            published = item.get("firstPublicationDate", "Date not listed")
            pmid = item.get("pmid")
            doi = item.get("doi")
            url = f"https://europepmc.org/article/MED/{pmid}" if pmid else (f"https://doi.org/{doi}" if doi else "https://europepmc.org/")
            lines += [
                f"### {index}. {title}", "",
                f"- **Published:** {published}",
                f"- **Journal:** {journal}",
                f"- **Authors:** {authors}",
                f"- **Source:** [{url}]({url})", "",
                "**Editorial checks required:** study design, population, intervention, comparator, endpoints, limitations, conflicts of interest, and relevance to the book.", ""
            ]
    lines += [
        "## Possible chapter links", "",
        "- [Balloons and Stents](../docs/book/balloons-and-stents.md)",
        "- [Calcium Modification](../docs/book/calcium-modification.md)",
        "- [Imaging and Physiology](../docs/book/imaging-and-physiology.md)",
        "- [Complications and Safety](../docs/book/complications-and-safety.md)", "",
        f"**Generated:** {dt.datetime.now(dt.timezone.utc).isoformat()}  ",
        "**Status:** Draft  ",
        "**Source search:** Europe PMC, last three days  ",
        "**Medical review:** Required"
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path} with {len(results)} candidate records")


if __name__ == "__main__":
    main()
