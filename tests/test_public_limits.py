import pytest
from public_server import PublicWorkspace, Budget, PublicError, valid_origin


def test_origin_requires_exact_configured_host_and_origin():
    assert valid_origin('stats.example.com', 'https://stats.example.com', 'https://stats.example.com')
    assert not valid_origin('evil.example.com', 'https://stats.example.com', 'https://stats.example.com')
    assert not valid_origin('stats.example.com', 'https://evil.example.com', 'https://stats.example.com')


def test_budget_is_atomic_persistent_and_fail_closed(tmp_path):
    b=Budget(tmp_path/'budget.sqlite3', daily=.02, monthly=.03)
    b.reserve(.015)
    with pytest.raises(PublicError, match='budget'): b.reserve(.01)
    again=Budget(tmp_path/'budget.sqlite3', daily=.02, monthly=.03)
    with pytest.raises(PublicError): again.reserve(.01)


def test_quota_survives_restart(tmp_path):
    b=Budget(tmp_path/'budget.sqlite3', per_client=1)
    b.operation('client')
    with pytest.raises(PublicError, match='limit'): b.operation('client')
    again=Budget(tmp_path/'budget.sqlite3', per_client=1)
    with pytest.raises(PublicError): again.operation('client')


def test_sessions_are_owned_and_expire(tmp_path):
    clock=[100.]
    w=PublicWorkspace(Budget(tmp_path/'b.sqlite3'),clock=lambda:clock[0],ttl=10)
    a=w.handle_public({'action':'analyze','mode':'offline','case':'trial','question':'Compare means',
                     'metadata':{'design':'independent','study_type':'observational'}},'owner','ip')
    with pytest.raises(PublicError): w.handle_public({'action':'followup','session':a['session'],'question':'Explain result'},'other','ip')
    clock[0]=111
    with pytest.raises(PublicError,match='expired'): w.handle_public({'action':'followup','session':a['session'],'question':'Explain result'},'owner','ip')
    assert not w.sessions


def test_public_csv_and_question_are_bounded(tmp_path):
    w=PublicWorkspace(Budget(tmp_path/'b.sqlite3'))
    with pytest.raises(PublicError): w.handle_public({'action':'analyze','question':'a'*2001},'owner','ip')
    with pytest.raises(PublicError): w.handle_public({'action':'analyze','question':'test','csv':'x,y\n'+'1,2\n'*10001},'owner','ip')


def test_offline_analysis_and_explanation_preserve_result(tmp_path):
    w=PublicWorkspace(Budget(tmp_path/'b.sqlite3'))
    a=w.handle_public({'action':'analyze','mode':'offline','case':'trial','question':'Compare means',
                      'metadata':{'design':'independent','study_type':'observational'}},'owner','ip')
    b=w.handle_public({'action':'followup','session':a['session'],'intent':'explain','question':'Explain result'},'owner','ip')
    assert b['result']==a['result'] and 'run_test' not in b['trace']


def test_budget_reservation_precedes_provider_and_is_not_refunded(tmp_path,monkeypatch):
    from public_server import BudgetAgents
    from stat_assistant.agents import DeepSeekAgents
    monkeypatch.setenv('DEEPSEEK_API_KEY','test-only-placeholder')
    monkeypatch.setenv('STATS_PRICED_MODEL','deepseek-chat')
    monkeypatch.setenv('DEEPSEEK_MODEL','deepseek-chat')
    monkeypatch.setenv('STATS_INPUT_USD_PER_MILLION','1')
    monkeypatch.setenv('STATS_OUTPUT_USD_PER_MILLION','1')
    b=Budget(tmp_path/'b.sqlite3',daily=.01)
    def fail(*args): raise ValueError('simulated network failure')
    monkeypatch.setattr(DeepSeekAgents,'_json',fail)
    a=BudgetAgents(b)
    with pytest.raises(ValueError,match='simulated'): a._json('system',{}, {},'planner')
    with pytest.raises(PublicError,match='budget'): a._json('system',{}, {},'planner')


def test_expiry_cleans_idle_sessions_without_new_analysis(tmp_path):
    clock=[100.]
    w=PublicWorkspace(Budget(tmp_path/'b.sqlite3'),clock=lambda:clock[0],ttl=10)
    w.handle_public({'action':'analyze','mode':'offline','case':'trial','question':'Compare means',
                     'metadata':{'design':'independent'}},'owner','ip')
    clock[0]=111; w.expire()
    assert not w.sessions and not w.owners
