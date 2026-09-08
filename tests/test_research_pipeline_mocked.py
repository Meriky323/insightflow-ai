import json
from app import db
from app.main import ResearchIn, _run_research

class FakeSerp:
    def __init__(self,*a,**k): pass
    def google_shopping(self, keyword, market, limit=20):
        return [{'source':'Google Shopping','market':market,'external_id':f'g-{market}','title':f'{keyword} product','url':'https://example.com/p','price':49.0,'currency':'USD','rating':4.5,'review_count':120,'seller':'Brand','raw':{}}]
    def walmart_search(self, keyword, limit=12):
        return [{'source':'Walmart','market':'US','external_id':'wm1','title':keyword,'url':'https://walmart.com/ip/wm1','price':39.0,'currency':'USD','rating':4.2,'review_count':80,'seller':'Brand','raw':{}}]
    def walmart_reviews(self, product, max_pages=2):
        return [
          {'source':'Walmart','market':'US','product_external_id':'wm1','product_title':product['title'],'review_external_id':'r1','text':'Compact and easy to carry. Works well.','rating':5,'review_date':'2 days ago','url':product['url']},
          {'source':'Walmart','market':'US','product_external_id':'wm1','product_title':product['title'],'review_external_id':'r2','text':'Gets hot and feels bulky in the hand.','rating':2,'review_date':'3 days ago','url':product['url']},
        ]
    def youtube_search(self, keyword, market, max_videos=4):
        return [{'video_id':f'v-{market}','title':f'{keyword} review','url':'https://youtube.com/watch?v=x','search_market':market}]
    def youtube_comments(self, video, max_pages=1):
        return [{'source':'YouTube','market':'GLOBAL','product_external_id':video['video_id'],'product_title':video['title'],'review_external_id':f"c-{video['video_id']}",'text':'I like the small size but heat is noticeable.','review_date':'1 day ago','url':video['url']}]
    def google_trends(self, keyword, market, days):
        return [{'market':market,'date_label':f'd{i}','timestamp':i,'value':v} for i,v in enumerate([20,25,30,35,40,45])]

def test_full_research_pipeline_collects_real_shaped_evidence(monkeypatch):
    monkeypatch.setenv('SERPAPI_API_KEY','fake')
    monkeypatch.delenv('LLM_API_KEY',raising=False)
    monkeypatch.setattr('app.main.SerpApiClient',FakeSerp)
    rid=db.create_research('portable device',['US','AU'],90,['shopping','walmart','youtube','trends'],'gtm')
    payload=ResearchIn(keyword='portable device',markets=['US','AU'],days=90,sources=['shopping','walmart','youtube','trends'],objective='gtm',depth='standard')
    _run_research(rid,payload,['US','AU'])
    r=db.get_research(rid)
    assert r['status']=='completed'
    products=db.rows_for(rid,'products'); reviews=db.rows_for(rid,'reviews'); trends=db.rows_for(rid,'trends')
    assert len(products)>=3
    assert len(reviews)>=4
    assert len(trends)==12
    assert any(x['source']=='Walmart' and x['market']=='US' for x in reviews)
    assert any(x['source']=='YouTube' and x['market']=='GLOBAL' for x in reviews)
    assert all(x.get('sentiment') in {'positive','neutral','negative'} for x in reviews)
    status=json.loads(r['source_status_json'])
    assert status['Google Shopping · US']['status']=='ok'
    assert status['Walmart reviews · US']['count']>=2
    assert status['Google Trends · AU']['status']=='ok'
