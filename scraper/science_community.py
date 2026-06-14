"""
学都「仙台・宮城」サイエンスコミュニティ スクレイパー
======================================================
対象URL: https://gakuto-sendaimiyagi.jp/ (要確認)
         https://www.science-day.com/ にリンクがある場合も

【イベントの特徴】
- 顕微鏡体験・川の生き物調査・自然観察など単発イベントが多い
- 東北大学・宮城教育大学の研究者が講師を務めることが多い
- 小学生向け・無料が多い → サイトとの相性が非常に良い
- イベントによって申込方法が異なる（メール・フォーム・当日受付など）

【取得方針】
- イベントカレンダーまたはイベント一覧ページから取得
- 子ども向けのタグが付いているものを優先的に収集する
- 開催場所が仙台市・宮城県内のものに絞る

【実装のヒント】
- サイトのニュース・お知らせ一覧をパースするのが最も簡単
- 日付は「YYYY年MM月DD日」形式が多い
- カテゴリやタグで「子ども向け」「小学生」などのキーワードでフィルタリング
"""

import re
from datetime import date
from typing import List

from scraper.base import BaseEventScraper, EventData

# 子ども向けイベントとして収集するキーワード
CHILD_KEYWORDS = [
    "小学生", "子ども", "こども", "親子", "体験", "工作",
    "観察", "自然", "科学", "実験", "昆虫", "生き物",
]


class ScienceCommunityScraper(BaseEventScraper):
    source_name = "サイエンスコミュニティ"
    source_url  = "https://science-community.jp/"

    # イベント一覧ページ（実際のURLに合わせて変更）
    EVENT_LIST_URL = "https://science-community.jp/events/"

    def fetch_events(self) -> List[EventData]:
        """
        サイエンスコミュニティのイベント情報を収集する。

        TODO:
        1. イベント一覧ページを取得
        2. CHILD_KEYWORDS でフィルタリングして子ども向けのみ抽出
        3. 各イベントの詳細をパース
        """
        # ========== 実装サンプル ==========
        # import requests
        # from bs4 import BeautifulSoup
        #
        # resp = requests.get(self.EVENT_LIST_URL, timeout=15)
        # resp.encoding = resp.apparent_encoding
        # soup = BeautifulSoup(resp.text, "lxml")
        #
        # events = []
        # for item in soup.select(".event-item"):  # ← 実際のセレクターに変更
        #     title   = item.select_one(".event-title").get_text(strip=True)
        #     summary = item.select_one(".event-desc").get_text(strip=True)
        #
        #     # 子ども向けキーワードチェック
        #     combined = title + summary
        #     if not any(kw in combined for kw in CHILD_KEYWORDS):
        #         continue
        #
        #     date_str = item.select_one(".event-date").get_text(strip=True)
        #     m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
        #     if not m:
        #         continue
        #     start_at = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        #
        #     url = item.select_one("a")["href"]
        #     if not url.startswith("http"):
        #         url = self.source_url.rstrip("/") + "/" + url.lstrip("/")
        #
        #     events.append(EventData(
        #         title      = title,
        #         summary    = summary,
        #         start_at   = start_at,
        #         venue_name = item.select_one(".venue").get_text(strip=True),
        #         url        = url,
        #         tags       = ["体験", "科学"],
        #         source     = self.source_name,
        #     ))
        # return events
        # ==================================

        raise NotImplementedError("ScienceCommunityScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = ScienceCommunityScraper()
    scraper.run("data/events.csv")
