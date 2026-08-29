from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
MODEL3 = HERE.parent
ROOT = MODEL3.parents[1]
RESULTS = HERE / "results"
CHARTS = RESULTS / "charts"
RESULTS.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(MODEL3))

from data_pipeline import (  # noqa: E402
    AVAIL_CAT, AVAIL_NUM, CAT_FEATURES, CONTEXT_NUM, HISTORY_NUM,
    INQUIRY_CAT, INQUIRY_NUM, LEAD_CAT, LEAD_NUM, MATCH_CAT, MATCH_NUM,
    NUM_FEATURES, SPOT_CAT, SPOT_NUM, build_snapshots, make_preprocessor,
    prepare_inquiries, read_data, stage_balanced_weights, temporal_split,
)
from models import SharedMultiHead, metric_bundle, predict, set_seed, train_model  # noqa: E402

SEED = 42
N_REPEATS = 5
RF_TREES = 350

FAMILIES = {
    "lead_intake": LEAD_CAT + LEAD_NUM,
    "current_inquiry": INQUIRY_CAT + INQUIRY_NUM,
    "spot_static": SPOT_CAT + SPOT_NUM,
    "lead_spot_match": MATCH_CAT + MATCH_NUM,
    "availability_asof": AVAIL_CAT + AVAIL_NUM,
    "interaction_history": HISTORY_NUM,
    "context_flags": CONTEXT_NUM,
}

FAMILY_EXPLANATION = {
    "lead_intake": "perfil conocido desde la creación del lead",
    "current_inquiry": "intención y restricciones de la inquiry actual",
    "spot_static": "características estructurales del inmueble consultado",
    "lead_spot_match": "compatibilidad entre lo que busca el lead y el inmueble",
    "availability_asof": "capacidad de atender la demanda con inventario observable",
    "interaction_history": "comportamiento acumulado y respuestas históricas ya observadas",
    "context_flags": "presencia o ausencia de contexto utilizable",
}


def normalize_frames(*frames: pd.DataFrame) -> None:
    for frame in frames:
        for c in CAT_FEATURES:
            frame[c] = frame[c].astype("object")
            frame[c] = frame[c].where(frame[c].notna(), np.nan)


