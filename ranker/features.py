import math

from .rubric import (
    MUST_HAVE_GROUPS,
    NICE_TO_HAVE_TERMS,
    SENIORITY,
    PREFERRED_LOCATIONS,
    WELCOME_LOCATIONS,
)

PROF = {
    "beginner": 0.35,
    "intermediate": 0.6,
    "advanced": 0.85,
    "expert": 1.0,
}


def _clip01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


# --------------------------- skill trust -----------------------------------

def _skill_trust(s, assessment_scores):
    """How much do we believe this self-reported skill? -> [0,1]."""

    prof = PROF.get(
        s.get("proficiency"),
        0.5,
    )

    endors = int(
        s.get("endorsements") or 0
    )

    dur = int(
        s.get("duration_months") or 0
    )

    # Endorsements: diminishing returns.
    e = (
        math.log1p(min(endors, 30))
        / math.log1p(30)
    )

    # Duration: 24+ months gives full credit.
    d = min(dur, 24) / 24.0

    trust = (
        0.35 * prof
        + 0.35 * d
        + 0.30 * e
    )

    # Platform assessment provides additional evidence.
    name = (s.get("name") or "").lower()

    if assessment_scores:
        matching_score = None

        for skill_name, score in assessment_scores.items():
            if skill_name.lower() == name:
                matching_score = score
                break

        if matching_score is not None:
            a = float(matching_score) / 100.0
            trust = (
                0.6 * trust
                + 0.4 * a
            )

    return _clip01(trust)


# --------------------------- skill matching -------------------------------

SKILL_ALIASES = {
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "llm": "llm",
}


def _normalise_skill(skill):
    """Normalize common variations of technical skill names."""

    skill = (skill or "").strip().lower()

    return SKILL_ALIASES.get(
        skill,
        skill,
    )


def _candidate_trusted_skills(c):
    """Return candidate skills with their trust scores."""

    assess = c.sig.get(
        "skill_assessment_scores"
    ) or {}

    trusted = {}

    for s in c.skills:
        if not isinstance(s, dict):
            continue

        name = _normalise_skill(
            s.get("name")
        )

        if not name:
            continue

        trust = _skill_trust(
            s,
            assess,
        )

        trusted[name] = max(
            trusted.get(name, 0.0),
            trust,
        )

    return trusted


def _skill_matches(candidate_skill, required_skill):
    """
    Flexible matching between a candidate skill and a JD skill.

    Example:
        candidate: "node.js"
        JD:        "node"

    or:
        candidate: "postgresql"
        JD:        "postgres"
    """

    candidate_skill = _normalise_skill(
        candidate_skill
    )

    required_skill = _normalise_skill(
        required_skill
    )

    if candidate_skill == required_skill:
        return True

    return (
        candidate_skill in required_skill
        or required_skill in candidate_skill
    )


def skill_score(c, jd_requirements=None):
    """
    Calculate skill coverage.

    If an uploaded JD is supplied, score the candidate against
    the skills extracted from that JD.

    Otherwise, preserve the original challenge rubric.
    """

    trusted = _candidate_trusted_skills(c)

    # ---------------------------------------------------------
    # Dynamic JD mode
    # ---------------------------------------------------------
    if jd_requirements is not None:

        required_skills = jd_requirements.get(
            "skills",
            [],
        )

        if not required_skills:
            return 1.0

        total = 0.0

        for required_skill in required_skills:

            best = 0.0

            for candidate_skill, trust in trusted.items():

                if _skill_matches(
                    candidate_skill,
                    required_skill,
                ):
                    best = max(
                        best,
                        trust,
                    )

            total += best

        return _clip01(
            total / len(required_skills)
        )

    # ---------------------------------------------------------
    # Original fixed-rubric mode
    # ---------------------------------------------------------
    total_w = 0.0
    got = 0.0

    for grp in MUST_HAVE_GROUPS.values():

        w = grp["weight"]

        total_w += w

        best = 0.0

        for term in grp["terms"]:

            for skill_name, trust in trusted.items():

                if term in skill_name:
                    best = max(
                        best,
                        trust,
                    )

        got += w * best

    return (
        _clip01(got / total_w)
        if total_w
        else 0.0
    )


