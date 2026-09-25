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

HireLens extracts:

- Required technical skills
- Nice-to-have skills
- Experience requirements
- Location requirements

This allows the application to evaluate candidates against different job descriptions.

### Candidate Dataset Upload

Candidate profiles can be uploaded as a JSON Lines (`.jsonl`) dataset.

Each line represents one candidate.

### Configurable Top-N Ranking

Users can choose how many candidates should appear in the final shortlist.

Example:

```text
Top 5
Top 10
Top 25
Top 50
```

The ranking pipeline returns the requested number of candidates when enough eligible candidates are available.

### Multi-Signal Candidate Scoring

HireLens evaluates candidates using multiple signals:

| Signal | Purpose |
|---|---|
| Evidence | Identifies relevant practical experience from career history |
| Skills | Measures relevant technical skill coverage |
| Semantic Similarity | Compares candidate profile text with the job description |
| Seniority | Considers candidate experience relative to the role |
| Trajectory | Considers career history and tenure |
| Location | Considers candidate location and relocation information |
| Behavioral Signals | Considers available activity and response indicators |
| Notice Period | Applies an availability adjustment |

These signals are combined to produce an overall candidate score.

---

## How HireLens Works

```text
                    Job Description
                           |
                           v
                +---------------------+
                | Job Description     |
                | Parser              |
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
                | Ranking Engine      |
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
```

---

## Job Description Processing

The job description is parsed before candidate scoring.

Example:

```text
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
```

The parser extracts structured requirements such as:

```json
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
```

This structured information is used by the ranking and explanation layers.

---

## Semantic Matching

One of the main components of HireLens is text-based similarity.

Candidate profiles contain information such as:

- Current role
- Professional summary
- Career history
- Companies
- Industries
- Skills

This information is converted into text and compared with the job description.

The current V1 application uses:

```text
TF-IDF
+
Cosine Similarity
```

The project also contains support for a precomputed semantic retrieval path using:

```text
Sentence Transformers
+
FAISS
```

This provides a path for stronger semantic retrieval in future versions.

---

## Explainable Candidate Ranking

A key design goal of HireLens is explainability.

Instead of displaying only:

```text
Candidate: CAND_001
Score: 82.4
```

the application exposes the factors behind the score.

Example:

```text
Full Stack Developer with 3 years of experience.

Matches required skills including:
Express, JavaScript, Node.js, PostgreSQL,
React, and TypeScript.

3 years of experience is within the requested
2.0-4.0 year range.

Location matches the JD requirement (India).

Active and responsive (90% recruiter response).
```

This makes the ranking easier to inspect and understand.

---

## Score Breakdown

When a candidate is selected, HireLens displays individual ranking signals.

Example:

```text
Evidence       24.0 / 30
Skills         17.6 / 22
Semantic       13.2 / 18
Seniority      12.0 / 12
Trajectory      7.0 / 10
Location        6.8 / 8
```

The application also provides visual indicators for the individual scores.

---

## Candidate Profile Inspection

Users can inspect the original candidate profile directly from the application.

This allows the ranking information and generated reasoning to be compared with the underlying candidate data.

---

## CSV Export

After ranking candidates, HireLens provides a downloadable CSV containing the selected Top-N candidates.

The export includes:

- Rank
- Candidate ID
- Current title
- Experience
- Location
- Overall score
- Reasoning
- Individual scoring signals

Example:

```text
rank,candidate_id,title,experience,location,score,reasoning
1,CAND_001,Full Stack Developer,3,Hyderabad,82.41,...
2,CAND_004,Software Engineer,4,Bangalore,79.32,...
3,CAND_007,Backend Developer,3,Pune,76.84,...
```

---

## Candidate Data Format

HireLens expects candidate data in JSONL format.

Example:

```json
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
```

---

## Project Architecture

```text
HireLens
|
+-- app.py
|      Streamlit user interface
|
+-- ranker/
|   |
|   +-- jd_parser.py
|   |      Job description parsing
|   |
|   +-- pipeline.py
|   |      End-to-end ranking pipeline
|   |
|   +-- schema.py
|   |      Candidate data representation
|   |
|   +-- embeddings.py
|   |      Semantic similarity
|   |
|   +-- features.py
|   |      Candidate feature calculations
|   |
|   +-- scoring.py
|   |      Signal combination and final score
|   |
|   +-- gates.py
|   |      Candidate validation and filtering
|   |
|   +-- reasoning.py
|   |      Explainable ranking reasons
|   |
|   +-- rubric.py
|          Ranking configuration
|
+-- data/
|   +-- demo_candidates.jsonl
|   +-- job_description.txt
|   +-- .gitkeep
|
+-- tests/
|
+-- precompute.py
+-- rank.py
+-- requirements.txt
+-- README.md
+-- STREAMLIT_V1.md
+-- .gitignore
```

