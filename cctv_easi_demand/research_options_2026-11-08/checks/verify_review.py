"""Verify the CCTV proposal routes and browser review without touching real notes."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PID = 'cctv-easi-design'
PREFIX = '/static/review'
SECTIONS = json.loads((ROOT / 'design_manifest.json').read_text())['canonical_sections']


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value and value.startswith('/'):
                self.urls.add(value)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--web', type=Path, default=Path('/root/data/Paper/央视数据/paper10-warning-consumption/web'))
    parser.add_argument('--base', default='http://127.0.0.1:8891')
    parser.add_argument('--chrome', default='/usr/bin/google-chrome')
    args = parser.parse_args()
    out = ROOT / 'checks'
    sys.path.insert(0, str(args.web))
    from app import app
    from review import evidence, projects

    registry = projects()
    assert len({p['id'] for p in registry}) == len(registry)
    assert {'food-easi', 'weather', PID}.issubset({p['id'] for p in registry})
    allowed = evidence(PID)
    expected = {f'research_options_2026-11-08/{s}.md' for s in SECTIONS}
    expected.add('research_options_2026-11-08/design_manifest.json')
    assert set(allowed) == expected
    assert all(p.resolve().is_relative_to(ROOT) for p in allowed.values())
    real_db = args.web / 'review_data' / 'reviews.sqlite3'
    before = digest(real_db)
    with tempfile.TemporaryDirectory(prefix='cctv-review-test-') as tmp:
        app.config.update(TESTING=True, REVIEW_DB=str(Path(tmp) / 'notes.sqlite3'))
        client = app.test_client()
        for slug in SECTIONS:
            response = client.get(f'/papers/{PID}/{slug}')
            assert response.status_code == 200
            assert len(response.data) > 5000 and b'MATHPH' not in response.data
        for key in expected:
            assert client.get(f'/papers/{PID}/files/{key}').status_code == 200
        assert client.get(f'/papers/{PID}/files/data/analysis_monthly.dta').status_code == 404
        assert client.get(f'/papers/{PID}/unknown').status_code == 404
        endpoint = f'/api/reviews/{PID}/heterogeneity'
        assert client.post(endpoint, json={'status': 'revising', 'note': 'isolated test'}).status_code == 200
        assert client.get(endpoint).json['note'] == 'isolated test'
        assert client.get(f'/api/reviews/{PID}/sensitivity').json['note'] == ''
        assert client.get('/api/reviews/food-easi/overview').json['note'] == ''
        assert client.post(endpoint, json={'status': 'invalid', 'note': 'x'}).status_code == 400
        assert client.post(endpoint, json={'status': 'pending', 'note': 'x' * 20001}).status_code == 400
        assert client.post(endpoint, json={'status': 'pending', 'note': 'x'}, headers={'Origin': 'https://foreign.example'}).status_code == 403
    assert digest(real_db) == before

    urls = {PREFIX + '/index.html'}
    for slug in SECTIONS:
        url = f'{PREFIX}/papers/{PID}/{slug}.html'
        with urlopen(args.base + url) as response:
            assert response.status == 200
            body = response.read().decode()
        assert 'window.REVIEW_PROJECTS=' in body
        links = Links()
        links.feed(body)
        urls.add(url)
        urls.update(u for u in links.urls if not u.startswith('/api/'))
    for path in sorted(urls):
        with urlopen(args.base + path) as response:
            assert response.status == 200, path

    report = {
        'date': '2026-11-08', 'base': args.base, 'project': PID,
        'econometric_models_run': False, 'sensitivity_search_run': False,
        'sections': len(SECTIONS), 'whitelisted_downloads': len(expected),
        'http_resources_checked': len(urls), 'backend_note_validation': 'passed_using_temporary_database',
        'real_review_database_unchanged_during_test': True,
        'browser_note_storage': 'current-browser-localStorage', 'screens': [],
    }
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chrome, headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.base + '/', wait_until='networkidle')
        page.wait_for_url('**/static/review/index.html')
        assert page.locator(f'a[href="{PREFIX}/papers/{PID}/overview.html"]').count() >= 1
        page.locator('#project-search').fill('央视食品需求')
        assert page.locator('.project-card:visible').count() == 1
        page.screenshot(path=str(out / 'portal_desktop.png'), full_page=True)
        page.locator('.project-card:visible h3 a').click()
        page.wait_for_selector('#review-save:not([disabled])')
        page.screenshot(path=str(out / 'overview_desktop.png'), full_page=True)

        old_key = 'manuscript-review-local:v1:food-easi:overview'
        sentinel = json.dumps({'status': 'pending', 'note': 'old-project-sentinel', 'updated_at': None})
        page.evaluate('([k,v])=>localStorage.setItem(k,v)', [old_key, sentinel])
        page.goto(args.base + f'{PREFIX}/papers/{PID}/heterogeneity.html', wait_until='networkidle')
        page.wait_for_selector('#review-save:not([disabled])')
        page.wait_for_function('document.querySelectorAll("mjx-container").length >= 3')
        assert page.locator('mjx-merror').count() == 0
        page.screenshot(path=str(out / 'heterogeneity_desktop.png'), full_page=True)
        page.locator('#review-status').select_option('revising')
        page.locator('#review-note').fill('QA: independent proposal review; remove after verification.')
        page.locator('#review-save').click()
        page.wait_for_function('document.querySelector("#review-feedback").textContent.includes("已保存")')
        page.reload(wait_until='networkidle')
        page.wait_for_selector('#review-save:not([disabled])')
        assert page.locator('#review-note').input_value().startswith('QA:')
        assert page.locator('#review-status').input_value() == 'revising'
        assert page.evaluate('(k)=>localStorage.getItem(k)', old_key) == sentinel
        with page.expect_download() as event:
            page.locator('.export-link').click()
        download = event.value
        assert download.suggested_filename == PID + '-review-browser.md'
        exported = Path(download.path()).read_text()
        assert 'QA: independent' in exported and 'old-project-sentinel' not in exported
        page.goto(args.base + f'{PREFIX}/papers/{PID}/sensitivity.html', wait_until='networkidle')
        page.wait_for_selector('#review-save:not([disabled])')
        assert page.locator('#review-note').input_value() == ''
        page.wait_for_function('document.querySelectorAll("mjx-container").length >= 3')
        assert page.locator('mjx-merror').count() == 0
        page.screenshot(path=str(out / 'sensitivity_desktop.png'), full_page=True)
        report['browser_math'] = 'passed_no_mathjax_errors'
        report['browser_save_reload_export_isolation'] = 'passed_in_fresh_context'
        page.evaluate('()=>Object.keys(localStorage).filter(k=>k.startsWith("manuscript-review-local:v1:")).forEach(k=>localStorage.removeItem(k))')

        for width, height in [(1440, 1000), (390, 844), (320, 740)]:
            page.set_viewport_size({'width': width, 'height': height})
            for slug in SECTIONS:
                page.goto(args.base + f'{PREFIX}/papers/{PID}/{slug}.html', wait_until='networkidle')
                page.wait_for_selector('#review-save:not([disabled])')
                if slug in {'heterogeneity', 'inference', 'sensitivity'}:
                    page.wait_for_function('document.querySelectorAll("mjx-container").length > 0')
                dimensions = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                assert dimensions['scroll'] <= width + 1, (slug, width, dimensions)
                assert page.locator('mjx-merror').count() == 0, (slug, width)
                report['screens'].append({'section': slug, 'width': width, 'horizontal_overflow': False})
                if width == 390 and slug in {'overview', 'heterogeneity', 'sensitivity', 'sources'}:
                    page.screenshot(path=str(out / f'{slug}_mobile.png'), full_page=True)
        page.evaluate('()=>Object.keys(localStorage).filter(k=>k.startsWith("manuscript-review-local:v1:")).forEach(k=>localStorage.removeItem(k))')
        context.close()
        browser.close()
    assert not errors, errors
    report['javascript_exceptions'] = errors
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
