import io
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; CampusSolveAI/1.0; "
        "+university-information-agent)"
    )
}


def normalize_domain(url):
    """
    Normalize a URL into a clean domain.
    """

    if not url:
        return ""

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        return (
            parsed.netloc
            .lower()
            .replace("www.", "")
            .split(":")[0]
        )

    except Exception:
        return ""


def _same_domain(url, official_domain):
    """
    Check whether URL belongs to official university domain.
    """

    domain = normalize_domain(url)

    return (
        domain == official_domain
        or domain.endswith("." + official_domain)
    )


def discover_university(
    name,
    provided_url="",
    provided_fb=""
):
    """
    Discover the university's likely official website.
    """

    name = name.strip()
    provided_url = provided_url.strip()
    provided_fb = provided_fb.strip()

    if provided_url:

        domain = normalize_domain(provided_url)

        if not domain:
            return {
                "ok": False,
                "message": "The provided university URL is invalid."
            }

        return {
            "ok": True,
            "university": {
                "name": name,
                "website": provided_url.rstrip("/"),
                "domain": domain,
                "facebook": provided_fb,
            }
        }

    query = f'"{name}" official university website'

    try:
        with DDGS() as ddgs:
            results = list(
                ddgs.text(
                    query,
                    max_results=8
                )
            )

    except Exception as e:
        return {
            "ok": False,
            "message": f"Website discovery failed: {e}"
        }

    candidates = []

    for result in results:

        href = result.get("href") or result.get("url")
        title = result.get("title", "")

        if not href:
            continue

        lower_url = href.lower()

        if (
            "facebook.com" in lower_url
            or "youtube.com" in lower_url
            or "linkedin.com" in lower_url
        ):
            continue

        domain = normalize_domain(href)

        if not domain:
            continue

        score = 0

        if (
            ".edu" in domain
            or ".ac." in domain
            or ".edu." in domain
        ):
            score += 5

        combined = f"{title} {href}".lower()

        if name.lower() in combined:
            score += 3

        if "official" in combined:
            score += 2

        candidates.append(
            {
                "score": score,
                "url": href,
                "domain": domain,
            }
        )

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    if not candidates:

        return {
            "ok": False,
            "message": (
                "No likely official website was found. "
                "Please enter the official university website manually."
            )
        }

    best = candidates[0]

    return {
        "ok": True,
        "university": {
            "name": name,
            "website": best["url"].rstrip("/"),
            "domain": best["domain"],
            "facebook": provided_fb,
        }
    }


def _extract_page(url):
    """
    Extract readable text from HTML or PDF.
    """

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )

        response.raise_for_status()

        content_type = (
            response.headers
            .get("content-type", "")
            .lower()
        )

        if (
            "application/pdf" in content_type
            or url.lower().split("?")[0].endswith(".pdf")
        ):
            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(response.content)
            )

            pages = []

            for page in reader.pages[:8]:
                pages.append(
                    page.extract_text() or ""
                )

            return "\n".join(pages)[:12000]

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            ["script", "style", "noscript", "svg"]
        ):
            tag.decompose()

        return soup.get_text(
            " ",
            strip=True
        )[:12000]

    except Exception:
        return ""


def _date_from_text(text):
    """
    Detect common date formats from page text.
    """

    patterns = [

        r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b",

        r"\b(\d{1,2}[-/]\d{1,2}[-/](?:20)?\d{2})\b",

        (
            r"\b(\d{1,2}\s+"
            r"(?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December)"
            r"\s+20\d{2})\b"
        ),

        (
            r"\b((?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December)"
            r"\s+\d{1,2},\s+20\d{2})\b"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text or "",
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def _search_ddgs(query, max_results):
    """
    Safe DDGS search wrapper.
    """

    try:

        with DDGS() as ddgs:
            return list(
                ddgs.text(
                    query,
                    max_results=max_results
                )
            )

    except Exception:
        return []


def search_university_sources(
    university,
    question,
    department="",
    level="",
    max_results=10
):
    """
    Search official university website first,
    then search Facebook candidates separately.
    """

    domain = university["domain"]
    name = university["name"]

    queries = []

    if level and level != "Any":
        queries.append(
            f'site:{domain} "{level}" "{question}"'
        )

    if department:
        queries.append(
            f'site:{domain} "{department}" "{question}"'
        )

    queries.extend(
        [
            f'site:{domain} "{question}"',
            f'site:{domain} notice "{question}"',
            f'site:{domain} circular "{question}"',
            f'site:{domain} PDF "{question}"',
        ]
    )

    all_results = []
    seen = set()

    # --------------------------------
    # Official university website
    # --------------------------------

    for query in queries:

        results = _search_ddgs(
            query,
            max_results
        )

        for result in results:

            url = (
                result.get("href")
                or result.get("url")
                or ""
            ).strip()

            if not url:
                continue

            if url in seen:
                continue

            if not _same_domain(url, domain):
                continue

            seen.add(url)

            all_results.append(
                {
                    "title": result.get(
                        "title",
                        ""
                    ),
                    "url": url,
                    "snippet": result.get(
                        "body",
                        ""
                    ),
                    "domain": domain,
                    "content": "",
                    "source_type":
                        "University Website",
                    "published_date": None,
                }
            )

    # --------------------------------
    # Facebook candidate search
    # --------------------------------

    fb_query = (
        f'site:facebook.com "{name}" "{question}"'
    )

    fb_results = _search_ddgs(
        fb_query,
        5
    )

    for result in fb_results:

        url = (
            result.get("href")
            or result.get("url")
            or ""
        ).strip()

        if not url:
            continue

        if "facebook.com" not in url.lower():
            continue

        if url in seen:
            continue

        seen.add(url)

        all_results.append(
            {
                "title": result.get(
                    "title",
                    ""
                ),
                "url": url,
                "snippet": result.get(
                    "body",
                    ""
                ),
                "domain": "facebook.com",
                "content": "",
                "source_type":
                    "Facebook Candidate",
                "published_date": None,
            }
        )

    # --------------------------------
    # Fetch content
    # --------------------------------

    for item in all_results[:16]:

        item["content"] = _extract_page(
            item["url"]
        )

        combined_text = (
            item.get("content", "")
            + " "
            + item.get("snippet", "")
        )

        item["published_date"] = (
            _date_from_text(combined_text)
        )

    return all_results[:16]