# --------------------------- career evidence -------------------------------

EVIDENCE_STRONG = [
    "ranking",
    "recommendation",
    "recommender",
    "search",
    "retrieval",
    "embeddings",
    "semantic search",
    "vector",
    "relevance",
    "matching",
    "personalization",
    "information retrieval",
    "learning to rank",
]

EVIDENCE_PROD = [
    "production",
    "deployed",
    "shipped",
    "scale",
    "users",
    "latency",
    "real-time",
    "serving",
    "a/b",
    "millions",
    "traffic",
]

PRODUCT_INDUSTRIES = [
    "product",
    "saas",
    "internet",
    "consumer",
    "e-commerce",
    "fintech",
    "technology",
    "software product",
]


def evidence_score(c):
    """
    Does the career history show relevant engineering evidence?

    This remains based on the original evidence model for now.
    We will make this fully JD-aware in a later improvement.
    """

    text = c.career_text().lower()

    strong = sum(
        1
        for t in EVIDENCE_STRONG
        if t in text
    )

    prod = sum(
        1
        for t in EVIDENCE_PROD
        if t in text
    )

    s_strong = min(
        strong,
        5,
    ) / 5.0

    s_prod = min(
        prod,
        4,
    ) / 4.0

    companies = c.companies()

    if companies:
        product_signal = 1.0
    else:
        product_signal = 1.0

    score = (
        0.6 * s_strong
        + 0.4 * s_prod
    ) * (
        0.7
        + 0.3 * product_signal
    )

    return _clip01(score)


# --------------------------- nice to have ----------------------------------

def nice_to_have_bonus(c, jd_requirements=None):
    """
    Small bonus for additional skills relevant to the uploaded JD.

    For a custom JD, this rewards candidates who match several
    requested technologies.

    For the original fixed challenge, the old rubric is preserved.
    """

    # Dynamic JD mode
    if jd_requirements is not None:

        required_skills = jd_requirements.get(
            "skills",
            [],
        )

        if not required_skills:
            return 0.0

        trusted = _candidate_trusted_skills(c)

        matched = 0

        for required_skill in required_skills:

            if any(
                _skill_matches(
                    candidate_skill,
                    required_skill,
                )
                for candidate_skill in trusted
            ):
                matched += 1

        # Small capped bonus.
        return _clip01(
            matched / max(
                len(required_skills),
                1,
            )
        )

    # Original fixed challenge behavior
    text = c.full_text().lower()

    hits = sum(
        1
        for t in NICE_TO_HAVE_TERMS
        if t in text
    )

    return _clip01(
        hits / 6.0
    )


# --------------------------- seniority -------------------------------------

def seniority_score(c, jd_requirements=None):
    """
    Compare candidate experience against the uploaded JD.

    If the JD does not specify experience, return a neutral
    full score rather than penalizing the candidate.
    """

    # Dynamic JD mode
    if jd_requirements is not None:

        min_exp = jd_requirements.get(
            "min_experience"
        )

        max_exp = jd_requirements.get(
            "max_experience"
        )

        # JD does not specify experience.
        if min_exp is None and max_exp is None:
            return 1.0

        y = c.yoe

        # JD specifies a range, e.g. 3-5 years.
        if min_exp is not None and max_exp is not None:

            if min_exp <= y <= max_exp:
                return 1.0

            if y < min_exp:
                gap = min_exp - y
                return _clip01(
                    1.0 - 0.18 * gap
                )

            gap = y - max_exp

            return _clip01(
                1.0 - 0.12 * gap
            )

        # JD specifies minimum experience, e.g. 4+ years.
        if min_exp is not None:

            if y >= min_exp:
                return 1.0

            gap = min_exp - y

            return _clip01(
                1.0 - 0.18 * gap
            )

        # JD specifies only a maximum.
        if max_exp is not None:

            if y <= max_exp:
                return 1.0

            gap = y - max_exp

            return _clip01(
                1.0 - 0.12 * gap
            )

    # Original fixed-rubric mode
    y = c.yoe

    lo = SENIORITY["ideal_lo"]
    hi = SENIORITY["ideal_hi"]

    if lo <= y <= hi:
        return 1.0

    if SENIORITY["ok_lo"] <= y <= SENIORITY["ok_hi"]:
        return 0.85

    if y < SENIORITY["ok_lo"]:
        return _clip01(
            0.85
            - 0.18 * (
                SENIORITY["ok_lo"] - y
            )
        )

    return _clip01(
        0.85
        - 0.12 * (
            y - SENIORITY["ok_hi"]
        )
    )


