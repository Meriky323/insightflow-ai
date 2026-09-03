from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

GENERIC_ISSUES = {
    'Performance / effectiveness': [r'not work', r'doesn.?t work', r'poor performance', r'slow', r'weak', r'ineffective', r'performance'],
    'Reliability / durability': [r'broken', r'broke', r'fail', r'died', r'loose', r'crack', r'durab', r'reliable', r'quality'],
    'Ease of use': [r'difficult', r'hard to use', r'confusing', r'easy to use', r'setup', r'install', r'convenient'],
    'Compatibility / fit': [r'compatib', r'doesn.?t fit', r'fit', r'connect', r'pair', r'supports?'],
    'Size / ergonomics': [r'heavy', r'bulky', r'thick', r'large', r'small', r'compact', r'lightweight', r'comfortable'],
    'Price / value': [r'expensive', r'overpriced', r'price', r'value', r'worth', r'cheap'],
    'Design / appearance': [r'design', r'looks?', r'finish', r'color', r'aesthetic', r'premium'],
    'Safety / comfort': [r'unsafe', r'safety', r'hot', r'overheat', r'burn', r'irritat', r'uncomfortable'],
    'Service / delivery': [r'refund', r'support', r'customer service', r'shipping', r'delivery', r'warranty', r'replacement'],
}
GENERIC_DRIVERS = {
    'Performance': [r'works? great', r'fast', r'powerful', r'effective', r'performance'],
    'Convenience': [r'convenient', r'easy', r'simple', r'quick setup', r'portable'],
    'Quality': [r'premium', r'well built', r'solid', r'durable', r'quality'],
    'Value': [r'good value', r'worth', r'affordable', r'great price'],
    'Design': [r'looks good', r'design', r'beautiful', r'sleek', r'compact'],
}
NEG = {'bad','worst','terrible','awful','hate','disappointed','useless','poor','problem','issue','slow','weak','broken','expensive','return','refund','annoying','fail','failed'}
POS = {'great','good','excellent','love','amazing','perfect','useful','convenient','fast','strong','recommend','happy','compact','premium','easy','reliable'}


def _contains(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.I) for p in patterns)


def _topics(row: dict) -> list[str]:
    raw = row.get('topics_json')
    if raw:
        try:
            xs = json.loads(raw) if isinstance(raw, str) else list(raw)
            return [str(x).strip() for x in xs if str(x).strip()]
        except Exception:
            pass
    return [row['issue']] if row.get('issue') else []


def sentiment(text: str, rating=None) -> str:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    score = sum(w in POS for w in words) - sum(w in NEG for w in words)
    if score >= 2:
        return 'positive'
    if score <= -2:
        return 'negative'
    if rating is not None:
        try:
            r = float(rating)
            if r <= 2:
                return 'negative'
            if r >= 4:
                return 'positive'
        except Exception:
            pass
    return 'neutral'


def _best_label(text: str, taxonomy: dict[str, list[str]]) -> str | None:
    scores = []
    for name, pats in taxonomy.items():
        score = sum(bool(re.search(p, text, re.I)) for p in pats)
        if score:
            scores.append((score, name))
    return max(scores)[1] if scores else None


def purchase_impact(text: str) -> str | None:
    t = text.lower()
    if re.search(r'\b(return|returned|returning|refund|refunded)\b', t):
        return 'Return / refund'
    if re.search(r'\b(switch|switched|another brand|different brand)\b', t):
        return 'Switch brand'
    if re.search(r'\b(wouldn.?t buy|would not buy|won.?t buy|avoid|dealbreaker|deal breaker|not purchase)\b', t):
        return 'Blocked purchase'
    if re.search(r'\b(recommend|recommended|would buy again|buy again|repurchase)\b', t):
        return 'Recommend / repeat'
    return None


def scenario(text: str) -> str | None:
    t = text.lower()
    patterns = [
        ('Travel / on the go', r'travel|flight|airport|trip|airplane|on the go'),
        ('Daily routine', r'commut|every day|daily|routine'),
        ('Work / office', r'office|meeting|workday|work day|desk'),
        ('Outdoor', r'camp|outdoor|festival|hiking|beach'),
        ('Home', r'at home|home use|kitchen|bedroom|living room'),
        ('Professional / creator', r'creator|shoot|filming|studio|professional|client'),
        ('Emergency / backup', r'emergency|backup|power outage'),
    ]
    for name, pat in patterns:
        if re.search(pat, t):
            return name
    return None


