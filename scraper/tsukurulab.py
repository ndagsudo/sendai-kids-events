"""
つくるラボ 仙台トラストシティ スクレイパー
==========================================
対象URL: https://tsukurulab.com/ (要確認)
所在地: 仙台トラストシティ内（青葉区）

【イベントの特徴】
- キャンドル・クラフト・工作系の単発ワークショップが多い
- 「親が子に体験させたいタイプ」のイベントと非常に相性良い
- 要予約・有料（材料費込みのことが多い）
- 単発イベントが多く、定期的に新しいテーマが追加される

【取得方針】
- ワークショップ一覧ページから未来日程のもののみを取得
- 日程・内容・定員・料金を抽出する
- SNS（Instagram/Twitter）でも告知している場合あり

【実装のヒント】
- Instagramのスクレイピングは規約に反する場合があるので公式サイトを使う
- ワークショップページに日程リストがある場合が多い
"""

import re
from datetime import date
from typing import List

from scraper.base import BaseEventScraper, EventData

VENUE_NAME = "つくるラボ 仙台トラストシティ（青葉区）"


class TsukuruLabScraper(BaseEventScraper):
    source_name = "つくるラボ"
    source_url  = "https://tsukurulab.com/sendai/"

    # ワークショップ一覧ページ（実際のURLに合わせて変更）
    WORKSHOP_URL = "https://tsukurulab.com/sendai/workshop/"

    def fetch_events(self) -> List[EventData]:
        """
        つくるラボのワークショップ一覧を取得する。

        TODO:
        1. WORKSHOP_URL からワークショップ一覧を取得
        2. 今日以降の開催日程のみを抽出
        3. 各ワークショップを EventData として返す
        """
        # ========== 実装サンプル ==========
        # import requests
        # from bs4 import BeautifulSoup
        #
        # resp = requests.get(self.WORKSHOP_URL, timeout=15)
        # resp.encoding = resp.apparent_encoding
        # soup = BeautifulSoup(resp.text, "lxml")
        #
        # events = []
        # today = date.today()
        #
        # for item in soup.select(".workshop-item"):
        #     title    = item.select_one("h3").get_text(strip=True)
        #     date_str = item.select_one(".date").get_text(strip=True)
        #     summary  = item.select_one(".desc").get_text(strip=True)
        #     url      = item.select_one("a")["href"]
        #
        #     m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
        #     if not m:
        #         continue
        #     start_at = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        #     if start_at < today:
        #         continue  # 過去のイベントはスキップ
        #
        #     events.append(EventData(
        #         title      = title,
        #         summary    = summary,
        #         start_at   = start_at,
        #         venue_name = VENUE_NAME,
        #         url        = url if url.startswith("http") else self.source_url + url,
        #         tags       = ["体験", "工作"],
        #         source     = self.source_name,
        #     ))
        # return events
        # ==================================

        raise NotImplementedError("TsukuruLabScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = TsukuruLabScraper()
    scraper.run("data/events.csv")