---

## Technology Stack

### Programming

- Python

### Frontend

- Streamlit

### Machine Learning / NLP

- Scikit-learn
- TF-IDF
- Cosine Similarity
- Sentence Transformers
- FAISS

### Data Processing

- Pandas
- NumPy
- JSON
- JSONL

### Development Tools

- Git
- GitHub
- VS Code

---

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/tejeshbatchu18/hirelens.git
cd hirelens
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start HireLens

```powershell
python -m streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## Using HireLens

1. Upload a Job Description `.txt` file.
2. Upload a Candidate Dataset `.jsonl` file.
3. Select the number of candidates to display.
4. Click **Rank Candidates**.
5. Review the ranked candidates.
6. Select a candidate to inspect the detailed scoring.
7. Review the candidate reasoning.
8. Download the Top-N shortlist as CSV.

---

## Demo Dataset

The repository contains a small synthetic candidate dataset for demonstrating the application.

The demo data is intended for development and demonstration purposes.

Real candidate information should not be committed to the public repository.

---

## Design Principles

### Explainability

The system exposes the major signals contributing to a candidate's ranking.

### Modularity

Parsing, candidate representation, semantic matching, scoring, and reasoning are separated into individual modules.

### Deterministic Processing

The ranking pipeline is designed to produce repeatable results for the same input and configuration.

### Configurable Ranking

The number of candidates returned is controlled by the user.

### Data Grounding

Candidate explanations are generated from candidate and ranking information rather than requiring a generative model to invent candidate details.

---

## Current Limitations

HireLens is currently a V1 personal project and is intended as decision-support software rather than an automatic hiring system.

Current limitations include:

- Job-description parsing is rule-based.
- Skill extraction currently relies on a defined skill vocabulary and aliases.
- Complex logical requirements such as `React OR Angular` require further parsing improvements.
- The current interface is implemented using Streamlit.
- Large-scale candidate processing has not yet been optimized for production deployment.
- Candidate ranking should be reviewed by humans before making hiring decisions.

---

## Future Roadmap

### V1 — Current

- Streamlit interface
- Job description upload
- Candidate JSONL upload
- Dynamic Top-N selection
- Job description parsing
- Candidate ranking
- Semantic matching
- Score breakdown
- Explainable reasoning
- CSV export

### V2 — Planned

- React frontend
- FastAPI backend
- REST API
- Improved job-description parsing
- Better required vs optional skill classification
- More flexible skill matching
- Candidate comparison
- Improved semantic retrieval
- Automated testing

### V3 — Planned

- Vercel deployment
- Persistent storage
- Authentication
- Job management
- Candidate management
- Recruiter feedback
- Ranking customization
- Production-scale processing
- Monitoring and analytics

---

## Why I Built HireLens

HireLens was built as a personal project to explore the intersection of:

- Software Engineering
- Natural Language Processing
- Machine Learning
- Information Retrieval
- Explainable AI
- Full-Stack Development

The project focuses on building an end-to-end intelligent application rather than only implementing a machine-learning model.

The complete workflow is:

```text
Input
  |
  v
Parsing
  |
  v
Data Processing
  |
  v
Feature Extraction
  |
  v
Similarity Matching
  |
  v
Scoring
  |
  v
Ranking
  |
  v
Explanation
  |
  v
Export
```

---

## Project Status

**Status:** Active Development

**Current Version:** V1

The current implementation is a working Streamlit application.

The next major architectural step is separating the ranking engine from the UI and exposing it through a backend API, allowing HireLens to evolve into a full-stack application.

---

## Author

### Tejesh Batchu

Computer Science Student | Software Developer

GitHub: https://github.com/tejeshbatchu18

LinkedIn: https://www.linkedin.com/in/tejesh-batchu/

---

## License

This project is intended for personal learning, experimentation, and portfolio purposes.
