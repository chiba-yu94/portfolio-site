#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render crawlable, bilingual GitHub Pages documents from one product catalog."""
from pathlib import Path
import html
import json
from urllib.parse import quote
from measurement import load_settings, campaign_url, measurement_head, settings_button, privacy_notice

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://chiba-yu94.github.io/portfolio-site'
CONTACT = 'yutchi.apps@gmail.com'
PRODUCTS = json.loads((ROOT / 'data/products.json').read_text())['products']
SETTINGS = load_settings(ROOT, PRODUCTS)
PAGES = []

def esc(value):
    return html.escape(str(value), quote=True)

def url(path=''):
    return '/portfolio-site/' + path.lstrip('/')

def route(lang, path=''):
    return ('en/' if lang == 'en' else '') + path

def text(lang, ja, en):
    return en if lang == 'en' else ja

def product_path(p):
    return 'matanenote/' if p['id'] == 'matanenote' else f"apps/{p['id']}/"

def store(p, lang, tracked=False):
    region = 'jp' if lang == 'ja' or 'us' not in p['store_urls'] else 'us'
    return campaign_url(SETTINGS, p, region) if tracked else p['store_urls'][region]

def offer(p, lang):
    return p['prices'].get('jp' if lang == 'ja' else 'us', p['prices']['jp'])

def link(href, label, cls=''):
    return f'<a href="{esc(href)}" class="{cls}">{label}</a>'

def icon(p, size=64):
    return f'<img class="app-icon" src="{url(p["icon"])}" alt="" width="{size}" height="{size}" loading="lazy" decoding="async">'

def mail(p=None):
    return 'mailto:' + CONTACT + ('?subject=' + quote(p['store_name'] + ' — Support') if p else '')

