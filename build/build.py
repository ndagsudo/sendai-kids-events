#!/usr/bin/env python3
"""
仙台・宮城の子どもイベント ビルドスクリプト
============================================
data/events.csv を読み込み、docs/ 以下の HTML を生成します。

使い方:
    cd sendai-kids-events
    python build/build.py

ローカル確認:
    cd docs
    python -m http.server 8000
    → ブラウザで http://localhost:8000 を開く
"""

import csv
import os
import shutil
from datetime import date, timedelta
from html import escape

# ==============================================================
# 設定（GitHubリポジトリに合わせて変更してください）
# ==============================================================
SITE_NAME = "仙台・宮城の子どもイベント"
SITE_DESC = (
    "仙台市・宮城県周辺の小学生・親子向けイベント情報。"
    "今週末に行けるイベントが簡単に探せます。"
)
# 環境変数 SITE_URL があれば優先、なければデフォルト値を使う
SITE_URL = os.environ.get(
    "SITE_URL",
    "https://your-username.github.io/sendai-kids-events"
)

# パス設定（このファイルからの相対位置で計算）
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE  = os.path.join(BASE_DIR, "data", "events.csv")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs")

# 曜日の日本語表記（Python の weekday() は 0=月 … 6=日）
WEEKDAYS_JP = "月火水木金土日"


# ==============================================================
# データ読み込み
# ==============================================================

def load_events():
    """
    events.csv を読み込んで dict のリストで返す。
    終了済みイベントは除外し、開始日順にソートする。
    """
    today  = date.today()
    events = []

    with open(DATA_FILE, encoding="utf-8-sig") as f:  # BOM 付き UTF-8 にも対応
        reader = csv.DictReader(f)
        for row in reader:
            # --- 開始日パース ---
            start_str = row.get("start_at", "").strip()
            if not start_str:
                continue
            try:
                start_at = date.fromisoformat(start_str)
            except ValueError:
                print(f"  [警告] 日付パース失敗: {row.get('title','?')} / {start_str!r}")
                continue

            # --- 終了日パース（空なら start_at と同じ） ---
            end_str = row.get("end_at", "").strip()
            try:
                end_at = date.fromisoformat(end_str) if end_str else start_at
            except ValueError:
                end_at = start_at

            # 終了済みイベントを除外
            if end_at < today:
                continue

            tags    = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]
            summary = row.get("summary", "").strip()
            title   = row.get("title",   "").strip()

            # 「無料」の判定：タグ・サマリー・タイトルのいずれかに含まれればOK
            is_free = any("無料" in s for s in [",".join(tags), summary, title])

            events.append({
                "title":      title,
                "summary":    summary,
                "start_at":   start_at,
                "end_at":     end_at,
                "venue_name": row.get("venue_name", "").strip(),
                "url":        row.get("url", "#").strip(),
                "tags":       tags,
                "source":     row.get("source", "").strip(),
                "is_free":    is_free,
            })

    events.sort(key=lambda e: e["start_at"])
    print(f"  イベント読み込み: {len(events)} 件")
    return events


# ==============================================================
# 日付ユーティリティ
# ==============================================================

def get_weekend():
    """
    「今週末」の土曜・日曜を (saturday, sunday) で返す。
    - 今日が土曜 → 今日と明日
    - 今日が日曜 → 昨日と今日
    - 月〜金    → 次の土日
    """
    today   = date.today()
    weekday = today.weekday()  # 0=月 … 5=土 … 6=日

    if weekday == 5:       # 土曜
        sat = today
        sun = today + timedelta(days=1)
    elif weekday == 6:     # 日曜
        sat = today - timedelta(days=1)
        sun = today
    else:                  # 月〜金
        days_to_sat = 5 - weekday
        sat = today + timedelta(days=days_to_sat)
        sun = sat + timedelta(days=1)

    return sat, sun


def fmt_date(d):
    """date → 「6月7日(日)」形式の文字列"""
    wd = WEEKDAYS_JP[d.weekday()]
    return f"{d.month}月{d.day}日({wd})"


