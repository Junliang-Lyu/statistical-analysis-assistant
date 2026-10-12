"""Deterministic profiling, diagnostics and statistical tools. No model calls."""
import hashlib
import warnings

import numpy as np
import pandas as pd
from scipy import stats


def fingerprint(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()
                          + repr(list(df.columns)).encode()).hexdigest()


def profile(df):
    if df.empty or len(df) > 100_000 or len(df.columns) > 100:
        raise ValueError('CSV must have 1–100000 rows and at most 100 columns.')
    if not df.columns.is_unique:
        raise ValueError('Column names must be unique.')
    return {'rows': len(df), 'columns': {str(c): {'dtype': str(df[c].dtype),
            'missing': int(df[c].isna().sum()), 'unique': int(df[c].nunique()),
            'labels': sorted(map(str, df[c].dropna().unique()))[:8] if not pd.api.types.is_numeric_dtype(df[c]) else []}
            for c in df.columns}}


def subset(df, p):
    f = p.get('filter')
    if not f:
        return df
    if f['column'] not in df:
        raise ValueError('Date filter column does not exist.')
    dates = pd.to_datetime(df[f['column']], format='mixed', errors='coerce', utc=True)
    start, end = pd.to_datetime(f['start'], utc=True), pd.to_datetime(f['end'], utc=True)
    if start > end or dates.isna().any():
        raise ValueError('Date filter requires valid dates and start <= end.')
    return df.loc[(dates >= start.normalize()) & (dates < end.normalize() + pd.Timedelta(days=1))]


def prepared(df, p):
    frame = subset(df, p)
    cols = [p['outcome'], p['group']] if p['goal'] == 'difference' else [p['x'], p['y']]
    if any(c not in frame for c in cols) or len(set(cols)) != 2:
        raise ValueError('Select two distinct existing columns.')
    numeric = [p['outcome']] if p['goal'] == 'difference' else ([] if p['goal']=='categorical' else cols)
    if any(not pd.api.types.is_numeric_dtype(frame[c]) or pd.api.types.is_bool_dtype(frame[c]) for c in numeric):
        raise ValueError('Analysis variables must be numeric; categorical codes need user judgement.')
    clean = frame[cols].dropna()
    if not np.isfinite(clean[numeric].to_numpy(dtype=float)).all():
        raise ValueError('Infinite values are not supported.')
    return frame, clean


def distribution(values):
    a = np.asarray(values, dtype=float)
    if len(a) < 3 or np.ptp(a) == 0:
        return {'n': len(a), 'constant': True, 'skew': 0., 'outliers': 0, 'extreme': 0, 'shapiro_p': None}
    q1, q3 = np.percentile(a, [25, 75]); iqr = q3 - q1
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        shapiro = float(stats.shapiro(a).pvalue) if len(a) <= 5000 else None
        skew = float(stats.skew(a, bias=False))
    return {'n': len(a), 'constant': False, 'skew': skew,
            'outliers': int(((a < q1 - 1.5*iqr) | (a > q3 + 1.5*iqr)).sum()),
            'extreme': int(((a < q1 - 3*iqr) | (a > q3 + 3*iqr)).sum()), 'shapiro_p': shapiro}


def diagnose(df, p):
    if p['goal'] in ('categorical','regression'):
        from .additional_tools import diagnose_additional
        return diagnose_additional(df,p)
    errors, notices, details = [], [], {}
    if p['goal'] not in ('difference', 'correlation'):
        return {'errors': ['Unsupported analysis: use independent Welch, Pearson, categorical chi-square or simple one-predictor regression.'], 'warnings': [], 'details': {}}
    if p['design'] != 'independent':
        errors.append('Independent observations must be confirmed; paired/clustered designs are not supported.')
    try:
        frame, clean = prepared(df, p)
        details.update(rows=len(frame), usable=len(clean), dropped=len(frame)-len(clean))
        if len(clean) < len(frame):
            notices.append('Complete-case deletion was used; missingness may bias results.')
        if p['goal'] == 'difference':
            groups = sorted(clean[p['group']].unique(), key=str)
            if len(groups) != 2:
                errors.append('Exactly two nonempty groups are required.')
            else:
                ds = {str(g): distribution(clean.loc[clean[p['group']] == g, p['outcome']]) for g in groups}
                details['groups'] = ds
                for g, d in ds.items():
                    if d['n'] < 5 or d['constant']:
                        errors.append(f'Group {g}: insufficient usable observations or constant outcome.')
                    if d['n'] < 30 and (abs(d['skew']) > 2 or d['extreme'] > 0):
                        errors.append(f'Group {g}: conservative MVP policy stops small samples with severe skew/extreme outliers; no automatic method switch.')
                notices.append('Welch does not require equal variances; independence is user-confirmed, not verified from CSV.')
                if any(d['shapiro_p'] is not None and d['shapiro_p'] < .05 for d in ds.values()):
                    notices.append('Non-normality diagnostic: not an automatic reason to change the estimand or test.')
        else:
            ds = {c: distribution(clean[c]) for c in [p['x'], p['y']]}
            details['variables'] = ds
            if len(clean) < 4 or any(d['constant'] for d in ds.values()):
                errors.append('Pearson needs at least four usable pairs under MVP policy and nonconstant variables.')
            notices.append('Pearson measures linear association; design, linearity and default inference assumptions are not guaranteed by these diagnostics.')
            if any(d['outliers'] > 0 for d in ds.values()):
                notices.append('Potential outliers: correlation may be sensitive; none were automatically removed.')
        if p['study_type'] != 'randomized':
            notices.append('Study design does not establish causality. Report association or group differences only.')
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
    return {'errors': errors, 'warnings': notices, 'details': details}


def compute(df, p):
    checks = diagnose(df, p)
    if checks['errors']:
        raise ValueError('; '.join(checks['errors']))
    if p['goal'] in ('categorical','regression'):
        from .additional_tools import compute_additional
        return compute_additional(df,p,checks)
    frame, clean = prepared(df, p)
    if p['goal'] == 'difference':
        labels = sorted(clean[p['group']].unique(), key=str)
        a = clean.loc[clean[p['group']] == labels[1], p['outcome']].to_numpy(dtype=float)
        b = clean.loc[clean[p['group']] == labels[0], p['outcome']].to_numpy(dtype=float)
        test = stats.ttest_ind(a, b, equal_var=False)
        ci = test.confidence_interval()
        r = {'method': 'welch_t_test', 'n': len(clean), 'n_groups': [len(a), len(b)],
             'contrast': f'{labels[1]} minus {labels[0]}', 'effect': float(a.mean()-b.mean()),
             'statistic': float(test.statistic), 'p': float(test.pvalue), 'df': float(test.df),
             'ci_low': float(ci.low), 'ci_high': float(ci.high)}
    else:
        test = stats.pearsonr(clean[p['x']], clean[p['y']]); ci = test.confidence_interval()
        r = {'method': 'pearson', 'n': len(clean), 'effect': float(test.statistic),
             'statistic': float(test.statistic), 'p': float(test.pvalue),
             'ci_low': float(ci.low), 'ci_high': float(ci.high)}
    if not all(np.isfinite(r[k]) for k in ['effect', 'statistic', 'p', 'ci_low', 'ci_high']):
        raise ValueError('Inference returned nonfinite values; no conclusion is generated.')
    return {**r, 'dropped': len(frame)-len(clean), 'confidence_level': .95, 'warnings': checks['warnings']}
