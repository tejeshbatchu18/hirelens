# Redrob Streamlit V1

Run with Python 3.11:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app uses the original **fixed** Senior AI Engineer job description and original ranking rubric. It supports a synthetic demo dataset or uploaded candidate JSONL files, configurable Top-N, candidate details, score breakdown and a CSV containing exactly the displayed candidates (or fewer if insufficient candidates qualify). It does **not** yet support ranking against arbitrary uploaded job descriptions. The included synthetic profiles are fictional and intended for demonstration only.

The optional precomputed embeddings in `data/artifacts` belong to a particular dataset and fixed JD. Do not reuse them for arbitrary uploaded candidate data; remove or move artifacts when running the Streamlit demo to use TF-IDF fallback. Avoid deploying real applicant data or confidential challenge datasets publicly.
