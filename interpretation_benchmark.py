"""Planted-error checks; labels are authored test expectations, not human-reviewed model accuracy."""
from copy import deepcopy
import json
from pathlib import Path
from benchmark_suite import cases
from stat_assistant.tools import compute
from stat_assistant.agents import OfflineAgents, Plan, check_interpretation, render_interpretation

ROOT=Path(__file__).resolve().parent


def challenges():
    rows=[];selected={c['id']:c for c in cases()}
    for cid in ['welch_clean','pearson_clean','chi_square_2x2','regression_clean']:
        c=selected[cid];p=Plan.model_validate({**c['plan'],**c['metadata']}).model_dump()
        result=compute(c['data'],p);base=OfflineAgents().interpret(p,result,[])
        def add(suffix,draft,expected,note):
            rows.append({'id':cid+'_'+suffix,'question':c['question'],'plan':p,'result':result,
                'draft':deepcopy(draft),'expected_valid':expected,'note':note,
                'source':'Authored test double / planted mutation; not a real model output.'})
        add('valid',base,True,'Correct controlled template with tool placeholders.')
        bad=deepcopy(base);bad['summary']=bad['summary'].replace('{p}','0.123')
        add('wrong_number',bad,False,'Inserted unsupported numerical literal and removed p placeholder.')
        bad=deepcopy(base);bad['summary']+=' This analysis causes improvement.'
        add('causal',bad,False,'Unqualified causal assertion despite observational design.')
    base=next(c for c in rows if c['id']=='welch_clean_valid')
    bad=deepcopy(base);bad.update(id='welch_wrong_method',expected_valid=False,note='Welch misdescribed as Pearson.')
    bad['draft']['summary']+=' This is Pearson correlation.';rows.append(bad)
    base=next(c for c in rows if c['id']=='pearson_clean_valid')
    bad=deepcopy(base);bad.update(id='pearson_percent_misinterpretation',expected_valid=False,
        note='Semantic blind spot: coefficient described as an eighty-percent increase using words, which can evade the current checks.')
    bad['draft']['summary']+=' This means the outcome increases by eighty percent.';rows.append(bad)
    base=next(c for c in rows if c['id']=='regression_clean_valid')
    bad=deepcopy(base);bad.update(id='regression_interval_probability',expected_valid=False,
        note='Semantic blind spot: frequentist interval described as probability of the fixed parameter.')
    bad['draft']['summary']+=' The fixed true slope has a ninety-five percent probability of lying inside this observed interval.';rows.append(bad)
    c=selected['pearson_nonlinear'];p=Plan.model_validate({**c['plan'],**c['metadata']}).model_dump();result=compute(c['data'],p)
    draft=OfflineAgents().interpret(p,result,[]);draft['summary']+=' There is no relationship between these variables.'
    rows.append({'id':'nonlinear_no_relationship','question':c['question'],'plan':p,'result':result,'draft':draft,
        'expected_valid':False,'note':'Near-zero Pearson does not exclude U-shaped dependence; this wording can evade current phrase checks.',
        'source':'Authored planted semantic error, not a model-output accuracy measurement.'})
    return rows


def run():
    root=ROOT/'examples/interpretation_checks';rows=challenges();evaluated=[]
    for row in rows:
        group='valid' if row['expected_valid'] else 'planted_errors';folder=root/group;folder.mkdir(parents=True,exist_ok=True)
        issues=check_interpretation(row['draft'],row['result'])
        record={**row,'rendered_text':render_interpretation(row['draft'],row['result']),
                'code_accepted':not issues,'code_feedback':issues,'detector_matches_label':bool(not issues)==row['expected_valid']}
        (folder/(row['id']+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8');evaluated.append(record)
    errors=[r for r in evaluated if not r['expected_valid']];missed=[r for r in errors if r['code_accepted']]
    lines=['# Interpretation challenge set','', 'Controlled templates and deliberately planted errors. This measures known detector coverage, not real-model semantic accuracy.',
        f'Planted errors caught: {len(errors)-len(missed)}/{len(errors)}. Valid templates accepted: {sum(r["code_accepted"] for r in evaluated if r["expected_valid"])}/4.',
        '', '| Case | Expected valid | Code accepted | Note |','|---|---|---|---|']
    lines += [f"| {r['id']} | {r['expected_valid']} | {r['code_accepted']} | {r['note']} |" for r in evaluated]
    lines += ['', 'Do not infer overall reliability from these counts. Missing semantic detections illustrate why format/keyword checks are insufficient. Inspect actual model outputs separately; no fabricated human-review scores.']
    (root/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Interpretation planted errors caught:',len(errors)-len(missed),'/',len(errors))


if __name__=='__main__':run()
