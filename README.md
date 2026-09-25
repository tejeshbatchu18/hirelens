# HireLens

## AI-Powered Candidate Ranking & Intelligence

HireLens is a personal project for intelligent and explainable candidate screening.

It analyzes candidate profiles against a given job description and generates a ranked shortlist using multiple signals such as technical skills, relevant experience, semantic similarity, career trajectory, location, and candidate activity.

The goal is to go beyond simple keyword matching and provide a transparent explanation of why candidates appear in the ranking.

---

## Overview

Recruiters often need to evaluate a large number of candidate profiles against a specific job description.

A simple keyword-based approach can produce misleading results:

- A candidate may list a technology without having practical experience with it.
- Relevant experience may exist in the candidate's career history but not in the skills section.
- Different candidates may use different terminology for similar technologies.
- A candidate's experience level may not match the requirements of the role.
- A numerical ranking without an explanation can be difficult to evaluate.

HireLens addresses these problems by combining structured candidate information, text similarity, job-description parsing, and multiple ranking signals into an explainable candidate-ranking pipeline.

---

## Key Features

### Dynamic Job Description

Users can upload a job description as a `.txt` file.

HireLens extracts information such as:

- Required technical skills
- Nice-to-have skills
- Experience requirements
- Location requirements

This allows the application to evaluate candidates against different job descriptions.

---

### Candidate Dataset Upload

Candidate profiles can be uploaded as a JSON Lines (`.jsonl`) dataset.

Each line represents one candidate.

This makes it possible to process multiple candidate profiles using a single input file.

---

### Configurable Top-N Ranking

Users can choose how many candidates should appear in the final shortlist.

For example:

