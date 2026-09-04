from pathlib import Path
import json
import numpy as np
import pandas as pd

ABT = Path('codexway/outputs/abt/abt_t1_first_inquiry.parquet')
OUT = Path('scratch/user_requested_temporal_drift_audit.json')

CATEGORICAL = [
    'user_type','company_size','industry','search_sector','search_modality',
    'preferred_state','preferred_municipality','preferred_corridor','source',
    'channel','asked_visit'
]
NUMERIC = [
    'target_area_sqm','min_budget_mxn_rent_monthly','max_budget_mxn_rent_monthly',
    'min_budget_mxn_sale_total','max_budget_mxn_sale_total','message_length',
    'requested_area_sqm','requested_budget_mxn_rent_monthly',
    'requested_budget_mxn_sale_total','urgency_days','days_from_lead_creation',
    'area_request_to_target_ratio','rent_request_to_lead_budget_ratio',
    'sale_request_to_lead_budget_ratio'
]

def _psi_from_probs(p, q, eps=1e-6):
    p = np.asarray(p, dtype=float); q = np.asarray(q, dtype=float)
    p = np.clip(p, eps, None); q = np.clip(q, eps, None)
    p = p / p.sum(); q = q / q.sum()
    return float(np.sum((q - p) * np.log(q / p)))

def categorical_drift(train, other, col):
    a = train[col].astype('string').fillna('<missing>')
    b = other[col].astype('string').fillna('<missing>')
    cats = sorted(set(a.unique()).union(set(b.unique())))
    pa = a.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    pb = b.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    return {
        'psi': _psi_from_probs(pa, pb),
        'total_variation': float(0.5*np.abs(pa-pb).sum()),
        'n_levels_train': int(a.nunique()),
        'n_levels_other': int(b.nunique()),
        'missing_train': float((a=='<missing>').mean()),
        'missing_other': float((b=='<missing>').mean()),
    }

def numeric_drift(train, other, col):
    a = pd.to_numeric(train[col], errors='coerce')
    b = pd.to_numeric(other[col], errors='coerce')
    nonnull = a.dropna()
    if nonnull.nunique() < 2:
        return {'psi': 0.0, 'std_mean_shift': 0.0, 'missing_train': float(a.isna().mean()), 'missing_other': float(b.isna().mean())}
    qs = np.unique(nonnull.quantile(np.linspace(0,1,11)).to_numpy())
    if len(qs) < 3:
        edges = np.array([-np.inf, nonnull.median(), np.inf])
    else:
        edges = qs.copy(); edges[0] = -np.inf; edges[-1] = np.inf
    ba = pd.cut(a, bins=edges, include_lowest=True)
    bb = pd.cut(b, bins=edges, include_lowest=True)
    cats = ba.cat.categories
    pa = ba.value_counts(normalize=True, sort=False).reindex(cats, fill_value=0).to_numpy()
    pb = bb.value_counts(normalize=True, sort=False).reindex(cats, fill_value=0).to_numpy()
    std = float(nonnull.std(ddof=0))
    mean_shift = 0.0 if not np.isfinite(std) or std == 0 else float((b.mean()-a.mean())/std)
    return {
        'psi': _psi_from_probs(pa,pb),
        'std_mean_shift': mean_shift,
        'median_train': None if pd.isna(a.median()) else float(a.median()),
        'median_other': None if pd.isna(b.median()) else float(b.median()),
        'missing_train': float(a.isna().mean()),
        'missing_other': float(b.isna().mean()),
    }

def label(psi):
    if psi < 0.10: return 'low'
    if psi < 0.25: return 'moderate'
    return 'high'

df = pd.read_parquet(ABT)
df = df[df['target_t1'].notna()].copy()
parts = {s: df[df['split'].eq(s)].copy() for s in ['train','validation','test']}
result = {'n': {k:int(len(v)) for k,v in parts.items()}, 'comparisons': {}}
for other_name in ['validation','test']:
    rows = []
    for c in CATEGORICAL:
        if c in df:
            r = categorical_drift(parts['train'], parts[other_name], c)
            rows.append({'feature':c,'type':'categorical',**r,'severity':label(r['psi'])})
    for c in NUMERIC:
        if c in df:
            r = numeric_drift(parts['train'], parts[other_name], c)
            rows.append({'feature':c,'type':'numeric',**r,'severity':label(r['psi'])})
    rows.sort(key=lambda x: x['psi'], reverse=True)
    result['comparisons'][f'train_to_{other_name}'] = rows
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
