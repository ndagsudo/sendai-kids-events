#!/usr/bin/env python3
"""
全スクレイパー一括実行スクリプト
=================================
各施設のスクレイパーを実行し、data/events.csv を最新情報に更新します。

【動作の仕組み】
  1. スクレイパーごとに古い同ソースのデータを CSV から削除
  2. 新しいイベントデータを取得して CSV に追加
  3. 全スクレイパー完了後にサイトを再ビルド

【使い方】
  cd sendai-kids-events
  python scraper/run_scrapers.py

【スクレイパーを追加するには】
  get_enabled_scrapers() 内の対象行のコメントを外してください。
"""

import csv
import os
import subprocess
import sys

# プロジェクトルートを Python パスに追加
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "events.csv")
sys.path.insert(0, BASE_DIR)


# ==============================================================
# 有効なスクレイパー一覧
# 実装済みのものからコメントを外してください
# ==============================================================
def get_enabled_scrapers():
    """実装済み・有効なスクレイパーのインスタンスを返す"""
    scrapers = []

    # --- 科学・学習系 ---
    from scraper.science_museum import ScienceMuseumScraper
    scrapers.append(ScienceMuseumScraper())

    # from scraper.science_day import ScienceDayScraper
    # scrapers.append(ScienceDayScraper())

    # from scraper.science_community import ScienceCommunityScraper
    # scrapers.append(ScienceCommunityScraper())

    # --- ショッピングモール ---
    from scraper.aeon_mall_kamisugi import AeonMallKamisugiScraper
    scrapers.append(AeonMallKamisugiScraper())

    # --- 自然・体験系 ---
    from scraper.komorebi_forest import KomorebiForestScraper
    scrapers.append(KomorebiForestScraper())

    # --- 歴史・博物館系 ---
    from scraper.sendai_jomon import SendaiJomonScraper
    scrapers.append(SendaiJomonScraper())

    # from scraper.tomizawa import TomizawaScraper
    # scrapers.append(TomizawaScraper())

    # --- 食育・体験系 ---
    from scraper.jr_fruit_park import JrFruitParkScraper
    scrapers.append(JrFruitParkScraper())

    # from scraper.kanezan import KanezanScraper
    # scrapers.append(KanezanScraper())

    # --- 工作・ものづくり系 ---
    # from scraper.tsukurulab import TsukuruLabScraper
    # scrapers.append(TsukuruLabScraper())

    return scrapers


# ==============================================================
# CSV ユーティリティ
# ==============================================================
FIELDNAMES = ["title", "summary", "start_at", "end_at",
              "venue_name", "url", "tags", "source"]


def remove_source_from_csv(source_name: str, csv_path: str) -> int:
    """
    CSV から指定ソース名の行を全て削除する。
    削除した行数を返す。
    """
    if not os.path.exists(csv_path):
        return 0

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    kept   = [r for r in rows if r.get("source", "").strip() != source_name]
    removed = len(rows) - len(kept)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(kept)

    return removed


def append_events_to_csv(events, source_name: str, csv_path: str) -> int:
    """
    EventData のリストを CSV に追記する。
    重複タイトルはスキップ（同一ソース削除後に呼ぶ想定なので通常は全件追加）。
    追加した件数を返す。
    """
    # 既存タイトルを読み込む（重複防止）
    existing_titles = set()
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                existing_titles.add(row.get("title", "").strip())

    new_rows = []
    for ev in events:
        if ev.title.strip() in existing_titles:
            continue
        tags_str = ",".join(ev.tags) if isinstance(ev.tags, list) else str(ev.tags)
        new_rows.append({
            "title":      ev.title,
            "summary":    ev.summary,
            "start_at":   ev.start_at.isoformat(),
            "end_at":     ev.end_at.isoformat() if ev.end_at else ev.start_at.isoformat(),
            "venue_name": ev.venue_name,
            "url":        ev.url,
            "tags":       tags_str,
            "source":     ev.source or source_name,
        })

    if not new_rows:
        return 0

    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)

    return len(new_rows)


# ==============================================================
# メイン処理
# ==============================================================
def main():
    print("=" * 56)
    print("  スクレイパー一括実行")
    print("=" * 56)

    scrapers = get_enabled_scrapers()
    if not scrapers:
        print("\n有効なスクレイパーがありません。")
        print("scraper/run_scrapers.py の get_enabled_scrapers() 内の")
        print("コメントを外して有効にしてください。")
        return

    total_added = 0
    errors = 0

    for scraper in scrapers:
        sname = scraper.source_name
        print(f"\n>> {sname}")

        # Step1: 同ソースの古いデータを削除
        removed = remove_source_from_csv(sname, DATA_FILE)
        if removed:
            print(f"  旧データ削除: {removed} 件")

        # Step2: 新しいイベントを取得
        try:
            events = scraper.fetch_events()
        except NotImplementedError as e:
            print(f"  [未実装] {e}")
            errors += 1
            continue
        except Exception as e:
            print(f"  [エラー] {e}")
            errors += 1
            continue

        if not events:
            print(f"  取得イベント: 0 件（スキップ）")
            continue

        # Step3: CSV に追加
        added = append_events_to_csv(events, sname, DATA_FILE)
        total_added += added
        print(f"  取得: {len(events)} 件  →  追加: {added} 件")

    print("\n" + "=" * 56)
    print(f"  完了  合計追加: {total_added} 件  エラー: {errors} 件")
    print("=" * 56)

    # ビルドを実行（GitHub Actions では常に実行する）
    if "--no-build" not in sys.argv and total_added >= 0:
        print("\nサイトを再ビルドしています...")
        build_script = os.path.join(BASE_DIR, "build", "build.py")
        subprocess.run([sys.executable, build_script], check=True)
    else:
        print("\n再ビルドするには: python build/build.py")


if __name__ == "__main__":
    main()
