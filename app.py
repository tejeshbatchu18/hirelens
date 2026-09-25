"""Streamlit V1 UI for the HireLens candidate ranker."""

import io
import json

import pandas as pd
import streamlit as st

from ranker.pipeline import rank_candidates
from ranker.rubric import SIGNAL_WEIGHTS


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="HireLens | Candidate Ranker",
    page_icon=None,
    layout="wide",
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("HireLens")
st.subheader("AI-Powered Candidate Ranking & Intelligence")

st.caption(
    "Explainable candidate ranking using evidence, skills, semantic "
    "similarity, seniority, trajectory, and location signals."
)


# ---------------------------------------------------------
# Sidebar — Ranking Setup
# ---------------------------------------------------------
with st.sidebar:
    st.header("Ranking Setup")

    # -----------------------------------------------------
    # Job Description Upload
    # -----------------------------------------------------
    jd_upload = st.file_uploader(
        "Job Description (.txt)",
        type=["txt"],
        help="Upload the job description as a plain text file.",
    )

    # -----------------------------------------------------
    # Candidate Dataset Upload
    # -----------------------------------------------------
    candidate_upload = st.file_uploader(
        "Candidate Dataset (.jsonl)",
        type=["jsonl"],
        help="Upload one candidate JSON object per line.",
    )

    # -----------------------------------------------------
    # Top-N
    # -----------------------------------------------------
    n = st.number_input(
        "Number of Candidates to Show",
        min_value=1,
        max_value=100000,
        value=10,
        step=1,
    )

    # -----------------------------------------------------
    # Run
    # -----------------------------------------------------
    run = st.button(
    "Rank Candidates",
    type="primary",
    width="stretch",
)

# ---------------------------------------------------------
# Uploaded JD Preview
# ---------------------------------------------------------
if jd_upload is not None:

    try:
        job_description = (
            jd_upload
            .getvalue()
            .decode("utf-8-sig")
            .strip()
        )

        if job_description:

            with st.expander("View Uploaded Job Description"):
                st.text(job_description)

        else:
            st.warning(
                "The uploaded job description is empty."
            )

    except UnicodeError:
        st.error(
            "Unable to read the job description. "
            "Please upload a UTF-8 encoded .txt file."
        )
        st.stop()

else:
    job_description = None


# ---------------------------------------------------------
# Candidate Dataset Preview
# ---------------------------------------------------------
if candidate_upload is not None:

    st.caption(
        f"Candidate dataset: {candidate_upload.name}"
    )


