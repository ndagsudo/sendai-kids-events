"""
仙台市縄文の森広場 スクレイパー
================================
対象URL: https://www.sendai-jomon.jp/

【HTML構造（確認済み）】
- トップページに体験スケジュールが直接記載
- <font> タグ内に 【体験名】時刻 と日付が <br> 区切りで並ぶ
  例:
    【シカの角のアクセサリー】13時開始
    6月7日（日曜日）、6月27日（土曜日）
    7月4日（土曜日）
- 日付は "X月Y日（曜日）" または "X月Y日（曜日）、X月Y日（曜日）" 形式
- 年は記載なし → 今年または翌年で推定

【スクレイピング方針】
1. <font> 要素を順に走査
2. 【】で囲まれたテキストをイベント名として抽出
3. 続く日付テキストを解析して各日付を個別イベントとして登録
"""

import re
import unicodedata
from datetime import date, timedelta
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseEventScraper, EventData

EVENT_URL  = "https://www.sendai-jomon.jp/"
VENUE_NAME = "仙台市縄文の森広場（宮城野区）"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SendaiKidsBot/1.0)"}

# 定例（毎日）の体験は除外（特定日付がない）
DAILY_KW = re.compile(r"予約不要で体験|毎日|申込不要")


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


class SendaiJomonScraper(BaseEventScraper):
    source_name = "縄文の森広場"
    source_url  = EVENT_URL

    def fetch_events(self) -> List[EventData]:
        resp = requests.get(EVENT_URL, timeout=15, headers=HEADERS)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")

        events = self._extract_events(soup)
        print(f"  [縄文の森] 取得: {len(events)} 件")
        return events

    def _extract_events(self, soup: BeautifulSoup) -> List[EventData]:
        today     = date.today()
        this_year = today.year
        next_year = today.year + 1
        events    = []
        seen      = set()

        # <font> タグの全テキストを収集（連続するブロックをまとめる）
        page_text = soup.get_text("\n", strip=True)
        page_text = _normalize(page_text)

        max_days = timedelta(days=180)   # 半年先までのイベントを対象とする

        # 【体験名】ブロックを正規表現で抽出
        # 【...】の後に時刻・注記（任意）と日付行が続くパターン
        event_block_pat = re.compile(
            r"【([^】]+)】([^\n]*)\n"  # 【体験名】行（G1=名前, G2=注記）
            r"((?:[^\n【]+\n)*)",      # 日付行（次の【】か文末まで）
        )

        date_in_line = re.compile(r"(\d{1,2})月(\d{1,2})日")

        for bm in event_block_pat.finditer(page_text):
            event_name = bm.group(1).strip()
            name_extra = bm.group(2).strip()   # 【体験名】行の注記部分
            date_block = bm.group(3).strip()

            # 定例（毎日・申込不要）体験は除外
            if DAILY_KW.search(date_block) or DAILY_KW.search(event_name) or DAILY_KW.search(name_extra):
                continue
            # "以降" を含む場合は特定日ではなく継続開催 → 除外
            if "以降" in date_block:
                continue
            if not date_in_line.search(date_block):
                continue

            # 日付を全て抽出（コンマ・改行区切り）
            for dm in date_in_line.finditer(date_block):
                month = int(dm.group(1))
                day   = int(dm.group(2))

                try:
                    ev_date = date(this_year, month, day)
                except ValueError:
                    continue
                if ev_date < today:
                    try:
                        ev_date = date(next_year, month, day)
                    except ValueError:
                        continue

                # 半年以上先は表示しない
                if ev_date - today > max_days:
                    continue

                key = (event_name, ev_date)
                if key in seen:
                    continue
                seen.add(key)

                price = self._find_price(event_name)
                summary = self._build_summary(ev_date, event_name, price)

                events.append(EventData(
                    title      = f"縄文体験「{event_name}」",
                    summary    = summary,
                    start_at   = ev_date,
                    end_at     = ev_date,
                    venue_name = VENUE_NAME,
                    url        = EVENT_URL,
                    tags       = ["体験"],
                    source     = self.source_name,
                ))

        events.sort(key=lambda e: e.start_at)

        # 同一体験は「次回の1件」のみ残す（リストが単調にならないよう）
        seen_type: set = set()
        unique = []
        for ev in events:
            if ev.title not in seen_type:
                seen_type.add(ev.title)
                unique.append(ev)
        return unique

    # -------------------------------------------------------
    # ヘルパー
    # -------------------------------------------------------
    @staticmethod
    def _find_price(event_name: str) -> Optional[str]:
        """体験名から料金を推定する（サイト記載の固定価格）"""
        price_map = {
            "縄文土器": "400円（土器(小)）",
            "シカの角のアクセサリー": "300円",
            "勾玉": "300円",
            "石のアクセサリー": "200円",
            "土笛": "200円",
            "石器": "200円",
            "手形・足形": "200円",
            "火おこし": "200円",
            "編布コースター": "200円",
        }
        for kw, price in price_map.items():
            if kw in event_name:
                return price
        return None

    @staticmethod
    def _build_summary(ev_date: date, event_name: str, price: Optional[str]) -> str:
        weekdays = "月火水木金土日"
        wd = weekdays[ev_date.weekday()]
        date_str = f"{ev_date.month}月{ev_date.day}日（{wd}）13時開始"
        parts = [f"{date_str}"]
        if price:
            parts.append(f"材料費：{price}")
        parts.append("予約推奨（電話 022-307-5665）")
        return "。".join(parts) + "。"


if __name__ == "__main__":
    scraper = SendaiJomonScraper()
    events = scraper.fetch_events()
    print(f"\n取得イベント数: {len(events)}")
    for ev in events:
        print(f"  {ev.start_at}  {ev.title}")
        print(f"    {ev.summary}")