def fmt_period(start_at, end_at):
    """期間を「6月7日(日)」または「5月30日(土)〜6月1日(月)」で返す"""
    if start_at == end_at:
        return fmt_date(start_at)
    return f"{fmt_date(start_at)}〜{fmt_date(end_at)}"


# ==============================================================
# HTML パーツ
# ==============================================================

def render_header(current="index"):
    """共通ヘッダー HTML。current には "index" / "weekend" / "about" / "privacy" を渡す"""
    def cls(page):
        return ' class="active"' if current == page else ""

    return f"""  <header>
    <div class="header-inner">
      <a href="index.html" class="site-title">🎪 {SITE_NAME}</a>
      <nav>
        <a href="index.html"{cls("index")}>すべてのイベント</a>
        <a href="weekend.html"{cls("weekend")}>今週末</a>
        <a href="about.html"{cls("about")}>このサイトについて</a>
        <a href="privacy.html"{cls("privacy")}>プライバシーポリシー</a>
      </nav>
    </div>
  </header>"""


def render_footer():
    """共通フッター HTML"""
    year = date.today().year
    return f"""  <footer>
    <div class="footer-links">
      <a href="index.html">イベント一覧</a>
      <a href="weekend.html">今週末のイベント</a>
      <a href="about.html">このサイトについて</a>
      <a href="privacy.html">プライバシーポリシー</a>
    </div>
    <p>{SITE_NAME} &copy; {year}</p>
    <p class="footer-note">掲載情報は各公式サイトをご確認ください。情報は変更になる場合があります。</p>
  </footer>"""


def _btn_label(raw_url):
    """
    URLの構造からボタンラベルを自動判定する。
    - パスが深い（イベント個別ページと思われる）→「このイベントの詳細・申し込み →」
    - パスが浅い（イベント一覧ページ）          →「公式イベント一覧で確認 →」
    - トップページ                               →「公式サイトで確認 →」
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(raw_url)
        # パスのセグメント数（空文字を除く）
        depth = len([s for s in parsed.path.split("/") if s])
        if depth >= 2:
            # 例: /event_/15037/ や /event/2026/06/post-123/ → 個別イベントページとみなす
            return "このイベントの詳細・申し込み →"
        elif depth >= 1:
            # 例: /event/ /reserve/ /news → イベント一覧・予約ページ
            return "公式イベント一覧で確認 →"
        else:
            # トップページ
            return "公式サイトで確認 →"
    except Exception:
        return "公式サイトで確認 →"


def _btn_note(raw_url):
    """ボタン下に表示する小さな補足テキスト（ドメイン表示）"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(raw_url).netloc
        return f'<span class="btn-domain">{domain}</span>'
    except Exception:
        return ""


def render_card(event, show_weekend_badge=False):
    """イベント1件のカード HTML を返す"""
    # HTML エスケープ（XSS防止）
    title   = escape(event["title"])
    summary = escape(event["summary"])
    venue   = escape(event["venue_name"])
    url     = escape(event["url"])
    period  = escape(fmt_period(event["start_at"], event["end_at"]))

    # data属性（JavaScriptの絞り込みに使う）
    start_iso   = event["start_at"].isoformat()
    end_iso     = event["end_at"].isoformat()
    is_free_str = "true" if event["is_free"] else "false"
    # 検索用テキスト（生の文字列を小文字化してから属性エスケープ）
    search_raw  = f"{event['title']} {event['summary']} {event['venue_name']}".lower()
    search_attr = escape(search_raw)

    # バッジ
    badges = ""
    if show_weekend_badge:
        badges += '<span class="badge badge-weekend">今週末</span>'
    if event["is_free"]:
        badges += '<span class="badge badge-free">無料</span>'
    badge_html = f'<div class="badge-group">{badges}</div>' if badges else ""

    # ボタンラベルとドメイン補足（URLの深さで自動判定）
    btn_label = _btn_label(event["url"])
    btn_note  = _btn_note(event["url"])

    return f"""    <article class="event-card"
               data-start="{start_iso}"
               data-end="{end_iso}"
               data-free="{is_free_str}"
               data-search="{search_attr}">
      <div class="card-top">
        <span class="event-date">📅 {period}</span>
        {badge_html}
      </div>
      <h2 class="event-title">{title}</h2>
      <p class="event-venue">📍 {venue}</p>
      <p class="event-summary">{summary}</p>
      <a href="{url}" target="_blank" rel="noopener noreferrer" class="btn-detail">
        {btn_label}
      </a>
      {btn_note}
    </article>"""


