import json
from app.analysis import annotate_fallback

def test_fallback_preserves_multiple_aspects_without_llm():
    row=annotate_fallback({'text':'Compact and easy to use, but it gets hot and does not fit.'})
    topics=json.loads(row['topics_json'])
    assert {'Size / ergonomics','Ease of use','Safety / comfort','Compatibility / fit'} <= set(topics)
    assert row['analysis_mode']=='local-fallback'

def test_chinese_compound_review_keeps_each_aspect():
    row=annotate_fallback({'text':'产品很薄，但使用时发热而且磁吸不稳定'})
    assert {'Slimness','Heat / thermal behavior','Magnetic stability'} <= set(json.loads(row['topics_json']))

def test_comparison_matches_overview(client=None):
    from fastapi.testclient import TestClient
    from app.main import app
    c=TestClient(app)
    demo=c.post('/api/demo/load').json()
    overview=c.get(f"/api/research/{demo['current_id']}/summary").json()
    baseline=overview['historical_delta']['baseline']['id']
    comparison=c.get(f"/api/research/{demo['current_id']}/compare/{baseline}").json()
    assert comparison['topic_changes']==overview['historical_delta']['topic_changes']
