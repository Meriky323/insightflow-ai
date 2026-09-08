"""Run real local API acceptance using the project's existing .env.

This spends connector/model quota. It does not load the curated demo, create
synthetic evidence, expose keys, or publish local research. Run from the BAT file.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def assess_research(summary: dict, reviews: list[dict], ask: dict) -> dict[str, bool]:
    """A completed job or a fallback answer alone must never pass AI acceptance."""
    meta = summary.get('research') or {}
    decisions = (meta.get('decision') or {}).get('opportunities') or []
    topics = {item.get('name') for item in summary.get('issues') or []}
    return {
        'Research completed': meta.get('status') == 'completed',
        'Collected consumer evidence': bool(reviews),
        'Every row has a source URL': bool(reviews) and all(
            r.get('source') and str(r.get('url') or '').startswith(('https://', 'http://'))
            for r in reviews
        ),
        'All consumer rows analyzed by LLM': bool(reviews) and all(
            r.get('analysis_mode') == 'llm' for r in reviews
        ),
        'Structured topics returned': bool(topics),
        'Grounded action plan returned': any(
            d.get('name') in topics and all(d.get(k) for k in
                ('insight', 'product_action', 'gtm_action', 'next_validation'))
            for d in decisions
        ),
        'Ask used the real LLM': ask.get('mode') == 'llm-grounded' and bool(str(ask.get('answer') or '').strip()),
    }


def run(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyword', default='magnetic power bank')
    parser.add_argument('--source', nargs='+', choices=['shopping', 'walmart', 'youtube', 'trends', 'community'],
                        default=['shopping', 'walmart', 'youtube', 'trends', 'community'])
    parser.add_argument('--timeout', type=int, default=900, help='Maximum wait for research completion, seconds')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    from fastapi.testclient import TestClient
    from app.config import get
    from app.main import app, ResearchIn, estimate_calls

    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'keyword': args.keyword,
              'checks': [], 'status': 'NOT_COMPLETED', 'research_id': None}
    secret_values = [get('SERPAPI_API_KEY'), get('LLM_API_KEY')]

    def redact(text):
        value = str(text)
        for secret in secret_values:
            if secret:
                value = value.replace(secret, '[REDACTED]')
        return value

    def check(name, passed, detail=''):
        item = {'name': name, 'status': 'PASS' if passed else 'FAIL', 'detail': redact(detail)}
        report['checks'].append(item)
        print(f"[{item['status']}] {name}" + (f": {item['detail']}" if detail else ''), flush=True)
        return passed

    def write_result():
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        (ROOT / 'LIVE_CHECK_RESULT.json').write_text(
            redact(json.dumps(report, ensure_ascii=False, indent=2)), encoding='utf-8')
        lines = ['InsightFlow real research acceptance', f"RESULT: {report['status']}",
                 f"Started: {report['started_at']}", f"Finished: {report['finished_at']}",
                 f"Keyword: {args.keyword}", f"Research ID: {report['research_id']}", '']
        lines += [f"[{x['status']}] {x['name']}: {x['detail']}" for x in report['checks']]
        lines += ['', 'PASS applies to this one run; it does not validate market conclusions.',
                  'Evidence and reports stay on this computer. No credentials are included.']
        (ROOT / 'LIVE_CHECK_RESULT.txt').write_text(redact('\n'.join(lines)), encoding='utf-8-sig')
        print(f"\nRESULT: {report['status']}\nOpen LIVE_CHECK_RESULT.txt in this folder.", flush=True)

    try:
        with TestClient(app) as client:
            def get_json(path, **kwargs):
                response = client.get(path, **kwargs)
                response.raise_for_status()
                return response.json()

            cfg = get_json('/api/config')
            if not check('Local analyst mode', not cfg['public_deployment'], 'This check runs locally only.'):
                report['status'] = 'BLOCKED'; return 2
            if not check('Saved connector settings', bool(cfg['serpapi'] and cfg['llm']),
                         'Requires SERPAPI_API_KEY, LLM_BASE_URL, LLM_MODEL and LLM_API_KEY in .env.'):
                report['status'] = 'BLOCKED'; return 2

            payload = ResearchIn(keyword=args.keyword, markets=['US'], sources=list(dict.fromkeys(args.source)),
                                 days=730, depth='quick')
            calls = estimate_calls(payload, ['US'])
            print(f'Planned SerpAPI search requests: up to {calls}; cached requests may reduce use.', flush=True)
            print('Also runs one short AI probe, evidence analysis, action planning and one Ask request.', flush=True)
            connection = get_json('/api/connections/test')
            serp = connection.get('serpapi') or {}; model = connection.get('llm') or {}
            a = check('SerpAPI account', serp.get('ok') is True, serp.get('message', ''))
            b = check('Actual model generation', model.get('ok') is True and model.get('generation_verified') is True,
                      model.get('message', ''))
            if not (a and b):
                report['status'] = 'BLOCKED'; return 2

            response = client.post('/api/research', json=payload.model_dump())
            response.raise_for_status(); rid = response.json()['id']; report['research_id'] = rid
            print(f'Created NEW research #{rid}. Waiting for real sources and AI analysis...', flush=True)
            deadline = time.monotonic() + args.timeout; previous = None
            while True:
                state = get_json(f'/api/research/{rid}')
                progress = (state['status'], state.get('progress'))
                if progress != previous:
                    print(f"Progress: {state.get('progress', 0)}% ({state['status']})", flush=True)
                    previous = progress
                if state['status'] not in {'queued', 'running'}:
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError('Research did not finish within the configured time limit.')
                time.sleep(2)

            summary = get_json(f'/api/research/{rid}/summary')
            message = state.get('message') or ''
            check('Research completed without warnings', state['status'] == 'completed' and 'warning(s)' not in message, message)
            evidence = get_json(f'/api/research/{rid}/reviews', params={'limit': 5000})
            reviews = evidence['rows']
            check('Complete evidence response', evidence['total'] == len(reviews), f"{len(reviews)} rows")
            source_names = {
                'shopping': 'Google Shopping · US', 'walmart': 'Walmart reviews · US',
                'youtube': 'YouTube comments · discovered via US', 'trends': 'Google Trends · US',
                'community': 'Community discussions · GLOBAL',
            }
            statuses = state.get('source_status') or {}
            for source in payload.sources:
                result = statuses.get(source_names[source]) or {}
                check(f'{source}: source returned data', result.get('status') == 'ok' and (result.get('count') or 0) > 0,
                      f"rows={result.get('count', 0)}; {result.get('message') or result.get('status') or 'no source result'}")

            answer = {}
            if reviews:
                response = client.post(f'/api/research/{rid}/ask', json={
                    'question': 'What should the product team validate first? Cite the supplied evidence and explain its limits.',
                    'language': 'zh',
                })
                response.raise_for_status(); answer = response.json()
            for name, passed in assess_research(summary, reviews, answer).items():
                check(name, passed)
            if answer.get('warning'):
                check('Ask without fallback warning', False, answer['warning'])

            for kind, signature in [('pdf', b'%PDF'), ('csv', b'\xef\xbb\xbf'), ('docx', b'PK')]:
                response = client.get(f'/api/research/{rid}/export/{kind}')
                check(f'{kind.upper()} export', response.status_code == 200 and response.content.startswith(signature))
            report['summary'] = {'consumer_rows': len(reviews), 'product_rows': summary.get('product_count', 0),
                                 'trend_points': summary.get('trend_points', 0), 'analysis_mode': state.get('analysis_mode')}
            report['status'] = 'PASS' if all(x['status'] == 'PASS' for x in report['checks']) else 'PARTIAL'
            print(f'View this run after starting the app: http://127.0.0.1:8000/?research={rid}', flush=True)
            return 0 if report['status'] == 'PASS' else 1
    except KeyboardInterrupt:
        report['status'] = 'INTERRUPTED'; check('Run completed', False, 'Stopped by user.'); return 2
    except Exception as exc:
        report['status'] = 'FAILED'; check('Run completed', False, f'{type(exc).__name__}: {exc}'); return 2
    finally:
        write_result()


if __name__ == '__main__':
    raise SystemExit(run())
