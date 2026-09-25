from .rubric import SIGNAL_WEIGHTS
from . import features as F


def score_candidate(c, semantic, jd_requirements=None):
    """
    Calculate the overall candidate score.

    jd_requirements contains structured requirements extracted
    from the uploaded job description.
    """

    sig = {
        "evidence": F.evidence_score(c),
        "skills": F.skill_score(c, jd_requirements),
        "semantic": semantic.score(c.id),
        "seniority": F.seniority_score(c, jd_requirements),
        "trajectory": F.trajectory_score(c),
        "location": F.location_score(c, jd_requirements),
    }

    # Combine the individual signals using the existing weights.
    fit = sum(
        SIGNAL_WEIGHTS[k] * v
        for k, v in sig.items()
    )

    # Small additional bonus for relevant nice-to-have skills.
    fit += 0.05 * F.nice_to_have_bonus(
        c,
        jd_requirements,
    )

    fit = min(fit, 1.0)

    # Candidate availability / engagement modifiers.
    beh = F.behavioral_modifier(c)
    notice = F.notice_period_penalty(c)

    final = fit * beh * notice

    breakdown = dict(sig)

    breakdown["fit"] = round(fit, 4)
    breakdown["behavioral_modifier"] = round(beh, 3)
    breakdown["notice_penalty"] = round(notice, 3)
    breakdown["final"] = round(
        final * 100.0,
        4,
    )

    return breakdown