def annotate_fallback(row: dict) -> dict:
    text = (row.get('title') or '') + ' ' + (row.get('text') or '')
    sent = sentiment(text, row.get('rating'))
    issue = _best_label(text, GENERIC_ISSUES)
    driver = _best_label(text, GENERIC_DRIVERS) if sent == 'positive' else None
    row['sentiment'] = sent
    row['issue'] = issue
    row['topics_json'] = json.dumps([issue] if issue else [], ensure_ascii=False)
    row['driver'] = driver
    row['barrier'] = issue if sent == 'negative' else None
    row['purchase_impact'] = purchase_impact(text)
    row['scenario'] = scenario(text)
    row['competitor_mentions_json'] = '[]'
    row['analysis_mode'] = 'local-fallback'
    return row


def apply_llm_extraction(row: dict, extracted: dict) -> dict:
    topics = [str(x).strip() for x in extracted.get('topics') or [] if str(x).strip()][:3]
    row['sentiment'] = extracted.get('sentiment') or 'neutral'
    row['issue'] = extracted.get('issue') or (topics[0] if topics else None)
    row['topics_json'] = json.dumps(topics, ensure_ascii=False)
    row['driver'] = extracted.get('driver')
    row['barrier'] = extracted.get('barrier')
    row['purchase_impact'] = extracted.get('purchase_impact')
    row['scenario'] = extracted.get('scenario')
    row['competitor_mentions_json'] = json.dumps(extracted.get('competitor_mentions') or [], ensure_ascii=False)
    row['analysis_mode'] = 'llm'
    return row




def _decision_impact(value: str | None) -> bool:
    """Count only explicit decision-changing outcomes, not generic criteria or comparison talk."""
    if not value:
        return False
    t=str(value).lower()
    return any(k in t for k in ('return','refund','switch','blocked','avoid','preference shift','abandon','cancel','reject'))

def _confidence_label(count: int, source_count: int) -> str:
    if count >= 30 and source_count >= 2:
        return 'High'
    if count >= 10 or (count >= 6 and source_count >= 2):
        return 'Medium'
    return 'Low'


def _overall_confidence(review_count: int, source_count: int) -> dict:
    sample_score = min(1.0, review_count / 150)
    source_score = min(1.0, source_count / 3)
    score = round(100 * (0.65 * sample_score + 0.35 * source_score))
    label = 'High' if score >= 75 else 'Medium' if score >= 45 else 'Low'
    return {'label': label, 'score': score, 'review_count': review_count, 'source_count': source_count}


