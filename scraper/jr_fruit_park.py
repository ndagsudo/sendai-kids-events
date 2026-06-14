"""
JRフルーツパーク仙台あらはま スクレイパー
==========================================
対象URL: https://stbl-fruit-farm.jp/arahama/news/

【HTML構造（確認済み）】
- WordPress ブログ形式
- <article> 要素に各ニュースが入る
  - <h3><a href="..."> → タイトル + 詳細URL
  - <p class="date">2026年05月18日</p> → 投稿日（≠ イベント開催日）
  - <section class="body"> → 本文（イベント日程・料金が記載）
- 詳細ページに 【開催期間】 "YYYY年M月D日(曜)～M月下旬" 形式の日程が含まれる

【スクレイピング方針】
1. ニュース一覧から子ども向けイベント記事を絞り込む
2. 詳細ページを取得して開催期間・料金を抽出
3. "8月中旬" などのあいまい表現は日付に変換（上旬=5日・中旬=15日・下旬=25日）
"""

import re
import time
from datetime import date
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseEventScraper, EventData

BASE_URL   = "https://stbl-fruit-farm.jp"
NEWS_URL   = BASE_URL + "/arahama/news/"
VENUE_NAME = "JRフルーツパーク仙台あらはま（若林区）"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SendaiKidsBot/1.0)"}

# 子ども向け体験イベントのキーワード
_KID_PAT = re.compile(
    r"(狩り|摘み|収穫|体験|スタンプ|こども|子ども|ファミリー|"
    r"さつまいも|ブルーベリー|いちご|りんご|ぶどう|みかん|もも|梨|)"
)


class JrFruitParkScraper(BaseEventScraper):
    source_name = "JRフルーツパーク"
    source_url  = NEWS_URL

    def fetch_events(self) -> List[EventData]:
        try:
            resp = requests.get(NEWS_URL, timeout=15, headers=HEADERS)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            print(f"  [フルーツパーク] 取得エラー: {e}")
            return []

        events = []
        today = date.today()

        for article in soup.find_all("article"):
            # タイトルとリンクを取得
            h3 = article.find("h3")
            if not h3:
                continue
            a = h3.find("a")
            if not a:
                continue
            title_raw = a.get_text(strip=True)
            detail_url = a.get("href", "")
            if not detail_url.startswith("http"):
                detail_url = BASE_URL + detail_url

            # 子ども向けキーワードチェック（タイトルに含まれる場合のみ詳細を取得）
            if not _KID_PAT.search(title_raw):
                continue

            # 詳細ページから開催期間・料金を取得
            ev = self._parse_detail(detail_url, title_raw, today)
            if ev:
                events.append(ev)
            time.sleep(0.5)

        print(f"  [フルーツパーク] 取得: {len(events)} 件")
        return events

    def _parse_detail(self, url: str, title_raw: str, today: date) -> Optional[EventData]:
        """詳細ページをパースして EventData を生成する"""
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            print(f"    取得エラー {url}: {e}")
            return None

        article = soup.find("article") or soup.find("main") or soup.body
        if not article:
            return None
        # <section class="body"> のみ対象（ヘッダーの投稿日を除外するため）
        body_sec = article.find("section", class_="body") or article
        text = body_sec.get_text("\n", strip=True)

        # 開催期間を探す（複数パターン対応）
        start_at, end_at = self._parse_period(text)
        if not start_at:
            return None

        # 期間が完全に過去ならスキップ
        if end_at < today:
            return None

        # タイトルを整形（"ご予約受付スタート！" などの付加文を削除）
        title = re.sub(r"[　\s]*(ご予約|受付|スタート|開始|について)[^！!]*[！!]?\s*$", "", title_raw).strip()
        if not title:
            title = title_raw

        # 料金を取得
        price = self._find_price(text)

        summary = self._build_summary(text, start_at, end_at, price)

        return EventData(
            title      = title,
            summary    = summary,
            start_at   = start_at,
            end_at     = end_at,
            venue_name = VENUE_NAME,
            url        = url,
            tags       = ["体験"],
            source     = self.source_name,
        )

    # -------------------------------------------------------
    # ヘルパー
    # -------------------------------------------------------
    @staticmethod
    def _parse_period(text: str) -> Tuple[Optional[date], Optional[date]]:
        """
        本文から開催期間の start_at / end_at を取得する。

        対応例:
          "2026年6月27日(土)～8月中旬"
          "2026年6月6日(土),7日(日)"
          "2026年7月1日（水）〜 2026年8月31日（火）"
        """
        # 完全形 "YYYY年M月D日"
        full_pat = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
        # 月のみ+旬 "M月上旬/中旬/下旬"
        jun_pat  = re.compile(r"(\d{1,2})月(上旬|中旬|下旬)")

        dates = []
        for m in full_pat.finditer(text):
            try:
                dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                pass

        if not dates:
            return None, None

        # 開始日 = 最初の日付
        start_at = dates[0]

        # 終了日: 複数の完全日付があれば最後の日付
        if len(dates) >= 2:
            end_at = dates[-1]
        else:
            # "～M月中旬" のような末尾表現を探す
            # テキスト中で start_at の後に来る旬表現
            end_at = start_at  # デフォルト: 同日
            for jm in jun_pat.finditer(text):
                month = int(jm.group(1))
                jun   = jm.group(2)
                day   = {"上旬": 5, "中旬": 15, "下旬": 25}[jun]
                # 基準年は start_at と同年（またはそれ以降）
                year = start_at.year
                try:
                    candidate = date(year, month, day)
                    if candidate >= start_at:
                        end_at = candidate
                except ValueError:
                    pass

        return start_at, end_at

    @staticmethod
    def _find_price(text: str) -> Optional[str]:
        """本文から代表的な料金を探す"""
        # 子ども料金 or 入場料など
        child_pat = re.compile(r"子ども[　\s]*[\d,，]+円")
        m = child_pat.search(text)
        if m:
            return m.group(0).replace("　", "").replace(" ", "")
        # 一般料金
        price_pat = re.compile(r"[\d,，]+円")
        m = price_pat.search(text)
        return m.group(0) if m else None

    @staticmethod
    def _build_summary(text: str, start_at: date, end_at: date, price: Optional[str]) -> str:
        """サマリー文を組み立てる"""
        weekdays = "月火水木金土日"
        s_wd = weekdays[start_at.weekday()]
        e_wd = weekdays[end_at.weekday()]
        if start_at == end_at:
            date_str = f"{start_at.month}月{start_at.day}日（{s_wd}）"
        else:
            date_str = f"{start_at.month}月{start_at.day}日（{s_wd}）〜{end_at.month}月{end_at.day}日（{e_wd}）"
        parts = [f"開催期間：{date_str}"]
        if price:
            parts.append(f"料金（子ども）：{price}")
        # 受付時間があれば追加
        time_m = re.search(r"\d{1,2}[:：]\d{2}[〜～〜-]\d{1,2}[:：]\d{2}", text)
        if time_m:
            parts.append(f"受付：{time_m.group(0)}")
        parts.append("要予約（公式サイトから）")
        return "。".join(parts) + "。"


if __name__ == "__main__":
    scraper = JrFruitParkScraper()
    events = scraper.fetch_events()
    print(f"\n取得イベント数: {len(events)}")
    for ev in events:
        print(f"  {ev.start_at}〜{ev.end_at}  [{ev.tags}]  {ev.title}")
        print(f"    {ev.summary}")
