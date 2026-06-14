"""
仙台市科学館 スクレイパー
==========================
対象URL: https://www.kagakukan.sendai-c.ed.jp/event/

【HTML構造（確認済み）】
- イベント一覧: /event/ の <a href="/event_/数字/"> リンク
- 各イベントページ:
    - <h2> または <title> に "YYYY年M月D日(曜)｜イベントタイトル" 形式
    - <dt>日時</dt><dd>...</dd>  ← 日時詳細
    - <dt>場所</dt><dd>...</dd>  ← 場所
    - <dt>対象</dt><dd>...</dd>  ← 対象者
    - <dt>参加費</dt><dd>...</dd> ← 参加費
    - <dt>申込</dt><dd>...</dd>  ← 申込方法
"""

import re
import time
from datetime import date
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseEventScraper, EventData


BASE_URL   = "https://www.kagakukan.sendai-c.ed.jp"
VENUE_NAME = "仙台市科学館（泉区）"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SendaiKidsBot/1.0; +https://github.com)"}


class ScienceMuseumScraper(BaseEventScraper):
    source_name = "仙台市科学館"
    source_url  = BASE_URL + "/"
    EVENT_LIST_URL = BASE_URL + "/event/"

    # -------------------------------------------------------
    # 公開メソッド
    # -------------------------------------------------------
    def fetch_events(self) -> List[EventData]:
        """イベント一覧ページから個別イベントURLを取得し、詳細をパースする"""
        event_urls = self._get_event_urls()
        print(f"  [科学館] イベントURL取得: {len(event_urls)} 件")

        events = []
        for url in event_urls:
            ev = self._parse_event(url)
            if ev:
                events.append(ev)
                print(f"  OK  {ev.start_at} {ev.title}")
            else:
                print(f"  NG  パース失敗: {url}")
            time.sleep(0.5)   # サーバー負荷軽減

        return events

    # -------------------------------------------------------
    # 内部メソッド
    # -------------------------------------------------------
    def _get_event_urls(self) -> List[str]:
        """イベント一覧ページから /event_/数字/ 形式のURLを収集する"""
        resp = requests.get(self.EVENT_LIST_URL, timeout=15, headers=HEADERS)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")

        seen, urls = set(), []
        for a in soup.select("a[href]"):
            href = a["href"]
            # /event_/12345/ 形式（絶対URL・相対URL どちらも対応）
            if re.search(r"/event_/\d+/?$", href):
                # 絶対URLはそのまま、相対URLはBASE_URLを付加
                if href.startswith("http"):
                    full = href.rstrip("/") + "/"
                else:
                    full = BASE_URL + href.rstrip("/") + "/"
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
        return urls

    def _parse_event(self, url: str) -> Optional[EventData]:
        """個別イベントページを取得してEventDataを生成する"""
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            print(f"    取得エラー {url}: {e}")
            return None

        # ── タイトル・日付テキストを取得 ──────────────────────────
        header_text = self._get_header_text(soup)
        if not header_text:
            return None

        # ｜で分割: "2026年6月6日(土)・13日(土)｜サイエンスショー「低温の科学」"
        if "｜" not in header_text:
            return None
        date_part, title = header_text.split("｜", 1)
        title = title.strip()
        # 申込状態・更新情報などの括弧書きを除去
        # 例: "イベント名（申込受付終了）" → "イベント名"
        # 例: "イベント名（申込受付中・6/9(火)〆切）" → "イベント名"
        # ※ [^）]* で全角）だけを除外（内側の半角括弧は通過させる）
        title = re.sub(r'\s*[（(](申込|受付|〆切|更新|予定)[^）]*[）)]\s*', '', title).strip()

        # ── 日付パース ──────────────────────────────────────────
        dates = self._parse_dates(date_part)
        if not dates:
            return None
        start_at = dates[0]
        end_at   = dates[-1]

        # 過去のイベントは除外（今日より前に終了）
        if end_at < date.today():
            return None

        # ── テーブルから詳細情報を取得 ────────────────────────────
        # 実際の構造: <table><tr><td>日　時</td><td>2026年...</td></tr>...
        # キーの全角スペース（U+3000）を除去して正規化
        info = {}
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    raw_key = cells[0].get_text(strip=True)
                    # 全角スペース・半角スペースを除去して正規化
                    key = re.sub(r"[　\s]+", "", raw_key)
                    val = cells[1].get_text(" ", strip=True)
                    info[key] = val

        # ── サマリーを組み立て ─────────────────────────────────
        summary = self._build_summary(info)

        # ── 無料タグの判定 ────────────────────────────────────
        fee = info.get("参加費", "")
        # 入館料のみ必要 or 無料 or 未記載 → 「無料」タグ
        if "無料" in fee or "入館料" in fee or not fee.strip():
            tags = ["無料"]
        else:
            tags = ["体験"]

        return EventData(
            title      = title,
            summary    = summary,
            start_at   = start_at,
            end_at     = end_at,
            venue_name = VENUE_NAME,
            url        = url,
            tags       = tags,
            source     = self.source_name,
        )

    # -------------------------------------------------------
    # ヘルパー
    # -------------------------------------------------------
    @staticmethod
    def _get_header_text(soup: BeautifulSoup) -> Optional[str]:
        """
        "YYYY年M月D日(曜)｜タイトル" 形式のテキストを
        h2 → h3 → <title>タグ の順で探す
        """
        for tag_name in ("h2", "h3"):
            for tag in soup.find_all(tag_name):
                text = tag.get_text(strip=True)
                if "｜" in text and re.search(r"\d{4}年\d{1,2}月\d{1,2}日", text):
                    return text

        # フォールバック: <title> タグから取得
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            # "2026年6月6日(土)｜イベント名｜HOKUSHU仙台市科学館" 形式
            parts = [p.strip() for p in raw.split("｜")]
            if len(parts) >= 2 and re.search(r"\d{4}年\d{1,2}月\d{1,2}日", parts[0]):
                return "｜".join(parts[:2])

        return None

    @staticmethod
    def _parse_dates(date_str: str) -> List[date]:
        """
        日付文字列を date のリストに変換する（昇順ソート）

        対応例:
          "2026年6月6日(土)・13日(土)"       → [2026-06-06, 2026-06-13]
          "2026年6月20日(土)"               → [2026-06-20]
          "2026年6月27日(土)～7月4日(土)"   → [2026-06-27, 2026-07-04]
          "2026年6月6日(土)　9:00～16:00"   → [2026-06-06]
        """
        result = []
        full_pat     = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
        monthday_pat = r"(?<!\d)(\d{1,2})月(\d{1,2})日"   # 年なし "M月D日"
        day_only_pat = r"(?<!\d)(\d{1,2})日(?!\d)"         # 日のみ "D日"

        # Step1: 完全形 "YYYY年M月D日" を全て抽出
        for m in re.finditer(full_pat, date_str):
            try:
                result.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                pass

        if not result:
            return []

        base_year = result[0].year

        # Step2: 完全形を除いた残りに "M月D日" があれば抽出（月またぎ対応）
        # 例: "2026年6月27日(土)・7月4日(土)" の "7月4日" 部分
        remaining = re.sub(full_pat, "___", date_str)
        for m in re.finditer(monthday_pat, remaining):
            try:
                d = date(base_year, int(m.group(1)), int(m.group(2)))
                if d not in result:
                    result.append(d)
            except ValueError:
                pass

        # Step3: さらに残った "D日" 単体は先頭の年・月で補完
        # 例: "2026年6月6日(土)・13日(土)" の "13日" 部分
        base_month = result[0].month
        remaining2 = re.sub(monthday_pat, "___", remaining)
        for day_str in re.findall(day_only_pat, remaining2):
            try:
                d = date(base_year, base_month, int(day_str))
                if d not in result:
                    result.append(d)
            except ValueError:
                pass

        result.sort()
        return result

    @staticmethod
    def _build_summary(info: dict) -> str:
        """テーブル情報からサマリー文を組み立てる（キーは正規化済み）"""
        parts = []
        if "対象" in info:
            parts.append(f"対象：{info['対象']}")
        if "参加費" in info:
            parts.append(f"参加費：{info['参加費']}")
        if "場所" in info:
            # 場所が長い場合は先頭50文字まで
            venue = info["場所"][:50].split("　")[0].split(" ")[0]
            parts.append(f"場所：{venue}")
        # 申込情報（長すぎる場合は短く）
        申込 = info.get("申込", "")
        if 申込 and len(申込) < 20:
            parts.append(f"申込：{申込}")
        return "。".join(parts) + "。" if parts else "仙台市科学館のイベントです。"


if __name__ == "__main__":
    # 単体テスト: python -m scraper.science_museum
    scraper = ScienceMuseumScraper()
    events = scraper.fetch_events()
    print(f"\n取得イベント数: {len(events)}")
    for ev in events:
        print(f"  {ev.start_at}〜{ev.end_at}  [{ev.tags}]  {ev.title}")
