'use strict';

// Offline, mock-only harness: this ID is a test fixture, never a deployed Google ID.
// The VM cannot fetch gtag.js; script insertion and every other network API are recorded.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'analytics.js'), 'utf8');
const ID = 'G-TESTONLY01';
const KEY = 'yutchi-apps:/portfolio-site/:analytics-consent';
const ORIGIN = 'https://chiba-yu94.github.io';
const CANONICAL = `${ORIGIN}/portfolio-site/apps/csv-preflight/`;
const STORE = 'https://apps.apple.com/us/app/csv-preflight/id6820027859';
const preference = (choice, extra = {}) => JSON.stringify({
  choice, version: 1, expires_at: Date.now() + 86400000, ...extra,
});

class Element {
  constructor(tag, doc) {
    this.tagName = tag.toUpperCase();
    this.ownerDocument = doc;
    this.children = [];
    this.attributes = new Map();
    this.listeners = new Map();
    this.style = {};
    this.hidden = false;
    this.textContent = '';
    this.dataset = new Proxy({}, {
      get: (_, key) => this.getAttribute(`data-${String(key).replace(/[A-Z]/g, c => `-${c.toLowerCase()}`)}`),
      set: (_, key, value) => { this.setAttribute(`data-${String(key).replace(/[A-Z]/g, c => `-${c.toLowerCase()}`)}`, value); return true; },
    });
  }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.has(name) ? this.attributes.get(name) : null; }
  removeAttribute(name) { this.attributes.delete(name); }
  get id() { return this.getAttribute('id') || ''; }
  set id(value) { this.setAttribute('id', value); }
  get src() { return this.getAttribute('src') || ''; }
  set src(value) { this.setAttribute('src', value); }
  get href() {
    const value = this.getAttribute('href');
    if (value === null) return '';
    try { return new URL(value, this.ownerDocument.location.href).href; } catch (_) { return value; }
  }
  set href(value) { this.setAttribute('href', value); }
  get className() { return this.getAttribute('class') || ''; }
  set className(value) { this.setAttribute('class', value); }
  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    if (child.tagName === 'SCRIPT' && child.src) this.ownerDocument.network.push({
      kind: 'script', src: child.src, node: child, queuedAtInsert: this.ownerDocument.queueSnapshot(),
    });
    return child;
  }
  append(...children) { children.forEach(child => this.appendChild(typeof child === 'string' ? this.ownerDocument.createTextNode(child) : child)); }
  removeChild(child) { this.children = this.children.filter(item => item !== child); child.parentNode = null; }
  remove() { this.parentNode?.removeChild(this); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  addEventListener(type, listener) { this.listeners.set(type, [...(this.listeners.get(type) || []), listener]); }
  dispatchEvent(event) {
    event.target ||= this;
    event.currentTarget = this;
    for (const listener of this.listeners.get(event.type) || []) listener(event);
    if (event.bubbles && this.parentNode) this.parentNode.dispatchEvent(event);
    return true;
  }
  click() { this.dispatchEvent({ type: 'click', bubbles: true, button: 0, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } }); }
  focus() { this.ownerDocument.activeElement = this; }
  matches(selector) {
    if (selector.startsWith('#')) return this.id === selector.slice(1);
    const match = selector.match(/^([a-z]+)?(?:\[([^=\]]+)(?:=["']?([^"'\]]+)["']?)?\])?$/i);
    return Boolean(match && (!match[1] || this.tagName === match[1].toUpperCase()) &&
      (!match[2] || (this.attributes.has(match[2]) && (match[3] === undefined || this.getAttribute(match[2]) === match[3]))));
  }
  closest(selector) { return this.matches(selector) ? this : this.parentNode?.closest(selector) || null; }
  querySelectorAll(selector) { return this.children.flatMap(child => child instanceof Element ? [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)] : []); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

