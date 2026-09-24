import json
from app.analysis import _competitor_benchmark

def test_brand_co_mention_does_not_assign_negative_sentiment_to_product():
    products=[{'source':'Official','external_id':'p1','title':'Alpha charger','seller':'Alpha','market':'AU'}]
    reviews=[{'id':1,'source':'Reddit','market':'GLOBAL','sentiment':'negative','competitor_mentions_json':json.dumps(['Alpha','Beta']),'topics_json':json.dumps(['Heat'])}]
    result=_competitor_benchmark(products,reviews)[0]
    assert result['evidence_sample']==1
    assert result['evidence_ids']==[1]
    assert result['negative_share'] is None

def test_direct_product_review_can_have_descriptive_negative_share():
    products=[{'source':'Walmart','external_id':'p1','title':'Alpha charger','market':'US'}]
    reviews=[{'id':1,'source':'Walmart','product_external_id':'p1','market':'US','sentiment':'negative'}]
    assert _competitor_benchmark(products,reviews)[0]['negative_share']==100
