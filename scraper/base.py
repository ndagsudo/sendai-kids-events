"""
スクレイパー基底クラス
======================
各施設のイベントを自動収集するスクレイパーはこのクラスを継承して作ります。

【使い方の例】
    from scraper.base import BaseEventScraper, EventData
    from datetime import date

    class ScienceMuseumScraper(BaseEventScraper):
        source_name = "仙台市科学館"
        source_url  = "https://www.sendai-kagakukan.jp/"

        def fetch_events(self):
            # requests + BeautifulSoup でページを取得してパース
            events = []
            # ...
            events.append(EventData(
                title      = "工作教室",
                summary    = "木工作品を作ろう",
                start_at   = date(2026, 7, 5),
                venue_name = "仙台市科学館",
                url        = "https://...",
                tags       = ["無料", "体験"],
            ))
            return events

    # 実行
    if __name__ == "__main__":
        scraper = ScienceMuseumScraper()
        scraper.run("data/events.csv")
"""

import csv
import os
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class EventData:
    """イベント1件を表すデータクラス"""
    title:      str            # イベント名（必須）
    summary:    str            # 短い説明（必須）
    start_at:   date           # 開始日（必須）
    venue_name: str            # 会場名（必須）
    url:        str            # 公式URL（必須）
    end_at:     Optional[date] = None         # 終了日（なければ start_at と同じ）
    tags:       List[str]      = field(default_factory=list)  # タグ例: ["無料", "体験"]
    source:     str            = ""           # データ取得元名


class BaseEventScraper:
    """
    全スクレイパー共通の基底クラス。
    サブクラスは fetch_events() をオーバーライドしてください。
    """

    source_name: str = ""  # スクレイパー名（例: "仙台市科学館"）
    source_url:  str = ""  # 対象URL

    def fetch_events(self) -> List[EventData]:
        """
        イベントを取得して EventData のリストで返す。
        サブクラスで必ずオーバーライドしてください。
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} は fetch_events() を実装してください"
        )

    def run(self, output_csv: str) -> None:
        """
        イベントを取得して CSV に追記する。

        Args:
            output_csv: 書き込み先の CSV ファイルパス（例: "data/events.csv"）
        """
        print(f"[{self.source_name}] スクレイピング開始 ...")

        try:
            events = self.fetch_events()
        except Exception as e:
            print(f"[{self.source_name}] エラーが発生しました: {e}")
            return

        print(f"[{self.source_name}] {len(events)} 件取得")
        if events:
            self._append_to_csv(events, output_csv)

    # ------------------------------------------------------------------ #
    # 内部メソッド
    # ------------------------------------------------------------------ #

    def _load_existing_titles(self, csv_path: str) -> set:
        """既存 CSV から title 一覧を読み込む（重複チェック用）"""
        if not os.path.exists(csv_path):
            return set()
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return {row.get("title", "").strip() for row in reader}

    def _append_to_csv(self, events: List[EventData], csv_path: str) -> None:
        """新規イベントのみ CSV に追記する（既存タイトルと重複するものはスキップ）"""
        existing = self._load_existing_titles(csv_path)

        new_events = []
        for ev in events:
            if ev.title.strip() in existing:
                print(f"  スキップ（重複）: {ev.title}")
            else:
                new_events.append(ev)

        if not new_events:
            print(f"[{self.source_name}] 追加する新規イベントはありませんでした")
            return

        # ファイルが存在しない場合はヘッダーを書く
        write_header = not os.path.exists(csv_path)
        fieldnames = ["title", "summary", "start_at", "end_at",
                      "venue_name", "url", "tags", "source"]

        with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            for ev in new_events:
                writer.writerow({
                    "title":      ev.title,
                    "summary":    ev.summary,
                    "start_at":   ev.start_at.isoformat(),
                    "end_at":     ev.end_at.isoformat() if ev.end_at else "",
                    "venue_name": ev.venue_name,
                    "url":        ev.url,
                    "tags":       ",".join(ev.tags),
                    "source":     ev.source or self.source_name,
                })

        print(f"[{self.source_name}] {len(new_events)} 件を CSV に追加しました")