function fixture(options = {}) {
  const network = [];
  const writes = [];
  const reloads = [];
  const events = new Map();
  const storage = new Map();
  if (options.stored !== undefined) storage.set(KEY, options.stored);
  const cookies = new Map(Object.entries(options.cookies || {}));
  const document = new Element('document');
  document.ownerDocument = document;
  document.network = network;
  document.readyState = 'complete';
  document.createElement = tag => new Element(tag, document);
  document.createTextNode = text => ({ textContent: String(text), parentNode: null });
  document.getElementById = id => document.querySelector(`#${id}`);
  document.documentElement = document.appendChild(document.createElement('html'));
  document.documentElement.lang = 'en';
  document.head = document.documentElement.appendChild(document.createElement('head'));
  document.body = document.documentElement.appendChild(document.createElement('body'));
  document.referrer = options.referrer ?? 'https://example.org/articles/?email=private@example.org#secret';
  Object.defineProperty(document, 'cookie', {
    get: () => [...cookies].map(([key, value]) => `${key}=${value}`).join('; '),
    set: value => {
      writes.push(value);
      const [name, ...parts] = value.split(';')[0].split('=');
      if (/max-age=0|expires=Thu, 01 Jan 1970/i.test(value)) cookies.delete(name);
      else cookies.set(name, parts.join('='));
    },
  });
  const config = {
    enabled: true, measurement_id: ID, canonical_url: CANONICAL,
    page_title: 'CSV Preflight', language: 'en', consent_version: 1,
    allowed_hashes: ['faq'], app_store_urls: [STORE],
    ...options.config,
  };
  if (!options.noConfig) {
    const node = document.createElement('script');
    node.id = 'site-measurement-config';
    node.type = 'application/json';
    node.textContent = options.configText ?? JSON.stringify(config);
    document.head.appendChild(node);
  }
  const settings = document.createElement('button');
  settings.setAttribute('data-analytics-settings', '');
  document.body.appendChild(settings);
  const url = new URL(options.href ?? CANONICAL);
  const location = {
    href: url.href, origin: url.origin, pathname: url.pathname,
    protocol: url.protocol, search: url.search, hash: url.hash,
    reload: () => reloads.push({ disabled: context[`ga-disable-${ID}`], commandCount: commands().length }),
  };
  document.location = location;
  const localStorage = {
    getItem: key => { if (options.getFails) throw new Error('mock storage read blocked'); return storage.get(key) ?? null; },
    setItem: (key, value) => { if (options.setFails) throw new Error('mock storage write blocked'); storage.set(key, String(value)); },
    removeItem: key => storage.delete(key),
  };
  const sandbox = {
    document, location, localStorage, URL, Date, JSON, console,
    navigator: { language: 'en', sendBeacon: url => { network.push({ kind: 'beacon', src: url }); return true; } },
    addEventListener: (type, fn) => events.set(type, [...(events.get(type) || []), fn]),
    fetch: url => { network.push({ kind: 'fetch', src: url }); throw new Error('mock network forbidden'); },
    XMLHttpRequest: class { constructor() { network.push({ kind: 'xhr' }); throw new Error('mock network forbidden'); } },
    setTimeout: () => 1, clearTimeout() {},
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  const commands = () => JSON.parse(JSON.stringify((context.dataLayer || []).map(item => Array.from(item))));
  document.queueSnapshot = commands;
  vm.runInContext(source, context, { filename: 'analytics.js' });
  const action = name => {
    const button = document.querySelector(`[data-analytics-action="${name}"]`);
    assert.ok(button, `consent action exists: ${name}`);
    button.click();
  };
  const load = () => {
    const loader = network.find(item => item.kind === 'script')?.node;
    assert.ok(loader, 'a mocked loader was inserted');
    if (typeof loader.onload === 'function') loader.onload();
    else loader.dispatchEvent({ type: 'load' });
  };
  const storageEvent = (value, key = KEY) => {
    if (key === null) storage.clear();
    else if (value === null) storage.delete(key); else storage.set(key, value);
    for (const fn of events.get('storage') || []) fn({ key, newValue: value, storageArea: localStorage });
  };
  const windowEvent = type => { for (const fn of events.get(type) || []) fn({ type }); };
  const link = href => {
    const node = document.createElement('a');
    node.href = href;
    node.textContent = 'private@example.org private label';
    document.body.appendChild(node);
    return node;
  };
  const rerun = () => vm.runInContext(source, context, { filename: 'analytics.js' });
  return { context, document, network, writes, reloads, storage, cookies, settings, action, load, commands, storageEvent, windowEvent, link, rerun };
}

function noCollection(env) {
  assert.equal(env.network.length, 0, 'no external resource or request');
  assert.equal(env.commands().length, 0, 'no gtag queue');
  assert.equal(env.context.gtag, undefined, 'gtag is not installed');
}

function measurementCommands(env) {
  return env.commands().filter(command => ['js', 'config', 'event'].includes(command[0]));
}

function privacyQueueOnly(commands) {
  assert.deepEqual(commands.map(command => command[0]), ['consent', 'set']);
  assert.equal(commands[0][1], 'default');
  assert.equal(commands[0][2].analytics_storage, 'granted');
  for (const field of ['ad_storage', 'ad_user_data', 'ad_personalization']) assert.equal(commands[0][2][field], 'denied');
  const defaults = commands[1][1];
  assert.equal(defaults.page_location, CANONICAL);
  assert.equal(defaults.page_referrer, 'https://example.org');
  assert.equal(defaults.send_page_view, false);
  assert.equal(defaults.cookie_prefix, 'yutchi_portfolio');
  assert.equal(defaults.cookie_domain, 'none');
  assert.equal(defaults.cookie_path, '/portfolio-site/');
  for (const field of ['allow_google_signals', 'allow_ad_personalization_signals', 'url_passthrough']) assert.equal(defaults[field], false);
  assert.equal(defaults.ads_data_redaction, true);
}

test('no consent and rejected preference never initialize collection', () => {
  noCollection(fixture());
  noCollection(fixture({ stored: preference('rejected') }));
  const env = fixture();
  env.action('reject');
  noCollection(env);
});

test('accept loads once and emits one page-view config, including duplicate input and load reentry', () => {
  const env = fixture();
  env.action('accept');
  assert.equal(env.network.length, 1);
  assert.equal(env.network[0].src, `https://www.googletagmanager.com/gtag/js?id=${ID}`);
  assert.equal(env.network[0].node.referrerPolicy, 'no-referrer');
  privacyQueueOnly(env.network[0].queuedAtInsert);
  privacyQueueOnly(env.commands());
  assert.equal(env.context[`ga-disable-${ID}`], true, 'measurement remains disabled during loader execution');
  assert.equal(measurementCommands(env).length, 0, 'only local privacy defaults are queued before load');
  env.action('accept');
  env.rerun();
  env.load();
  env.load();
  assert.equal(env.network.length, 1);
  const configs = env.commands().filter(command => command[0] === 'config');
  assert.equal(configs.length, 1);
  assert.equal(configs[0][1], ID);
  assert.equal(configs[0][2].send_page_view, true);
  assert.equal(env.commands().filter(command => command[0] === 'js').length, 1);
  assert.equal(env.commands().filter(command => command[0] === 'consent').length, 1);
  assert.equal(env.commands().filter(command => command[0] === 'set').length, 1);
  assert.equal(env.commands().filter(command => command[0] === 'event' && command[1] === 'page_view').length, 0);
  assert.equal(JSON.parse(env.storage.get(KEY)).choice, 'accepted');
});

test('withdrawal disables before reload, cleans only owned cookies, and sends no denied pings', () => {
  const env = fixture({ cookies: {
    yutchi_portfolio_ga: 'own', yutchi_portfolio_ga_TEST: 'own',
    _ga: 'other-property', yutchi_portfolio_garbage: 'unrelated', session: 'unrelated',
  } });
  env.action('accept');
  env.load();
  const before = env.commands().length;
  env.settings.click();
  env.action('reject');
  assert.equal(env.context[`ga-disable-${ID}`], true);
  assert.equal(env.reloads.length, 1);
  assert.equal(env.reloads[0].disabled, true);
  assert.equal(env.commands().length, before, 'withdrawal must not call gtag');
  assert.equal(env.network.length, 1, 'withdrawal must not request another resource');
  assert.deepEqual([...new Set(env.writes.map(value => value.split('=')[0]))].sort(), ['yutchi_portfolio_ga', 'yutchi_portfolio_ga_TEST']);
  assert.ok(env.writes.every(value => value.includes('Max-Age=0') && value.includes('Path=/portfolio-site/') && !/domain=/i.test(value)));
  assert.equal(env.cookies.get('_ga'), 'other-property');
  assert.equal(env.cookies.get('yutchi_portfolio_garbage'), 'unrelated');
  assert.equal(env.cookies.get('session'), 'unrelated');
});

test('withdraw before loader completion permits only the prior local privacy queue', () => {
  const env = fixture();
  env.action('accept');
  env.action('reject');
  env.load();
  assert.equal(env.context[`ga-disable-${ID}`], true);
  privacyQueueOnly(env.commands());
  assert.equal(measurementCommands(env).length, 0);
});

test('malformed, expired, stale and unavailable storage fail closed', () => {
  for (const stored of ['not-json', 'null', '{}', preference('accepted', { version: 0 }), preference('accepted', { expires_at: 0 }), preference('accepted', { expires_at: Date.now() + 181 * 86400000 }), preference('other')]) {
    noCollection(fixture({ stored }));
  }
  const readFailure = fixture({ getFails: true, stored: preference('accepted') });
  noCollection(readFailure);
  const writeFailure = fixture({ setFails: true });
  writeFailure.action('accept');
  noCollection(writeFailure);
  const options = {};
  const lateReadFailure = fixture(options);
  lateReadFailure.action('accept');
  options.getFails = true;
  lateReadFailure.load();
  privacyQueueOnly(lateReadFailure.commands());
  assert.equal(measurementCommands(lateReadFailure).length, 0, 'read failure during load cannot configure collection');
  assert.equal(lateReadFailure.context[`ga-disable-${ID}`], true);
});

test('cross-tab rejection, deletion and storage clearing revoke without new collection commands', () => {
  for (const [value, key] of [[preference('rejected'), KEY], [null, KEY], [null, null]]) {
    const env = fixture({ stored: preference('accepted') });
    env.load();
    const before = env.commands().length;
    env.storageEvent(preference('rejected'), 'unrelated-key');
    assert.equal(env.reloads.length, 0);
    env.storageEvent(value, key);
    assert.equal(env.context[`ga-disable-${ID}`], true);
    assert.equal(env.reloads.length, 1);
    assert.equal(env.commands().length, before);
  }
});

test('failed loader stays disabled even if a late load event arrives', () => {
  const env = fixture();
  env.action('accept');
  env.network[0].node.onerror();
  env.load();
  assert.equal(env.context[`ga-disable-${ID}`], true);
  privacyQueueOnly(env.commands());
  assert.equal(measurementCommands(env).length, 0);
  assert.equal(env.network.length, 1);
});

test('page location and referrer exclude query/hash PII and advertising consent stays denied', () => {
  const env = fixture({ config: { canonical_url: `${CANONICAL}?email=private@example.org#private-fragment` } });
  env.action('accept');
  env.load();
  const commands = env.commands();
  const payload = JSON.stringify(commands);
  assert.doesNotMatch(payload, /private@example|private-token|private-fragment|[?&#]email=|[?&]token=/);
  const defaults = Object.assign({}, ...commands.flat().filter(item => item && typeof item === 'object' && !Array.isArray(item)));
  assert.equal(defaults.page_location, CANONICAL);
  assert.ok(!defaults.page_referrer || (!defaults.page_referrer.includes('?') && !defaults.page_referrer.includes('#')));
  const consent = commands.find(command => command[0] === 'consent' && command[1] === 'default')?.[2];
  assert.ok(consent);
  assert.equal(consent.analytics_storage, 'granted');
  for (const field of ['ad_storage', 'ad_user_data', 'ad_personalization']) assert.equal(consent[field], 'denied');
});

test('disabled, malformed config, missing ID and unapproved location never load analytics', () => {
  for (const options of [
    { config: { enabled: false } }, { noConfig: true }, { configText: '{bad-json' },
    { config: { measurement_id: '' } }, { config: { measurement_id: 'G-XXXXXXXXXX' } },
    { config: { measurement_id: 'G-0000000000' } },
    { config: { canonical_url: 'https://example.org/portfolio-site/' } },
    { config: { canonical_url: `${ORIGIN}/portfolio-site/different-page/` } },
    { config: { consent_version: 0 } }, { config: { language: 'other' } },
    { config: { allowed_hashes: null } }, { config: { app_store_urls: null } },
    { config: { app_store_urls: [STORE + '?email=private@example.org'] } },
    { config: { app_store_urls: ['https://apps.apple.com/us/app/unknown/id1234567890'] } },
    { href: 'https://example.org/portfolio-site/' },
    { href: `${ORIGIN}/some-other-site/` },
    { href: `${ORIGIN}/portfolio-site-imitation/` },
  ]) noCollection(fixture({ stored: preference('accepted'), ...options }));
});

test('query strings and unknown fragments fail closed; only declared static fragments are allowed', () => {
  for (const suffix of ['?email=private@example.org', '?utm_source=anything', '#private-fragment', '#faq?email=private@example.org']) {
    const env = fixture({ stored: preference('accepted'), href: CANONICAL + suffix });
    noCollection(env);
  }
  const allowed = fixture({ stored: preference('accepted'), href: CANONICAL + '#faq' });
  allowed.load();
  const config = allowed.commands().find(command => command[0] === 'config');
  assert.equal(config[2].page_location, CANONICAL, 'even approved fragments are excluded from measurement');
  allowed.context.location.hash = '#private-fragment';
  allowed.context.location.href = CANONICAL + '#private-fragment';
  const before = allowed.commands().length;
  allowed.windowEvent('hashchange');
  assert.equal(allowed.context[`ga-disable-${ID}`], true);
  assert.equal(allowed.reloads.length, 1);
  assert.equal(allowed.commands().length, before);
  const race = fixture({ stored: preference('accepted') });
  race.context.location.search = '?email=private@example.org';
  race.load();
  privacyQueueOnly(race.commands());
  assert.equal(measurementCommands(race).length, 0, 'URL changed during load cannot initialize measurement');
  assert.equal(race.context[`ga-disable-${ID}`], true);
});

test('only a fully allowlisted App Store URL emits one minimal click event after loaded consent', () => {
  const env = fixture();
  const approved = env.link(STORE);
  env.action('accept');
  approved.click();
  privacyQueueOnly(env.commands());
  assert.equal(measurementCommands(env).length, 0, 'no event or initialization before successful loader completion');
  env.load();
  approved.click();
  const clicks = env.commands().filter(command => command[0] === 'event');
  assert.deepEqual(clicks, [['event', 'click', { link_url: STORE, link_domain: 'apps.apple.com', outbound: true }]]);
  for (const href of [
    'mailto:private@example.org', 'https://example.org/?email=private@example.org',
    'https://apps.apple.com/us/app/unknown/id1234567890',
    STORE + '?email=private@example.org', STORE + '?pt=123&ct=mock_campaign&mt=12',
    STORE + '#private-fragment', '#private-fragment',
  ]) env.link(href).click();
  assert.equal(env.commands().filter(command => command[0] === 'event').length, 1);
  assert.doesNotMatch(JSON.stringify(env.commands()), /private@example|private label|private-fragment|mock_campaign/);
  // Campaign values below are offline mock fixtures, not real attribution tokens.
  const campaignUrl = STORE + '?pt=123&ct=mock_campaign&mt=12';
  const campaign = fixture({ stored: preference('accepted'), config: { app_store_urls: [campaignUrl] } });
  campaign.load();
  campaign.link(campaignUrl).click();
  assert.deepEqual(campaign.commands().filter(command => command[0] === 'event'), [
    ['event', 'click', { link_url: campaignUrl, link_domain: 'apps.apple.com', outbound: true }],
  ]);
});

test('rejected and withdrawn consent never emits outbound clicks', () => {
  const rejected = fixture({ stored: preference('rejected') });
  rejected.link(STORE).click();
  noCollection(rejected);
  const withdrawn = fixture();
  withdrawn.action('accept');
  withdrawn.load();
  withdrawn.settings.click();
  withdrawn.action('reject');
  const before = withdrawn.commands().length;
  withdrawn.link(STORE).click();
  assert.equal(withdrawn.commands().length, before);
});