# ==============================================================
# ページ生成
# ==============================================================

def build_index(events, sat, sun):
    """index.html を生成する"""
    print("  index.html ...")

    weekend_label = f"{fmt_date(sat)}・{fmt_date(sun)}"

    # カード HTML（今週末バッジの有無を判定）
    cards = []
    for ev in events:
        is_weekend = ev["start_at"] <= sun and ev["end_at"] >= sat
        cards.append(render_card(ev, show_weekend_badge=is_weekend))
    cards_html = "\n".join(cards) if cards else (
        '<p class="empty-message">現在掲載中のイベントはありません。</p>'
    )

    # JavaScript（絞り込み機能）
    # ※ Python f-string の中で JS の { } は {{ }} と書く
    js = f"""  <script>
    // 今週末の範囲（build.py 実行時の日付で固定）
    var WKND_START = new Date("{sat.isoformat()}");
    var WKND_END   = new Date("{sun.isoformat()}");
    WKND_END.setHours(23, 59, 59);

    var currentFilter = "all";
    var currentSearch = "";

    function applyFilter() {{
      var cards = document.querySelectorAll(".event-card");
      var count = 0;

      cards.forEach(function(card) {{
        var start  = new Date(card.dataset.start);
        var end    = new Date(card.dataset.end);
        end.setHours(23, 59, 59);
        var isFree = card.dataset.free === "true";
        var text   = card.dataset.search || "";

        var show = true;

        // フィルター条件
        if (currentFilter === "weekend") {{
          show = start <= WKND_END && end >= WKND_START;
        }} else if (currentFilter === "free") {{
          show = isFree;
        }}

        // 検索条件（AND）
        if (show && currentSearch) {{
          show = text.indexOf(currentSearch) !== -1;
        }}

        card.classList.toggle("hidden", !show);
        if (show) count++;
      }});

      // 件数更新
      var el = document.getElementById("result-count");
      if (el) el.textContent = count + " 件のイベント";

      // 空メッセージ
      var empty = document.getElementById("empty-message");
      if (empty) empty.style.display = count === 0 ? "block" : "none";
    }}

    // フィルターボタン
    document.querySelectorAll(".filter-btn").forEach(function(btn) {{
      btn.addEventListener("click", function() {{
        var f = btn.dataset.filter;
        // 同じボタンを再クリックで解除
        currentFilter = (currentFilter === f && f !== "all") ? "all" : f;

        document.querySelectorAll(".filter-btn").forEach(function(b) {{
          b.classList.toggle("active", b.dataset.filter === currentFilter);
        }});
        applyFilter();
      }});
    }});

    // 検索ボックス（200ms デバウンス）
    var timer;
    var input = document.getElementById("search-input");
    if (input) {{
      input.addEventListener("input", function() {{
        clearTimeout(timer);
        timer = setTimeout(function() {{
          currentSearch = input.value.trim().toLowerCase();
          applyFilter();
        }}, 200);
      }});
    }}

    // 初期表示
    applyFilter();
  </script>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>仙台・宮城の子どもイベント｜今週末に行けるイベントを探そう</title>
  <meta name="description" content="仙台市・宮城県の子ども・親子向けイベント情報。今週末のおでかけに役立つ無料イベント・体験教室・工作・科学・自然体験など小学生向けイベントを掲載。">
  <meta property="og:title" content="仙台・宮城の子どもイベント">
  <meta property="og:description" content="仙台市・宮城県の子ども・親子向けイベント情報。今週末のおでかけ先を探そう。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/index.html">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:image" content="{SITE_URL}/ogp.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE_URL}/ogp.png">
  <link rel="stylesheet" href="style.css">
  <link rel="canonical" href="{SITE_URL}/index.html">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1651709617297400" crossorigin="anonymous"></script>
</head>
<body>
{render_header("index")}

  <main>
    <div class="container">
      <div class="hero">
        <h1>仙台・宮城の子どもイベント</h1>
        <p>仙台市・宮城県周辺の親子・小学生向けイベントを掲載しています。<br>
           今週末（{weekend_label}）のおでかけにぜひ活用してください。</p>
        <p>科学体験・工作・自然観察・スポーツ・ワークショップなど、<br>
           子どもが楽しめるイベントを毎朝自動更新でお届けします。<br>
           無料イベントも多数掲載中！お気に入りを見つけてください。</p>
      </div>

      <!-- 掲載施設紹介 -->
      <div class="about-sites">
        <h2>掲載中の施設・会場</h2>
        <ul class="venue-list">
          <li><strong>仙台市科学館</strong>（青葉区） — 科学実験・ものづくり体験など、親子で楽しめるイベントを定期開催。</li>
          <li><strong>イオンモール仙台上杉</strong>（青葉区） — 大型ショッピングモール内で開催されるキッズワークショップや体験イベント。</li>
          <li><strong>宮城県こもれびの森 森林科学館</strong>（川崎町） — 豊かな自然の中で竹工作・苔玉作りなど季節の体験教室を実施。</li>
          <li><strong>仙台市縄文の森広場</strong>（太白区） — 縄文時代の暮らしを体験できる施設。土器・石器体験など子ども向け企画が充実。</li>
          <li><strong>JRフルーツパーク仙台あらはま</strong>（若林区） — 果物の収穫体験・農業体験ができる公園型施設。季節ごとのイベントあり。</li>
        </ul>
        <p style="margin-top:8px;">※ 掲載施設は順次追加予定です。</p>
      </div>

      <!-- 検索・絞り込みエリア -->
      <div class="filter-section">
        <div class="search-box">
          <input type="search" id="search-input"
                 placeholder="イベント名・会場名で検索..."
                 aria-label="イベントを検索">
        </div>
        <div class="filter-buttons">
          <button class="filter-btn active" data-filter="all">すべて</button>
          <button class="filter-btn" data-filter="weekend">🗓 今週末（{weekend_label}）</button>
          <button class="filter-btn" data-filter="free">🎁 無料イベント</button>
        </div>
      </div>

      <p class="result-count" id="result-count">{len(events)} 件のイベント</p>

      <!-- イベント一覧 -->
      <div class="events-grid">
{cards_html}
      </div>

      <div id="empty-message" class="empty-message" style="display:none;">
        <p>条件に合うイベントが見つかりませんでした。<br>
           キーワードや絞り込みを変えてお試しください。</p>
      </div>
    </div>
  </main>

{render_footer()}
{js}
</body>
</html>"""

    _write(html, "index.html")


