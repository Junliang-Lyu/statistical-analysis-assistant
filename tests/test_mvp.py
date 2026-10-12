import numpy as np
import pandas as pd
import pytest
from scipy import stats
from langgraph.types import Command

from stat_assistant.tools import profile, diagnose, compute
from stat_assistant.agents import Plan, OfflineAgents
from stat_assistant.workflow import build_graph


def trial():
    rng = np.random.default_rng(42)
    return pd.DataFrame({'group': ['control'] * 25 + ['treatment'] * 25,
                         'outcome': np.r_[rng.normal(0, 1, 25), rng.normal(1, 1, 25)]})


def plan(**kwargs):
    return Plan(goal='difference', outcome='outcome', group='group', design='independent',
                study_type='observational', reason='Compare means', **kwargs).model_dump()


def test_welch_matches_reference():
    df = trial()
    result = compute(df, plan())
    ref = stats.ttest_ind(df.outcome[df.group == 'treatment'], df.outcome[df.group == 'control'], equal_var=False)
    assert result['p'] == pytest.approx(ref.pvalue)
    assert result['statistic'] == pytest.approx(ref.statistic)
    assert result['ci_low'] == pytest.approx(ref.confidence_interval().low)


def test_constant_correlation_stops():
    df = pd.DataFrame({'x': [1.] * 10, 'y': range(10)})
    p = Plan(goal='correlation', x='x', y='y', design='independent', reason='Association').model_dump()
    assert diagnose(df, p)['errors']


def test_profile_does_not_guess_design():
    assert 'design' not in profile(trial())


def test_nonfinite_data_rejected():
    df = trial(); df.loc[0, 'outcome'] = np.inf
    assert diagnose(df, plan())['errors']


def test_missing_rows_reported():
    df = trial(); df.loc[0, 'outcome'] = np.nan
    assert compute(df, plan())['dropped'] == 1


def test_graph_interrupt_resume_and_trace():
    g = build_graph(OfflineAgents())
    c = {'configurable': {'thread_id': 'trial'}}
    result = g.invoke({'data': trial().to_dict(orient='records'), 'question': 'Compare outcome between group', 'metadata': {}}, c)
    assert '__interrupt__' in result
    result = g.invoke(Command(resume={'design': 'independent', 'study_type': 'observational'}), c)
    assert result['status'] == 'completed'
    assert result['result']['method'] == 'welch_t_test'
    assert 'planner' in result['trace'] and 'interpret' in result['trace']
    assert result['interpretation']['causal_claim'] is False


def test_followup_recomputes_and_does_not_reuse_results():
    df = pd.DataFrame({'x': range(20), 'y': np.arange(20) + np.sin(np.arange(20)),
                       'date': ['2024-01-01'] * 10 + ['2025-01-01'] * 10})
    g = build_graph(OfflineAgents()); c = {'configurable': {'thread_id': 'corr'}}
    first = g.invoke({'data': df.to_dict(orient='records'), 'question': 'Correlation x y', 'metadata': {'design': 'independent'}}, c)
    second = g.invoke({'question': 'Only the last year', 'metadata': {'design': 'independent',
                        'filter': {'column': 'date', 'start': '2025-01-01', 'end': '2025-12-31'}}}, c)
    assert first['result']['n'] == 20 and second['result']['n'] == 10
    assert second['plan']['x'] == 'x' and second['plan']['y'] == 'y'
    assert second['rewrites'] == 0 and second['revisions'] == 0


def test_invalid_plan_stops_after_one_revision():
    class Bad(OfflineAgents):
        def plan(self, *args, **kwargs):
            return Plan(goal='difference', outcome='missing', group='group', design='independent', reason='Bad')
    g = build_graph(Bad())
    r = g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare', 'metadata': {'design': 'independent'}},
                 {'configurable': {'thread_id': 'bad'}})
    assert r['status'] == 'stopped' and r['revisions'] == 1
    assert r['result'] is None


def test_invalid_interpretation_preserves_numbers_and_stops():
    class Bad(OfflineAgents):
        def interpret(self, *args, **kwargs):
            return {'summary': 'This proves treatment works', 'causal_claim': True, 'limitations': []}
    g = build_graph(Bad())
    r = g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare outcome group', 'metadata': {'design': 'independent'}},
                 {'configurable': {'thread_id': 'bad-text'}})
    assert r['status'] == 'results_only' and r['rewrites'] == 1
    assert r['result']['p'] is not None and r['interpretation'] is None


def test_new_dataset_does_not_inherit_old_plan():
    g = build_graph(OfflineAgents()); c = {'configurable': {'thread_id': 'change'}}
    g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare outcome group', 'metadata': {'design': 'independent'}}, c)
    r = g.invoke({'data': pd.DataFrame({'a': range(10), 'b': np.arange(10)**2}).to_dict(orient='records'),
                  'question': 'correlation a b', 'metadata': {'design': 'independent'}}, c)
    assert r['plan']['x'] == 'a' and r['result']['method'] == 'pearson'


def test_paired_design_not_silently_changed():
    g = build_graph(OfflineAgents())
    r = g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare outcome group', 'metadata': {'design': 'paired'}},
                 {'configurable': {'thread_id': 'paired'}})
    assert r['status'] == 'stopped' and r['result'] is None


