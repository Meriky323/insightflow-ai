"""Build ONLY the repository's public demo in a fresh isolated database.

Never read the analyst's database or .env. Run: python scripts/build_public.py
"""
import json
import ast
import re
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ['PUBLIC_DEPLOYMENT'] = '1'
os.environ['ALLOW_PUBLIC_LIVE_RESEARCH'] = '0'
for key in ['SERPAPI_API_KEY', 'LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL']:
    os.environ.pop(key, None)

with tempfile.TemporaryDirectory(prefix='insightflow-public-') as tmp:
    os.environ['DATA_DIR'] = tmp
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    def get(path):
        response = client.get(path)
        response.raise_for_status()
        return response.json()
    demo = client.post('/api/demo/load').json()
    records = get('/api/researches')
    out = ROOT / 'cloudflare' / 'public'
    out.mkdir(parents=True, exist_ok=True)
    for p in (ROOT / 'static').iterdir():
        if p.is_file():
            shutil.copy2(p, out / p.name)
    snapshots = {}
    for record in records:
        rid = record['id']
        prefix = f'/api/research/{rid}'
        item = {'research': record}
        for resource in ['summary', 'products', 'trends']:
            item[resource] = get(f'{prefix}/{resource}')
        item['reviews'] = get(f'{prefix}/reviews?limit=5000')['rows']
        item['comparisons'] = {str(r['id']): get(f"{prefix}/compare/{r['id']}") for r in records}
        for row in item['reviews']:
            row['evidence_type'] = 'curated_paraphrase'
        dest = out / 'downloads' / str(rid)
        dest.mkdir(parents=True, exist_ok=True)
        for kind in ['pdf', 'csv', 'docx']:
            response = client.get(f'{prefix}/export/{kind}')
            response.raise_for_status()
            (dest / f'insightflow.{kind}').write_bytes(response.content)
        snapshots[str(rid)] = item
    ui_source=(ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
    translations=ast.literal_eval(re.search(r'const DEMO_TEXT_ZH\s*=\s*(\{.*?\});',ui_source,re.S).group(1))
    payload = {'demo': demo, 'researches': records, 'snapshots': snapshots, 'translations':translations}
    (ROOT / 'cloudflare' / 'snapshot.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    source=(ROOT / 'cloudflare' / 'worker.mjs').read_text(encoding='utf-8')
    source=source.replace("import data from './snapshot.json' with { type: 'json' };", 'const data = '+json.dumps(payload, ensure_ascii=False)+';')
    (ROOT / 'cloudflare' / 'worker-built.mjs').write_text(source, encoding='utf-8')
    (out / '_worker.js').write_text(source, encoding='utf-8')
    (out / '_routes.json').write_text(json.dumps({'version':1,'include':['/api/*'],'exclude':[]}), encoding='utf-8')
    shutil.make_archive(str(ROOT / 'cloudflare' / 'insightflow-pages'), 'zip', out)
    print(f'Built {len(records)} public snapshots; no analyst data or credentials included.')
