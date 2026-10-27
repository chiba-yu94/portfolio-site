/* Basic consent: no Google tag or measurement commands before a saved opt-in. */
(() => {
  'use strict';
  const ORIGIN = 'https://chiba-yu94.github.io';
  const SCOPE = '/portfolio-site/';
  const KEY = 'yutchi-apps:/portfolio-site/:analytics-consent';
  const COOKIE_PREFIX = 'yutchi_portfolio';
  const LIFETIME = 180 * 24 * 60 * 60 * 1000;
  if (window.__yutchiAnalyticsConsentBooted) return;
  window.__yutchiAnalyticsConsentBooted = true;

  function boot() {
    let config;
    let canonical;
    let approvedStoreUrls;
    let locationAllowed;
    try {
      const node = document.getElementById('site-measurement-config');
      config = JSON.parse(node ? node.textContent : 'null');
      if (!config || config.enabled !== true || config.account_settings_reviewed !== true) return;
      if (window.location.origin !== ORIGIN || !window.location.pathname.startsWith(SCOPE)) return;
      if (!/^G-[A-Z0-9]{10}$/.test(config.measurement_id) || /^(G-XXXXXXXXXX|G-0000000000)$/.test(config.measurement_id)) return;
      if (config.consent_version !== 1 || !['ja', 'en'].includes(config.language)) return;
      if (typeof config.page_title !== 'string' || !config.page_title.trim() || config.page_title.length > 300) return;
      if (!Array.isArray(config.allowed_hashes) || !config.allowed_hashes.every(id => typeof id === 'string' && /^[A-Za-z0-9_:.-]{1,128}$/.test(id))) return;
      if (!Array.isArray(config.app_store_urls) || config.app_store_urls.length > 64) return;
      approvedStoreUrls = new Set(config.app_store_urls.map(value => {
        if (typeof value !== 'string') throw new Error('Invalid store URL');
        const target = new URL(value);
        const match = target.pathname.match(/\/id(\d+)\/?$/);
        if (target.origin !== 'https://apps.apple.com' || target.username || target.password || target.hash || !match || !['6820027859', '6820943200', '6760961992', '6820426754'].includes(match[1])) throw new Error('Unapproved store URL');
        const seen = new Set();
        target.searchParams.forEach((value, name) => {
          if (seen.has(name) || !['pt', 'ct', 'mt'].includes(name)) throw new Error('Unapproved campaign parameter');
          if ((name === 'pt' && !/^\d{1,20}$/.test(value)) || (name === 'ct' && !/^[A-Za-z0-9_.-]{1,80}$/.test(value)) || (name === 'mt' && !/^(8|12)$/.test(value))) throw new Error('Invalid campaign value');
          seen.add(name);
        });
        return target.href;
      }));
      canonical = new URL(config.canonical_url);
      const cleanPath = path => path.replace(/index\.html$/, '');
      if (canonical.origin !== ORIGIN || canonical.username || canonical.password || !canonical.pathname.startsWith(SCOPE)) return;
      if (cleanPath(canonical.pathname) !== cleanPath(window.location.pathname)) return;
      canonical.search = '';
      canonical.hash = '';
      locationAllowed = () => {
        if (window.location.origin !== ORIGIN || window.location.search || cleanPath(window.location.pathname) !== cleanPath(canonical.pathname)) return false;
        if (!window.location.hash) return true;
        try { return config.allowed_hashes.includes(decodeURIComponent(window.location.hash.slice(1))); }
        catch (_) { return false; }
      };
      if (!locationAllowed()) return;
    } catch (_) {
      return;
    }

    const disableKey = 'ga-disable-' + config.measurement_id;
    window[disableKey] = true;
    const ja = config.language === 'ja';
    const settings = Array.from(document.querySelectorAll('[data-analytics-settings]'));
    let loading = false;
    let initialized = false;
    let requested = false;
    let withdrawn = false;
    let failed = false;
    let generation = 0;
    let expiryTimer;
    let loader;
    let panel;
    let heading;
    let status;
    let returnFocus;

    function readPreference() {
      const raw = window.localStorage.getItem(KEY);
      if (raw === null) return null;
      let value;
      try { value = JSON.parse(raw); } catch (_) { return null; }
      const now = Date.now();
      if (!value || value.version !== config.consent_version || !['accepted', 'rejected'].includes(value.choice)) return null;
      if (!Number.isSafeInteger(value.expires_at) || value.expires_at <= now || value.expires_at > now + LIFETIME + 5000) return null;
      return value;
    }

    function clearCookies() {
      try {
        document.cookie.split(';').forEach(part => {
          const name = part.trim().split('=')[0];
          if (/^yutchi_portfolio_ga(?:_|$)/.test(name)) {
            document.cookie = name + '=; Max-Age=0; Path=' + SCOPE + '; SameSite=Lax; Secure';
          }
        });
      } catch (_) { /* Cookie restrictions never grant consent. */ }
    }

    function stop() {
      window[disableKey] = true;
      generation += 1;
      window.clearTimeout(expiryTimer);
      clearCookies();
      if (loader) loader.remove();
      if (requested && !withdrawn) {
        withdrawn = true;
        // Remove the third-party runtime/listeners without sending a denied ping.
        window.location.reload();
      }
    }

    function element(tag, className, copy) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (copy) node.textContent = copy;
      return node;
    }

    function show(preference, focus) {
      panel.hidden = false;
      status.textContent = preference
        ? (preference.choice === 'accepted'
          ? (ja ? '現在の設定：同意しています。' : 'Current choice: accepted.')
          : (ja ? '現在の設定：拒否しています。' : 'Current choice: rejected.'))
        : '';
      if (focus) heading.focus();
    }

    function hide() {
      panel.hidden = true;
      if (returnFocus) {
        returnFocus.focus();
        returnFocus = null;
      }
    }

    function storageFailure() {
      failed = true;
      stop();
      if (panel) {
        panel.hidden = false;
        status.textContent = ja
          ? '選択を保存できないため、アクセス解析は無効のままです。'
          : 'Your choice could not be saved. Analytics remains off.';
      }
    }

    function scheduleExpiry(preference) {
      window.clearTimeout(expiryTimer);
      expiryTimer = window.setTimeout(reconcile, Math.min(preference.expires_at - Date.now(), 2147483647));
    }

    function start(preference) {
      if (failed || withdrawn || loading || initialized) return;
      if (!locationAllowed()) { stop(); return; }
      let current;
      try { current = readPreference(); } catch (_) { storageFailure(); return; }
      if (!current || current.choice !== 'accepted') { stop(); return; }
      if (window.gtag || window.dataLayer) { failed = true; stop(); return; }
      const token = generation;
      window.dataLayer = [];
      window.gtag = function () {
        if (!window[disableKey] && locationAllowed()) window.dataLayer.push(arguments);
      };
      let referrer = '';
      try {
        const source = new URL(document.referrer);
        if (source.protocol === 'https:' || source.protocol === 'http:') referrer = source.origin;
      } catch (_) { /* No usable public referrer. */ }
      const defaults = {
        page_location: canonical.href,
        page_title: config.page_title,
        page_referrer: referrer,
        allow_google_signals: false,
        allow_ad_personalization_signals: false,
        ads_data_redaction: true,
        url_passthrough: false,
        send_page_view: false,
        cookie_prefix: COOKIE_PREFIX,
        cookie_domain: 'none',
        cookie_path: SCOPE,
        cookie_flags: 'SameSite=Lax;Secure'
      };
      // Consent is already saved. Queue only protective defaults before Google
      // can execute; initialization and page_view still wait for the load check.
      function queueDefaults() { window.dataLayer.push(arguments); }
      queueDefaults('consent', 'default', {
        analytics_storage: 'granted',
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied'
      });
      queueDefaults('set', defaults);
      loading = true;
      requested = true;
      loader = document.createElement('script');
      loader.id = 'yutchi-analytics-loader';
      loader.async = true;
      loader.referrerPolicy = 'no-referrer';
      loader.src = 'https://www.googletagmanager.com/gtag/js?id=' + config.measurement_id;
      loader.onload = () => {
        if (token !== generation || withdrawn || failed || initialized) return;
        if (!locationAllowed()) { stop(); return; }
        let latest;
        try { latest = readPreference(); } catch (_) { storageFailure(); return; }
        if (!latest || latest.choice !== 'accepted') { stop(); return; }
        initialized = true;
        loading = false;
        window[disableKey] = false;
        window.gtag('js', new Date());
        // Enhanced measurement is disabled in the property; only approved links
        // below get a click event. Never send link text or arbitrary href values.
        window.gtag('config', config.measurement_id, Object.assign({}, defaults, {
          send_page_view: true,
          cookie_prefix: COOKIE_PREFIX,
          cookie_domain: 'none',
          cookie_path: SCOPE,
          cookie_flags: 'SameSite=Lax;Secure',
          cookie_expires: Math.max(1, Math.floor((latest.expires_at - Date.now()) / 1000)),
          cookie_update: false
        }));
        scheduleExpiry(latest);
      };
      loader.onerror = () => {
        if (token !== generation) return;
        window[disableKey] = true;
        failed = true;
        loading = false;
        clearCookies();
        show(preference, false);
        status.textContent = ja
          ? 'アクセス解析を読み込めませんでした。計測は無効のままです。'
          : 'Analytics could not load. Measurement remains off.';
      };
      document.head.appendChild(loader);
    }

    function choose(choice) {
      if (choice === 'rejected') window[disableKey] = true;
      const preference = {choice, version: config.consent_version, expires_at: Date.now() + LIFETIME};
      try {
        window.localStorage.setItem(KEY, JSON.stringify(preference));
        const saved = readPreference();
        if (!saved || saved.choice !== choice || saved.expires_at !== preference.expires_at) throw new Error('Preference not saved');
      } catch (_) { storageFailure(); return; }
      hide();
      if (choice === 'rejected') {
        stop();
      } else if (withdrawn || failed) {
        window.location.reload();
      } else {
        scheduleExpiry(preference);
        start(preference);
      }
    }

    function reconcile() {
      if (withdrawn || failed) return;
      if (!locationAllowed()) { stop(); hide(); return; }
      let preference;
      try { preference = readPreference(); } catch (_) { storageFailure(); return; }
      if (!preference || preference.choice !== 'accepted') {
        stop();
        if (preference) hide(); else show(null, false);
      } else {
        scheduleExpiry(preference);
        start(preference);
      }
    }

    let preference;
    try { preference = readPreference(); } catch (_) { clearCookies(); return; }
    panel = element('section', 'analytics-consent');
    panel.id = 'analytics-consent';
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-labelledby', 'analytics-consent-title');
    heading = element('h2', '', ja ? 'アクセス解析の設定' : 'Analytics preferences');
    heading.id = 'analytics-consent-title';
    heading.tabIndex = -1;
    panel.appendChild(heading);
    panel.appendChild(element('p', '', ja
      ? '同意すると、Google Analyticsでページ閲覧とApp Storeリンクのクリックを計測します。拒否した場合は読み込みません。選択は180日間保存し、いつでも変更できます。'
      : 'With your permission, Google Analytics measures page visits and App Store link clicks. It does not load if you reject. Your choice lasts 180 days and can be changed at any time.'));
    const notice = element('a', 'analytics-notice', ja ? 'Webサイトのプライバシーについて' : 'Website privacy notice');
    notice.href = SCOPE + (ja ? '' : 'en/') + 'privacy-policies/#website-privacy';
    panel.appendChild(notice);
    const actions = element('div', 'analytics-consent-actions');
    [['accept', 'accepted', ja ? '同意する' : 'Accept'], ['reject', 'rejected', ja ? '拒否する' : 'Reject']].forEach(([action, choice, label]) => {
      const button = element('button', 'analytics-choice', label);
      button.type = 'button';
      button.setAttribute('data-analytics-action', action);
      button.addEventListener('click', () => choose(choice));
      actions.appendChild(button);
    });
    panel.appendChild(actions);
    status = element('p', 'analytics-consent-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    panel.appendChild(status);
    document.body.appendChild(panel);
    settings.forEach(button => {
      button.hidden = false;
      button.addEventListener('click', () => {
        let current;
        try { current = readPreference(); } catch (_) { storageFailure(); return; }
        returnFocus = button;
        show(current, true);
      });
    });
    window.addEventListener('storage', event => {
      if (event.key === KEY || event.key === null) reconcile();
    });
    window.addEventListener('focus', reconcile);
    window.addEventListener('pageshow', reconcile);
    window.addEventListener('hashchange', reconcile);
    window.addEventListener('popstate', reconcile);
    document.addEventListener('click', event => {
      if (!initialized || withdrawn || failed || window[disableKey]) return;
      if (!locationAllowed()) { stop(); return; }
      let current;
      try { current = readPreference(); } catch (_) { storageFailure(); return; }
      if (!current || current.choice !== 'accepted') { stop(); return; }
      const anchor = event.target && typeof event.target.closest === 'function' ? event.target.closest('a[href]') : null;
      if (!anchor) return;
      let target;
      try { target = new URL(anchor.href).href; } catch (_) { return; }
      if (!approvedStoreUrls.has(target)) return;
      window.gtag('event', 'click', {link_url: target, link_domain: 'apps.apple.com', outbound: true});
    }, {capture: true});
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') reconcile();
    });
    if (preference) hide(); else show(null, false);
    reconcile();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once: true});
  else boot();
})();
