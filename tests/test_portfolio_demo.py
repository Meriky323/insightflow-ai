import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def load_demo():
    r=client.post('/api/demo/load',json={})
    assert r.status_code==200
    return r.json()['current_id']


def test_health_version():
    r=client.get('/api/health')
    assert r.status_code==200
    assert r.json()['version']=='2.0.0'
    assert r.json()['community_discovery'] is True
    assert r.json()['evidence_thread'] is True
    assert r.json()['bilingual_ui'] is True


def test_demo_is_traceable_and_market_guardrail_blocks_bad_comparison():
    rid=load_demo()
    s=client.get(f'/api/research/{rid}/summary').json()
    assert s['review_count']==18
    assert s['product_count']==8
    assert s['research']['decision']['demo_meta']['demo_schema_version']=='1.6'
    assert s['research_quality']['label'] in {'Thin','Directional','Strong'}
    assert s['market_comparison']['available'] is False
    assert 'No consumer-voice source' in s['market_comparison']['reason']
    assert s['historical_delta'] is not None


def test_demo_evidence_has_urls_and_unknown_dates_are_visible():
    rid=load_demo()
    data=client.get(f'/api/research/{rid}/reviews?limit=100').json()
    assert data['total']==18
    assert all((x.get('url') or '').startswith('https://') for x in data['rows'])
    assert any(x.get('window_status')=='unknown' for x in data['rows'])


def test_public_mode_hides_non_portfolio_research_and_disables_paid_paths(monkeypatch):
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','0')
    shell=client.post('/api/research',json={'keyword':'private local case','markets':['US'],'days':90,'sources':[],'objective':'gtm','depth':'quick'})
    assert shell.status_code==200
    private_id=shell.json()['id']
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','1')
    monkeypatch.setenv('ALLOW_PUBLIC_LIVE_RESEARCH','0')
    assert client.get(f'/api/research/{private_id}').status_code==404
    assert client.post('/api/research',json={'keyword':'should block','markets':['US'],'days':90,'sources':[]}).status_code==403
    assert client.get('/api/connections/test').status_code==403
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','0')


def test_public_demo_ask_is_local_and_grounded(monkeypatch):
    rid=load_demo()
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','1')
    monkeypatch.setenv('ALLOW_PUBLIC_LIVE_RESEARCH','0')
    monkeypatch.setenv('LLM_API_KEY','fake')
    monkeypatch.setenv('LLM_BASE_URL','http://127.0.0.1:9/v1')
    monkeypatch.setenv('LLM_MODEL','fake')
    r=client.post(f'/api/research/{rid}/ask',json={'question':'Can we safely compare US and AU consumer preferences?','language':'zh'})
    assert r.status_code==200
    assert r.json()['mode']=='local'
    assert '不支持 US 与 AU' in r.json()['answer']
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','0')


def test_pdf_and_csv_exports_work():
    rid=load_demo()
    pdf=client.get(f'/api/research/{rid}/export/pdf')
    csv=client.get(f'/api/research/{rid}/export/csv')
    assert pdf.status_code==200 and pdf.content[:4]==b'%PDF'
    assert csv.status_code==200 and b'source' in csv.content[:200]


def test_target_company_case_surface():
    page = client.get('/case-insta360-x6.html')
    assert page.status_code == 200
    text = page.text
    assert 'Insta360 X6' in text
    assert 'workflow becomes the product story' in text
    assert 'DECISION BOUNDARY' in text

def test_railway_auto_enables_public_mode(monkeypatch):
    monkeypatch.delenv('PUBLIC_DEPLOYMENT', raising=False)
    monkeypatch.setenv('RAILWAY_PUBLIC_DOMAIN', 'insightflow-ai.up.railway.app')
    from app.config import config_status
    assert config_status()['public_deployment'] is True


def test_bilingual_ui_surfaces_exist():
    home=client.get('/').text
    assert 'data-lang-toggle' in home
    js=client.get('/app.js').text
    assert '消费者洞察' in js
    case=client.get('/case-study.html').text
    x6=client.get('/case-insta360-x6.html').text
    assert "storageGet('if_lang')" in case
    assert "storageGet('if_lang')" in x6


def test_public_demo_ask_can_answer_english(monkeypatch):
    rid=load_demo()
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','1')
    monkeypatch.setenv('ALLOW_PUBLIC_LIVE_RESEARCH','0')
    r=client.post(f'/api/research/{rid}/ask',json={'question':'Can US and AU consumer preferences be compared?','language':'en'})
    assert r.status_code==200
    assert r.json()['mode']=='local'
    assert 'does not support' in r.json()['answer']
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','0')


def test_research_contract_accepts_community_source(monkeypatch):
    monkeypatch.setenv('PUBLIC_DEPLOYMENT','0')
    shell=client.post('/api/research',json={'keyword':'community-only shell','markets':['US'],'days':90,'sources':[],'objective':'gtm','depth':'quick'})
    assert shell.status_code==200
    # Pydantic contract is exercised separately from paid live collection.
    from app.main import ResearchIn, estimate_calls
    p=ResearchIn(keyword='action camera',markets=['US','AU'],days=90,sources=['community'],depth='quick')
    assert estimate_calls(p,['US','AU'])==1

def test_ui_has_evidence_drawer_and_motion_surface():
    home=client.get('/').text
    assert 'evidenceDrawer' in home
    assert 'hero-signal-stage' in home
    assert 'Reddit / Forums' in home
    motion=client.get('/motion.js')
    assert motion.status_code==200
    assert 'spotlight-card' in motion.text

def test_community_discussions_parser_uses_real_snippet_shape_without_geo_inference(monkeypatch):
    from app.collectors.serpapi import SerpApiClient
    c=SerpApiClient('x')
    fixture={'discussions_and_forums':[{'title':'Which camera is easiest to edit? - Reddit','link':'https://www.reddit.com/r/cameras/comments/abc/thread/','date':'2w','source':'Reddit','answers':[{'snippet':'The editing workflow matters more to me than another spec bump.','link':'https://www.reddit.com/r/cameras/comments/abc/thread/comment1','extensions':['Top answer','24 votes']}]}]}
    monkeypatch.setattr(c,'search',lambda **kwargs: fixture)
    rows=c.community_discussions('action camera','AU',10)
    assert len(rows)==1
    assert rows[0]['source']=='Reddit'
    assert rows[0]['market']=='GLOBAL'
    assert rows[0]['helpful']==24
    assert 'workflow matters' in rows[0]['text']
