"""
宮城県 こもれびの森 森林科学館 スクレイパー
==========================================
対象URL: https://m-komorebi.com/?page_id=607

【HTML構造（確認済み）】
- WordPress サイトの自由形式テキスト
- <p> タグの中に <strong> タグ入れ子
- イベントパターン（3種類）:
    A) タイトル専用<p>（「」括弧）→ 日付<p> → 料金<p>
    B) 日付+タイトルが同じ<p>: "6月7日(日） 竹ポックリ作り をします。"
    C) 日付<p>のみ（"初心者大歓迎"）→ 同<p>内 <a href="苔玉.jpg"> でタイトル推定

【スクレイピング方針】
1. <p> 要素単位で処理（<strong> 単体では文脈が足りない）
2. 日付を含む<p>を見つけたら:
   a. 同<p>の非日付テキストからキーワードで抽出（パターンB）
   b. 直前1〜2<p>の 「」 括弧テキストから抽出（パターンA）
   c. 同<p>内の <a href> 画像ファイル名から推定（パターンC）
3. 料金は直後1〜2<p>の "X円" パターンから取得
"""

import re
import unicodedata
from datetime import date
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseEventScraper, EventData

EVENT_URL  = "https://m-komorebi.com/?page_id=607"
VENUE_NAME = "宮城県こもれびの森 森林科学館（川崎町）"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; SendaiKidsBot/1.0)"}


def _normalize(text: str) -> str:
    """全角数字・記号を半角に変換"""
    return unicodedata.normalize("NFKC", text)


class KomorebiForestScraper(BaseEventScraper):
    source_name = "こもれびの森"
    source_url  = EVENT_URL

    def fetch_events(self) -> List[EventData]:
        resp = requests.get(EVENT_URL, timeout=15, headers=HEADERS)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")

        # メインコンテンツを取得
        main = (soup.find("div", class_="entry-content")
                or soup.find("main")
                or soup.find("article")
                or soup.find("div", id="content")
                or soup.body)

        if not main:
            return []

        events = self._extract_events(main)
        print(f"  [こもれびの森] 取得: {len(events)} 件")
        return events

    def _extract_events(self, container) -> List[EventData]:
        today     = date.today()
        this_year = today.year
        next_year = today.year + 1

        paras    = container.find_all("p")
        date_pat = re.compile(r"(\d{1,2})月(\d{1,2})日")
        events   = []

        for i, p in enumerate(paras):
            p_text = _normalize(p.get_text(" ", strip=True))
            m = date_pat.search(p_text)
            if not m:
                continue

            month = int(m.group(1))
            day   = int(m.group(2))

            # 今年の日付のみ対象（過去はスキップ、来年繰り上げなし）
            try:
                ev_date = date(this_year, month, day)
            except ValueError:
                continue
            if ev_date < today:
                continue

            # タイトルを探す
            title = self._find_title(paras, i, p)
            if not title:
                continue

            # 料金を探す（直後2〜3パラグラフ）
            price = self._find_price_after(paras, i)

            summary = self._build_summary(ev_date, price)
            is_free = price is not None and "無料" in price

            events.append(EventData(
                title      = title,
                summary    = summary,
                start_at   = ev_date,
                end_at     = ev_date,
                venue_name = VENUE_NAME,
                url        = EVENT_URL,
                tags       = ["無料"] if is_free else ["体験"],
                source     = self.source_name,
            ))

        # 同日の重複を除去（同じ日付が複数<p>に現れる場合、最初の1件のみ保持）
        seen, unique = set(), []
        for ev in events:
            if ev.start_at not in seen:
                seen.add(ev.start_at)
                unique.append(ev)

        return unique

    # -------------------------------------------------------
    # タイトル抽出 (3段階フォールバック)
    # -------------------------------------------------------
    @staticmethod
    def _find_title(paras: list, idx: int, date_p) -> Optional[str]:
        """
        (a) 同<p>の非日付テキストにキーワードがあれば抽出（パターンB）
        (b) 直前1〜2<p>の 「」 括弧テキストを探す（パターンA）
        (c) 同<p>内の <a href> 画像ファイル名から推定（パターンC）
        """
        date_pat   = re.compile(r"\d{1,2}月\d{1,2}日[（(]?[^）)]*[）)]?")
        kw_pat     = re.compile(r"(体験|教室|観察|作り|工作|ふれあい|採取|収穫|つかみ)")
        bracket_pat = re.compile(r"[「『](.*?)[」』]")

        # ── (a) 同<p>から日付を除いてキーワード検索 ──
        p_text   = _normalize(date_p.get_text(" ", strip=True))
        residual = date_pat.sub("", p_text).strip()
        # "をします" "です" など文末助動詞を除去
        residual = re.sub(r"\s*(をします|をしよう|です|ます)[。！.!]?\s*$", "", residual).strip()
        residual = re.sub(r"[　\s]+", " ", residual).strip()
        if residual and len(residual) > 2 and kw_pat.search(residual):
            return residual[:40]

        # ── (b) 直前1〜2<p>の 「」 括弧テキストを探す ──
        for j in range(max(0, idx - 2), idx):
            t = _normalize(paras[j].get_text(" ", strip=True))
            bm = bracket_pat.search(t)
            if bm:
                title = bm.group(1).strip(" 　")
                if len(title) > 2:
                    return title

        # ── (c) 同<p>内の <a href> 画像ファイル名 ──
        for a in date_p.find_all("a"):
            href = a.get("href", "")
            if re.search(r"\.(jpg|jpeg|png|gif)$", href, re.IGNORECASE):
                basename = href.split("/")[-1]
                basename = re.sub(r"\.\w+$", "", basename)      # 拡張子除去
                basename = _normalize(basename)
                # サイズ表記 "-709x1024" や月表記 "6月" を除去
                basename = re.sub(r"-\d+x\d+$", "", basename)
                basename = re.sub(r"\d{1,2}月|\d{4}年", "", basename).strip()
                if len(basename) >= 2:
                    return basename + "体験"

        return None

    # -------------------------------------------------------
    # 料金抽出（直後パラグラフ）
    # -------------------------------------------------------
    @staticmethod
    def _find_price_after(paras: list, idx: int, window: int = 3) -> Optional[str]:
        """直後 window 件の<p>から料金を探す"""
        price_pat = re.compile(r"(\d[\d,，]+円|無料)")
        for j in range(idx, min(len(paras), idx + window + 1)):
            t = _normalize(paras[j].get_text(" ", strip=True))
            pm = price_pat.search(t)
            if pm:
                return pm.group(0)
        return None

    # -------------------------------------------------------
    # サマリー生成
    # -------------------------------------------------------
    @staticmethod
    def _build_summary(ev_date: date, price: Optional[str]) -> str:
        weekdays  = "月火水木金土日"
        wd        = weekdays[ev_date.weekday()]
        date_str  = f"{ev_date.month}月{ev_date.day}日（{wd}）開催"
        price_str = f"参加費：{price}" if price else "参加費：要確認"
        return f"{date_str}。{price_str}。要申込（電話またはホームページ）。"


if __name__ == "__main__":
    scraper = KomorebiForestScraper()
    events = scraper.fetch_events()
    print(f"\n取得イベント数: {len(events)}")
    for ev in events:
        print(f"  {ev.start_at}  [{ev.tags}]  {ev.title}")
        print(f"    {ev.summary}")
