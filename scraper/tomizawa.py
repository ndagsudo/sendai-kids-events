"""
仙台市富沢遺跡保存館 スクレイパー
====================================
対象URL: https://www.city.sendai.jp/hakubutsukan/tomizawa/
所在地: 宮城野区 / 太白区（要確認）
電話: 022-246-9153

【イベントの特徴】
- 縄文時代・旧石器時代の遺跡が地下に保存された博物館
- 土器・石器のレプリカに触れる体験学習が充実
- 小学校の社会・歴史学習と連携したプログラムが多い
- 入館無料または低価格
- 「地底のミュージアム」として学校需要が高い

【取得方針】
- 仙台市博物館ネットワークのサイトからイベントを取得
- 「体験」「学習」「こども」のカテゴリを優先
- 年間スケジュールがPDFで公開されている場合あり

【実装のヒント】
- 仙台市のサイト構成は比較的統一されている
- イベントURLは https://www.city.sendai.jp/ 以下にある
"""

import re
from datetime import date
from typing import List

from scraper.base import BaseEventScraper, EventData

VENUE_NAME = "仙台市富沢遺跡保存館（太白区）"


class TomizawaScraper(BaseEventScraper):
    source_name = "富沢遺跡保存館"
    # 正式名称：地底の森ミュージアム 仙台市富沢遺跡保存館
    source_url  = "https://ssbj.jp/facility/t-forest/"

    # イベント情報ページ（実際のURLに合わせて変更）
    EVENT_URL = "https://ssbj.jp/facility/t-forest/"

    def fetch_events(self) -> List[EventData]:
        """
        富沢遺跡保存館のイベント情報を収集する。

        TODO:
        1. EVENT_URL を requests で取得
        2. イベントリストをパース
        3. 縄文・体験・工作系イベントのみ抽出
        """
        # ========== 実装サンプル ==========
        # import requests
        # from bs4 import BeautifulSoup
        #
        # resp = requests.get(self.EVENT_URL, timeout=15)
        # resp.encoding = resp.apparent_encoding
        # soup = BeautifulSoup(resp.text, "lxml")
        #
        # events = []
        # for item in soup.select(".event-list li"):
        #     text  = item.get_text(strip=True)
        #     link  = item.find("a")
        #     title = link.get_text(strip=True) if link else text[:30]
        #     url   = link["href"] if link else self.source_url
        #     if not url.startswith("http"):
        #         url = "https://www.city.sendai.jp" + url
        #
        #     m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
        #     if not m:
        #         continue
        #     start_at = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        #
        #     events.append(EventData(
        #         title      = title,
        #         summary    = "縄文・旧石器時代の遺跡で本物の体験学習ができます。",
        #         start_at   = start_at,
        #         venue_name = VENUE_NAME,
        #         url        = url,
        #         tags       = ["無料", "体験", "歴史"],
        #         source     = self.source_name,
        #     ))
        # return events
        # ==================================

        raise NotImplementedError("TomizawaScraper.fetch_events() を実装してください。")


if __name__ == "__main__":
    scraper = TomizawaScraper()
    scraper.run("data/events.csv")
