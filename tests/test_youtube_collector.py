from app.collectors.serpapi import SerpApiClient


def test_youtube_comments_uses_comment_token_and_returns_rows(monkeypatch):
    c=SerpApiClient('fake')
    calls=[]
    def fake_search(**params):
        calls.append(params)
        if 'v' in params:
            return {
              'comments_sorting_token':[{'title':'Newest first','token':'NEWEST'}],
              'comments_next_page_token':'TOP'
            }
        if params.get('next_page_token')=='NEWEST':
            return {'comments':[{'comment_id':'c1','content':'Real user comment','published_date':'2 days ago','channel':{'name':'User'},'extracted_vote_count':3}]}
        return {}
    monkeypatch.setattr(c,'search',fake_search)
    rows=c.youtube_comments({'video_id':'v1','title':'Review','url':'https://youtube.com/watch?v=v1'},max_pages=1)
    assert len(rows)==1
    assert rows[0]['text']=='Real user comment'
    assert rows[0]['market']=='GLOBAL'
    assert calls[1]['next_page_token']=='NEWEST'
