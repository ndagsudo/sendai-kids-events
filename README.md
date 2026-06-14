# 仙台・宮城の子どもイベント

仙台市・宮城県周辺の小学生・親子向けイベント情報を掲載する静的サイトです。  
Python で HTML を生成し、GitHub Pages で公開します。

## 特徴

- 📱 スマホ優先デザイン（親がサッと見られる）
- 🗓 今週末に行けるイベントをワンクリックで絞り込み
- 🎁 無料イベントを一目で確認
- 🔍 イベント名・会場名でリアルタイム検索
- ⚡ 静的サイト（バックエンド・DB 不要）

---

## ディレクトリ構成

```
sendai-kids-events/
├── README.md
├── requirements.txt              # Python 依存ライブラリ（現在は標準ライブラリのみ）
├── .gitignore
│
├── data/
│   └── events.csv               # ★ イベントデータ（ここを編集してイベントを追加）
│
├── build/
│   └── build.py                 # HTML ビルドスクリプト（これを実行するとサイト生成）
│
├── static/
│   └── style.css                # CSS スタイル
│
├── scraper/                     # 将来の自動収集スクレイパー置き場
│   ├── __init__.py
│   └── base.py                  # 基底クラス（新スクレイパーはこれを継承）
│
├── docs/                        # ★ ビルド出力（GitHub Pages のルート）
│   ├── index.html
│   ├── weekend.html
│   ├── privacy.html
│   ├── sitemap.xml
│   ├── robots.txt
│   └── style.css
│
└── .github/
    └── workflows/
        └── build.yml            # GitHub Actions 自動ビルド設定
```

---

## セットアップ・ビルド手順

### 必要なもの
- Python 3.8 以上（Windows / Mac / Linux 対応）

### 1. リポジトリを用意する

```bash
git clone https://github.com/あなたのユーザー名/sendai-kids-events.git
cd sendai-kids-events
```

### 2. SITE_URL を変更する

`build/build.py` の先頭にある `SITE_URL` をあなたの GitHub Pages URL に変更してください：

```python
SITE_URL = os.environ.get(
    "SITE_URL",
    "https://あなたのユーザー名.github.io/sendai-kids-events"  # ← ここを変更
)
```

### 3. サイトをビルドする

```bash
python build/build.py
```

`docs/` フォルダに HTML ファイルが生成されます。

### 4. ローカルで確認する

```bash
cd docs
python -m http.server 8000
```

ブラウザで `http://localhost:8000` を開いてください。

---

## イベントの追加・編集方法

`data/events.csv` をテキストエディタで開き、1行追加するだけです。  
その後 `python build/build.py` を実行してください。

### CSV のフィールド

| フィールド | 説明 | 例 |
|-----------|------|-----|
| `title` | イベント名 | 仙台市科学館「工作教室」 |
| `summary` | 短い説明（100文字程度） | 親子で楽しめる… |
| `start_at` | 開始日 `YYYY-MM-DD` | `2026-06-07` |
| `end_at` | 終了日（空欄なら1日のみ） | `2026-06-08` |
| `venue_name` | 会場名 | 仙台市科学館（太白区） |
| `url` | 公式サイト URL | `https://...` |
| `tags` | タグ（カンマ区切り） | `無料,体験,工作` |
| `source` | データ取得元 | 仙台市科学館 |

### ポイント

- **終了済みイベント**は自動的に非表示になります
- `tags` または `summary` または `title` に **「無料」** を含めると「無料」バッジが表示されます
- `end_at` が空の場合は1日のみのイベントとして扱います

---

## GitHub Pages への公開方法

1. GitHub でリポジトリを新規作成
2. このプロジェクトを push
3. `python build/build.py` を実行して `docs/` を生成
4. `docs/` もコミットして push
5. GitHubリポジトリの **Settings → Pages** を開く
6. Source を **Deploy from a branch** → Branch: `main` / `docs` フォルダに設定
7. 数分後にサイトが公開されます

---

## GitHub Actions による自動ビルド

`.github/workflows/build.yml` が設定済みです。  
`data/events.csv` を更新して push するだけで、自動的にサイトが再ビルドされます。

### SITE_URL の設定（Actions 向け）

GitHub リポジトリの **Settings → Variables → Actions** から  
`SITE_URL` という変数を追加してください（値: あなたの GitHub Pages URL）。

---

## スクレイパーの追加（将来の拡張）

`scraper/base.py` の `BaseEventScraper` を継承して各施設のスクレイパーを作れます：

```python
# scraper/science_museum.py
from scraper.base import BaseEventScraper, EventData
from datetime import date
import requests
from bs4 import BeautifulSoup

class ScienceMuseumScraper(BaseEventScraper):
    source_name = "仙台市科学館"
    source_url  = "https://www.sendai-kagakukan.jp/"

    def fetch_events(self):
        # requests で HTML を取得し BeautifulSoup でパース
        resp = requests.get(self.source_url)
        soup = BeautifulSoup(resp.text, "lxml")
        events = []
        # ... イベント情報を抽出 ...
        return events

# 実行例
if __name__ == "__main__":
    ScienceMuseumScraper().run("data/events.csv")
```

### 対応予定の取得元

- 仙台市科学館
- 仙台市天文台
- 仙台市博物館
- 宮城県図書館
- せんだいメディアテーク
- 三井アウトレットパーク仙台港
- イオンモール仙台上杉
- JRフルーツパーク仙台あらはま

---

## ライセンス

MIT License

---

掲載のイベント情報は各施設・主催者の公式サイトを参考に作成しています。  
最新情報は必ず公式サイトでご確認ください。
