from urllib.parse import urlparse


def _domain(url):
    if not url:
        return ""

    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .replace("www.", "")
            .split(":")[0]
        )
    except Exception:
        return ""


def _normalize_url(url):
    if not url:
        return ""

    url = url.strip()

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    return url.rstrip("/")


def _same_domain(url, official_domain):
    domain = _domain(url)

    return (
        domain == official_domain
        or domain.endswith("." + official_domain)
    )


def _same_facebook_page(url, official_fb):
    """
    Compare the configured official Facebook URL
    with the discovered Facebook URL.
    """

    if not official_fb:
        return False

    return (
        _normalize_url(url).lower()
        == _normalize_url(official_fb).lower()
    )


def _relevance_score(source):
    text = (
        source.get("title", "")
        + " "
        + source.get("snippet", "")
        + " "
        + source.get("content", "")
    ).lower()

    keywords = [
        "notice",
        "circular",
        "exam",
        "examination",
        "registration",
        "form fill",
        "form-fill",
        "admission",
        "result",
        "fee",
        "deadline",
        "schedule",
        "routine",
        "ordinance",
        "office order",
        "application",
    ]

    return sum(
        2 for keyword in keywords
        if keyword in text
    )


def rank_and_verify_sources(
    sources,
    university
):
    """
    Rank sources and explicitly mark which ones
    are valid official evidence.
    """

    official_domain = university["domain"]
    official_fb = university.get(
        "facebook",
        ""
    )

    verified = []
    candidates = []

    for source in sources:

        item = dict(source)

        url = item.get("url", "")

        # ----------------------------
        # Official university website
        # ----------------------------

        if _same_domain(
            url,
            official_domain
        ):

            item["tier"] = (
                "Priority 1 — Official University Website"
            )

            item["tier_score"] = 100
            item["is_valid_official"] = True

        # ----------------------------
        # Configured official Facebook
        # ----------------------------

        elif _same_facebook_page(
            url,
            official_fb
        ):

            item["tier"] = (
                "Priority 2 — Official Facebook Page"
            )

            item["tier_score"] = 75
            item["is_valid_official"] = True

        # ----------------------------
        # Unverified Facebook candidate
        # ----------------------------

        elif (
            _domain(url) == "facebook.com"
            or _domain(url).endswith(
                ".facebook.com"
            )
        ):

            item["tier"] = (
                "Facebook Candidate — Not Verified"
            )

            item["tier_score"] = 30
            item["is_valid_official"] = False

        # ----------------------------
        # Other source
        # ----------------------------

        else:

            item["tier"] = "Other Source"
            item["tier_score"] = 10
            item["is_valid_official"] = False

        relevance = _relevance_score(item)

        item["verification_score"] = (
            item["tier_score"]
            + relevance
        )

        if item["is_valid_official"]:
            verified.append(item)
        else:
            candidates.append(item)

    # Official sources first
    verified.sort(
        key=lambda x: x["verification_score"],
        reverse=True
    )

    # Candidates separately
    candidates.sort(
        key=lambda x: x["verification_score"],
        reverse=True
    )

    # Keep verified sources first.
    # Candidates remain available for UI inspection.
    return verified + candidates