def build_weekend(events, sat, sun):
    """weekend.html を生成する"""
    print("  weekend.html ...")

    weekend_events = [
        ev for ev in events
        if ev["start_at"] <= sun and ev["end_at"] >= sat
    ]
    weekend_label = f"{fmt_date(sat)}・{fmt_date(sun)}"

    if weekend_events:
        cards_html = "\n".join(render_card(ev, show_weekend_badge=True) for ev in weekend_events)
    else:
        cards_html = """      <div class="empty-message">
        <p>今週末のイベントは現在掲載されていません。<br>
           <a href="index.html">すべてのイベント →</a></p>
      </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>今週末のイベント（{weekend_label}）｜仙台・宮城の子どもイベント</title>
  <meta name="description" content="{weekend_label}に仙台・宮城で開催される子ども・親子向けイベント一覧。小学生と行けるおすすめのおでかけスポットをご紹介。">
  <meta property="og:title" content="今週末のイベント｜仙台・宮城の子どもイベント">
  <meta property="og:description" content="{weekend_label}に仙台・宮城で開催される子ども・親子向けイベント。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/weekend.html">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:image" content="{SITE_URL}/ogp.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE_URL}/ogp.png">
  <link rel="stylesheet" href="style.css">
  <link rel="canonical" href="{SITE_URL}/weekend.html">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1651709617297400" crossorigin="anonymous"></script>
</head>
<body>
{render_header("weekend")}

  <main>
    <div class="container">
      <!-- 今週末の説明ブロック -->
      <div class="weekend-info">
        <h1>🗓 今週末のイベント（{weekend_label}）</h1>
        <p>
          仙台・宮城で今週末に開催・参加できる子ども・親子向けイベントをまとめました。<br>
          お子さんと一緒に楽しい週末をお過ごしください。
        </p>
      </div>

      <p class="result-count">{len(weekend_events)} 件のイベント</p>

      <div class="events-grid">
{cards_html}
      </div>

      <div style="text-align:center; margin-top:32px; padding-bottom:8px;">
        <a href="index.html">← すべてのイベントを見る</a>
      </div>
    </div>
  </main>

{render_footer()}
</body>
</html>"""

    _write(html, "weekend.html")