# --------------------------- trajectory ------------------------------------

def trajectory_score(c):
    """Reward stable tenure and product time."""

    avg = c.avg_tenure_months()

    if avg <= 0:
        base = 0.5
    elif avg < 18:
        base = 0.35
    elif avg < 30:
        base = 0.7
    else:
        base = 1.0

    long_stint = any(
        (r.get("duration_months") or 0) >= 36
        for r in c.career
        if isinstance(r, dict)
    )

    if long_stint:
        base = min(
            1.0,
            base + 0.1,
        )

    return _clip01(base)


# --------------------------- location --------------------------------------

def location_score(c, jd_requirements=None):
    """
    Compare candidate location with the uploaded JD location.

    If the JD does not specify a location, return a neutral score.
    """

    # Dynamic JD mode
    if jd_requirements is not None:

        required_locations = jd_requirements.get(
            "locations",
            [],
        )

        # No location requirement in the JD.
        if not required_locations:
            return 1.0

        candidate_location = c.location.lower()
        candidate_country = c.country.lower()

        for required in required_locations:

            required = required.lower()

            # Remote role.
            if required == "remote":
                return 1.0

            # Direct location match.
            if required in candidate_location:
                return 1.0

            # Country match.
            if required in candidate_country:
                return 1.0

            # India-wide match.
            if (
                required == "india"
                and "india" in candidate_country
            ):
                return 1.0

        # Candidate is in India and willing to relocate.
        if (
            "india" in required_locations
            and c.sig.get("willing_to_relocate")
        ):
            return 0.75

        return 0.3

    # Original fixed challenge behavior
    loc = c.location.lower()

    relocate = bool(
        c.sig.get("willing_to_relocate")
    )

    in_india = (
        "india" in loc
        or c.country.lower() == "india"
    )

    if any(
        p in loc
        for p in PREFERRED_LOCATIONS
    ):
        return 1.0

    if any(
        w in loc
        for w in WELCOME_LOCATIONS
    ):
        return 0.85

    if in_india and relocate:
        return 0.72

    if in_india:
        return 0.55

    return (
        0.30
        if relocate
        else 0.18
    )


# --------------------------- behavioral modifier ---------------------------

def behavioral_modifier(c):
    """
    Multiplier on the fit score from availability and engagement.
    """

    from .schema import TODAY, _d

    rr = float(
        c.s(
            "recruiter_response_rate",
            0.0,
        )
    )

    icr = float(
        c.s(
            "interview_completion_rate",
            0.0,
        )
    )

    compl = float(
        c.s(
            "profile_completeness_score",
            0.0,
        )
    ) / 100.0

    open_w = (
        1.0
        if c.sig.get("open_to_work_flag")
        else 0.0
    )

    la = _d(
        c.sig.get("last_active_date")
    )

    if la:
        days = (
            TODAY - la
        ).days

        recency = (
            1.0
            if days <= 14
            else 0.8
            if days <= 45
            else 0.55
            if days <= 120
            else 0.3
        )
    else:
        recency = 0.4

    verified = (
        (
            1.0
            if c.sig.get("verified_email")
            else 0.0
        ) * 0.5
        +
        (
            1.0
            if c.sig.get("verified_phone")
            else 0.0
        ) * 0.5
    )

    raw = (
        0.32 * rr
        + 0.26 * recency
        + 0.14 * icr
        + 0.12 * compl
        + 0.10 * open_w
        + 0.06 * verified
    )

    return 0.55 + 0.55 * _clip01(raw)


# --------------------------- notice period ---------------------------------

def notice_period_penalty(c):
    """Small multiplicative penalty for long notice period."""

    np_ = int(
        c.s(
            "notice_period_days",
            60,
        )
    )

    if np_ <= 30:
        return 1.0

    if np_ <= 60:
        return 0.97

    if np_ <= 90:
        return 0.93

    return 0.88