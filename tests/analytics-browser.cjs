'use strict';

// Real Chrome/Google traffic, not a mocked gtag. Use an isolated, unauthenticated
// context. Candidate mode serves only local site assets at the production origin;
// Google scripts and collect requests are never fulfilled or altered.
// NODE_PATH may point to an existing Playwright installation; no package install.
const {chromium} = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const ROOT = path.resolve(__dirname, '..');
const BASE = 'https://chiba-yu94.github.io/portfolio-site/';
const ID = 'G-74EBNQ9ZC0';
const KEY = 'yutchi-apps:/portfolio-site/:analytics-consent';
const OUT = process.env.GA4_EVIDENCE_DIR;
const MODE = process.env.GA4_TEST_MODE || 'candidate';
const HEADED = process.env.GA4_HEADED === '1';
if (!OUT || !['candidate', 'production', 'disabled'].includes(MODE)) throw new Error('Set GA4_EVIDENCE_DIR and optional GA4_TEST_MODE=candidate|production|disabled');
const report = {mode: MODE, started_at: new Date().toISOString(), source: MODE === 'candidate' ? 'Local generated candidate at production origin; real unmodified Google endpoints' : 'Unmodified deployed production site', checks: [], stages: [], requests: [], failures: []};
const pending = new Set();
const sessions = [];
let browser;

function tracking(url) {
  const u = new URL(url);
  return /(^|\.)(google-analytics\.com|googletagmanager\.com|doubleclick\.net|googleadservices\.com|googlesyndication\.com)$/.test(u.hostname) || (/\.google\.com$/.test(u.hostname) && /collect|conversion|ccm|pagead|ga-audiences/.test(u.pathname));
}
function parsed(request) {
  const u = new URL(request.url());
  const base = Object.fromEntries(u.searchParams);
  return (request.postData() || '').split('\n').map(line => ({...base, ...Object.fromEntries(new URLSearchParams(line))}));
}
function check(name, condition) {
  report.checks.push({name, pass: Boolean(condition)});
  assert.ok(condition, name);
}
function safeParams(params) {
  return Object.fromEntries(Object.entries(params).map(([k, v]) => [k, /^(tid|v|en|dl|dr|dt|gcs|gcd|npa|dma|ep\.link_url|ep\.link_domain|ep\.outbound|ep\.ads_data_redaction|ep\.url_passthrough)$/.test(k) || (k === 'id' && v === ID) ? v : '<redacted>']));
}
function events(session, since = 0, name) {
  return session.requests.slice(since).filter(x => x.collect).flatMap(x => x.params).filter(p => !name || p.en === name);
}
function googleCount(session, since = 0) { return session.requests.slice(since).length; }
async function settle(page, ms = 2200) { await page.waitForTimeout(ms); }
async function waitFor(test, label) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) { if (test()) return; await new Promise(r => setTimeout(r, 100)); }
  throw new Error('Timeout: ' + label);
}
async function snapshot(session, name) {
  await Promise.allSettled([...pending]);
  const cookies = await session.context.cookies();
  const pref = await session.page.evaluate(key => {
    const v = localStorage.getItem(key); return v === null ? null : JSON.parse(v);
  }, KEY);
  const safeCookies = cookies.map(({value, ...rest}) => ({...rest, value: '<redacted>'}));
  const result = {name, google_requests: session.requests.length, cdp_google_requests: session.cdpCount(), event_counts: Object.fromEntries(['page_view', 'click', 'user_engagement'].map(n => [n, events(session, 0, n).length])), cookies: safeCookies, preference: pref};
  report.stages.push(result);
  return {cookies, pref};
}
async function isolated(label) {
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, serviceWorkers: 'block'});
  if (MODE === 'candidate') {
    await context.route(BASE + '**', async route => {
      const u = new URL(route.request().url());
      const relative = decodeURIComponent(u.pathname.slice(new URL(BASE).pathname.length));
      const file = path.resolve(ROOT, relative.endsWith('/') || !relative ? relative + 'index.html' : relative);
      if (!file.startsWith(ROOT + path.sep)) return route.abort();
      try {
        const body = await fs.readFile(file);
        const type = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp'}[path.extname(file)] || 'application/octet-stream';
        await route.fulfill({status: 200, contentType: type, body});
      } catch { await route.abort(); }
    });
  }
  // Store navigation is not a purchase test. Abort Apple document navigation
  // where routing applies; independently classify any Apple session cookies.
  // The trusted click and its real Google collection remain unaffected.
  await context.route('https://apps.apple.com/**', route => route.abort());
  const page = await context.newPage();
  const session = {label, context, page, requests: [], unexpectedExternalRequests: [], cdpRequests: 0};
  session.cdpCount = () => session.cdpRequests;
  sessions.push(session);
  await watch(session, page);
  return session;
}
async function watch(session, page) {
  const cdp = await session.context.newCDPSession(page);
  await cdp.send('Network.enable');
  cdp.on('Network.requestWillBeSent', e => { if (tracking(e.request.url)) session.cdpRequests++; });
  page.on('request', request => {
    const destination = new URL(request.url());
    if (destination.protocol.startsWith('http') && destination.origin !== new URL(BASE).origin && destination.hostname !== 'apps.apple.com' && !tracking(request.url())) session.unexpectedExternalRequests.push(destination.origin + destination.pathname);
    if (!tracking(request.url())) return;
    const u = new URL(request.url());
    const row = {session: session.label, destination: u.origin + u.pathname, collect: /\/(g\/)?collect$/.test(u.pathname), params: parsed(request), method: request.method(), status: null, referrer: null};
    session.requests.push(row);
    const task = request.allHeaders().then(h => { row.referrer = h.referer || ''; });
    pending.add(task); task.finally(() => pending.delete(task));
  });
  page.on('response', response => {
    const req = response.request();
    if (!tracking(req.url())) return;
    const row = session.requests.findLast(x => x.destination === new URL(req.url()).origin + new URL(req.url()).pathname && x.status === null);
    if (row) row.status = response.status();
  });
}
async function goto(session, relative, options = {}) {
  await session.page.goto(BASE + relative, {waitUntil: 'load', ...options});
  await settle(session.page, 1000);
}
async function accept(session) {
  await session.page.locator('[data-analytics-action="accept"]').click();
  await waitFor(() => events(session, 0, 'page_view').length > 0, 'real page_view request');
  await settle(session.page);
}
async function settings(session) { await session.page.locator('[data-analytics-settings]').click(); }
async function reject(session) { await session.page.locator('[data-analytics-action="reject"]').click(); await settle(session.page); }
async function noNewTraffic(session, start, name) {
  await settle(session.page, 4000);
  check(name + ': no new Google traffic', googleCount(session, start) === 0);
}