def build_privacy():
    """privacy.html を生成する"""
    print("  privacy.html ...")

    updated = date.today().strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プライバシーポリシー｜仙台・宮城の子どもイベント</title>
  <meta name="description" content="仙台・宮城の子どもイベントサイトのプライバシーポリシー。個人情報・Cookie・Google アナリティクス・AdSense についての説明をご確認ください。">
  <link rel="stylesheet" href="style.css">
  <link rel="canonical" href="{SITE_URL}/privacy.html">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1651709617297400" crossorigin="anonymous"></script>
</head>
<body>
{render_header("privacy")}

  <main>
    <div class="container">
      <div class="privacy-wrap">
        <div class="privacy-card">
          <h1>プライバシーポリシー</h1>
          <p class="updated">最終更新日：{updated}</p>

          <p>「仙台・宮城の子どもイベント」（以下「当サイト」）は、ユーザーのプライバシーを尊重し、
          個人情報の保護に努めます。本ページでは当サイトにおける情報の取り扱いについてご説明します。</p>

          <h2>1. 収集する情報について</h2>
          <p>当サイトは会員登録・お問い合わせフォームなどの機能を持たず、ユーザーから直接個人情報を
          収集することはありません。ただし、下記のツールにより閲覧情報が自動的に取得される場合があります。</p>

          <h2>2. アクセス解析（Google アナリティクス）</h2>
          <p>当サイトはサービス向上を目的として <strong>Google アナリティクス</strong> を使用しています
          （または使用する予定があります）。Google アナリティクスは Cookie を使用してアクセス情報を収集しますが、
          個人を特定する情報は含みません。</p>
          <ul>
            <li>Google のプライバシーポリシー：
              <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">policies.google.com/privacy</a>
            </li>
            <li>Cookie の無効化（オプトアウト）：
              <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Google アナリティクス オプトアウト アドオン</a>
            </li>
          </ul>

          <h2>3. 広告（Google AdSense）</h2>
          <p>当サイトでは <strong>Google AdSense</strong> による広告を掲載しています
          （または掲載する予定があります）。Google などの第三者配信事業者は Cookie を使用し、
          ユーザーの過去のアクセス情報に基づいて広告を配信することがあります。</p>
          <p>広告のカスタマイズを無効にする場合は
          <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">広告設定ページ</a>
          をご確認ください。</p>

          <h2>4. Cookie について</h2>
          <p>当サイト自体は Cookie を直接発行しませんが、上記の Google サービスが Cookie を使用する場合があります。
          ブラウザの設定から Cookie を無効にすることも可能ですが、一部の広告・機能が正常に動作しない場合があります。</p>

          <h2>5. 掲載情報について</h2>
          <p>掲載イベント情報は各施設・主催者の公式サイトから収集した公開情報をもとにしています。
          内容・日程は変更または中止になる場合があります。最新情報は必ず各公式サイトでご確認ください。</p>

          <h2>6. 免責事項</h2>
          <p>当サイトからリンクしている外部サイトのコンテンツについて当サイトは責任を負いません。
          掲載情報の利用によって生じたいかなる損害についても責任を負いかねますのでご了承ください。</p>

          <h2>7. プライバシーポリシーの変更</h2>
          <p>本ポリシーは法令改正・サービス変更等に応じて予告なく変更することがあります。
          変更後は当サイトに掲載した時点から効力を生じます。</p>

          <h2>8. お問い合わせ</h2>
          <p>本ポリシーに関するお問い合わせは、当サイトの GitHub リポジトリの Issue ページよりお願いします。</p>
        </div>
      </div>
    </div>
  </main>

