"""Method-specific chi-square and one-predictor OLS; no model or method switching."""
import numpy as np
import pandas as pd
from scipy import stats


def regression_fit(clean, p):
    x=clean[p['x']].to_numpy(dtype=float);y=clean[p['y']].to_numpy(dtype=float)
    X=np.column_stack([np.ones(len(x)),x])
    if np.linalg.matrix_rank(X)<2:
        raise ValueError('Predictor/intercept matrix is numerically rank deficient.')
    fit=stats.linregress(x,y)
    residual=y-(fit.intercept+fit.slope*x)
    sse=float(residual@residual)
    if not np.isfinite(sse) or not np.isfinite(residual).all() or not all(np.isfinite(v) for v in [fit.slope,fit.intercept,fit.stderr,fit.pvalue]):
        raise ValueError('Regression overflow or nonfinite fit; rescale and inspect the data before analysis.')
    if sse <= 1e-24*max(float(np.sum((y-y.mean())**2)),1.):
        raise ValueError('Near-perfect fit: residual inference is unstable under MVP policy.')
    return x,y,fit,residual,sse


def diagnose_additional(df,p):
    from .tools import prepared, distribution
    errors=[];notices=[];details={}
    if p['design']!='independent':
        errors.append('Independent observations must be confirmed; paired/clustered designs are not supported.')
    try:
        frame,clean=prepared(df,p)
        details.update(rows=len(frame),usable=len(clean),dropped=len(frame)-len(clean))
        if len(clean)<len(frame):
            notices.append('Complete-case deletion was used; missingness may bias results.')
        if p['goal']=='categorical':
            if any(pd.api.types.is_numeric_dtype(clean[c]) and not pd.api.types.is_bool_dtype(clean[c]) for c in [p['x'],p['y']]):
                raise ValueError('Categorical meaning must be explicit: convert numeric category codes to named text labels before this analysis.')
            table=pd.crosstab(clean[p['x']],clean[p['y']])
            if min(table.shape)<2 or max(table.shape)>20:
                raise ValueError('Chi-square requires two to twenty observed categories per variable.')
            expected=stats.contingency.expected_freq(table.values)
            details.update(contingency={'row_labels':list(map(str,table.index)),
                'column_labels':list(map(str,table.columns)),'observed':table.values.tolist(),
                'expected':expected.tolist()},min_expected=float(expected.min()),
                fraction_expected_below_five=float((expected<5).mean()))
            if (expected<1).any() or (expected<5).mean()>.2:
                errors.append('Chi-square approximation policy failed: expected count below one or more than twenty percent below five. Stop; no automatic Fisher fallback.')
            elif (expected<5).any():
                notices.append('Some expected counts are below five; accepted under documented approximation policy, not a guarantee of accuracy.')
            notices.append("Pearson chi-square without Yates correction. Cramer's V is unsigned association strength; no effect interval is computed.")
        else:
            if len(clean)<5 or any(clean[c].nunique()<2 for c in [p['x'],p['y']]):
                raise ValueError('Regression requires at least five complete pairs and nonconstant predictor/outcome under MVP policy.')
            x,y,fit,residual,sse=regression_fit(clean,p)
            n=len(x);mse=sse/(n-2)
            leverage=1/n+(x-x.mean())**2/np.sum((x-x.mean())**2)
            cooks=(residual**2/(2*mse))*leverage/np.maximum((1-leverage)**2,np.finfo(float).eps)
            squared=residual**2
            bp=float(n*stats.linregress(x,squared).rvalue**2) if np.ptp(squared)>0 else 0.
            bp_p=float(stats.chi2.sf(bp,1))
            details.update(residuals=distribution(residual),max_leverage=float(leverage.max()),
                max_cooks_distance=float(cooks.max()),influential_count=int((cooks>4/n).sum()),
                breusch_pagan_lm=bp,breusch_pagan_p=bp_p,
                diagnostic_note='Asymptotic LM from squared residuals regressed on intercept and x; small samples limit reliability.')
            if (cooks>4/n).any():
                notices.append('Potential influential observations (Cook distance threshold four divided by n); none removed automatically.')
            if bp_p<.05:
                notices.append('Heteroscedasticity diagnostic warning: ordinary slope p-value/interval may be unreliable. No automatic estimator change.')
            if details['residuals']['shapiro_p'] is not None and details['residuals']['shapiro_p']<.05:
                notices.append('Residual normality diagnostic warning; ordinary slope inference requires judgement.')
            notices.append('OLS with intercept: x is predictor, y is outcome. Linear mean model, independence and constant error variance are not established by diagnostics. No extrapolation or causal claims.')
        notices.append('This analysis does not establish causality, including when randomization is user-reported.')
    except (ValueError,TypeError,KeyError,np.linalg.LinAlgError) as exc:
        errors.append(str(exc))
    return {'errors':errors,'warnings':notices,'details':details}


def compute_additional(df,p,checks):
    from .tools import prepared
    frame,clean=prepared(df,p)
    if p['goal']=='categorical':
        table=pd.crosstab(clean[p['x']],clean[p['y']])
        test=stats.chi2_contingency(table.values,correction=False)
        r={'method':'chi_square','n':len(clean),'effect_name':"Cramer's V",
           'effect':float(np.sqrt(test.statistic/(len(clean)*min(table.shape[0]-1,table.shape[1]-1)))),
           'statistic':float(test.statistic),'p':float(test.pvalue),'df':int(test.dof),
           'ci_low':None,'ci_high':None,'confidence_level':None,
           'interval_note':'Effect interval not computed.','contrast':'Categorical association',
           'correction':False,'contingency':checks['details']['contingency']}
    else:
        x,y,fit,residual,sse=regression_fit(clean,p)
        margin=stats.t.ppf(.975,len(clean)-2)*fit.stderr
        if fit.stderr<=0:
            raise ValueError('Slope standard error is nonpositive; no inferential result.')
        r={'method':'linear_regression','n':len(clean),'effect_name':'Slope',
           'effect':float(fit.slope),'intercept':float(fit.intercept),'r_squared':float(fit.rvalue**2),
           'statistic':float(fit.slope/fit.stderr),'p':float(fit.pvalue),'df':len(clean)-2,
           'ci_low':float(fit.slope-margin),'ci_high':float(fit.slope+margin),'confidence_level':.95,
           'slope_stderr':float(fit.stderr),'contrast':f"{p['y']} per unit of {p['x']}"}
    if any(not np.isfinite(v) for k,v in r.items() if isinstance(v,float)):
        raise ValueError('Inference returned nonfinite values; no conclusion is generated.')
    return {**r,'dropped':len(frame)-len(clean),'warnings':checks['warnings']}
