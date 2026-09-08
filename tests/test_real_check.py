"""Acceptance must reject fallback and canned demo output as live AI proof."""
import pytest
from verify_real_research import assess_research


def valid_result():
    summary = {'research': {'status': 'completed', 'decision': {'opportunities': [{
        'name': 'Export reliability', 'insight': 'fixture', 'product_action': 'fixture',
        'gtm_action': 'fixture', 'next_validation': 'fixture',
    }]}}, 'issues': [{'name': 'Export reliability'}]}
    reviews = [{'source': 'Fixture', 'url': 'https://example.com/fixture', 'analysis_mode': 'llm'}]
    return summary, reviews, {'mode': 'llm-grounded', 'answer': 'fixture'}


def test_live_acceptance_accepts_complete_result():
    assert all(assess_research(*valid_result()).values())


@pytest.mark.parametrize('mode', ['local', 'local-fallback'])
def test_live_acceptance_rejects_ask_fallback(mode):
    summary, reviews, answer = valid_result(); answer['mode'] = mode
    assert not assess_research(summary, reviews, answer)['Ask used the real LLM']


def test_live_acceptance_rejects_curated_demo_and_missing_source():
    summary, reviews, answer = valid_result()
    reviews[0]['analysis_mode'] = 'curated-demo'; reviews[0]['url'] = None
    checks = assess_research(summary, reviews, answer)
    assert not checks['All consumer rows analyzed by LLM']
    assert not checks['Every row has a source URL']


def test_live_acceptance_rejects_empty_research_and_unmatched_action():
    summary, _, answer = valid_result()
    summary['research']['decision']['opportunities'][0]['name'] = 'Unsupported topic'
    checks = assess_research(summary, [], answer)
    assert not checks['Collected consumer evidence']
    assert not checks['Grounded action plan returned']