def shell(lang, path, title, description, body, product=None, active=''):
    this = route(lang, path)
    other = route('ja' if lang == 'en' else 'en', path)
    og_image = BASE + '/' + (product['icon'] if product else 'assets/yutchi-developer-avatar.png')
    nav = [('apps/', 'アプリ', 'Apps'), ('support/', 'サポート', 'Support'), ('about/', '開発者について', 'About'), ('privacy-policies/', 'プライバシー', 'Privacy')]
    navigation = ''.join(link(url(route(lang, r)), text(lang, ja, en), 'nav-link' + (' current' if active == r else '')) for r, ja, en in nav)
    data = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Yutchi Apps', 'url': BASE + '/', 'inLanguage': ['ja', 'en'], 'publisher': {'@type': 'Person', 'name': 'Yutchi', 'url': BASE + '/about/'}}
    if product:
        data = {'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': product['store_name'], 'url': BASE + '/' + this, 'image': og_image, 'description': description, 'operatingSystem': product['os'][lang], 'applicationCategory': product['category'], 'softwareVersion': product['version'], 'downloadUrl': store(product, lang), 'author': {'@type': 'Person', 'name': 'Yutchi'}, 'offers': {'@type': 'Offer', 'price': offer(product, lang)['price'], 'priceCurrency': offer(product, lang)['currency'], 'url': store(product, lang)}}
    structured_json = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    measurement = measurement_head(SETTINGS, lang, BASE + '/' + this, title, body, PRODUCTS)
    output = f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE}/{this}"><link rel="alternate" hreflang="ja" href="{BASE}/{path}"><link rel="alternate" hreflang="en" href="{BASE}/en/{path}"><link rel="alternate" hreflang="x-default" href="{BASE}/{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Yutchi Apps"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{BASE}/{this}"><meta property="og:image" content="{og_image}"><meta property="og:locale" content="{'ja_JP' if lang == 'ja' else 'en_US'}"><meta name="twitter:card" content="summary">
{measurement}<meta name="theme-color" content="#F7F8F6"><link rel="icon" href="{url('assets/yutchi-developer-avatar.png')}"><link rel="stylesheet" href="{url('styles.css')}"><script src="{url('site.js')}" defer></script><script type="application/ld+json">{structured_json}</script></head>
<body><a class="skip-link" href="#main">{text(lang, '本文へ移動', 'Skip to content')}</a>
<header class="site-header"><div class="container header-inner">{link(url(route(lang)), '<span class="brand-symbol" aria-hidden="true">y.</span><span>Yutchi Apps</span>', 'brand')}<nav aria-label="{text(lang, 'メインナビゲーション', 'Main navigation')}">{navigation}</nav>{link(url(other), 'English' if lang == 'ja' else '日本語', 'language-switch')}</div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="container footer-grid"><div><a class="brand footer-brand" href="{url(route(lang))}">Yutchi Apps</a><p>Small tools. Better everyday.</p><p class="fine">{text(lang, 'Yutchiによる個人開発のアプリ。', 'Independent apps by Yutchi.')}</p></div><nav aria-label="{text(lang, 'フッターナビゲーション', 'Footer navigation')}">{navigation}</nav><div><span class="eyebrow">{text(lang, 'お問い合わせ', 'Say hello')}</span><a class="contact-link" href="mailto:{CONTACT}">{CONTACT}</a>{settings_button(lang)}<p class="fine">© 2026 Yutchi Apps</p></div></div></footer></body></html>'''
    destination = ROOT / this / 'index.html'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output)
    PAGES.append(this)

def cards(lang, items, screenshots=False):
    result = []
    for p in items:
        image = ''
        if screenshots:
            shot = p['screenshots'][0]
            image = f'<a class="card-shot {p["platform"].lower()}" href="{url(route(lang, product_path(p)))}" tabindex="-1" aria-hidden="true"><img src="{url(shot["src"])}" alt="" width="{shot["width"]}" height="{shot["height"]}" loading="lazy" decoding="async"></a>'
        result.append(f'''<article class="app-card" data-platform="{p['platform']}">{image}<div class="card-content"><div class="app-identity">{icon(p)}<div><span class="platform-label">{p['platform']}</span><h3>{esc(p['name'][lang])}</h3></div></div><p>{esc(p['summary'][lang])}</p><div class="card-links">{link(url(route(lang, product_path(p))), text(lang, '詳しく見る', 'Explore app') + '<span aria-hidden="true"> ↗</span>', 'text-link')}{link(store(p, lang, tracked=True), 'App Store<span class="sr-only"> — ' + esc(p['store_name']) + '</span>', 'store-link')}</div></div></article>''')
    return ''.join(result)

def faqs(lang, p):
    return ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in p['faq'][lang])

for lang in ('ja', 'en'):
    featured = [p for p in PRODUCTS if p['id'] in ('matanenote', 'csv-preflight')]
    body = f'''<section class="hero container"><div class="hero-copy"><span class="eyebrow">INDEPENDENT APPS · MACOS & IOS</span><h1>Small tools.<br><span>Better everyday.</span></h1><p class="hero-subtitle">Independent apps for macOS &amp; iOS.</p><p class="hero-japanese" lang="ja">macOSとiOSに、小さくて使いやすいアプリを。</p><div class="actions">{link(url(route(lang, 'apps/')), 'Explore Apps <span aria-hidden="true">↗</span>', 'button primary')}{link(url(route(lang, 'support/')), 'Get Support', 'button secondary')}</div></div><aside class="hero-note"><div class="icon-shelf">{''.join(icon(p, 56) for p in PRODUCTS)}</div><span class="eyebrow">{text(lang, '必要なときに、ちょうどいい。', 'A little less friction.')}</span><p>{text(lang, 'ファイルを渡す前の確認も、<br>次のお客様との会話も。<br>いつもの作業を、少し心地よく。', 'Before a file handoff.<br>Before the next conversation.<br>Small, considered steps for your day.')}</p><span class="note-line">{text(lang, 'シンプルな道具を、ひとつずつ。', 'Useful software, one app at a time.')}</span></aside></section>
<section class="section container"><div class="section-heading"><div><span class="eyebrow">THE APP SHELF</span><h2>{text(lang, 'いつもの作業に、小さな助けを。', 'A small place in your everyday.')}</h2></div>{link(url(route(lang, 'apps/')), text(lang, 'すべてのアプリ', 'View all apps') + ' →', 'text-link')}</div><div class="app-grid featured-grid">{cards(lang, featured, True)}</div></section>
<section class="platform-section container"><div><span class="eyebrow">FIND YOUR NEXT TOOL</span><h2>{text(lang, '使うデバイスから探す。', 'Made for the device you use.')}</h2></div><div class="platform-choices">{link(url(route(lang, 'apps/')) + '#macos', '<span class="platform-glyph" aria-hidden="true">▱</span><span><strong>macOS</strong><small>' + text(lang, 'ファイルの確認を、手元のMacで。', 'Thoughtful checks, right on your Mac.') + '</small></span><span aria-hidden="true">↗</span>', 'platform-choice')}{link(url(route(lang, 'apps/')) + '#ios', '<span class="platform-glyph" aria-hidden="true">▯</span><span><strong>iOS</strong><small>' + text(lang, '日々のメモと、小さな楽しみ。', 'Everyday notes and small discoveries.') + '</small></span><span aria-hidden="true">↗</span>', 'platform-choice')}</div></section>
<section class="section container philosophy"><div><span class="eyebrow">MADE WITH INTENTION</span><h2>{text(lang, '使いやすさは、<br>小さな配慮から。', 'Less complexity.<br>More consideration.')}</h2>{link(url(route(lang, 'about/')), text(lang, 'Yutchiについて', 'Meet the developer') + ' →', 'text-link')}</div><div class="principles"><article><span>01</span><h3>{text(lang, 'わかりやすく', 'Clear by design')}</h3><p>{text(lang, '何ができて、何ができないか。使い始める前に、わかる説明を大切にします。', 'Clear interfaces and honest explanations of what an app can—and cannot—do.')}</p></article><article><span>02</span><h3>{text(lang, '必要なことを、丁寧に', 'Useful, without the clutter')}</h3><p>{text(lang, '機能を増やすことより、ひとつの作業が気持ちよく進むことを。', 'Focused tools for specific tasks, with less unnecessary complexity.')}</p></article><article><span>03</span><h3>{text(lang, 'プライバシーへの配慮', 'Thoughtful about privacy')}</h3><p>{text(lang, '可能な場面では端末内で処理し、情報の取り扱いはアプリごとに説明します。', 'Local workflows where practical, with app-specific explanations of how information is handled.')}</p></article></div></section>
<section class="container support-callout"><div><span class="eyebrow">HERE TO HELP</span><h2>{text(lang, '困ったときも、迷わずに。', 'A clear place to get help.')}</h2><p>{text(lang, '使い方、よくある質問、お問い合わせをまとめました。', 'Usage notes, common questions, and one official support contact.')}</p></div>{link(url(route(lang, 'support/')), text(lang, 'サポートを開く', 'Visit support') + ' ↗', 'button primary')}</section>'''
    shell(lang, '', text(lang, 'Yutchi Apps — 小さくて使いやすいmacOS・iOSアプリ', 'Yutchi Apps — Small tools. Better everyday.'), text(lang, 'macOSとiOSに、小さくて使いやすいアプリを。Yutchiによる個人開発アプリの公式サイト。公開中のアプリ、使い方、サポートをご案内します。', 'Focused, thoughtfully designed apps for macOS and iOS. Discover independent apps by Yutchi, explore their features, and find official support.'), body)
    body = f'''<section class="page-intro container"><span class="eyebrow">YUTCHI APPS COLLECTION</span><h1>{text(lang, 'あなたの毎日に、<br>ちょうどいいアプリを。', 'Find your next<br>small, useful app.')}</h1><p>{text(lang, '現在App Storeで公開中のアプリをご紹介します。', 'Available now on the App Store. Each app has a clear purpose and a page with the details.')}</p></section><section class="container catalog section"><div class="catalog-toolbar"><h2>{text(lang, 'アプリ一覧', 'All apps')}</h2><div class="filter-bar" hidden aria-label="{text(lang, 'プラットフォームで絞り込み', 'Filter by platform')}"><button data-filter="all" aria-pressed="true">{text(lang, 'すべて', 'All apps')}</button><button id="macos" data-filter="macOS" aria-pressed="false">macOS</button><button id="ios" data-filter="iOS" aria-pressed="false">iOS</button></div></div><p class="sr-only" data-filter-status aria-live="polite"></p><div class="app-grid">{cards(lang, PRODUCTS)}</div><p class="fine catalog-note">{text(lang, '配信地域・対応OS・最新の価格はApp Storeでご確認ください。', 'Availability, supported devices, and current prices are shown on the App Store. Some apps are available in Japan only.')}</p></section>'''
    shell(lang, 'apps/', text(lang, 'アプリ一覧', 'Apps') + ' | Yutchi Apps', text(lang, 'CSV Preflight、File Transfer Preflight、またねノート、SIGNALS: Code Creatures。公開中のmacOS・iOSアプリを探す。', 'Explore CSV Preflight, File Transfer Preflight, MataneNote, and SIGNALS: Code Creatures. Official features, screenshots, and App Store links.'), body, active='apps/')
    for p in PRODUCTS:
        shots = ''.join(f'<figure><img src="{url(s["src"])}" width="{s["width"]}" height="{s["height"]}" alt="{esc(s["alt"][lang])}" loading="lazy" decoding="async"><figcaption>{esc(s["alt"][lang])}</figcaption></figure>' for s in p['screenshots'][:3])
        body = f'''<section class="container product-intro"><a class="breadcrumb" href="{url(route(lang, 'apps/'))}">← {text(lang, 'アプリ一覧', 'All apps')}</a><div class="product-heading">{icon(p, 88)}<div><span class="platform-label">{p['platform']}</span><h1>{esc(p['name'][lang])}</h1></div></div><p class="product-tagline">{esc(p['summary'][lang])}</p><div class="actions">{link(store(p, lang, tracked=True), text(lang, 'App Storeで見る', 'View on the App Store') + ' ↗', 'button primary')}{link(url(route(lang, 'support/')) + '#' + p['id'], text(lang, '使い方・サポート', 'Usage & support'), 'button secondary')}</div><div class="product-facts"><span>{esc(p['os'][lang])}</span><span>{esc(p['price'][lang])}</span><span>{esc(p['languages'][lang])}</span></div><p class="fine">{text(lang, '公開情報の確認日：', 'Store information checked: ')}{p['verified_date']} · {text(lang, '価格・配信地域はストアでご確認ください。', 'Check the store for current prices and regional availability.')}</p></section>
<section class="container product-story"><div><span class="eyebrow">A SMALL TOOL FOR A REAL TASK</span><h2>{esc(p['problem'][lang])}</h2><p>{esc(p['audience'][lang])}</p></div><div class="feature-panel"><h2>{text(lang, 'できること', 'What it does')}</h2><ul>{''.join('<li>' + esc(f) + '</li>' for f in p['features'][lang])}</ul></div></section><section class="container section screenshots-section"><div class="section-heading"><div><span class="eyebrow">A LOOK INSIDE</span><h2>{text(lang, '実際のアプリ画面', 'Inside the app')}</h2></div></div><div class="screenshot-gallery {p['platform'].lower()}">{shots}</div></section>
<section class="container details-grid section"><article class="info-panel"><span class="eyebrow">KNOW THE SCOPE</span><h2>{text(lang, '大切な制限事項', 'Important limitations')}</h2><ul>{''.join('<li>' + esc(f) + '</li>' for f in p['limits'][lang])}</ul></article><article class="info-panel"><span class="eyebrow">PRIVACY, EXPLAINED</span><h2>{text(lang, '情報の取り扱い', 'Privacy characteristics')}</h2><p>{esc(p['privacy'][lang])}</p>{link(p['privacy_url'][lang], text(lang, 'このアプリのプライバシーポリシー', 'Read this app’s privacy policy') + ' ↗', 'text-link')}</article></section><section class="container faq-section section"><div><span class="eyebrow">GOOD TO KNOW</span><h2>{text(lang, 'よくある質問', 'Common questions')}</h2></div><div class="faq-list">{faqs(lang, p)}</div></section><section class="container support-callout"><div><h2>{text(lang, 'お困りですか？', 'Need a hand?')}</h2><p>{text(lang, 'アプリ名・OS・状況を添えてお問い合わせください。', 'Tell us the app name, OS version, and what happened.')}</p></div>{link(mail(p), text(lang, 'メールで問い合わせる', 'Email support'), 'button primary')}</section>'''
        shell(lang, product_path(p), p['name'][lang] + text(lang, 'の機能・サポート | Yutchi Apps', ' | Yutchi Apps'), p['summary'][lang] + ' ' + p['problem'][lang], body, p, 'apps/')
    sections = ''.join(f'''<section class="support-product" id="{p['id']}"><div class="support-product-heading">{icon(p, 52)}<div><span class="platform-label">{p['platform']}</span><h2>{esc(p['name'][lang])}</h2></div></div><p>{esc(p['support_note'][lang])}</p><div class="inline-links">{link(url(route(lang, product_path(p))), text(lang, '機能・制限事項', 'Features & limitations'), 'text-link')}{link(p['support_url'][lang], text(lang, '既存サポート・利用ガイド', 'Product support & usage notes') + ' ↗', 'text-link')}{link(p['privacy_url'][lang], text(lang, 'プライバシーポリシー', 'Privacy policy') + ' ↗', 'text-link')}</div><div class="faq-list">{faqs(lang, p)}</div>{link(mail(p), esc(CONTACT) + ' ↗', 'text-link')}</section>''' for p in PRODUCTS)
    body = f'''<section class="page-intro container"><span class="eyebrow">YUTCHI APPS SUPPORT</span><h1>{text(lang, '必要な答えを、<br>見つけやすく。', 'A little help.<br>A clearer next step.')}</h1><p>{text(lang, 'アプリを選んで、使い方やよくある質問をご確認ください。', 'Choose an app for usage notes, common questions, and its privacy policy.')}</p><a class="email-pill" href="mailto:{CONTACT}">{CONTACT}<span aria-hidden="true"> ↗</span></a></section><div class="container support-layout"><nav class="support-app-nav" aria-label="{text(lang, 'アプリを選ぶ', 'Choose your app')}">{''.join(link('#' + p['id'], esc(p['name'][lang])) for p in PRODUCTS)}</nav><div>{sections}</div></div><section class="container info-panel support-checklist"><h2>{text(lang, 'お問い合わせの前に', 'Before you email')}</h2><ul><li>{text(lang, 'アプリ名とバージョン、OSのバージョンをお知らせください。', 'Include the app name and version, and your OS version.')}</li><li>{text(lang, '何をしたときに、何が起きたかを具体的にご記載ください。', 'Describe what you tried and what happened.')}</li><li>{text(lang, '個人情報・顧客メモ・秘密のファイルは送らず、問題を再現できる架空のサンプルをご用意ください。', 'Use a fictional sample to reproduce an issue. Do not send personal data, customer notes, passwords, or confidential files.')}</li></ul></section>'''
    shell(lang, 'support/', text(lang, 'サポート・使い方', 'Support & usage notes') + ' | Yutchi Apps', text(lang, 'Yutchi Appsの公式サポート。アプリ別の使い方・FAQ・トラブルシューティング・プライバシーポリシーとお問い合わせ先。', 'Official Yutchi Apps support. Find app-specific usage notes, troubleshooting, privacy policies, and the support email.'), body, active='support/')
    body = f'''<section class="page-intro container about-intro"><span class="eyebrow">HELLO, I'M YUTCHI</span><h1>{text(lang, '小さな使いやすさを、<br>ひとつずつ。', 'Thoughtful software.<br>One small app at a time.')}</h1></section><section class="container about-content"><img class="developer-avatar" src="{url('assets/yutchi-developer-avatar.png')}" width="160" height="160" alt="{text(lang, 'Yutchiのイラストアイコン', 'Yutchi’s illustrated developer icon')}"><div><h2>Yutchi · Independent developer</h2><p>{text(lang, 'macOS・iOS向けのアプリを個人開発しています。Yutchi Appsは、そのアプリとサポートをひとつにまとめた公式の窓口です。', 'I’m an independent developer creating apps for macOS and iOS. Yutchi Apps is the official home for those apps and their support.')}</p><p>{text(lang, '日々の作業で感じる小さな不便を、シンプルで使いやすい道具に。わかりやすい画面と丁寧な使い心地、可能な場面での端末内処理、維持しやすいソフトウェアを大切にしています。', 'I turn small everyday frustrations into focused, useful tools. I care about clear interfaces, thoughtful interactions, local processing where practical, and software that is straightforward to maintain.')}</p><p>{text(lang, 'Yutchi Appsは個人開発者のブランドです。アプリの販売元など、必要な法的表示は各App Store掲載をご確認ください。', 'Yutchi Apps is an independent developer brand. Required seller and legal identity information is available on each App Store listing.')}</p><a class="text-link" href="mailto:{CONTACT}">{CONTACT} ↗</a></div></section>'''
    shell(lang, 'about/', text(lang, 'Yutchiについて', 'About Yutchi') + ' | Yutchi Apps', text(lang, 'YutchiはmacOSとiOSのアプリを作る個人開発者です。シンプルで役立つ道具と、丁寧な使い心地を大切にしています。', 'Yutchi is an independent macOS and iOS developer who values clear interfaces, practical tools, privacy-conscious design, and thoughtful user experience.'), body, active='about/')
    policy_cards = ''.join(f'<article class="policy-card">{icon(p, 48)}<div><h2>{esc(p["name"][lang])}</h2><p>{esc(p["privacy"][lang])}</p>{link(p["privacy_url"][lang], text(lang, "アプリ固有のポリシーを読む", "Read the app-specific policy") + " ↗", "text-link")}</div></article>' for p in PRODUCTS)
    body = f'''<section class="page-intro container"><span class="eyebrow">PRIVACY, APP BY APP</span><h1>{text(lang, '情報の取り扱いを、<br>わかりやすく。', 'Privacy, explained.<br>App by app.')}</h1><p>{text(lang, 'アプリによって機能と情報の取り扱いが異なります。各アプリのポリシーをご確認ください。', 'Each app has its own features and privacy characteristics. Read the policy for the app you use.')}</p></section><section class="container policy-list">{policy_cards}</section>{privacy_notice(lang, SETTINGS)}'''
    shell(lang, 'privacy-policies/', text(lang, 'プライバシーポリシー一覧', 'Privacy policies') + ' | Yutchi Apps', text(lang, '公開中の各アプリの個別プライバシーポリシーへの公式案内。既存のポリシーURLを維持しています。', 'Find the existing, app-specific privacy policies for Yutchi Apps. Each app’s original privacy policy remains available.'), body, active='privacy-policies/')
    clauses = [('1. 取得する情報', '1. Information handled', '本アプリでは、ユーザーがアプリ内に入力したメモ情報を取り扱います。', 'The app handles the note information users enter in the app.'), ('2. 利用目的', '2. Purpose of use', '取得した情報は、ユーザーが端末上でメモを保存、表示、編集するために利用します。', 'This information is used to save, display, and edit notes on the user’s device.'), ('3. 外部送信について', '3. External transmission', '本アプリは、ユーザーの入力内容を開発者のサーバーへ送信しません。ただし、Apple が提供する課金機能など、OS・ストア提供者による処理が行われる場合があります。', 'The app does not send user-entered content to the developer’s server. Processing by the OS or store provider, such as Apple’s payment features, may occur.'), ('4. 第三者提供', '4. Third-party provision', '本アプリは、ユーザー情報を第三者へ提供しません。', 'The app does not provide user information to third parties.')]
    body = f'''<article class="container legal-page"><a class="breadcrumb" href="{url(route(lang, 'privacy-policies/'))}">← {text(lang, 'ポリシー一覧', 'All privacy policies')}</a><span class="eyebrow">MATANENOTE</span><h1>{text(lang, 'またねノート<br>プライバシーポリシー', 'MataneNote<br>Privacy policy')}</h1><p>{text(lang, 'またねノート（以下、「本アプリ」）は、ユーザー体験の提供に必要な範囲でのみ情報を取り扱います。', 'MataneNote (the “app”) handles information only to the extent necessary to provide the user experience.')}</p>{''.join('<section><h2>' + text(lang, ja, en) + '</h2><p>' + text(lang, jp, eng) + '</p></section>' for ja, en, jp, eng in clauses)}<section><h2>{text(lang, '5. お問い合わせ', '5. Contact')}</h2><p>{text(lang, '本ポリシーに関するお問い合わせは、以下までご連絡ください。', 'For questions about this policy, please contact:')}<br><a href="mailto:{CONTACT}">{CONTACT}</a></p></section><p class="fine">{text(lang, '制定日：2026年3月22日。2026年10月26日：お問い合わせ先のみ変更。情報の取り扱いに関する内容は変更していません。', 'Established March 22, 2026. October 26, 2026: support contact updated only; data handling provisions remain unchanged. This is a translation of the Japanese policy.')}</p></article>'''
    shell(lang, 'privacy/', text(lang, 'またねノート プライバシーポリシー', 'MataneNote privacy policy') + ' | Yutchi Apps', text(lang, 'またねノートの既存プライバシーポリシー。情報の取得・利用目的・外部送信・第三者提供・お問い合わせについて。', 'MataneNote’s privacy policy: information handled, purposes of use, external transmission, third-party provision, and contact information.'), body, active='privacy-policies/')

(ROOT / '.nojekyll').touch()
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(f'<url><loc>{BASE}/{p}</loc></url>' for p in PAGES) + '\n</urlset>\n')
(ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
print(f'Rendered {len(PAGES)} bilingual static pages.')