{render_footer()}
</body>
</html>"""

    _write(html, "privacy.html")


def build_about():
    """about.html を生成する"""
    print("  about.html ...")

    updated = date.today().strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>このサイトについて｜仙台・宮城の子どもイベント</title>
  <meta name="description" content="「仙台・宮城の子どもイベント」は、仙台市・宮城県の親子・小学生向けイベント情報を毎日自動更新で掲載するサイトです。無料体験・工作・科学・自然体験など幅広いジャンルのイベントを紹介しています。">
  <meta property="og:title" content="このサイトについて｜仙台・宮城の子どもイベント">
  <meta property="og:description" content="仙台市・宮城県の親子・小学生向けイベント情報を毎日自動更新で掲載。">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/about.html">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:image" content="{SITE_URL}/ogp.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{SITE_URL}/ogp.png">
  <link rel="stylesheet" href="style.css">
  <link rel="canonical" href="{SITE_URL}/about.html">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1651709617297400" crossorigin="anonymous"></script>
</head>
<body>
{render_header("about")}

  <main>
    <div class="container">
      <div class="privacy-wrap">
        <div class="privacy-card">
          <h1>このサイトについて</h1>
          <p class="updated">最終更新日：{updated}</p>

          <h2>サイトの目的</h2>
          <p>「仙台・宮城の子どもイベント」は、仙台市・宮城県内で開催される<strong>子ども・親子向けのイベント情報</strong>をまとめて確認できるサイトです。</p>
          <p>「今週末、子どもと一緒にどこかに行きたいけれど、どんなイベントがあるか分からない」という保護者の方に向けて、複数の施設・会場のイベント情報を一か所で確認できるよう作りました。</p>
          <p>科学体験・工作教室・自然観察・スポーツ体験・縄文文化体験など、幅広いジャンルのイベントを掲載しています。<strong>無料で参加できるイベント</strong>も多数紹介しています。</p>

          <h2>掲載エリア</h2>
          <p>仙台市内（青葉区・太白区・若林区など）および宮城県内の施設・会場を中心に掲載しています。対象施設は順次拡大予定です。</p>

          <h2>掲載中の施設・会場</h2>
          <ul>
            <li>
              <strong>仙台市科学館</strong>（青葉区）<br>
              科学実験・ものづくりワークショップ・天文観察など、子どもが科学に親しめるイベントを定期的に開催しています。小学生から楽しめるプログラムが充実しており、夏休み・冬休みなどの長期休暇中はとくに多くのイベントが企画されます。
            </li>
            <li>
              <strong>イオンモール仙台上杉</strong>（青葉区）<br>
              仙台市青葉区にある大型ショッピングモールで、週末を中心にキッズ向けワークショップや体験イベントが開催されます。雨の日でも屋内で楽しめるため、天候を問わず参加できるのが魅力です。
            </li>
            <li>
              <strong>宮城県こもれびの森 森林科学館</strong>（川崎町）<br>
              宮城県の豊かな森林の中にある体験施設です。竹を使った工作・苔玉作り・木工体験など、自然素材を活かした季節のイベントが人気です。仙台市内から車で約40分ほどの距離にあります。
            </li>
            <li>
              <strong>仙台市縄文の森広場</strong>（太白区）<br>
              縄文時代の竪穴住居が復元された歴史体験施設です。土器づくり・火おこし体験・勾玉づくりなど、教科書では学べないリアルな縄文文化を体験できます。子どもの歴史への興味を育てるきっかけになります。
            </li>
            <li>
              <strong>JRフルーツパーク仙台あらはま</strong>（若林区）<br>
              仙台市若林区にある農業体験型公園です。いちご・ぶどう・りんごなど季節の果物の収穫体験ができるほか、野菜の収穫・農業体験イベントも開催されます。食農教育の場として家族連れに人気です。
            </li>
          </ul>

          <h2>更新頻度</h2>
          <p>掲載情報は<strong>毎朝6時に自動更新</strong>されます。各施設の公式サイトから最新のイベント情報を収集し、過去のイベントは自動的に削除されます。常に「これから参加できるイベント」のみが表示される仕組みです。</p>

          <h2>サイトの使い方</h2>
          <ol>
            <li><strong>「今週末」ボタン</strong>で今週の土日に開催されるイベントだけを絞り込めます。</li>
            <li><strong>「無料イベント」ボタン</strong>で参加費無料のイベントだけを表示できます。</li>
            <li><strong>キーワード検索</strong>でイベント名・会場名から探すことができます。</li>
            <li>各イベントカードの「詳細・申し込み」ボタンから公式サイトで詳細を確認できます。</li>
          </ol>

          <h2>注意事項</h2>
          <ul>
            <li>掲載情報は各施設の公式サイトをもとに収集していますが、内容・日程・料金は変更または中止になる場合があります。参加前に必ず各公式サイトをご確認ください。</li>
            <li>申し込みが必要なイベントがあります。定員に達している場合がありますのでご注意ください。</li>
            <li>掲載漏れや情報の誤りがある場合はご容赦ください。</li>
          </ul>

          <h2>運営について</h2>
          <p>本サイトは仙台・宮城在住の個人が運営しています。子どもと一緒に地域のイベントをもっと活用してほしいという思いで作りました。掲載施設の拡充やサイトの改善を随時進めています。</p>
          <p>ご意見・ご要望は <a href="https://github.com/ndagsudo/sendai-kids-events/issues" target="_blank" rel="noopener">GitHubのIssueページ</a> よりお寄せください。</p>
        </div>
      </div>
    </div>
  </main>

{render_footer()}
</body>
</html>"""

    _write(html, "about.html")


