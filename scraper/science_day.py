"""
学都「仙台・宮城」サイエンス・デイ スクレイパー
================================================
対象URL: https://www.science-day.com/
主催: 東北大学 / 宮城教育大学 など

【イベントの特徴】
- 年1回、7月中旬〜下旬に東北大学川内北キャンパスで開催される大規模科学イベント
- 100以上の体験ブースが出展する体験型・対話型の科学フェスティバル
- 入場無料・申込不要（一部ブースは事前申込あり）
- サイトコンセプトと非常に相性が良いイベント

【取得方針】
- 毎年1件の大型イベントを追加する形でOK
- 詳細ページ（各ブース）は多数あるが、イベント全体を1件として登録する
- 開催日程はトップページまたはニュースページで確認できる

【実装のヒント】
- トップページに「開催日: ○月○日（○）」の記載がある
- 会場・時間・参加費（無料）は毎年ほぼ同じ
"""

import re
from datetime import date
from typing import List

from scraper.base import BaseEventScraper, EventData


class ScienceDayScraper(BaseEventScraper):
    source_name = "サイエンス・デイ"
    source_url  = "https://www.science-day.com/"

    def fetch_events(self) -> List[EventData]:
        """
        サイエンス・デイの開催情報を取得する。
        年1回のイベントなので、毎年1件のEventDataを返す。

        TODO:
        1. トップページから今年の開催日を取得
        2. EventData を1件作成して返す
        """
        # ========== 実装サンプル ==========
        # import requests
        # from bs4 import BeautifulSoup
        #
        # resp = requests.get(self.source_url, timeout=15)
        # resp.encoding = resp.apparent_encoding
        # soup = BeautifulSoup(resp.text, "lxml")
        #
        # # トップページの開催日テキストを探す（例: "2026年7月19日（日）"）
        # text = soup.get_text()
        # m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
        # if not m:
        #     print("  開催日が見つかりませんでした")
        #     return []
        #
        # event_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # year = event_date.year
        #
        # return [EventData(
        #     title      = f"学都「仙台・宮城」サイエンス・デイ{year}",
        #     summary    = (
        #         "東北大学・宮城教育大学などが共同開催する体験型科学の祭典。"
        #         "100以上の科学実験・工作ブースに自由参加できます。入場無料。"
        #     ),
        #     start_at   = event_date,
        #     venue_name = "東北大学川内北キャンパス（青葉区）",
        #     url        = self.source_url,
        #     tags       = ["無料", "体験", "科学"],
        #     source     = self.source_name,
        # )]
        # ==================================

        raise NotImplementedError("ScienceDayScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = ScienceDayScraper()
    scraper.run("data/events.csv")
