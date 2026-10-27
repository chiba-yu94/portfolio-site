# -*- coding: utf-8 -*-
"""Optional, fail-closed website measurement; no application metadata changes."""
import html
import json
import re
from urllib.parse import parse_qs, urlsplit


def load_settings(root, products):
    settings = json.loads((root / 'data/measurement.json').read_text(encoding='utf-8'))
    token = settings.get('google_site_verification', '')
    if not isinstance(token, str) or (token and not re.fullmatch(r'[A-Za-z0-9_-]+', token)):
        raise ValueError('Invalid Google verification token; use the actual Google value.')
    analytics = settings.get('analytics', {})
    if type(analytics.get('enabled')) is not bool or type(analytics.get('account_settings_reviewed')) is not bool:
        raise ValueError('Analytics switches must be explicit booleans.')
    measurement_id = analytics.get('measurement_id', '')
    if not isinstance(measurement_id, str) or (measurement_id and (not re.fullmatch(r'G-[A-Z0-9]{10}', measurement_id) or measurement_id in ('G-XXXXXXXXXX', 'G-0000000000'))):
        raise ValueError('Use a real Measurement ID from the GA4 interface, or leave it empty.')
    if analytics.get('consent_version') != 1:
        raise ValueError('Consent version changes require a runtime and disclosure review.')
    if analytics['enabled'] and (not measurement_id or not analytics['account_settings_reviewed']):
        raise ValueError('Analytics stays disabled until a real ID and account settings review are available.')
    campaigns = settings.get('apple_campaign_links', {})
    known = {p['id']: p for p in products}
    if not isinstance(campaigns, dict) or not set(campaigns).issubset(known):
        raise ValueError('Campaigns must refer to existing released catalog products.')
    for product_id, regions in campaigns.items():
        if not isinstance(regions, dict) or not set(regions).issubset(known[product_id]['store_urls']):
            raise ValueError('Campaign region must have an existing verified store destination.')
        for region, entry in regions.items():
            if not isinstance(entry, dict) or entry.get('source') != 'App Store Connect' or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', entry.get('verified_at', '')):
                raise ValueError('Campaign requires its real App Store Connect source and verification date.')
            target = urlsplit(entry.get('url', ''))
            original_id = re.search(r'/id(\d+)', known[product_id]['store_urls'][region]).group(1)
            params = parse_qs(target.query, keep_blank_values=True)
            if target.scheme != 'https' or target.netloc != 'apps.apple.com' or target.fragment or not re.search(r'/id' + original_id + r'$', target.path):
                raise ValueError('Campaign must preserve the verified App Store app ID.')
            if set(params) != {'pt', 'ct', 'mt'} or any(len(values) != 1 for values in params.values()):
                raise ValueError('Campaign requires exactly one real pt, ct, and mt parameter.')
            if not re.fullmatch(r'\d+', params['pt'][0]) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,30}', params['ct'][0]) or params['mt'][0] not in ('8', '12'):
                raise ValueError('Campaign values require review; do not guess or silently rewrite them.')
    return settings


def campaign_url(settings, product, region):
    return settings['apple_campaign_links'].get(product['id'], {}).get(region, {}).get('url', product['store_urls'][region])


