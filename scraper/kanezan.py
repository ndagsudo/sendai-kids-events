"""
鐘崎総本店 笹かま館 スクレイパー
====================================
対象URL: https://www.kanezan.co.jp/
電話: 022-238-7170

【イベントの特徴】
- 笹かまぼこの手焼き体験が有名（「食＋体験」）
- 予約制で通年開催（季節限定プログラムあり）
- 家族連れに人気が高い
- 仙台土産としても有名なため観光客も多い
- 有料だが金額は手ごろ（1人 数百円〜）

【取得方針】
- 体験予約ページに料金・時間・予約方法が記載されている
- 基本的に通年開催のため「イベント」ではなく「体験プログラム」として登録
- 開始・終了日は月単位（例: 2026-06-01〜2026-08-31）で設定するのが適切

【注意事項】
- 閑散期や臨時休業があるため、公式サイトへのリンクを必ず案内する
- 予約なしでは体験できない場合があるため説明文に「要事前予約」を記載
"""

import re
from datetime import date
from typing import List

from scraper.base import BaseEventScraper, EventData

VENUE_NAME = "鐘崎総本店 笹かま館（若林区）"


class KanezanScraper(BaseEventScraper):
    source_name = "鐘崎笹かま館"
    source_url  = "https://www.kanezaki.co.jp/shop/belle_factory/"

    # 体験予約ページ（実際のURLに合わせて変更）
    EXPERIENCE_PAGE = "https://www.kanezaki.co.jp/shop/belle_factory/kanezakiya.html"

    def fetch_events(self) -> List[EventData]:
        """
        笹かま館の体験プログラムを取得する。

        通年開催の場合、当月〜3ヶ月後を開催期間として1件のEventDataを返す。

        TODO:
        1. EXPERIENCE_PAGE の内容を取得
        2. 体験プログラムの内容・料金・予約方法を抽出
        3. 開催期間を設定して EventData を返す
        """
        # ========== 実装サンプル ==========
        # import requests
        # from bs4 import BeautifulSoup
        # from datetime import date, timedelta
        #
        # resp = requests.get(self.EXPERIENCE_PAGE, timeout=15)
        # resp.encoding = resp.apparent_encoding
        # soup = BeautifulSoup(resp.text, "lxml")
        #
        # # 体験プログラムの説明文を取得
        # desc = soup.select_one(".experience-desc")
        # summary = desc.get_text(strip=True)[:120] if desc else (
        #     "自分で練ったかまぼこを炭火で焼く、仙台ならではの食育体験。"
        #     "家族連れに大人気。要事前予約・有料。"
        # )
        #
        # today   = date.today()
        # # 当月初日〜3ヶ月後の月末を開催期間とする
        # start   = today.replace(day=1)
        # end_m   = (today.month + 2) % 12 or 12
        # end_y   = today.year + (today.month + 2) // 13
        # end     = date(end_y, end_m, 1) - timedelta(days=1)
        #
        # return [EventData(
        #     title      = "鐘崎笹かま館 笹かまぼこ手焼き体験",
        #     summary    = summary,
        #     start_at   = start,
        #     end_at     = end,
        #     venue_name = VENUE_NAME,
        #     url        = self.source_url,
        #     tags       = ["体験", "食育"],
        #     source     = self.source_name,
        # )]
        # ==================================

        raise NotImplementedError("KanezanScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = KanezanScraper()
    scraper.run("data/events.csv")
