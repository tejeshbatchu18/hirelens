CSV_SAFE = str.maketrans({
    '"': "'",
    "\n": " ",
    "\r": " ",
})


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
}


def _normalise_skill(skill):
    skill = (skill or "").strip().lower()

    return SKILL_ALIASES.get(
        skill,
        skill,
    )


def _candidate_skills(c):
    """Return normalized candidate skill names."""

    return {
        _normalise_skill(s.get("name"))
        for s in c.skills
        if isinstance(s, dict)
        and s.get("name")
    }


def _matched_required_skills(c, jd_requirements):
    """
    Find which skills required by the uploaded JD are
    present in the candidate profile.
    """

    if not jd_requirements:
        return []

    required = jd_requirements.get(
        "skills",
        [],
    )

    candidate_skills = _candidate_skills(c)

    matched = []

    for required_skill in required:

        required_normalized = _normalise_skill(
            required_skill
        )

        for candidate_skill in candidate_skills:

            if (
                candidate_skill == required_normalized
                or candidate_skill in required_normalized
                or required_normalized in candidate_skill
            ):
                matched.append(required_skill)
                break

    return matched


def _experience_reason(c, jd_requirements):
    """Create an explanation for the experience requirement."""

    if not jd_requirements:
        return None

    min_exp = jd_requirements.get(
        "min_experience"
    )

    max_exp = jd_requirements.get(
        "max_experience"
    )

    if min_exp is None and max_exp is None:
        return None

    years = c.yoe

    if min_exp is not None and max_exp is not None:

        if min_exp <= years <= max_exp:
            return (
                f"{years:g} years of experience is "
                f"within the requested {min_exp}-{max_exp} year range."
            )

        if years < min_exp:
            return (
                f"{years:g} years of experience is below "
                f"the requested {min_exp}-{max_exp} year range."
            )

        return (
            f"{years:g} years of experience is above "
            f"the requested {min_exp}-{max_exp} year range."
        )

    if min_exp is not None:

        if years >= min_exp:
            return (
                f"{years:g} years of experience meets "
                f"the {min_exp}+ year requirement."
            )

        return (
            f"{years:g} years of experience is below "
            f"the {min_exp}+ year requirement."
        )

    if max_exp is not None:

        if years <= max_exp:
            return (
                f"{years:g} years of experience is within "
                f"the maximum {max_exp}-year requirement."
            )

        return (
            f"{years:g} years of experience exceeds "
            f"the {max_exp}-year maximum."
        )

    return None


def _location_reason(c, jd_requirements):
    """Create an explanation for the location requirement."""

    if not jd_requirements:
        return None

    required_locations = jd_requirements.get(
        "locations",
        [],
    )

    if not required_locations:
        return None

    candidate_location = c.location.lower()
    candidate_country = c.country.lower()

    for location in required_locations:

        location = location.lower()

        if location == "remote":
            return "The role allows remote work."

        if location in candidate_location:
            return (
                f"Location matches the JD requirement "
                f"({location.title()})."
            )

        if location in candidate_country:
            return (
                f"Country matches the JD requirement "
                f"({location.title()})."
            )

    if c.sig.get("willing_to_relocate"):
        return (
            "Current location does not directly match "
            "the stated JD location, but the candidate is "
            "willing to relocate."
        )

    return (
        "Current location does not directly match "
        "the stated JD location."
    )


def _match_summary(c, jd_requirements):
    """Summarize required-skill coverage."""

    if not jd_requirements:
        return None

    required = jd_requirements.get(
        "skills",
        [],
    )

    if not required:
        return None

    matched = _matched_required_skills(
        c,
        jd_requirements,
    )

    return (
        len(matched),
        len(required),
        matched,
    )


def build_reason(c, b, jd_requirements=None):
    """
    Build a deterministic explanation grounded in the
    candidate profile and the uploaded JD.
    """

    parts = []

    role = c.title or "Unknown role"
    yrs = f"{c.yoe:g}"

    parts.append(
        f"{role} with {yrs} years of experience."
    )

    # ---------------------------------------------------------
    # Uploaded JD mode
    # ---------------------------------------------------------
    if jd_requirements is not None:

        summary = _match_summary(
            c,
            jd_requirements,
        )

        if summary:

            matched_count, required_count, matched = summary

            if matched:
                display = ", ".join(
                    matched[:6]
                )

                if matched_count == required_count:
                    parts.append(
                        f"Matches all {required_count} "
                        f"detected required skills: {display}."
                    )
                else:
                    parts.append(
                        f"Matches {matched_count} of "
                        f"{required_count} detected required skills: "
                        f"{display}."
                    )
            else:
                parts.append(
                    f"No direct matches found among the "
                    f"{required_count} detected required skills."
                )

        experience_reason = _experience_reason(
            c,
            jd_requirements,
        )

        if experience_reason:
            parts.append(
                experience_reason
            )

        location_reason = _location_reason(
            c,
            jd_requirements,
        )

        if location_reason:
            parts.append(
                location_reason
            )

        # Evidence
        if b["evidence"] >= 0.55:
            parts.append(
                "Career history contains strong evidence of "
                "hands-on technical work."
            )
        elif b["skills"] >= 0.55:
            parts.append(
                "Required skills are present, but the career "
                "history provides more limited supporting evidence."
            )

    # ---------------------------------------------------------
    # Original fixed-JD fallback
    # ---------------------------------------------------------
    else:

        if b["evidence"] >= 0.55:
            parts.append(
                "Career history shows strong hands-on "
                "technical evidence."
            )
        elif b["skills"] >= 0.55:
            parts.append(
                "Skills are present but production evidence "
                "is more limited."
            )

        if b["seniority"] >= 0.85:
            parts.append(
                "Experience aligns with the configured "
                "seniority range."
            )

        if b["location"] >= 0.85:
            parts.append(
                "Location aligns with the configured "
                "location preference."
            )

    # ---------------------------------------------------------
    # Availability
    # ---------------------------------------------------------
    rr = float(
        c.s(
            "recruiter_response_rate",
            0.0,
        )
    )

    if b["behavioral_modifier"] >= 1.0:

        parts.append(
            f"Active and responsive "
            f"({rr * 100:.0f}% recruiter response)."
        )

    elif b["behavioral_modifier"] <= 0.72:

        parts.append(
            f"Lower availability signal "
            f"({rr * 100:.0f}% recruiter response or inactive)."
        )

    # ---------------------------------------------------------
    # Notice period
    # ---------------------------------------------------------
    notice = int(
        c.s(
            "notice_period_days",
            60,
        )
    )

    if notice > 60:
        parts.append(
            f"Notice period: {notice} days."
        )

    # ---------------------------------------------------------
    # Career trajectory
    # ---------------------------------------------------------
    if b["trajectory"] <= 0.4:
        parts.append(
            "Career history contains relatively short stints."
        )

    return " ".join(parts).translate(
        CSV_SAFE
    ).strip()