def measurement_head(settings, lang, canonical, title, body, products):
    # Only fixed generated values enter this config; visitor URL/query data never does.
    catalog_urls = {campaign_url(settings, p, region) for p in products for region in p['store_urls']}
    body_links = {html.unescape(href) for href in re.findall(r'\bhref="([^"]+)"', body)}
    approved = sorted(catalog_urls & body_links)
    config = dict(settings['analytics'], canonical_url=canonical, page_title=title, language=lang,
                  allowed_hashes=sorted({'main', *re.findall(r'\bid="([^"]+)"', body)}),
                  app_store_urls=approved)
    encoded = json.dumps(config, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    tag = ''
    if canonical == 'https://chiba-yu94.github.io/portfolio-site/' and settings['google_site_verification']:
        tag = '<meta name="google-site-verification" content="' + html.escape(settings['google_site_verification'], quote=True) + '">'
    return tag + '<meta name="referrer" content="origin"><script id="site-measurement-config" type="application/json">' + encoded + '</script><script src="/portfolio-site/analytics.js" defer></script>'


def settings_button(lang):
    label = '解析の同意設定を変更' if lang == 'ja' else 'Analytics preferences'
    return '<button type="button" class="analytics-settings" data-analytics-settings hidden>' + label + '</button>'


def privacy_notice(lang, settings):
    active = settings['analytics']['enabled']
    if lang == 'ja':
        status = 'このWebサイトでは、同意した場合に限りGoogle Analytics 4（GA4）を読み込みます。' if active else '現在、このWebサイトのアクセス解析は無効です。以下は有効化する場合の仕組みです。'
        paragraphs = [
            status + '同意前・拒否後はGoogleの解析タグを読み込まず、解析リクエストも送信しません。コンテンツの閲覧に同意は不要です。',
            '目的はサイトの利用状況とApp Storeリンクのクリックを把握し、案内を改善することです。送信先はGoogleです。同意後は、公開ページのURLとタイトル、流入元のドメイン、許可されたApp Storeリンク、ブラウザ・端末情報、GA4の識別子などが処理されます。通信に伴うIPアドレスもGoogle側で処理されます。クリックは購入・ダウンロード完了を意味しません。',
            'メールアドレス、入力内容、アプリ内の情報、ファイル名・ファイル内容は測定対象にしません。任意のクエリを含むURLや未定義のアンカーでは解析を停止します。UTMなどを含む訪問も測定されない場合があります。広告・リマーケティング・Google Signals・Meta Pixelは使用しません。',
            '同意の選択だけをこのサイト用のブラウザ保存領域に最長180日保存します。同意した場合のみ、このサイト用のGA4 Cookieを使用します。フッターの「解析の同意設定を変更」から拒否に変更でき、以後の計測を停止して対象Cookieを削除します。既に送信済み・送信開始済みの情報を取り消す操作ではありません。',
            'これはWebサイトの解析についての説明です。アプリ本体の機能・情報の取り扱いは各アプリ固有のポリシーをご確認ください。この静的サイトはGitHub Pagesで配信し、問い合わせフォームや利用者アカウントはありません。メールリンクはお使いのメールアプリを開きます。Google等による国外での処理についても、以下の各社説明をご確認ください。'
        ]
        title = 'このWebサイトの解析とプライバシー'
        links = [('https://policies.google.com/privacy', 'Googleのプライバシーポリシー'), ('https://policies.google.com/technologies/partner-sites', 'Googleによるサイト利用情報の取り扱い'), ('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'GitHubのプライバシーに関する説明')]
    else:
        status = 'This website loads Google Analytics 4 (GA4) only after you consent.' if active else 'Website analytics is currently disabled. The following describes the controls prepared for activation.'
        paragraphs = [
            status + ' No Google analytics tag or measurement request is loaded before consent or after rejection. Consent is optional and is not needed to read the site.',
            'The purpose is to improve product information using website usage and App Store link clicks. Google is the external recipient. After consent, processed data includes public page URLs and titles, the referring domain, approved App Store destinations, browser/device information, and GA4 identifiers. Google also processes the IP address used for the connection. A click is not a completed purchase or download.',
            'Email addresses, entered content, application data, filenames, and file contents are not measurement targets. Measurement stops on URLs containing query parameters or unknown anchors; visits with UTM parameters may therefore be excluded. Advertising, remarketing, Google Signals, and Meta Pixel are not used.',
            'Only the consent preference is stored in this website’s browser storage for up to 180 days. Its GA4 cookies are used only after consent. Choose Analytics preferences in the footer to reject later: future measurement stops and this integration’s cookies are removed. Withdrawal cannot recall information already sent or requests already started.',
            'This notice describes website measurement. Each application’s own policy continues to describe the app itself. The static website is hosted on GitHub Pages, with no contact form or visitor accounts. Email links open your email app. Review the linked providers’ information, including processing outside your country.'
        ]
        title = 'Website analytics and privacy'
        links = [('https://policies.google.com/privacy', 'Google privacy policy'), ('https://policies.google.com/technologies/partner-sites', 'How Google uses information from partner sites'), ('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'GitHub privacy statement')]
    return '<section id="website-privacy" class="container info-panel website-privacy"><h2>' + title + '</h2>' + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs) + '<p>' + ' · '.join('<a href="' + u + '">' + html.escape(label) + '</a>' for u, label in links) + '</p></section>'