def _trend_summary(trends: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for r in trends:
        if r.get('value') is not None:
            grouped[r.get('market') or 'UNKNOWN'].append(r)
    out = []
    for market, rows in grouped.items():
        rows = sorted(rows, key=lambda x: x.get('timestamp') or 0)
        vals = [float(x.get('value') or 0) for x in rows]
        if len(vals) < 4:
            continue
        k = max(1, len(vals) // 4)
        start = sum(vals[:k]) / k
        end = sum(vals[-k:]) / k
        growth = None if start == 0 else round((end - start) * 100 / start, 1)
        out.append({
            'market': market,
            'start_index_avg': round(start, 1),
            'end_index_avg': round(end, 1),
            'relative_growth_pct': growth,
            'note': 'Within-market normalized Google Trends index; do not compare absolute index levels across separately requested markets.',
        })
    return out


def _coverage(products: list[dict], reviews: list[dict], trends: list[dict], requested_markets: list[str]) -> dict:
    rows: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for p in products:
        rows[(p.get('source') or 'Unknown', 'products')][p.get('market') or 'UNKNOWN'] += 1
    for r in reviews:
        rows[(r.get('source') or 'Unknown', 'consumer voice')][r.get('market') or 'UNKNOWN'] += 1
    for t in trends:
        rows[('Google Trends', 'search trend')][t.get('market') or 'UNKNOWN'] += 1

    matrix = []
    for (source, kind), counts in sorted(rows.items()):
        comparable = bool(requested_markets) and all(counts.get(m, 0) > 0 for m in requested_markets)
        matrix.append({
            'source': source,
            'kind': kind,
            'counts': dict(counts),
            'comparable_across_requested_markets': comparable,
        })
    return {'markets': requested_markets, 'rows': matrix}


def _market_comparison(reviews: list[dict], requested_markets: list[str]) -> dict:
    if len(requested_markets) < 2:
        return {'available': False, 'reason': 'Select at least two markets.'}
    source_by_market = {m: set() for m in requested_markets}
    for r in reviews:
        market = r.get('market')
        if market in source_by_market:
            source_by_market[market].add(r.get('source'))
    common = set.intersection(*(source_by_market[m] for m in requested_markets)) if requested_markets else set()
    common.discard(None)
    if not common:
        return {
            'available': False,
            'reason': 'No consumer-voice source currently covers every requested market with the same measurement basis.',
            'common_sources': [],
        }
    result = {}
    for market in requested_markets:
        subset = [r for r in reviews if r.get('market') == market and r.get('source') in common]
        topics = Counter(t for r in subset for t in _topics(r))
        result[market] = {
            'sample': len(subset),
            'top_topics': [{'name': k, 'count': v, 'share': round(v * 100 / max(1, len(subset)), 1)} for k, v in topics.most_common(8)],
        }
    return {'available': True, 'common_sources': sorted(common), 'markets': result}



def _competitor_benchmark(products: list[dict], reviews: list[dict]) -> list[dict]:
    """Link consumer evidence to products via connector IDs first, then conservative brand/entity mentions.

    Cross-source mention linkage is intentionally brand-level, not market-level. GLOBAL consumer evidence must
    not be reinterpreted as country-specific preference just because a product row is sold in that market.
    """
    by_key = defaultdict(list)
    mention_rows = defaultdict(list)
    for r in reviews:
        pid = r.get('product_external_id')
        if pid:
            by_key[(r.get('source'), str(pid))].append(r)
        try:
            mentions = json.loads(r.get('competitor_mentions_json') or '[]')
        except Exception:
            mentions = []
        for m in mentions if isinstance(mentions, list) else []:
            key = re.sub(r'[^a-z0-9]+', '', str(m).lower())
            if len(key) >= 3:
                mention_rows[key].append(r)

    rows = []
    for p in products:
        pid = p.get('external_id')
        linked = list(by_key.get((p.get('source'), str(pid)), [])) if pid is not None else []
        title_key = re.sub(r'[^a-z0-9]+', '', (p.get('title') or '').lower())
        seller_key = re.sub(r'[^a-z0-9]+', '', (p.get('seller') or '').lower())
        # Conservative entity resolution: only link an explicit brand/name mention if it appears in title/seller.
        for mention, rs in mention_rows.items():
            if mention in title_key or (seller_key and mention in seller_key):
                for r in rs:
                    if r not in linked:
                        linked.append(r)
        negative = sum(1 for r in linked if r.get('sentiment') == 'negative')
        topics = Counter(t for r in linked for t in _topics(r))
        drivers = Counter(r.get('driver') for r in linked if r.get('driver'))
        barriers = Counter(r.get('barrier') for r in linked if r.get('barrier'))
        global_n = sum(1 for r in linked if r.get('market') == 'GLOBAL')
        rows.append({
            'source': p.get('source'),
            'market': p.get('market'),
            'external_id': p.get('external_id'),
            'title': p.get('title'),
            'url': p.get('url'),
            'price': p.get('price'),
            'currency': p.get('currency'),
            'rating': p.get('rating'),
            'review_count': p.get('review_count'),
            'seller': p.get('seller'),
            'evidence_sample': len(linked),
            'global_evidence_sample': global_n,
            'negative_share': round(negative * 100 / max(1, len(linked)), 1) if linked else None,
            'top_topics': [{'name': k, 'count': v} for k, v in topics.most_common(3)],
            'top_drivers': [{'name': k, 'count': v} for k, v in drivers.most_common(2)],
            'top_barriers': [{'name': k, 'count': v} for k, v in barriers.most_common(2)],
            'consumer_voice_coverage': bool(linked),
            'linkage_note': 'Brand/entity mention linkage; GLOBAL evidence is not market-specific.' if linked and global_n else 'Direct product evidence linkage.' if linked else None,
        })
    rows.sort(key=lambda x: (x['consumer_voice_coverage'], x['evidence_sample'], x.get('review_count') or 0), reverse=True)
    return rows[:20]


def _research_quality(reviews: list[dict], products: list[dict], trends: list[dict], requested_markets: list[str]) -> dict:
    n=len(reviews); sources={r.get('source') for r in reviews if r.get('source')}
    dated=sum(1 for r in reviews if r.get('window_status')=='in_window')
    unknown=sum(1 for r in reviews if r.get('window_status')=='unknown')
    ai=sum(1 for r in reviews if r.get('analysis_mode')=='llm')
    comparable=_market_comparison(reviews, requested_markets).get('available',False)
    sample=min(1,n/120); diversity=min(1,len(sources)/4); freshness=(dated/max(1,n)) if n else 0; structured=(ai/max(1,n)) if n else 0
    score=round(100*(0.45*sample+0.30*diversity+0.15*freshness+0.10*structured))
    label='Strong' if score>=72 and n>=50 and len(sources)>=3 else 'Directional' if score>=38 and n>=12 else 'Thin'
    warnings=[]
    if n<12:warnings.append('Consumer-voice sample is small; treat outputs as exploratory signals.')
    if len(sources)<2:warnings.append('Consumer voice is concentrated in one source; add an independent source before strong decisions.')
    if n and unknown/n>0.35:warnings.append('Many evidence rows have unverified dates, weakening time-window claims.')
    if len(requested_markets)>=2 and not comparable:warnings.append('Cross-market consumer preference comparison is blocked because equivalent voice coverage is missing.')
    if not trends:warnings.append('No search-trend signal is available for this research.')
    if not products:warnings.append('No product/retail benchmark signal is available for this research.')
    return {
        'label':label,'score':score,'consumer_voice_rows':n,'source_count':len(sources),
        'verified_date_share':round(100*dated/max(1,n),1) if n else 0,'unverified_date_rows':unknown,
        'llm_structured_share':round(100*structured,1) if n else 0,'cross_market_voice_comparable':comparable,
        'warnings':warnings,
        'note':'Quality score is an internal research-readiness heuristic, not a statistical confidence interval.'
    }


def summarize(products: list[dict], reviews: list[dict], trends: list[dict], requested_markets: list[str] | None = None) -> dict:
    requested_markets = requested_markets or sorted({x.get('market') for x in products + trends if x.get('market') and x.get('market') != 'GLOBAL'})
    n = len(reviews)
    sent = Counter(r.get('sentiment') or 'unknown' for r in reviews)
    topic_counts = Counter(t for r in reviews for t in _topics(r))
    drivers = Counter(r.get('driver') for r in reviews if r.get('driver'))
    impacts = Counter(r.get('purchase_impact') for r in reviews if r.get('purchase_impact'))
    sources = Counter(r.get('source') for r in reviews)
    markets = Counter(r.get('market') for r in reviews)
    analysis_modes = Counter(r.get('analysis_mode') or 'unknown' for r in reviews)
    window_unknown_count = sum(1 for r in reviews if r.get('window_status') == 'unknown')

    issue_details = []
    for name, count in topic_counts.most_common():
        topic_rows = [r for r in reviews if name in _topics(r)]
        impacted = sum(1 for r in topic_rows if _decision_impact(r.get('purchase_impact')))
        ratings = [float(r['rating']) for r in topic_rows if r.get('rating') is not None]
        src_count = len({r.get('source') for r in topic_rows if r.get('source')})
        issue_details.append({
            'name': name,
            'count': count,
            'share': round(count * 100 / max(1, n), 1),
            'purchase_impact_rate': round(impacted * 100 / max(1, len(topic_rows)), 1),
            'avg_rating': round(sum(ratings) / len(ratings), 2) if ratings else None,
            'source_count': src_count,
            'confidence': _confidence_label(count, src_count),
        })

    prod_text = ' '.join((p.get('title', '') + ' ' + (p.get('raw_json') or '')) for p in products).lower()
    max_issue = max([x['count'] for x in issue_details], default=1)
    max_sources = max(1, len(sources))
    opportunities = []
    for x in issue_details[:12]:
        tokens = [w.lower() for w in re.findall(r'[A-Za-z0-9]+', x['name']) if len(w) >= 4]
        coverage = (sum(1 for t in tokens if t in prod_text) / len(tokens)) if tokens else 0.5
        volume = x['count'] / max_issue
        impact = x['purchase_impact_rate'] / 100
        diversity = min(1.0, x['source_count'] / max_sources)
        # Priority is driven by observed evidence, not by a weak text-match claim of competitor whitespace.
        confidence_factor={'High':1.0,'Medium':0.65,'Low':0.35}.get(x.get('confidence'),0.35)
        score = round(100 * (0.42 * volume + 0.30 * impact + 0.18 * diversity + 0.10 * confidence_factor))
        opportunities.append({
            **x,
            'benchmark_coverage': round(coverage * 100),
            'opportunity_score': score,
            'label': 'Validation hypothesis',
            'score_note':'Ranks validation priority from observed volume, decision impact, source diversity and evidence confidence; not market size or whitespace proof.',
        })
    opportunities.sort(key=lambda z: z['opportunity_score'], reverse=True)

    return {
        'review_count': n,
        'product_count': len(products),
        'trend_points': len(trends),
        'sentiment': dict(sent),
        'issues': issue_details,
        'drivers': [{'name': k, 'count': v, 'share': round(v * 100 / max(1, n), 1)} for k, v in drivers.most_common()],
        'impacts': dict(impacts),
        'sources': dict(sources),
        'markets': dict(markets),
        'analysis_modes': dict(analysis_modes),
        'window_unknown_count': window_unknown_count,
        'evidence_confidence': _overall_confidence(n, len(sources)),
        'research_quality': _research_quality(reviews, products, trends, requested_markets),
        'source_coverage': _coverage(products, reviews, trends, requested_markets),
        'market_comparison': _market_comparison(reviews, requested_markets),
        'trend_summary': _trend_summary(trends),
        'competitor_benchmark': _competitor_benchmark(products, reviews),
        'opportunities': opportunities,
        'top_products': products[:20],
        'trends': trends,
    }
