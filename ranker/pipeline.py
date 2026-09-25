from collections import Counter

from .schema import Candidate
from . import schema
from .gates import gate
from .embeddings import SemanticScorer
from .scoring import score_candidate
from .reasoning import build_reason
from .jd_parser import parse_job_description


def rank_candidates(
    raw_candidates,
    top_n=25,
    job_description=None,
):
    """
    Rank candidates against the supplied job description.

    Pipeline:
        candidates
            ↓
        candidate validation
            ↓
        JD parsing
            ↓
        gating
            ↓
        semantic scoring
            ↓
        feature scoring
            ↓
        final ranking
            ↓
        explanations
            ↓
        Top-N results
    """

    # ---------------------------------------------------------
    # Validate Top-N
    # ---------------------------------------------------------
    if top_n < 1:
        raise ValueError(
            "top_n must be at least 1"
        )

    # ---------------------------------------------------------
    # Parse Job Description
    # ---------------------------------------------------------
    if job_description:
        jd_requirements = parse_job_description(
            job_description
        )
    else:
        jd_requirements = None

    # ---------------------------------------------------------
    # Convert raw dictionaries into Candidate objects
    # ---------------------------------------------------------
    candidates = [
        c if isinstance(c, Candidate)
        else Candidate(c)
        for c in raw_candidates
    ]

    # ---------------------------------------------------------
    # Set dataset reference date
    # ---------------------------------------------------------
    dates = [
        schema._d(
            c.sig.get("last_active_date")
        )
        for c in candidates
    ]

    dates = [
        d
        for d in dates
        if d
    ]

    schema.set_reference_date(
        max(dates)
        if dates
        else schema.date(2025, 1, 1)
    )

    # ---------------------------------------------------------
    # Gate candidates before scoring
    # ---------------------------------------------------------
    survivors = []
    rejected = []

    for c in candidates:

        ok, reason, kind = gate(c)

        if ok:

            survivors.append(c)

        else:

            rejected.append({
                "candidate_id": c.id,
                "gated": True,
                "kind": kind,
                "reason": reason,
            })

    # ---------------------------------------------------------
    # Semantic scoring
    # ---------------------------------------------------------
    #
    # If an uploaded JD is provided, SemanticScorer uses
    # the uploaded JD.
    #
    # Otherwise it falls back to the original fixed JD.
    # ---------------------------------------------------------
    semantic = SemanticScorer(
        survivors,
        job_description=job_description,
    )

    # ---------------------------------------------------------
    # Candidate scoring
    # ---------------------------------------------------------
    scored = []

    for c in survivors:

        breakdown = score_candidate(
            c,
            semantic,
            jd_requirements,
        )

        scored.append(
            (
                c,
                breakdown,
            )
        )

    # ---------------------------------------------------------
    # Round score used for deterministic ranking
    # ---------------------------------------------------------
    for c, breakdown in scored:

        breakdown["_score_r"] = round(
            breakdown["final"],
            4,
        )

    # ---------------------------------------------------------
    # Sort highest score first
    #
    # Candidate ID provides deterministic ordering when
    # two candidates have exactly the same score.
    # ---------------------------------------------------------
    scored.sort(
        key=lambda pair: (
            -pair[1]["_score_r"],
            str(pair[0].id),
        )
    )

    # ---------------------------------------------------------
    # Build result rows
    # ---------------------------------------------------------
    rows = []

    audit = rejected[:]

    for rank, (c, b) in enumerate(
        scored,
        1,
    ):

        # IMPORTANT:
        # Pass jd_requirements here so the explanation is
        # generated from the uploaded JD rather than the
        # original fixed rubric.
        reason = build_reason(
            c,
            b,
            jd_requirements,
        )

        row = {
            "rank": rank,

            "candidate_id": c.id,

            "title": c.title,

            "experience": c.yoe,

            "location": c.location,

            "score": b["_score_r"],

            "reasoning": reason,

            "breakdown": {
                key: b[key]
                for key in (
                    "evidence",
                    "skills",
                    "semantic",
                    "seniority",
                    "trajectory",
                    "location",
                    "fit",
                    "behavioral_modifier",
                    "notice_penalty",
                    "final",
                )
            },

            "profile": c.raw,
        }

        rows.append(row)

        # -----------------------------------------------------
        # Full scoring audit
        # -----------------------------------------------------
        audit.append({
            "candidate_id": c.id,
            "gated": False,
            **b,
        })

    # ---------------------------------------------------------
    # Return Top-N + audit + summary
    # ---------------------------------------------------------
    return (
        rows[:top_n],
        audit,
        {
            "processed": len(candidates),

            "eligible": len(survivors),

            "rejected": len(rejected),

            "semantic_mode": semantic.mode,

            "rejection_types": dict(
                Counter(
                    item["kind"]
                    for item in rejected
                )
            ),
        },
    )