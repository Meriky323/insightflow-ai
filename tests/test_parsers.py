from app.analysis import annotate, summarize
from app.collectors.serpapi import SerpApiClient


def test_annotation():
    r=annotate({'text':'It gets too hot and I am returning it.','rating':1})
    assert r['sentiment']=='negative'
    assert r['issue']=='Heat & safety'
    assert r['purchase_impact']=='Return / refund'


def test_summary():
    reviews=[annotate({'text':'It gets too hot and I am returning it.','rating':1,'source':'Walmart','market':'US'}),annotate({'text':'Compact and convenient for travel, I recommend it.','rating':5,'source':'Walmart','market':'US'})]
    s=summarize([],reviews,[])
    assert s['review_count']==2
    assert s['issues'][0]['name']=='Heat & safety'
