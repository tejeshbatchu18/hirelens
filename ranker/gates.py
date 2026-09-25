from .rubric import (
    SERVICES_FIRMS,
    RESEARCH_ONLY_MARKERS,
    PRODUCTION_MARKERS,
    OFF_DOMAIN_MARKERS,
    NLP_IR_MARKERS,
    NON_TECHNICAL_TITLE_MARKERS,
    TECHNICAL_TITLE_MARKERS,
)


# ----------------------------- honeypots -----------------------------------

def honeypot_reason(c):
    """
    Detect obviously inconsistent or impossible candidate data.

    These checks are JD-independent and are therefore safe to
    use for both the original challenge and uploaded JDs.
    """

    # ---------------------------------------------------------
    # (1) Multiple expert skills with zero months of experience
    # ---------------------------------------------------------
    zero_expert = 0

    for s in c.skills:
        if not isinstance(s, dict):
            continue

        if (
            s.get("proficiency") == "expert"
            and int(s.get("duration_months") or 0) == 0
        ):
            zero_expert += 1

    if zero_expert >= 2:
        return (
            "impossible skills: multiple "
            "'expert' skills with 0 months of use"
        )

    # ---------------------------------------------------------
    # (2) Claimed experience significantly exceeds career history
    # ---------------------------------------------------------
    if (
        c.yoe > 5
        and (
            c.yoe * 12
            - c.total_career_months()
        ) > 72
    ):
        return (
            "experience inflated: years_of_experience "
            "far exceeds career history"
        )

    # ---------------------------------------------------------
    # (3) Impossible individual career tenure
    # ---------------------------------------------------------
    cap = (
        c.yoe * 12 + 24
        if c.yoe
        else 480
    )

    for r in c.career:

        if not isinstance(r, dict):
            continue

        dur = int(
            r.get("duration_months") or 0
        )

        if (
            dur > max(cap, 60)
            or dur > 480
        ):
            return (
                "impossible tenure: single role "
                "longer than entire career"
            )

    return None


# --------------------------- original challenge gate -----------------------

def original_disqualifier_reason(c):
    """
    Original challenge-specific disqualifiers.

    These are retained for backward compatibility with the original
    Senior AI Engineer challenge, but should NOT be used as universal
    rules for arbitrary uploaded JDs.
    """

    title = c.title.lower()
    ctext = c.career_text().lower()
    companies = c.companies()

    # (1) Non-technical current title
    if (
        any(
            term in title
            for term in NON_TECHNICAL_TITLE_MARKERS
        )
        and not any(
            term in title
            for term in TECHNICAL_TITLE_MARKERS
        )
    ):
        return (
            "non-technical role for an AI-engineering "
            f"position (title: {c.title})"
        )

    # (2) Entire career at services/consulting firms
    if companies:

        services_hits = sum(
            1
            for co in companies
            if any(
                firm in co
                for firm in SERVICES_FIRMS
            )
        )

        if services_hits == len(companies):
            return (
                "career entirely at services/consulting "
                "firms (no product experience)"
            )

    # (3) Pure research without production evidence
    research = any(
        term in ctext
        for term in RESEARCH_ONLY_MARKERS
    )

    production = any(
        term in ctext
        for term in PRODUCTION_MARKERS
    )

    if research and not production:
        return (
            "pure-research background with "
            "no production deployment"
        )

    # (4) CV/speech/robotics without NLP/IR
    off_domain = any(
        term in ctext
        for term in OFF_DOMAIN_MARKERS
    )

    nlp_ir = any(
        term in ctext
        for term in NLP_IR_MARKERS
    )

    if off_domain and not nlp_ir:
        return (
            "primary expertise in CV/speech/robotics "
            "without NLP/IR exposure"
        )

    return None


# ----------------------------- gate ----------------------------------------

def gate(c, jd_requirements=None):
    """
    Returns:

        (passed, reason, kind)

    kind is either:
        "honeypot"
        "disqualifier"
        None

    For uploaded/custom JDs, only generic data-quality checks
    are applied.

    The original challenge-specific disqualifiers are only used
    when jd_requirements is None.
    """

    # ---------------------------------------------------------
    # Always perform generic data-quality validation.
    # ---------------------------------------------------------
    reason = honeypot_reason(c)

    if reason:
        return (
            False,
            reason,
            "honeypot",
        )

    # ---------------------------------------------------------
    # Custom JD mode
    # ---------------------------------------------------------
    if jd_requirements is not None:
        return (
            True,
            None,
            None,
        )

    # ---------------------------------------------------------
    # Original fixed-JD mode
    # ---------------------------------------------------------
    reason = original_disqualifier_reason(c)

    if reason:
        return (
            False,
            reason,
            "disqualifier",
        )

    return (
        True,
        None,
        None,
    )