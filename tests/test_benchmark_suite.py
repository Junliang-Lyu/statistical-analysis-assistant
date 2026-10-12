import pytest
from benchmark_suite import cases, reference, evaluate, PrespecifiedAgents, run


@pytest.mark.parametrize('case',cases(),ids=lambda c:c['id'])
def test_prespecified_benchmark_mechanics(case):
    r=evaluate(case,PrespecifiedAgents(case))
    assert r['mechanical_pass'],r['checks']
    if case['expected_behavior']=='result':
        assert r['interpretation_accepted']


def test_benchmark_unknown_case_rejected():
    with pytest.raises(ValueError,match='Unknown cases'):
        run(selected=['not_a_case'],export_only=True)


def test_reference_missing_and_filter_denominators():
    by_id={c['id']:c for c in cases()}
    assert reference(by_id['chi_square_missing'])['n']==79
    assert reference(by_id['regression_2025'])['n']==30
    assert reference(by_id['correlation_2025'])['n']==10
