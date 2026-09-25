import os
import numpy as np

ARTIFACT_DIR = os.environ.get(
    "REDROB_ARTIFACTS",
    "data/artifacts"
)


def _minmax(x):
    x = np.asarray(x, dtype="float32")
    lo, hi = float(x.min()), float(x.max())

    if hi - lo < 1e-9:
        return np.zeros_like(x)

    return (x - lo) / (hi - lo)


def _load_precomputed():
    """Return precomputed candidate vectors and fixed JD vector."""
    emb = os.path.join(
        ARTIFACT_DIR,
        "embeddings.npy"
    )

    ids = os.path.join(
        ARTIFACT_DIR,
        "embedding_ids.npy"
    )

    jd = os.path.join(
        ARTIFACT_DIR,
        "jd_vector.npy"
    )

    if not (
        os.path.exists(emb)
        and os.path.exists(ids)
        and os.path.exists(jd)
    ):
        return None

    V = np.load(emb).astype("float32")
    I = np.load(ids, allow_pickle=True)
    q = np.load(jd).astype("float32")

    # L2-normalize so dot product == cosine similarity
    V /= (
        np.linalg.norm(
            V,
            axis=1,
            keepdims=True
        )
        + 1e-9
    )

    q /= np.linalg.norm(q) + 1e-9

    return I, V, q


class SemanticScorer:

    def __init__(
        self,
        candidates,
        job_description=None
    ):
        self.mode = None
        self._scores = {}

        # A custom JD must use dynamic scoring.
        # Precomputed embeddings contain only the
        # original fixed JD.
        if job_description:
            self._fit_tfidf(
                candidates,
                job_description
            )
            self.mode = "tf-idf (uploaded job description)"
            return

        # No custom JD supplied:
        # use the original precomputed semantic model.
        pre = _load_precomputed()

        if pre is not None:
            ids, V, q = pre

            sims = V @ q

            sims = _minmax(sims)

            self._scores = {
                cid: float(score)
                for cid, score in zip(ids, sims)
            }

            self.mode = (
                "sentence-transformers+faiss "
                "(precomputed)"
            )

        else:
            # Fallback to the original fixed JD.
            from .rubric import JD_QUERY_TEXT

            self._fit_tfidf(
                candidates,
                JD_QUERY_TEXT
            )

            self.mode = (
                "tf-idf "
                "(fixed job description fallback)"
            )

    def _fit_tfidf(
        self,
        candidates,
        job_description
    ):
        from sklearn.feature_extraction.text import (
            TfidfVectorizer
        )
        from sklearn.metrics.pairwise import (
            linear_kernel
        )

        corpus = [
            c.full_text()
            for c in candidates
        ]

        if (
            not corpus
            or not any(
                text.strip()
                for text in corpus
            )
        ):
            self._scores = {
                getattr(c, "id", ""): 0.0
                for c in candidates
            }
            return

        vec = TfidfVectorizer(
            sublinear_tf=True,
            ngram_range=(1, 2),
            min_df=3,
            max_df=0.6,
            max_features=60000,
            stop_words="english",
        )

        try:
            X = vec.fit_transform(corpus)

        except ValueError:
            # Small or degenerate candidate dataset.
            # Relax TF-IDF constraints.
            vec = TfidfVectorizer(
                sublinear_tf=True,
                stop_words="english"
            )

            X = vec.fit_transform(corpus)

        q = vec.transform(
            [job_description]
        )

        sims = linear_kernel(
            q,
            X
        ).ravel()

        sims = _minmax(sims)

        self._scores = {
            c.id: float(score)
            for c, score in zip(
                candidates,
                sims
            )
        }

    def score(self, candidate_id):
        return self._scores.get(
            candidate_id,
            0.0
        )