# ---------------------------------------------------------
# Ranking
# ---------------------------------------------------------
if run:

    # -----------------------------------------------------
    # Validate Job Description
    # -----------------------------------------------------
    if jd_upload is None:
        st.error(
            "Please upload a Job Description (.txt) file."
        )
        st.stop()

    if not job_description:
        st.error(
            "The uploaded Job Description is empty."
        )
        st.stop()

    # -----------------------------------------------------
    # Validate Candidate Dataset
    # -----------------------------------------------------
    if candidate_upload is None:
        st.error(
            "Please upload a Candidate Dataset (.jsonl) file."
        )
        st.stop()

    try:

        # -------------------------------------------------
        # Read candidate JSONL
        # -------------------------------------------------
        data = (
            candidate_upload
            .getvalue()
            .decode("utf-8-sig")
        )

        records = []

        for line_number, line in enumerate(
            io.StringIO(data),
            1,
        ):

            # Ignore blank lines.
            if not line.strip():
                continue

            try:
                item = json.loads(line)

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Line {line_number}: invalid JSON. "
                    f"{exc.msg}"
                ) from exc

            if not isinstance(item, dict):
                raise ValueError(
                    f"Line {line_number}: expected a JSON object."
                )

            if not item.get("candidate_id"):
                raise ValueError(
                    f"Line {line_number}: candidate_id is required."
                )

            records.append(item)

        # -------------------------------------------------
        # Validate dataset
        # -------------------------------------------------
        if not records:
            raise ValueError(
                "No candidates found in the uploaded JSONL file."
            )

        candidate_ids = [
            record["candidate_id"]
            for record in records
        ]

        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError(
                "Candidate IDs must be unique."
            )

        # -------------------------------------------------
        # Rank candidates
        # -------------------------------------------------
        with st.spinner(
            "Analyzing job description and ranking candidates..."
        ):

            result = rank_candidates(
                records,
                top_n=int(n),
                job_description=job_description,
            )

            st.session_state["result"] = result

            # Store metadata for display.
            st.session_state["candidate_count"] = len(
                records
            )

    except (
        UnicodeError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:

        st.error(
            f"Unable to rank this dataset: {exc}"
        )

        st.stop()


# ---------------------------------------------------------
# No results yet
# ---------------------------------------------------------
if "result" not in st.session_state:

    st.info(
        "Upload a Job Description and Candidate Dataset, "
        "choose the number of candidates to show, and "
        "click Rank Candidates."
    )

    st.stop()


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------
rows, audit, summary = st.session_state["result"]


# ---------------------------------------------------------
# Summary Metrics
# ---------------------------------------------------------
a, b, c = st.columns(3)

a.metric(
    "Candidates Processed",
    f"{summary['processed']:,}",
)

b.metric(
    "Eligible Candidates",
    f"{summary['eligible']:,}",
)

c.metric(
    "Candidates Shown",
    len(rows),
)


st.caption(
    f"Semantic scoring mode: {summary['semantic_mode']}"
)


# ---------------------------------------------------------
# No eligible candidates
# ---------------------------------------------------------
if not rows:

    st.warning(
        "No candidates were available for the requested ranking."
    )

    st.stop()


# ---------------------------------------------------------
# Ranked Candidates
# ---------------------------------------------------------
st.subheader("Ranked Candidates")

visible_cols = [
    "rank",
    "candidate_id",
    "title",
    "experience",
    "location",
    "score",
]

ranked_df = pd.DataFrame(rows)[visible_cols]

st.dataframe(
    ranked_df,
    hide_index=True,
    width="stretch",
)


# ---------------------------------------------------------
# Candidate Details
# ---------------------------------------------------------
st.subheader("Candidate Details")

options = {
    (
        f"#{r['rank']} — "
        f"{r['candidate_id']} "
        f"({r['score']:.2f})"
    ): r
    for r in rows
}

chosen = st.selectbox(
    "Select a Candidate to View Details",
    list(options),
)

selected = options[chosen]


st.markdown(
    f"**{selected['title'] or 'Title unavailable'}** · "
    f"{selected['location'] or 'Location unavailable'} · "
    f"{selected['experience']:g} years"
)


st.metric(
    "Overall Score",
    f"{selected['score']:.2f} / 100",
)


# ---------------------------------------------------------
# Score Breakdown
# ---------------------------------------------------------
st.markdown("#### Score Breakdown")

for signal, weight in SIGNAL_WEIGHTS.items():

    score = selected["breakdown"][signal]

    weighted_points = (
        score
        * weight
        * 100
    )

    st.write(
        f"{signal.title()} — "
        f"{weighted_points:.1f} / "
        f"{weight * 100:g} weighted points"
    )

    st.progress(
        min(
            max(
                float(score),
                0.0,
            ),
            1.0,
        )
    )


st.caption(
    "Overall score also includes a small nice-to-have bonus, "
    "behavioral modifier, and notice-period penalty."
)


# ---------------------------------------------------------
# Candidate Explanation
# ---------------------------------------------------------
st.markdown("#### Why This Candidate?")

st.write(
    selected["reasoning"]
)


# ---------------------------------------------------------
# Original Candidate Profile
# ---------------------------------------------------------
with st.expander(
    "View Original Candidate Profile"
):
    st.json(
        selected["profile"]
    )


# ---------------------------------------------------------
# CSV Download
# ---------------------------------------------------------
st.subheader("Download Shortlist")

export_cols = [
    "rank",
    "candidate_id",
    "title",
    "experience",
    "location",
    "score",
    "reasoning",
]


export = pd.DataFrame(
    [
        {
            **{
                key: row[key]
                for key in export_cols
            },
            **{
                f"{key}_score": row["breakdown"][key]
                for key in SIGNAL_WEIGHTS
            },
        }
        for row in rows
    ]
)


st.download_button(
    "Download Top-N CSV",
    export.to_csv(
        index=False
    ).encode("utf-8"),
    file_name=(
        f"hirelens_top_{len(rows)}.csv"
    ),
    mime="text/csv",
)