from app.research_strategy import community_queries


def test_community_query_plan_is_small_and_objective_aware():
    assert community_queries('action camera','gtm','quick') == ['action camera']
    standard=community_queries('action camera','product_launch','standard')
    assert len(standard)==2 and 'problems' in standard[1]
    deep=community_queries('action camera','competitor','deep')
    assert len(deep)==3 and any('alternatives' in q for q in deep)


def test_community_query_plan_dedupes_whitespace():
    assert community_queries('  magnetic   power bank  ','gtm','quick') == ['magnetic power bank']


def test_estimated_serpapi_calls_reflect_query_expansion():
    from app.main import ResearchIn, estimate_calls
    quick=ResearchIn(keyword='action camera',markets=['US'],days=90,sources=['community'],objective='gtm',depth='quick')
    standard=ResearchIn(keyword='action camera',markets=['US'],days=90,sources=['community'],objective='gtm',depth='standard')
    deep=ResearchIn(keyword='action camera',markets=['US'],days=90,sources=['community'],objective='gtm',depth='deep')
    assert estimate_calls(quick,['US'])==1
    assert estimate_calls(standard,['US'])==2
    assert estimate_calls(deep,['US'])==3


def test_polish_assets_and_design_demos_are_served():
    from fastapi.testclient import TestClient
    from app.main import app
    c=TestClient(app)
    assert c.get('/polish-v21.css').status_code==200
    assert c.get('/polish-v21.js').status_code==200
    assert c.get('/demos/final_selected_hybrid.html').status_code==200
