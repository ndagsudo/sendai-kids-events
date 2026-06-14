"""
ステンドグラス仙臺ガラス工房 スクレイパー
==========================================
対象URL: 要確認（Google Maps: ステンドグラス仙臺ガラス工房）
電話: 022-725-5178
Google Maps評価: ★5.0

【イベントの特徴】
- ステンドグラス・ガラス体験の予約制ワークショップ
- 評価が5.0と非常に高く、体験の質が高い
- 小学生以上・親子体験として人気
- 仙台市内（青葉区周辺）

【取得方針】
- 公式サイトまたは予約サービス（Airリザーブ等）から日程を取得
- 定期的な空き枠情報がある場合はそれを活用
- 通年開催の場合は3ヶ月先までを1件として登録

【注意事項】
- ガラス使用のため対象年齢の確認が必要
- 要事前予約・有料のため説明文に明記する
"""

import re
from datetime import date, timedelta
from typing import List

from scraper.base import BaseEventScraper, EventData

VENUE_NAME = "ステンドグラス仙臺ガラス工房（青葉区）"


class GlassStudioScraper(BaseEventScraper):
    source_name = "ステンドグラス仙臺ガラス工房"
    # ← 実際の公式URLに変更してください
    source_url  = "https://sendai-glass.com/"

    def fetch_events(self) -> List[EventData]:
        """
        ガラス工房の体験ワークショップ情報を取得する。

        公式サイトが確認できない場合は、通年開催として
        当月〜3ヶ月後までの期間で1件登録する簡易実装でも可。

        TODO:
        1. 公式URLを確認してサイト構造を調査する
        2. 予約カレンダーまたはワークショップ一覧をパース
        3. EventData を生成して返す
        """
        # ========== 簡易実装（公式URL未確認の場合） ==========
        # 通年開催として当月〜3ヶ月後の期間で登録する
        # import requests
        # from bs4 import BeautifulSoup
        #
        # today = date.today()
        # start = today.replace(day=1)
        # # 3ヶ月後の末日を計算
        # future_month = (today.month + 2) % 12 or 12
        # future_year  = today.year + (today.month + 2) // 13
        # end = date(future_year, future_month, 1) + timedelta(days=31)
        # end = end.replace(day=1) - timedelta(days=1)  # 月末日
        #
        # return [EventData(
        #     title      = "ステンドグラス体験ワークショップ",
        #     summary    = (
        #         "色とりどりのガラスを使ってステンドグラス作品を作る体験ワークショップ。"
        #         "小学生以上・親子での参加も歓迎。要事前予約・有料。"
        #     ),
        #     start_at   = start,
        #     end_at     = end,
        #     venue_name = VENUE_NAME,
        #     url        = self.source_url,
        #     tags       = ["体験", "工作", "ものづくり"],
        #     source     = self.source_name,
        # )]
        # =====================================================

        raise NotImplementedError("GlassStudioScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = GlassStudioScraper()
    scraper.run("data/events.csv")
