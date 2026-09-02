from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


ALIASES = {
    'source': ['source', 'platform', 'channel', 'origin'],
    'market': ['market', 'country', 'country_code', 'region', 'locale'],
    'product_title': ['product_title', 'product', 'product_name', 'item', 'item_name'],
    'product_external_id': ['product_external_id', 'product_id', 'item_id', 'sku', 'asin'],
    'review_external_id': ['review_external_id', 'review_id', 'comment_id', 'id', 'external_id'],
    'title': ['title', 'review_title', 'headline', 'subject'],
    'text': ['text', 'review', 'comment', 'content', 'body', 'message', 'feedback', 'review_text'],
    'rating': ['rating', 'stars', 'star_rating', 'score'],
    'author': ['author', 'user', 'username', 'reviewer', 'nickname'],
    'review_date': ['review_date', 'date', 'published_at', 'created_at', 'timestamp', 'time'],
    'url': ['url', 'link', 'permalink', 'source_url'],
    'helpful': ['helpful', 'likes', 'like_count', 'helpful_count', 'upvotes'],
}


def _norm_key(value: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '_' for ch in str(value)).strip('_')


def _pick(row: dict, field: str):
    normalized = {_norm_key(k): v for k, v in row.items()}
    for alias in ALIASES[field]:
        key = _norm_key(alias)
        if key in normalized and normalized[key] not in (None, ''):
            return normalized[key]
    return None


def _float(v):
    if v in (None, ''):
        return None
    try:
        s = str(v).strip().replace(',', '')
        return float(s)
    except Exception:
        return None


def _int(v):
    if v in (None, ''):
        return None
    try:
        return int(float(str(v).strip().replace(',', '')))
    except Exception:
        return None


def _rows_from_content(content: bytes, filename: str) -> list[dict]:
    suffix = Path(filename or '').suffix.lower()
    text = content.decode('utf-8-sig', errors='replace')
    if suffix == '.json' or text.lstrip().startswith(('[', '{')):
        data = json.loads(text)
        if isinstance(data, dict):
            for key in ('rows', 'data', 'items', 'reviews', 'comments'):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            raise ValueError('JSON must be a list of evidence rows, or contain rows/data/items/reviews/comments as a list.')
        return [x for x in data if isinstance(x, dict)]
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
    except Exception:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def parse_evidence_file(content: bytes, filename: str, max_rows: int = 1000) -> tuple[list[dict], dict]:
    raw_rows = _rows_from_content(content, filename)
    if not raw_rows:
        return [], {'raw_rows': 0, 'accepted': 0, 'skipped_missing_text': 0, 'truncated': False}
    rows = []
    skipped = 0
    truncated = len(raw_rows) > max_rows
    for idx, raw in enumerate(raw_rows[:max_rows]):
        text = _pick(raw, 'text')
        if text is None or not str(text).strip():
            skipped += 1
            continue
        source = str(_pick(raw, 'source') or 'Imported Evidence').strip()
        market = str(_pick(raw, 'market') or 'GLOBAL').strip().upper()
        title = _pick(raw, 'title')
        product_title = _pick(raw, 'product_title')
        external = _pick(raw, 'review_external_id')
        if not external:
            digest = hashlib.sha1(f'{source}|{market}|{title}|{text}'.encode('utf-8', errors='ignore')).hexdigest()[:16]
            external = f'import:{digest}'
        rows.append({
            'source': source,
            'market': market,
            'product_external_id': str(_pick(raw, 'product_external_id') or '') or None,
            'product_title': str(product_title).strip() if product_title not in (None, '') else None,
            'review_external_id': str(external),
            'title': str(title).strip() if title not in (None, '') else None,
            'text': ' '.join(str(text).split()),
            'rating': _float(_pick(raw, 'rating')),
            'author': str(_pick(raw, 'author')).strip() if _pick(raw, 'author') not in (None, '') else None,
            'review_date': str(_pick(raw, 'review_date')).strip() if _pick(raw, 'review_date') not in (None, '') else None,
            'url': str(_pick(raw, 'url')).strip() if _pick(raw, 'url') not in (None, '') else None,
            'helpful': _int(_pick(raw, 'helpful')),
        })
    return rows, {
        'raw_rows': len(raw_rows),
        'accepted': len(rows),
        'skipped_missing_text': skipped,
        'truncated': truncated,
        'max_rows': max_rows,
    }
