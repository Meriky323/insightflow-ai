"""Offline regression tests; fixture data is never shipped as research evidence."""
import json
import httpx
from fastapi.testclient import TestClient
from app.main import app, ResearchIn, estimate_calls
from app import llm

client = TestClient(app)


def test_import_dedup_filter_and_export_end_to_end(monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    rid = client.post('/api/research', json={
        'keyword': 'acceptance fixture', 'sources': [], 'days': 90,
    }).json()['id']
    content = ('source,text,date,url\n'
               'Survey,Compact and easy to carry.,today,https://example.com/fixture\n'
               'Survey,Compact and easy to carry.,today,https://example.com/fixture\n')
    def upload():
        return client.post(f'/api/research/{rid}/import', files={
            'file': ('test.csv', content.encode(), 'text/csv'),
        })
    first = upload()
    assert first.status_code == 200
    assert first.json()['imported'] == 1
    assert upload().json()['imported'] == 0
    rows = client.get(f'/api/research/{rid}/reviews', params={'q': 'Compact'}).json()
    assert rows['total'] == 1 and rows['rows'][0]['market'] == 'GLOBAL'
    assert client.get(f'/api/research/{rid}/reviews?q=absent').json()['total'] == 0
    assert client.get(f'/api/research/{rid}/summary').json()['review_count'] == 1
    ask = client.post(f'/api/research/{rid}/ask', json={'question': 'What is supported?'})
    assert ask.status_code == 200 and ask.json()['mode'] == 'local'
    for kind, signature in [('pdf', b'%PDF'), ('docx', b'PK'), ('csv', b'\xef\xbb\xbf')]:
        export = client.get(f'/api/research/{rid}/export/{kind}')
        assert export.status_code == 200 and export.content.startswith(signature)


def test_youtube_budget_includes_token_request():
    for depth, expected in [('quick', 3), ('standard', 5), ('deep', 7)]:
        payload = ResearchIn(keyword='camera', sources=['youtube'], depth=depth)
        assert estimate_calls(payload, ['US', 'AU']) == expected * 2


def test_connection_test_requires_generation_not_just_models(monkeypatch):
    for key, value in {'LLM_API_KEY': 'test-only', 'LLM_BASE_URL': 'https://fixture.invalid/v1', 'LLM_MODEL': 'fixture-model'}.items():
        monkeypatch.setenv(key, value)
    original = httpx.Client
    requested = []
    def handler(request):
        requested.append(request.url.path)
        if request.url.path.endswith('/models'):
            return httpx.Response(200, json={'data': [{'id': 'fixture-model'}]})
        payload = json.loads(request.content)
        assert payload['model'] == 'fixture-model'
        return httpx.Response(200, json={'choices': [{'message': {'content': 'OK'}}]})
    monkeypatch.setattr(llm.httpx, 'Client', lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    result = llm.test_llm_connection()
    assert result['ok'] and result['generation_verified']
    assert requested == ['/v1/models', '/v1/chat/completions']


def test_llm_structured_extraction_keeps_missing_fields_empty(monkeypatch):
    monkeypatch.setattr(llm, '_chat', lambda *a, **kw: json.dumps({'items': [
        {'i': 0, 'sentiment': 'negative', 'topics': ['Export reliability'], 'barrier': 'Export crashes'},
    ]}))
    result = llm.analyze_review_batch([{'text': 'Export crashes.'}], 'camera app')
    assert result[0]['barrier'] == 'Export crashes'
    assert result[0]['scenario'] is None
    assert result[0]['competitor_mentions'] == []
