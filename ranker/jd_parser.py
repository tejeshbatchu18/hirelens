import re


# ---------------------------------------------------------
# Known technical skills
# ---------------------------------------------------------
COMMON_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "node.js",
    "nodejs",
    "fastapi",
    "django",
    "flask",
    "spring boot",
    "spring",
    "sql",
    "mysql",
    "postgresql",
    "postgres",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "kafka",
    "spark",
    "hadoop",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "nlp",
    "llm",
    "generative ai",
    "rag",
    "faiss",
    "embeddings",
    "vector search",
    "information retrieval",
    "data science",
    "data engineering",
    "express",
    "express.js",
    "rest api",
    "graphql",
    "git",
    "github",
]


# ---------------------------------------------------------
# Skill aliases
# ---------------------------------------------------------
SKILL_ALIASES = {
    "nodejs": "node.js",
    "node.js": "node.js",

    "express.js": "express",

    "postgres": "postgresql",

    "reactjs": "react",
    "react.js": "react",

    "vue.js": "vue",

    "scikit learn": "scikit-learn",

    "ml": "machine learning",

    "dl": "deep learning",

    "gen ai": "generative ai",
    "genai": "generative ai",
}


# ---------------------------------------------------------
# Optional / nice-to-have indicators
# ---------------------------------------------------------
OPTIONAL_MARKERS = [
    "nice to have",
    "nice-to-have",
    "nice to have:",
    "preferred",
    "preferably",
    "plus",
    "bonus",
    "optional",
    "good to have",
    "good-to-have",
    "would be a plus",
    "is a plus",
]


# ---------------------------------------------------------
# Required indicators
# ---------------------------------------------------------
REQUIRED_MARKERS = [
    "required",
    "requirements",
    "must have",
    "must-have",
    "mandatory",
    "essential",
    "strong",
    "proficient",
    "proficiency",
    "experience with",
    "hands-on experience",
]


# ---------------------------------------------------------
# Normalization
# ---------------------------------------------------------
def _normalize_skill(skill):
    """
    Normalize skill names so aliases are represented
    consistently.
    """

    skill = skill.strip().lower()

    return SKILL_ALIASES.get(
        skill,
        skill,
    )


# ---------------------------------------------------------
# Skill matching
# ---------------------------------------------------------
def _skill_pattern(skill):
    """
    Build a regex that matches the complete skill rather
    than an arbitrary substring.

    This prevents:
        java -> matching javascript

    while still allowing:
        node.js
        nodejs
        react.js
    """

    escaped = re.escape(skill)

    # Allow optional whitespace around punctuation such as ".".
    escaped = escaped.replace(
        r"\.",
        r"\s*\.\s*",
    )

    return rf"(?<![a-zA-Z0-9+#]){escaped}(?![a-zA-Z0-9+#])"


def _find_skills_in_text(text):
    """
    Find known technical skills using word-boundary-aware
    matching.

    Returns normalized unique skill names.
    """

    if not text:
        return set()

    found = set()

    for skill in COMMON_SKILLS:

        pattern = _skill_pattern(
            skill
        )

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found.add(
                _normalize_skill(skill)
            )

    return found


# ---------------------------------------------------------
# Extract all skills
# ---------------------------------------------------------
def _extract_skills(text):
    """
    Find known technical skills mentioned in the JD.

    Uses boundary-aware matching so that:
        JavaScript != Java

    Returns unique normalized skills.
    """

    return sorted(
        _find_skills_in_text(text)
    )


# ---------------------------------------------------------
# Extract required vs nice-to-have skills
# ---------------------------------------------------------
def _extract_skill_categories(text):
    """
    Split detected skills into:

        required_skills
        nice_to_have_skills

    Classification is based on the sentence/line in which
    the skill appears.

    Example:

        React
        PostgreSQL
        Docker is a plus

    becomes:

        required:
            React
            PostgreSQL

        nice-to-have:
            Docker
    """

    required = set()
    nice_to_have = set()

    lines = re.split(
        r"[\r\n]+",
        text,
    )

    for line in lines:

        line = line.strip()

        if not line:
            continue

        line_skills = _find_skills_in_text(
            line
        )

        if not line_skills:
            continue

        lower_line = line.lower()

        is_optional = any(
            marker in lower_line
            for marker in OPTIONAL_MARKERS
        )

        if is_optional:

            nice_to_have.update(
                line_skills
            )

        else:

            required.update(
                line_skills
            )

    # A skill explicitly marked nice-to-have should not
    # remain in the required list.
    required -= nice_to_have

    return (
        sorted(required),
        sorted(nice_to_have),
    )


