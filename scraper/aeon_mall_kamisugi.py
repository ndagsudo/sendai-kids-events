"""
イオンモール仙台上杉 スクレイパー
===================================
対象URL: https://sendaikamisugi.aeonmall.com/news?tabs=event_news

【HTML構造（確認済み）】
- イベント一覧: <a href="/news/detail/数字?t=event_news">
  - <p class="ttl">  → タイトル
  - <p class="space"> → フロア・会場
  - <p class="date">  → 日付 "2026/06/06(土) 〜 2026/06/07(日)" 形式
  - <div class="text"> → 説明文（省略あり）

【フィルタリング方針】
- 子ども・ファミリー向けキーワードを含むイベントのみ抽出
- 過去イベント（end_at < today）は除外
"""

import re
from datetime import date
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseEventScraper, EventData

BASE_URL   = "https://sendaikamisugi.aeonmall.com"
LIST_URL   = BASE_URL + "/news?tabs=event_news"
VENUE_NAME = "イオンモール仙台上杉（青葉区）"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SendaiKidsBot/1.0)"}

# 子ども・ファミリー向けキーワード（タイトルor説明文に含まれる場合に採用）
_KID_PAT = re.compile(
    r"(子ども|子供|こども|キッズ|ファミリー|小学|幼児|保育|"
    r"あそ|遊び|工作|体験|ワークショップ|"
    r"水遊|水鉄砲|プラレール|トミカ|恐竜|バルーン|"
    r"サッカー|スポーツ|ゲーム大会|コンテスト|発表会|"
    r"アニメ|マジック|縁日|ショー|キャラクター|なりきり)"
)

# 明らかに大人向け・ショッピング系は除外
_ADULT_PAT = re.compile(
    r"(福袋|タイムセール|スタッフ募集|求人|採用|ポイント5倍|"
    r"クーポン配布|パブリックビューイング|健康診断|保険|FIFAワールドカップ|"
    r"快眠|寝具|ヘルス|ウェルネス|睡眠|美容|コスメ|ファッション)"
)


class AeonMallKamisugiScraper(BaseEventScraper):
    source_name = "イオンモール仙台上杉"
    source_url  = LIST_URL

    def fetch_events(self) -> List[EventData]:
        resp = requests.get(LIST_URL, timeout=15, headers=HEADERS)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")

        events = self._parse_list(soup)
        print(f"  [イオンモール] 取得: {len(events)} 件")
        return events

    def _parse_list(self, soup: BeautifulSoup) -> List[EventData]:
        today    = date.today()
        date_pat = re.compile(r"(\d{4})/(\d{2})/(\d{2})")
        events   = []
        seen     = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not re.search(r"/news/detail/\d+", href):
                continue

            title_p = a.find("p", class_="ttl")
            date_p  = a.find("p", class_="date")
            text_d  = a.find("div", class_="text")
            space_p = a.find("p", class_="space")

            if not title_p or not date_p:
                continue  # 日付なし・タイトルなしは除外

            title    = title_p.get_text(strip=True)
            date_str = date_p.get_text(strip=True)
            desc     = text_d.get_text(strip=True)[:300] if text_d else ""
            space    = space_p.get_text(strip=True) if space_p else ""

            # 子ども向けフィルタ
            combined = title + " " + desc
            if not _KID_PAT.search(combined):
                continue
            if _ADULT_PAT.search(title):
                continue

            # 日付パース
            dates_found = []
            for dm in date_pat.finditer(date_str):
                try:
                    d = date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                    dates_found.append(d)
                except ValueError:
                    pass

            if not dates_found:
                continue

            start_at = dates_found[0]
            end_at   = dates_found[-1]

            if end_at < today:
                continue

            # 重複除去
            key = (title, start_at)
            if key in seen:
                continue
            seen.add(key)

            # 絶対URLに変換
            url = BASE_URL + href if href.startswith("/") else href

            summary = self._build_summary(title, space, date_str, desc)

            events.append(EventData(
                title      = title,
                summary    = summary,
                start_at   = start_at,
                end_at     = end_at,
                venue_name = VENUE_NAME,
                url        = url,
                tags       = ["無料"],
                source     = self.source_name,
            ))

        return events

    @staticmethod
    def _build_summary(title: str, space: str, date_str: str, desc: str) -> str:
        """サマリー文を組み立てる"""
        parts = []
        # 日付
        parts.append(f"開催：{date_str}")
        # フロア
        if space:
            parts.append(f"場所：{space}")
        # 説明文（先頭80文字まで）
        if desc:
            # 改行・連続スペースを整理
            desc_clean = re.sub(r"[\s　]+", " ", desc).strip()
            parts.append(desc_clean[:80])
        return "。".join(parts) + "。"


if __name__ == "__main__":
    scraper = AeonMallKamisugiScraper()
    events = scraper.fetch_events()
    print(f"\n取得イベント数: {len(events)}")
    for ev in events:
        print(f"  {ev.start_at}〜{ev.end_at}  [{ev.tags}]  {ev.title}")
        print(f"    {ev.summary[:80]}")