async function run() {
  await fs.mkdir(path.join(OUT, 'proofs'), {recursive: true});
  browser = await chromium.launch({channel: 'chrome', headless: !HEADED});
  report.browser = browser.version();
  report.headless = !HEADED;
  if (MODE === 'disabled') {
    const s = await isolated('deployed-disabled');
    for (const relative of ['', 'en/', 'en/apps/file-transfer-preflight/', 'privacy-policies/', 'support/']) {
      await goto(s, relative);
      check('deployed config disabled: ' + relative, await s.page.locator('#site-measurement-config').evaluate(e => JSON.parse(e.textContent).enabled) === false);
    }
    await noNewTraffic(s, 0, 'deployed disabled site');
    const state = await snapshot(s, 'deployed-disabled');
    check('disabled site has no cookies or preference', state.cookies.length === 0 && state.pref === null);
    check('disabled state independently verified by CDP', s.cdpCount() === 0);
    report.result = 'PASS deployed disabled state; reactivation not deployed';
    await s.context.close();
    return;
  }
  const a = await isolated('fresh-and-rejected');
  await goto(a, '');
  check('candidate is enabled', await a.page.locator('#site-measurement-config').evaluate(e => JSON.parse(e.textContent).enabled) === true);
  check('fresh consent UI displayed', await a.page.locator('#analytics-consent').isVisible());
  await noNewTraffic(a, 0, 'before consent');
  let state = await snapshot(a, 'before-consent-ja');
  check('fresh has no cookies or preference', state.cookies.length === 0 && state.pref === null);
  await a.page.screenshot({path: path.join(OUT, 'proofs/before-consent-ja.png')});
  await a.page.locator('a.language-switch').click();
  await settle(a.page);
  check('fresh language navigation works', new URL(a.page.url()).pathname === '/portfolio-site/en/');
  await reject(a);
  await a.page.reload(); await settle(a.page);
  await goto(a, 'apps/file-transfer-preflight/');
  await goto(a, 'en/apps/file-transfer-preflight/');
  await noNewTraffic(a, 0, 'rejection across reload and languages');
  state = await snapshot(a, 'rejected-en-product');
  check('rejected preference only necessary fields', state.pref.choice === 'rejected' && Object.keys(state.pref).sort().join(',') === 'choice,expires_at,version');
  check('rejected has no cookies', state.cookies.length === 0);
  check('CDP independently observes zero rejected Google requests', a.cdpCount() === 0);
  await a.context.close();

  const c = await isolated('accepted-and-withdrawn');
  await goto(c, '', {referer: 'https://example.com/verification?qa_marker=public-test'});
  await accept(c);
  check('one initial page_view after accept', events(c, 0, 'page_view').length === 1);
  await settings(c); await c.page.locator('[data-analytics-action="accept"]').click(); await settle(c.page);
  check('repeated accept does not duplicate initialization', events(c, 0, 'page_view').length === 1 && c.requests.filter(x => x.destination === 'https://www.googletagmanager.com/gtag/js').length === 1);
  state = await snapshot(c, 'accepted-ja');
  const firstParty = state.cookies.filter(x => x.domain === 'chiba-yu94.github.io');
  check('only expected analytics cookies created', state.cookies.length === 2 && firstParty.every(x => /^yutchi_portfolio_ga(?:_|$)/.test(x.name)));
  check('cookies host-only scoped Secure Lax and at most 180 days', firstParty.every(x => x.path === '/portfolio-site/' && x.secure && x.sameSite === 'Lax' && x.expires > Date.now()/1000 && x.expires <= Date.now()/1000 + 180*86400 + 10));
  check('no third-party cookies observed', state.cookies.every(x => x.domain === 'chiba-yu94.github.io'));
  const productStart = c.requests.length;
  await goto(c, 'en/apps/file-transfer-preflight/');
  await waitFor(() => events(c, productStart, 'page_view').length === 1, 'product page_view');
  await settle(c.page);
  check('one page_view per English product load', events(c, productStart, 'page_view').length === 1);
  const popupPromise = c.context.waitForEvent('page');
  await c.page.getByRole('link', {name: 'View on the App Store ↗', exact: true}).click({modifiers: ['Meta']});
  const popup = await popupPromise; await popup.close();
  await waitFor(() => events(c, productStart, 'click').length === 1, 'App Store click');
  await settle(c.page, 3500);
  check('one App Store click without duplicates', events(c, productStart, 'click').length === 1);
  const click = events(c, productStart, 'click')[0];
  check('approved click fields received in actual payload', click['ep.link_url'] === 'https://apps.apple.com/us/app/file-transfer-preflight/id6820943200' && click['ep.link_domain'] === 'apps.apple.com' && click['ep.outbound'] === 'true');
  await snapshot(c, 'accepted-en-product-and-click');
  await c.page.screenshot({path: path.join(OUT, 'proofs/accepted-en-product.png')});
  const withdrawalStart = c.requests.length;
  await settings(c); await reject(c);
  await noNewTraffic(c, withdrawalStart, 'immediate withdrawal');
  state = await snapshot(c, 'withdrawn-en-product');
  check('withdrawal preference rejected and site cookies removed', state.pref.choice === 'rejected' && state.cookies.filter(x => x.domain === 'chiba-yu94.github.io').length === 0);
  await goto(c, ''); await goto(c, 'en/'); await c.page.reload();
  await noNewTraffic(c, withdrawalStart, 'withdrawal navigation and reload');
  await snapshot(c, 'withdrawn-returned');

  const h = await isolated('fragments-and-queries');
  for (const suffix of ['?utm_source=verification', '?qa_marker=public-test', '#unlisted-verification']) {
    await goto(h, suffix);
    await noNewTraffic(h, 0, 'fresh filtered ' + suffix);
    check('filtered URL does not expose consent controls: ' + suffix, await h.page.locator('#analytics-consent').count() === 0);
  }
  state = await snapshot(h, 'filtered-fresh'); check('filtered fresh cookies absent', state.cookies.length === 0);
  // A hash-only transition out of an initially blocked URL deliberately does
  // not initialize the runtime; test an actual page load with the allowed hash.
  await goto(h, '#main'); await h.page.reload(); await settle(h.page); await accept(h);
  check('allowed fragment is removed from collected URL', events(h, 0, 'page_view')[0].dl === BASE);
  let filteredStart = h.requests.length;
  await goto(h, '?utm_source=verification'); await noNewTraffic(h, filteredStart, 'accepted preference on UTM URL');
  await goto(h, '#unlisted-verification'); await noNewTraffic(h, filteredStart, 'accepted preference on unknown fragment');
  await snapshot(h, 'filtered-with-existing-consent');

  const t = await isolated('cross-tab');
  await goto(t, 'en/'); await accept(t);
  const second = await t.context.newPage(); await watch(t, second);
  await second.goto(BASE, {waitUntil: 'load'}); await settle(second);
  await waitFor(() => events(t, 0, 'page_view').length === 2, 'two accepted tabs');
  const crossStart = t.requests.length;
  await second.locator('[data-analytics-settings]').click();
  await second.locator('[data-analytics-action="reject"]').click();
  await settle(t.page, 4500);
  await t.page.reload(); await second.reload();
  await noNewTraffic(t, crossStart, 'cross-tab withdrawal');
  state = await snapshot(t, 'cross-tab-withdrawn');
  check('cross-tab withdrawal removes site cookies', state.cookies.length === 0 && state.pref.choice === 'rejected');

  await Promise.allSettled([...pending]);
  check('no unrecognized external destinations', sessions.every(s => s.unexpectedExternalRequests.length === 0));
  for (const s of [c, h, t]) {
    for (const req of s.requests) {
      check(s.label + ': approved endpoint', req.destination === 'https://www.googletagmanager.com/gtag/js' || /^https:\/\/([a-z0-9-]+\.)*google-analytics\.com\/g\/collect$/.test(req.destination));
      if (req.collect) {
        check(s.label + ': HTTP referrer origin only', req.referrer === 'https://chiba-yu94.github.io/');
        for (const data of req.params) {
          check(s.label + ': correct real ID and fixed public page URL', data.tid === ID && data.dl?.startsWith(BASE) && !new URL(data.dl).search && !new URL(data.dl).hash);
          check(s.label + ': approved referrer field', !data.dr || ['https://example.com', 'https://chiba-yu94.github.io'].includes(data.dr));
          check(s.label + ': no user identifiers or private test parameters', !Object.keys(data).some(k => /^(uid|user_id|up\.|upn\.)/.test(k)) && !/qa_marker|utm_source|unlisted-verification|yutchi\.apps(%40|@)gmail/i.test(JSON.stringify(data)));
          check(s.label + ': advertising consent denied', data.gcs === 'G101' && data.npa === '1');
        }
      } else {
        check(s.label + ': correct loader ID', req.params[0].id === ID);
        check(s.label + ': loader sends no HTTP referrer', req.referrer === '');
      }
    }
  }
  check('real collection HTTP success observed', sessions.flatMap(s => s.requests).filter(x => x.collect).every(x => x.status === 204 || x.status === 200));
  report.result = MODE === 'candidate' ? 'PASS candidate; production acceptance still requires approved deployment' : 'PASS production real-browser checks; confirm GA4 Realtime separately';
  await c.context.close(); await h.context.close(); await t.context.close();
}
run().catch(e => { report.result = 'HOLD'; report.failures.push(e.message); process.exitCode = 1; }).finally(async () => {
  if (browser) await browser.close();
  await Promise.allSettled([...pending]);
  report.requests = sessions.flatMap(s => s.requests.map(req => ({...req, params: req.params.map(safeParams)})));
  report.unexpected_external_destinations = sessions.flatMap(s => s.unexpectedExternalRequests);
  report.finished_at = new Date().toISOString();
  await fs.mkdir(OUT, {recursive: true});
  await fs.writeFile(path.join(OUT, 'browser-evidence.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({result: report.result, checks: report.checks.length, failures: report.failures, evidence: path.join(OUT, 'browser-evidence.json')}));
});
