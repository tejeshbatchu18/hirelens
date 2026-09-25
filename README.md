# HireLens

## AI-Powered Candidate Ranking & Intelligence

HireLens is a personal project that helps hiring teams analyze candidate profiles against a job description and generate an explainable shortlist.

The system combines job-description parsing, text similarity, technical skills, experience, career history, location, and candidate activity signals to rank candidates and provide understandable reasons behind the ranking.

---

## What HireLens Does

HireLens allows users to:

- Upload a Job Description as a `.txt` file
- Upload a Candidate Dataset as a `.jsonl` file
- Choose the number of candidates to display
- Rank candidates against the selected job description
- View the ranked candidate list
- Inspect individual candidate scores
- View the score breakdown
- Understand why a candidate was ranked
- Inspect the original candidate profile
- Download the Top-N shortlist as a CSV file

---

## Application Workflow

```text
              Job Description
                     |
                     v
            Job Description Parser
                     |
                     v
             Candidate Dataset
                     |
                     v
          Candidate Validation
                     |
                     v
            Semantic Matching
                     |
                     v
           Feature-based Scoring
                     |
                     v
              Ranking Engine
                     |
                     v
          Explainable Results
              /      |      \
             /       |       \
            v        v        v
       Candidate   Score     Reasoning
        Details   Breakdown
                     |
                     v
                Top-N CSV