def build_sitemap():
    """sitemap.xml を生成する"""
    print("  sitemap.xml ...")

    today = date.today().isoformat()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/index.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{SITE_URL}/weekend.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{SITE_URL}/about.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{SITE_URL}/privacy.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>"""

    _write(xml, "sitemap.xml")


def build_robots():
    """robots.txt を生成する"""
    print("  robots.txt ...")
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    _write(content, "robots.txt")


# ==============================================================
# ユーティリティ
# ==============================================================

def _write(content, filename):
    """OUTPUT_DIR にファイルを書き出す"""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"    書き出し完了: {path}")


def copy_static():
    """static/ のファイルを docs/ にコピーする"""
    if not os.path.isdir(STATIC_DIR):
        print("  [警告] static/ ディレクトリが見つかりません")
        return
    for name in os.listdir(STATIC_DIR):
        src = os.path.join(STATIC_DIR, name)
        dst = os.path.join(OUTPUT_DIR, name)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  コピー: {name}")


# ==============================================================
# メイン処理
# ==============================================================

def main():
    print("=" * 52)
    print(f"  {SITE_NAME} ビルド開始")
    print("=" * 52)

    # 出力ディレクトリを作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # イベントデータを読み込む
    print("\n[1/6] イベントデータ読み込み")
    events = load_events()

    # 今週末の範囲を取得
    sat, sun = get_weekend()
    print(f"  今週末: {fmt_date(sat)}・{fmt_date(sun)}")

    # HTML ページを生成
    print("\n[2/6] index.html")
    build_index(events, sat, sun)

    print("\n[3/6] weekend.html")
    build_weekend(events, sat, sun)

    print("\n[4/6] privacy.html")
    build_privacy()

    print("\n[5/6] about.html")
    build_about()

    print("\n[7/7] sitemap.xml / robots.txt")
    build_sitemap()
    build_robots()

    print("\n[7/7] 静的ファイルのコピー")
    copy_static()

    print("\n" + "=" * 52)
    print("  ビルド完了！")
    print(f"  出力先: {OUTPUT_DIR}")
    print("  確認方法: cd docs && python -m http.server 8000")
    print("=" * 52)


if __name__ == "__main__":
    main()