def score_ranking(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    return float(average_precision_score(y, p)), float(roc_auc_score(y, p))


def permute_columns(raw: pd.DataFrame, columns: list[str], rng: np.random.Generator) -> pd.DataFrame:
    out = raw.copy()
    order = rng.permutation(len(out))
    for c in columns:
        out[c] = out[c].to_numpy()[order]
    return out


def multihead_permutation_importance(
    model: SharedMultiHead,
    prep: ColumnTransformer,
    raw_test: pd.DataFrame,
    y_test: np.ndarray,
    feature_groups: dict[str, list[str]],
    n_repeats: int = N_REPEATS,
) -> tuple[pd.DataFrame, tuple[float, float]]:
    x_base = np.asarray(prep.transform(raw_test[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    stage = np.full(len(raw_test), 2, dtype=np.int64)
    base_pred = predict(model, x_base, stage)
    base_ap, base_auc = score_ranking(y_test, base_pred)
    rows = []

    for name, cols in feature_groups.items():
        drops_ap, drops_auc = [], []
        for rep in range(n_repeats):
            rng = np.random.default_rng(SEED + rep * 1009 + sum(map(ord, name)))
            shuffled = permute_columns(raw_test, cols, rng)
            x = np.asarray(prep.transform(shuffled[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
            pred = predict(model, x, stage)
            ap, auc = score_ranking(y_test, pred)
            drops_ap.append(base_ap - ap)
            drops_auc.append(base_auc - auc)
        rows.append({
            "feature": name,
            "columns": "|".join(cols),
            "ap_drop_mean": float(np.mean(drops_ap)),
            "ap_drop_std": float(np.std(drops_ap, ddof=1)) if len(drops_ap) > 1 else 0.0,
            "auc_drop_mean": float(np.mean(drops_auc)),
            "auc_drop_std": float(np.std(drops_auc, ddof=1)) if len(drops_auc) > 1 else 0.0,
        })
    return pd.DataFrame(rows).sort_values("ap_drop_mean", ascending=False), (base_ap, base_auc)


def make_rf_pipeline() -> Pipeline:
    cat = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(
            handle_unknown="ignore", min_frequency=5, sparse_output=False, dtype=np.float32
        )),
    ])
    num = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    prep = ColumnTransformer(
        [("cat", cat, CAT_FEATURES), ("num", num, NUM_FEATURES)],
        remainder="drop", sparse_threshold=0.0,
    )
    rf = RandomForestClassifier(
        n_estimators=RF_TREES,
        min_samples_leaf=12,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=SEED,
    )
    return Pipeline([("prep", prep), ("rf", rf)])


def rf_raw_permutation_importance(
    pipe: Pipeline,
    raw_test: pd.DataFrame,
    y_test: np.ndarray,
    n_repeats: int = N_REPEATS,
) -> tuple[pd.DataFrame, tuple[float, float]]:
    base = pipe.predict_proba(raw_test[CAT_FEATURES + NUM_FEATURES])[:, 1]
    base_ap, base_auc = score_ranking(y_test, base)
    rows = []
    for feature in CAT_FEATURES + NUM_FEATURES:
        drops_ap, drops_auc = [], []
        for rep in range(n_repeats):
            rng = np.random.default_rng(SEED + rep * 1237 + sum(map(ord, feature)))
            shuffled = raw_test[CAT_FEATURES + NUM_FEATURES].copy()
            shuffled[feature] = shuffled[feature].to_numpy()[rng.permutation(len(shuffled))]
            pred = pipe.predict_proba(shuffled)[:, 1]
            ap, auc = score_ranking(y_test, pred)
            drops_ap.append(base_ap - ap)
            drops_auc.append(base_auc - auc)
        rows.append({
            "feature": feature,
            "ap_drop_mean": float(np.mean(drops_ap)),
            "ap_drop_std": float(np.std(drops_ap, ddof=1)) if len(drops_ap) > 1 else 0.0,
            "auc_drop_mean": float(np.mean(drops_auc)),
            "auc_drop_std": float(np.std(drops_auc, ddof=1)) if len(drops_auc) > 1 else 0.0,
        })
    return pd.DataFrame(rows).sort_values("ap_drop_mean", ascending=False), (base_ap, base_auc)


def map_transformed_feature(name: str) -> str:
    if name.startswith("cat__"):
        rest = name[len("cat__"):]
        for col in sorted(CAT_FEATURES, key=len, reverse=True):
            if rest == col or rest.startswith(col + "_"):
                return col
        return rest
    if name.startswith("num__"):
        rest = name[len("num__"):]
        if rest.startswith("missingindicator_"):
            rest = rest[len("missingindicator_"):]
        return rest
    return name


def rf_impurity_importance(pipe: Pipeline) -> pd.DataFrame:
    prep = pipe.named_steps["prep"]
    rf = pipe.named_steps["rf"]
    names = prep.get_feature_names_out()
    rows = pd.DataFrame({"transformed_feature": names, "importance": rf.feature_importances_})
    rows["feature"] = rows["transformed_feature"].map(map_transformed_feature)
    return rows.groupby("feature", as_index=False)["importance"].sum().sort_values(
        "importance", ascending=False
    )


def family_for_feature(feature: str) -> str:
    for family, cols in FAMILIES.items():
        if feature in cols:
            return family
    return "other"


def directionality_rows(df: pd.DataFrame, top_features: list[str]) -> pd.DataFrame:
    rows = []
    target = "target_30d"
    for feature in top_features:
        valid = df[df[feature].notna()].copy()
        if len(valid) < 60:
            continue

        if feature in NUM_FEATURES:
            x = pd.to_numeric(valid[feature], errors="coerce")
            valid = valid[x.notna()].copy()
            x = pd.to_numeric(valid[feature], errors="coerce")
            if x.nunique() >= 4:
                q25, q75 = x.quantile([0.25, 0.75])
                low = valid[x <= q25]
                high = valid[x >= q75]
                rows.append({
                    "feature": feature, "kind": "numeric_quartiles",
                    "low_group": f"<=Q25 ({q25:.4g})", "low_n": int(len(low)),
                    "low_rate": float(low[target].mean()),
                    "high_group": f">=Q75 ({q75:.4g})", "high_n": int(len(high)),
                    "high_rate": float(high[target].mean()),
                    "delta_pp": float((high[target].mean() - low[target].mean()) * 100),
                })
                continue

        groups = valid.groupby(feature, dropna=False)[target].agg(["size", "mean"]).reset_index()
        groups = groups[groups["size"] >= 30].sort_values("mean")
        if len(groups) >= 2:
            lo, hi = groups.iloc[0], groups.iloc[-1]
            rows.append({
                "feature": feature, "kind": "categorical_or_low_cardinality",
                "low_group": str(lo[feature]), "low_n": int(lo["size"]), "low_rate": float(lo["mean"]),
                "high_group": str(hi[feature]), "high_n": int(hi["size"]), "high_rate": float(hi["mean"]),
                "delta_pp": float((hi["mean"] - lo["mean"]) * 100),
            })
    return pd.DataFrame(rows)


def plot_ranked(df: pd.DataFrame, path: Path, top_n: int = 15) -> None:
    p = df.nlargest(top_n, "ap_drop_mean").sort_values("ap_drop_mean")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(p["feature"], p["ap_drop_mean"])
    ax.axvline(0, linewidth=1)
    ax.set_xlabel("Average Precision drop after permutation")
    ax.set_ylabel("")
    ax.set_title("T2 feature importance — direct multi-head permutation")
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def plot_family(df: pd.DataFrame, path: Path) -> None:
    p = df.sort_values("ap_drop_mean")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.barh(p["family"], p["ap_drop_mean"])
    ax.axvline(0, linewidth=1)
    ax.set_xlabel("Average Precision drop after joint permutation")
    ax.set_ylabel("")
    ax.set_title("T2 information by feature family")
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def human_feature(feature: str) -> str:
    names = {
        "hist_prior_inquiries": "número de inquiries previas",
        "hist_prior_unique_spots": "spots distintos consultados previamente",
        "hist_prior_asked_visit_rate": "tasa histórica de solicitudes de visita",
        "hist_prior_message_length_mean": "longitud media histórica de mensajes",
        "hist_prior_urgency_mean": "urgencia histórica media",
        "hist_prior_realized_responses": "respuestas históricas ya observadas",
        "hist_prior_accepted_responses": "respuestas históricas aceptadas",
        "hist_prior_accept_rate": "tasa histórica de aceptación",
        "hist_prior_median_response_hours": "mediana histórica de horas de respuesta",
        "days_since_first_inquiry": "días desde la primera inquiry",
        "inquiry_number": "número secuencial de inquiry",
        "days_from_lead_creation": "días desde la creación del lead",
        "urgency_days": "urgencia declarada en días",
        "message_length": "longitud del mensaje actual",
        "requested_area_sqm": "área solicitada",
        "requested_to_spot_area_ratio": "ratio área solicitada / área del spot",
        "rent_budget_to_price_ratio": "ratio presupuesto de renta / renta del spot",
        "sale_budget_to_price_ratio": "ratio presupuesto de compra / precio del spot",
        "same_preferred_corridor": "coincidencia con corredor preferido",
        "same_preferred_municipality": "coincidencia con municipio preferido",
        "same_sector": "coincidencia de sector",
        "availability_competing_inquiries_30d": "inquiries competidoras del spot en 30 días",
        "availability_days_until_available": "días hasta disponibilidad del spot",
        "availability_is_available": "disponibilidad actual del spot",
        "availability_snapshot_age_days": "antigüedad del snapshot de disponibilidad",
    }
    return names.get(feature, feature.replace("_", " "))


def build_report(
    mh_imp: pd.DataFrame,
    family_imp: pd.DataFrame,
    direction: pd.DataFrame,
    fidelity: dict,
    concordance: dict,
) -> str:
    top = mh_imp.head(10)
    strongest_family = family_imp.sort_values("ap_drop_mean", ascending=False).iloc[0]
    top_feature = top.iloc[0]
    direction_map = direction.set_index("feature") if not direction.empty else None

    lines = [
        "# Qué está dando señal en T2", "",
        "## Resumen ejecutivo", "",
        f"La familia con mayor dependencia predictiva es **{FAMILY_EXPLANATION.get(strongest_family['family'], strongest_family['family'])}**. "
        f"Al romper conjuntamente esa información, Average Precision cae {strongest_family['ap_drop_mean']:+.3f}.",
        f"La variable individual más influyente para el head es **{human_feature(top_feature['feature'])}** "
        f"(ΔAP {top_feature['ap_drop_mean']:+.3f}; ΔAUC {top_feature['auc_drop_mean']:+.3f}).",
        f"El análisis usa {fidelity['test_population']['n']:,} snapshots T2 de test temporal, "
        f"con tasa positiva de {fidelity['test_population']['positive_rate']:.1%}.",
        "",
        "T2 no mejora simplemente porque el modelo conoce la etapa. Mejora porque a esa altura del funnel existe información que no estaba disponible en T0/T1: comportamiento acumulado, intención actual, encaje con el inmueble y disponibilidad observable.",
        "",
        "## Fidelidad del análisis", "",
        f"- Head T2 reentrenado: ROC-AUC **{fidelity['retrained_multihead']['roc_auc']:.3f}**, AP **{fidelity['retrained_multihead']['average_precision']:.3f}**.",
        f"- Head T2 original: ROC-AUC **{fidelity['original_t2']['roc_auc']:.3f}**, AP **{fidelity['original_t2']['average_precision']:.3f}**.",
        f"- Random Forest diagnóstico: ROC-AUC **{fidelity['random_forest']['roc_auc']:.3f}**, AP **{fidelity['random_forest']['average_precision']:.3f}**.",
        "",
        "El ranking principal de variables viene del head T2 reentrenado. El Random Forest se usa como segunda opinión, no como sustituto del Modelo 3.",
        "",
        "## Variables con mayor poder predictivo", "",
        "| Rank | Variable | Familia | ΔAP | ΔAUC | Perfil descriptivo |",
        "|---:|---|---|---:|---:|---|",
    ]
    for rank, row in enumerate(top.itertuples(), 1):
        profile = ""
        if direction_map is not None and row.feature in direction_map.index:
            d = direction_map.loc[row.feature]
            if isinstance(d, pd.DataFrame):
                d = d.iloc[0]
            profile = (
                f"{d['low_group']}: {d['low_rate']:.1%} vs "
                f"{d['high_group']}: {d['high_rate']:.1%} ({d['delta_pp']:+.1f} pp)"
            )
        if not profile:
            profile = FAMILY_EXPLANATION.get(family_for_feature(row.feature), "")
        lines.append(
            f"| {rank} | {human_feature(row.feature)} | {family_for_feature(row.feature)} | "
            f"{row.ap_drop_mean:+.4f} | {row.auc_drop_mean:+.4f} | {profile} |"
        )

    lines += [
        "", "### Cómo leer la importancia", "",
        "Una caída positiva significa que al destruir esa información en test el ranking empeora. "
        "Una importancia cercana a cero puede significar poca señal incremental o que otras variables correlacionadas pueden sustituirla.",
        "",
        "## Importancia por familia", "",
        "| Familia | ΔAP | ΔAUC | Qué representa |",
        "|---|---:|---:|---|",
    ]
    for row in family_imp.sort_values("ap_drop_mean", ascending=False).itertuples():
        lines.append(
            f"| {row.family} | {row.ap_drop_mean:+.4f} | {row.auc_drop_mean:+.4f} | "
            f"{FAMILY_EXPLANATION.get(row.family, row.family)} |"
        )

    lines += [
        "", "## ¿Coincide el Random Forest?", "",
        f"- Spearman head vs RF permutation: **{concordance['spearman_multihead_vs_rf_permutation']:.3f}**.",
        f"- Spearman head vs RF impurity importance: **{concordance['spearman_multihead_vs_rf_mdi']:.3f}**.",
        "",
        "El permutation importance es más confiable aquí que la importancia MDI del Random Forest, porque MDI puede favorecer variables continuas o de alta cardinalidad.",
        "",
        "## Qué significa para Spot2", "",
        "1. **Lead Quality debe seguir siendo dinámico.** El incremento de información aparece cuando ya existe comportamiento real.",
        "2. **El siguiente feature engineering debería concentrarse en las familias dinámicas que más ΔAP generan**, no en agregar más variables estáticas indiscriminadamente.",
        "3. **Compatibilidad lead↔spot y disponibilidad deben evaluarse como bloques.** Variables correlacionadas pueden repartirse señal y parecer débiles por separado.",
        "4. **No convertir importancia en causalidad.** Una variable puede ser un excelente marcador de intención sin ser una palanca causal de conversión.",
        "",
        "## Limitaciones", "",
        "- El target es scheduled_visit, no cierre.",
        "- Los datos son sintéticos.",
        "- Permutation importance mide dependencia predictiva, no efecto causal.",
        "- Variables correlacionadas pueden ocultarse entre sí.",
        "- Los perfiles de dirección son descriptivos y univariados.",
        "",
        "## Recomendación", "",
        "Usaría este ranking para diseñar el siguiente experimento de feature engineering: profundizar primero en las dos familias con mayor caída conjunta y validar el lift incremental con el mismo split temporal y controles de leakage.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    set_seed()
    leads, inquiries_raw, spots, attrs, availability = read_data(ROOT)
    inquiries = prepare_inquiries(inquiries_raw)
    snapshots = temporal_split(build_snapshots(leads, inquiries, spots, attrs, availability))

    train = snapshots[snapshots["split"].eq("train")].copy().reset_index(drop=True)
    val = snapshots[snapshots["split"].eq("val")].copy().reset_index(drop=True)
    test = snapshots[snapshots["split"].eq("test")].copy().reset_index(drop=True)
    normalize_frames(train, val, test)

    prep = make_preprocessor()
    x_train = np.asarray(prep.fit_transform(train[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    x_val = np.asarray(prep.transform(val[CAT_FEATURES + NUM_FEATURES]), dtype=np.float32)
    y_train = train["target_30d"].to_numpy(dtype=np.int64)
    y_val = val["target_30d"].to_numpy(dtype=np.int64)
    s_train = train["stage_id"].to_numpy(dtype=np.int64)
    s_val = val["stage_id"].to_numpy(dtype=np.int64)
    weights = stage_balanced_weights(train)

    set_seed()
    model = SharedMultiHead(x_train.shape[1])
    model, history = train_model(
        model, x_train, y_train, s_train, weights, x_val, y_val, s_val
    )
    history.to_csv(RESULTS / "multihead_training_history.csv", index=False)

    t2_test = test[test["stage_id"].eq(2)].copy().reset_index(drop=True)
    t2_train = train[train["stage_id"].eq(2)].copy().reset_index(drop=True)
    y_t2_test = t2_test["target_30d"].to_numpy(dtype=np.int64)

    individual_groups = {f: [f] for f in CAT_FEATURES + NUM_FEATURES}
    mh_imp, (mh_ap, mh_auc) = multihead_permutation_importance(
        model, prep, t2_test, y_t2_test, individual_groups
    )
    mh_imp["family"] = mh_imp["feature"].map(family_for_feature)
    mh_imp.to_csv(RESULTS / "multihead_permutation_importance.csv", index=False)

    family_imp, _ = multihead_permutation_importance(
        model, prep, t2_test, y_t2_test, FAMILIES
    )
    family_imp = family_imp.rename(columns={"feature": "family"})
    family_imp.to_csv(RESULTS / "family_importance.csv", index=False)

    rf = make_rf_pipeline()
    rf.fit(t2_train[CAT_FEATURES + NUM_FEATURES], t2_train["target_30d"].to_numpy(dtype=np.int64))
    rf_pred = rf.predict_proba(t2_test[CAT_FEATURES + NUM_FEATURES])[:, 1]
    rf_metrics = metric_bundle(y_t2_test, rf_pred)

    rf_imp, _ = rf_raw_permutation_importance(rf, t2_test, y_t2_test)
    rf_imp["family"] = rf_imp["feature"].map(family_for_feature)
    rf_imp.to_csv(RESULTS / "rf_permutation_importance.csv", index=False)

    mdi = rf_impurity_importance(rf)
    mdi["family"] = mdi["feature"].map(family_for_feature)
    mdi.to_csv(RESULTS / "rf_impurity_importance.csv", index=False)

    rank_join = (
        mh_imp[["feature", "ap_drop_mean"]].rename(columns={"ap_drop_mean": "mh"})
        .merge(rf_imp[["feature", "ap_drop_mean"]].rename(columns={"ap_drop_mean": "rf"}), on="feature")
        .merge(mdi[["feature", "importance"]].rename(columns={"importance": "mdi"}), on="feature")
    )
    concordance = {
        "spearman_multihead_vs_rf_permutation": float(rank_join[["mh", "rf"]].corr(method="spearman").iloc[0, 1]),
        "spearman_multihead_vs_rf_mdi": float(rank_join[["mh", "mdi"]].corr(method="spearman").iloc[0, 1]),
        "n_features": int(len(rank_join)),
    }
    (RESULTS / "rank_concordance.json").write_text(
        json.dumps(concordance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    direction = directionality_rows(t2_test, mh_imp.head(12)["feature"].tolist())
    direction.to_csv(RESULTS / "directionality.csv", index=False)

    original = pd.read_csv(MODEL3 / "results" / "metrics_by_stage.csv")
    original_t2 = original[
        original["model"].eq("multihead_calibrated") & original["stage"].eq("T2_engaged")
    ].iloc[0]
    fidelity = {
        "original_t2": {
            "roc_auc": float(original_t2["roc_auc"]),
            "average_precision": float(original_t2["average_precision"]),
        },
        "retrained_multihead": {
            "roc_auc": float(mh_auc),
            "average_precision": float(mh_ap),
        },
        "random_forest": {
            "roc_auc": float(rf_metrics["roc_auc"]),
            "average_precision": float(rf_metrics["average_precision"]),
            "brier": float(rf_metrics["brier"]),
            "log_loss": float(rf_metrics["log_loss"]),
            "lift_top_10pct": float(rf_metrics["lift_top_10pct"]),
            "recall_top_20pct": float(rf_metrics["recall_top_20pct"]),
        },
        "test_population": {
            "n": int(len(t2_test)),
            "positive_rate": float(y_t2_test.mean()),
        },
    }
    (RESULTS / "model_fidelity.json").write_text(
        json.dumps(fidelity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    plot_ranked(mh_imp, CHARTS / "multihead_feature_importance.png")
    plot_family(family_imp, CHARTS / "family_importance.png")

    report = build_report(mh_imp, family_imp, direction, fidelity, concordance)
    (RESULTS / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
