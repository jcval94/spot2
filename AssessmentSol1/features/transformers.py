from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


VALID_MODEL_ROLES = {"LEAD_QUALITY", "MATCHING", "INVENTORY"}
VALID_STATUSES = {"REQUIRED", "SUPPORTED", "EXPERIMENTAL"}


def feature_registry_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FeatureRegistryGate:
    """Fail closed when a model asks for an unregistered or disallowed feature."""

    def __init__(self, registry_path: Path):
        self.registry_path = Path(registry_path)
        self.registry = pd.read_csv(self.registry_path)
        if self.registry["feature_name"].duplicated().any():
            dupes = self.registry.loc[
                self.registry["feature_name"].duplicated(), "feature_name"
            ].tolist()
            raise ValueError(f"Duplicate feature registry entries: {dupes}")

    def assert_allowed(
        self,
        features: Sequence[str],
        *,
        stage: str,
        model_roles: Iterable[str] = ("LEAD_QUALITY",),
        statuses: Iterable[str] = ("REQUIRED", "SUPPORTED"),
    ) -> None:
        roles = set(model_roles)
        allowed_statuses = set(statuses)
        reg = self.registry.set_index("feature_name", drop=False)
        missing = sorted(set(features) - set(reg.index))
        if missing:
            raise ValueError(f"Features missing from FEATURE_REGISTRY: {missing}")

        errors: list[str] = []
        for f in features:
            row = reg.loc[f]
            stages = set(str(row["stage"]).split("|"))
            if stage not in stages:
                errors.append(f"{f}: stage={row['stage']}")
            if row["model_role"] == "FORBIDDEN" or row["status"] == "REJECTED":
                errors.append(
                    f"{f}: hard-blocked model_role={row['model_role']} status={row['status']}"
                )
            elif row["model_role"] not in roles:
                errors.append(f"{f}: model_role={row['model_role']}")
            if row["status"] not in allowed_statuses:
                errors.append(f"{f}: status={row['status']}")
            available = str(row["earliest_available_at"])
            if available.upper().startswith(("UNPROVEN", "NOT OBSERVABLE", "FORBIDDEN")):
                errors.append(f"{f}: earliest_available_at={available}")
        if errors:
            raise ValueError("Feature registry gate failed: " + "; ".join(errors))


def _require_train_only(fit_roles: Sequence[str] | pd.Series | np.ndarray | None) -> None:
    if fit_roles is None:
        raise ValueError("fit_roles is required; learned transforms must prove TRAIN-only fit")
    roles = {str(x) for x in list(fit_roles)}
    if roles != {"TRAIN"}:
        raise ValueError(f"Learned transform saw non-TRAIN rows: {sorted(roles)}")


class GuardedPreprocessor(BaseEstimator, TransformerMixin):
    """Fold-aware sklearn preprocessor for Logistic Regression.

    Structural/not-applicable states must already be represented by explicit
    categorical *_state / *_applicable features. Numeric NaNs are therefore
    genuinely unknown or unavailable-within-an-otherwise-applicable field and
    are median-imputed from TRAIN only.
    """

    def __init__(
        self,
        numeric_features: Sequence[str],
        categorical_features: Sequence[str],
        *,
        scale_numeric: bool = True,
    ):
        self.numeric_features = list(numeric_features)
        self.categorical_features = list(categorical_features)
        self.scale_numeric = scale_numeric
        self._preprocessor: ColumnTransformer | None = None
        self.fit_columns_: list[str] | None = None

    def _build(self) -> ColumnTransformer:
        num_steps: list[tuple[str, object]] = [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True))
        ]
        if self.scale_numeric:
            num_steps.append(("scaler", StandardScaler()))
        numeric = Pipeline(num_steps)
        categorical = Pipeline(
            [
                (
                    "imputer",
                    SimpleImputer(strategy="constant", fill_value="__UNKNOWN__"),
                ),
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                ),
            ]
        )
        return ColumnTransformer(
            [
                ("numeric", numeric, self.numeric_features),
                ("categorical", categorical, self.categorical_features),
            ],
            remainder="drop",
        )

    def fit(self, X: pd.DataFrame, y=None, *, fit_roles=None):
        _require_train_only(fit_roles)
        requested = self.numeric_features + self.categorical_features
        missing = sorted(set(requested) - set(X.columns))
        if missing:
            raise ValueError(f"Preprocessor missing columns: {missing}")
        self.fit_columns_ = requested
        self._preprocessor = self._build()
        self._preprocessor.fit(X[requested], y)
        return self

    def transform(self, X: pd.DataFrame):
        if self._preprocessor is None:
            raise RuntimeError("GuardedPreprocessor must be fit before transform")
        return self._preprocessor.transform(X[self.fit_columns_])

    def get_feature_names_out(self):
        if self._preprocessor is None:
            raise RuntimeError("GuardedPreprocessor must be fit before names are available")
        return self._preprocessor.get_feature_names_out()


class FoldAwareEstimator(BaseEstimator):
    """Generic wrapper that refuses to fit without an all-TRAIN role vector."""

    def __init__(self, estimator):
        self.estimator = estimator
        self.estimator_ = None

    def fit(self, X, y=None, *, fit_roles=None, **fit_params):
        _require_train_only(fit_roles)
        self.estimator_ = clone(self.estimator)
        self.estimator_.fit(X, y, **fit_params)
        return self

    def predict(self, X):
        if self.estimator_ is None:
            raise RuntimeError("Estimator is not fit")
        return self.estimator_.predict(X)

    def transform(self, X):
        if self.estimator_ is None:
            raise RuntimeError("Estimator is not fit")
        if not hasattr(self.estimator_, "transform"):
            raise AttributeError("Wrapped estimator has no transform")
        return self.estimator_.transform(X)


class FoldAwareKMeans(BaseEstimator, TransformerMixin):
    """Optional profile clusterer; never used by the frozen core T1 plan."""

    def __init__(self, n_clusters: int = 4, random_state: int = 20260830):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model_: KMeans | None = None

    def fit(self, X, y=None, *, fit_roles=None):
        _require_train_only(fit_roles)
        self.model_ = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init="auto",
        )
        self.model_.fit(X)
        return self

    def transform(self, X):
        if self.model_ is None:
            raise RuntimeError("FoldAwareKMeans is not fit")
        return self.model_.transform(X)

    def predict(self, X):
        if self.model_ is None:
            raise RuntimeError("FoldAwareKMeans is not fit")
        return self.model_.predict(X)


def classify_columns(
    frame: pd.DataFrame,
    features: Sequence[str],
) -> tuple[list[str], list[str]]:
    """Return numeric/categorical lists without fitting on validation data."""
    numeric: list[str] = []
    categorical: list[str] = []
    for f in features:
        if pd.api.types.is_numeric_dtype(frame[f]):
            numeric.append(f)
        else:
            categorical.append(f)
    return numeric, categorical