def test_pearson_interval_matches_reference():
    x = np.arange(20, dtype=float); y = x + np.sin(x)
    df = pd.DataFrame({'x': x, 'y': y})
    p = Plan(goal='correlation', x='x', y='y', design='independent', reason='Linear association').model_dump()
    r = compute(df, p); ref = stats.pearsonr(x, y)
    assert r['effect'] == pytest.approx(ref.statistic)
    assert r['p'] == pytest.approx(ref.pvalue)
    assert r['ci_high'] == pytest.approx(ref.confidence_interval().high)


def test_date_subset_invalid_dates_stop():
    df = pd.DataFrame({'x': range(10), 'y': np.arange(10)**2, 'date': ['invalid'] * 10})
    p = Plan(goal='correlation', x='x', y='y', design='independent', reason='Association',
             filter={'column': 'date', 'start': '2025-01-01', 'end': '2025-12-31'}).model_dump()
    assert diagnose(df, p)['errors']


def test_interrupt_does_not_repeat_planner_call():
    class Counting(OfflineAgents):
        count = 0
        def plan(self, *args, **kwargs):
            self.count += 1
            return super().plan(*args, **kwargs)
    a = Counting(); g = build_graph(a); c = {'configurable': {'thread_id': 'count'}}
    g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare', 'metadata': {}}, c)
    g.invoke(Command(resume={'design': 'independent'}), c)
    assert a.count == 1


def test_separate_threads_do_not_leak_prior_data():
    g = build_graph(OfflineAgents())
    g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare', 'metadata': {'design': 'independent'}},
             {'configurable': {'thread_id': 'one'}})
    r = g.invoke({'question': 'only last year', 'metadata': {}}, {'configurable': {'thread_id': 'two'}})
    assert r['status'] == 'stopped' and r['result'] is None


def test_unsupported_with_clarification_asks_instead_of_stopping():
    class Ambiguous(OfflineAgents):
        def plan(self, question, overview, prior, metadata, feedback):
            if not metadata.get('design'):
                return Plan(goal='unsupported', reason='Design missing', clarification='Confirm design')
            return super().plan(question, overview, prior, metadata, feedback)
    g = build_graph(Ambiguous()); c = {'configurable': {'thread_id': 'clarify'}}
    r = g.invoke({'data': trial().to_dict(orient='records'), 'question': 'compare', 'metadata': {}}, c)
    assert '__interrupt__' in r
    r = g.invoke(Command(resume={'design': 'independent'}), c)
    assert r['status'] == 'completed'


def test_noncausal_wording_not_rejected_by_keyword_alone():
    from stat_assistant.agents import check_interpretation
    r = compute(trial(), plan())
    raw = OfflineAgents().interpret(plan(), r, [])
    raw['limitations'] = ['This cannot establish a causal relationship.', 'It does not show that treatment causes improvement.']
    assert check_interpretation(raw, r) == []


def test_inconclusive_caveat_can_negate_no_difference_claim():
    from stat_assistant.agents import check_interpretation
    r = compute(trial(), plan())
    raw = OfflineAgents().interpret(plan(), r, [])
    raw['limitations'].append('A nonsignificant result does not establish that there is no difference.')
    assert check_interpretation(raw, r) == []


def test_date_filter_does_not_erase_variable_clarification():
    class Ambiguous(OfflineAgents):
        def plan(self, *args, **kwargs):
            return Plan(goal='difference', outcome='outcome', group='group', design='independent',
                        reason='Unclear', clarification='Which outcome should be used?')
    df = trial(); df['date'] = '2025-01-01'
    g = build_graph(Ambiguous())
    r = g.invoke({'data':df.to_dict(orient='records'),'question':'compare','metadata':{'design':'independent',
                  'filter':{'column':'date','start':'2025-01-01','end':'2025-12-31'}}},
                 {'configurable':{'thread_id':'filter-clarify'}})
    assert '__interrupt__' in r


def test_welch_interpretation_cannot_call_result_pearson():
    from stat_assistant.agents import check_interpretation
    r = compute(trial(), plan())
    raw = OfflineAgents().interpret(plan(), r, [])
    raw['summary'] += ' This is a Pearson-type linear association.'
    assert check_interpretation(raw, r)


def test_clarified_plan_does_not_retain_stale_design_reason():
    class Unconfirmed(OfflineAgents):
        def plan(self, *args, **kwargs):
            return Plan(goal='difference', outcome='outcome', group='group', reason='Design not confirmed', clarification='Confirm design')
    g = build_graph(Unconfirmed()); c = {'configurable':{'thread_id':'stale'}}
    g.invoke({'data':trial().to_dict(orient='records'),'question':'compare','metadata':{}},c)
    r = g.invoke(Command(resume={'design':'independent','study_type':'observational'}),c)
    assert 'not confirmed' not in r['plan']['reason'].lower()


def test_null_hypothesis_description_is_not_a_no_difference_conclusion():
    from stat_assistant.agents import check_interpretation
    r=compute(trial(),plan()); raw=OfflineAgents().interpret(plan(),r,[])
    raw['summary'] += ' The null hypothesis is no difference in population means.'
    assert check_interpretation(raw,r)==[]


def test_unqualified_no_difference_statement_is_rejected():
    from stat_assistant.agents import check_interpretation
    r=compute(trial(),plan()); raw=OfflineAgents().interpret(plan(),r,[])
    raw['summary'] += ' There is no difference between groups.'
    assert check_interpretation(raw,r)