```text
Top 5
Top 10
Top 25
Top 50

The ranking pipeline returns the requested number of candidates when enough eligible candidates are available.

Multi-Signal Candidate Scoring

HireLens evaluates candidates using multiple signals:

Signal	Purpose
Evidence	Identifies relevant practical experience from career history
Skills	Measures relevant technical skill coverage
Semantic Similarity	Compares candidate profile text with the job description
Seniority	Considers candidate experience relative to the role
Trajectory	Considers career history and tenure
Location	Considers candidate location and relocation information
Behavioral Signals	Considers available activity and response indicators
Notice Period	Applies an availability adjustment

These signals are combined to produce an overall candidate score.

How HireLens Works
                    Job Description
                           |
                           v
                +---------------------+
                |   Job Description   |
                |       Parser        |
                +---------------------+
                           |
                           v
                 Candidate Dataset
                           |
                           v
                +---------------------+
                | Candidate Validation|
                +---------------------+
                           |
                           v
                +---------------------+
                | Semantic Matching   |
                |                     |
                | TF-IDF / Similarity |
                +---------------------+
                           |
                           v
                +---------------------+
                | Feature Scoring     |
                |                     |
                | Skills              |
                | Evidence            |
                | Seniority           |
                | Trajectory          |
                | Location            |
                +---------------------+
                           |
                           v
                +---------------------+
                |   Ranking Engine    |
                +---------------------+
                           |
                           v
                +---------------------+
                | Explainable Results |
                +---------------------+
                    /       |       \
                   /        |        \
                  v         v         v
             Candidate   Score    Reasoning
              Details   Breakdown
                           |
                           v
                       Top-N CSV
Job Description Processing

The job description is parsed before candidate scoring.

For example:

Full Stack Developer

Requirements:
2-4 years of experience
JavaScript
TypeScript
React
Node.js
Express
PostgreSQL

Location:
India

The parser can extract structured requirements such as:

{
  "required_skills": [
    "express",
    "javascript",
    "node.js",
    "postgresql",
    "react",
    "typescript"
  ],
  "nice_to_have_skills": [],
  "min_experience": 2,
  "max_experience": 4,
  "locations": [
    "india"
  ]
}

This structured information is used by the ranking and explanation layers.

Semantic Matching

One of the main components of HireLens is text-based similarity.

Candidate profiles contain information such as:

Current role
Professional summary
Career history
Companies
Industries
Skills

This information is converted into text and compared with the job description.

The current V1 application uses:

TF-IDF
   +
Cosine Similarity

The project also contains support for a precomputed semantic retrieval path using:

Sentence Transformers
        +
FAISS

This allows the project to be extended toward stronger semantic retrieval in future versions.

Explainable Candidate Ranking

A key design goal of HireLens is explainability.

Instead of displaying only:

Candidate: CAND_001
Score: 82.4

the application exposes the factors behind the score.

Example:

Full Stack Developer with 3 years of experience.

Matches required skills including:
Express, JavaScript, Node.js, PostgreSQL,
React, and TypeScript.

3 years of experience is within the requested
2.0-4.0 year range.

Location matches the JD requirement (India).

Active and responsive (90% recruiter response).

This makes the ranking easier to inspect and understand.

Score Breakdown

When a candidate is selected, HireLens displays individual ranking signals.

Example:

Evidence       24.0 / 30
Skills         17.6 / 22
Semantic       13.2 / 18
Seniority      12.0 / 12
Trajectory      7.0 / 10
Location        6.8 / 8

The application also provides visual indicators for the individual scores.

Candidate Profile Inspection

Users can inspect the original candidate profile directly from the application.

This allows the generated explanation and ranking information to be compared with the underlying candidate data.

CSV Export

After ranking candidates, HireLens provides a downloadable CSV containing the selected Top-N candidates.

The export includes information such as:

Rank
Candidate ID
Current title
Experience
Location
Overall score
Reasoning
Individual scoring signals

Example:

rank,candidate_id,title,experience,location,score,reasoning
1,CAND_001,Full Stack Developer,3,Hyderabad,82.41,...
2,CAND_004,Software Engineer,4,Bangalore,79.32,...
3,CAND_007,Backend Developer,3,Pune,76.84,...
Candidate Data Format

HireLens expects candidate data in JSONL format.

Example:

{
  "candidate_id": "CAND_001",
  "profile": {
    "current_title": "Full Stack Developer",
    "current_company": "Example Technologies",
    "years_of_experience": 3,
    "location": "Hyderabad",
    "country": "India",
    "headline": "Full Stack Developer with experience in React and Node.js",
    "summary": "Software engineer building web applications and APIs."
  },
  "skills": [
    {
      "name": "JavaScript",
      "proficiency": "advanced",
      "duration_months": 36
    },
    {
      "name": "React",
      "proficiency": "advanced",
      "duration_months": 30
    },
    {
      "name": "Node.js",
      "proficiency": "intermediate",
      "duration_months": 24
    }
  ],
  "career_history": [
    {
      "title": "Full Stack Developer",
      "company": "Example Technologies",
      "duration_months": 30,
      "industry": "Software",
      "description": "Developed React applications and Node.js APIs."
    }
  ]
}
Project Architecture
HireLens
│
├── app.py
│       Streamlit user interface
│
├── ranker/
│   │
│   ├── jd_parser.py
│   │       Job description parsing
│   │
│   ├── pipeline.py
│   │       End-to-end ranking pipeline
│   │
│   ├── schema.py
│   │       Candidate data representation
│   │
│   ├── embeddings.py
│   │       Semantic similarity
│   │
│   ├── features.py
│   │       Candidate feature calculations
│   │
│   ├── scoring.py
│   │       Signal combination and final score
│   │
│   ├── gates.py
│   │       Candidate validation and filtering
│   │
│   ├── reasoning.py
│   │       Explainable ranking reasons
│   │
│   └── rubric.py
│           Ranking configuration
│
├── data/
│   ├── demo_candidates.jsonl
│   ├── job_description.txt
│   └── .gitkeep
│
├── tests/
│
├── precompute.py
├── rank.py
├── requirements.txt
├── README.md
├── STREAMLIT_V1.md
└── .gitignore
Technology Stack
Programming
Python
Frontend
Streamlit
Machine Learning / NLP
Scikit-learn
TF-IDF
Cosine Similarity
Sentence Transformers
FAISS
Data Processing
Pandas
NumPy
JSON
JSONL
Development Tools
Git
GitHub
VS Code