# ---------------------------------------------------------
# Experience extraction
# ---------------------------------------------------------
def _extract_experience(text):
    """
    Extract common experience requirements.

    Supported examples:

        4+ years
        3-5 years
        3 to 5 years
        3 years of experience
        minimum 3 years
        at least 3 years
    """

    text_lower = text.lower()

    # -----------------------------------------------------
    # Range:
    # 3-5 years
    # 3 to 5 years
    # -----------------------------------------------------
    range_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(?:-|to)\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"years?\b",
        text_lower,
    )

    if range_match:

        low = float(
            range_match.group(1)
        )

        high = float(
            range_match.group(2)
        )

        return low, high

    # -----------------------------------------------------
    # Minimum:
    # 4+ years
    # 4+ years of experience
    # at least 4 years
    # minimum 4 years
    # -----------------------------------------------------
    minimum_match = re.search(
        r"(?:at least|minimum of?|minimum)?\s*"
        r"(\d+(?:\.\d+)?)\s*\+?\s*"
        r"years?\b",
        text_lower,
    )

    if minimum_match:

        value = float(
            minimum_match.group(1)
        )

        # Detect explicit upper-range syntax separately.
        if "+" in minimum_match.group(0):
            return value, None

        # If words "minimum" or "at least" appear,
        # this is also a minimum.
        prefix = text_lower[
            max(
                0,
                minimum_match.start() - 15,
            ):minimum_match.start()
        ]

        if (
            "minimum" in prefix
            or "at least" in prefix
        ):
            return value, None

    # -----------------------------------------------------
    # Plain:
    # 3 years of experience
    # -----------------------------------------------------
    plain_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*"
        r"years?\s+"
        r"(?:of\s+)?experience\b",
        text_lower,
    )

    if plain_match:

        value = float(
            plain_match.group(1)
        )

        return value, value

    return None, None


# ---------------------------------------------------------
# Location extraction
# ---------------------------------------------------------
LOCATIONS = [
    "india",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "chennai",
    "mumbai",
    "pune",
    "delhi",
    "new delhi",
    "vijayawada",
    "usa",
    "united states",
    "uk",
    "united kingdom",
    "canada",
    "australia",
    "remote",
]


def _extract_location(text):
    """
    Extract simple location requirements using
    boundary-aware matching.
    """

    found = []

    for location in LOCATIONS:

        pattern = rf"(?<![a-zA-Z]){re.escape(location)}(?![a-zA-Z])"

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            found.append(
                location
            )

    return sorted(
        set(found)
    )


# ---------------------------------------------------------
# Main JD parser
# ---------------------------------------------------------
def parse_job_description(job_description):
    """
    Convert raw JD text into structured requirements.

    Returns:

        {
            "skills": [...],
            "required_skills": [...],
            "nice_to_have_skills": [...],
            "min_experience": ...,
            "max_experience": ...,
            "locations": [...],
            "raw_text": "..."
        }
    """

    if not job_description or not job_description.strip():

        raise ValueError(
            "Job description cannot be empty."
        )

    text = job_description.strip()

    required_skills, nice_to_have_skills = (
        _extract_skill_categories(
            text
        )
    )

    min_experience, max_experience = (
        _extract_experience(
            text
        )
    )

    locations = _extract_location(
        text
    )

    return {
        # Keep "skills" for compatibility with the
        # current scoring/reasoning code.
        "skills": required_skills,

        "required_skills": required_skills,

        "nice_to_have_skills": nice_to_have_skills,

        "min_experience": min_experience,

        "max_experience": max_experience,

        "locations": locations,

        "raw_text": text,
    }