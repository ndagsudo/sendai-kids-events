"""
はなゆう仙台（HANAYU）陶芸体験 スクレイパー
============================================
所在地: 仙台市内（要確認）
電話: 022-739-7367
Google Maps評価: ★3.3

【イベントの特徴】
- 陶芸体験教室（親子体験需要あり）
- 予約制で随時開催
- 仙台市内では貴重な陶芸体験スポット

【取得方針】
- 公式サイトまたは予約ページから体験スケジュールを取得
- 親子向けの体験コースに絞って掲載する
- 通年開催の場合は期間を設定して1件として登録

【注意事項】
- 年齢制限（小学生以上など）の確認が必要
- 要事前予約・有料のため説明文に必ず明記
- Google Maps評価が3.3なので、掲載判断は要検討（体験の質を確認推奨）
"""

import re
from datetime import date, timedelta
from typing import List

from scraper.base import BaseEventScraper, EventData

VENUE_NAME = "はなゆう仙台（仙台市内）"


class PotteryHanayuScraper(BaseEventScraper):
    source_name = "はなゆう仙台"
    # ← 実際の公式URLに変更してください
    source_url  = "https://hanayu-sendai.com/"

    def fetch_events(self) -> List[EventData]:
        """
        はなゆう仙台の陶芸体験情報を取得する。

        TODO:
        1. 公式URLを確認してサイト構造を調査する
        2. 体験メニュー・料金・開催スケジュールをパース
        3. 親子向けのコースを EventData として返す
        """
        # ========== 簡易実装例 ==========
        # from datetime import date, timedelta
        #
        # today = date.today()
        # start = today.replace(day=1)
        # # 2ヶ月後の末日まで
        # future = today.month + 1
        # fyear  = today.year + future // 13
        # fmonth = future % 12 or 12
        # end = date(fyear, fmonth, 1) + timedelta(days=31)
        # end = end.replace(day=1) - timedelta(days=1)
        #
        # return [EventData(
        #     title      = "はなゆう仙台 親子陶芸体験",
        #     summary    = (
        #         "手びねりや電動ろくろで世界にひとつだけの陶器を作る陶芸体験。"
        #         "小学生以上の親子でお楽しみいただけます。要事前予約・有料。"
        #     ),
        #     start_at   = start,
        #     end_at     = end,
        #     venue_name = VENUE_NAME,
        #     url        = self.source_url,
        #     tags       = ["体験", "工作", "ものづくり"],
        #     source     = self.source_name,
        # )]
        # =================================

        raise NotImplementedError("PotteryHanayuScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = PotteryHanayuScraper()
    scraper.run("data/events.csv")
