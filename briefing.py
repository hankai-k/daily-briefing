import os
import json
import urllib.request
import csv
import io
from datetime import datetime, timedelta, timezone

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
BARK_URL = os.environ["BARK_URL"].strip()
BARK_URL_FRIEND = os.environ["BARK_URL_FRIEND"].strip()

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTWQ8mUiMlgwETfVBmFBs3x250op9OJ0S3A1OXmjB5VuBUbgdbufoK00-9_x64Xp6D9aQwvLr_4OBc8/pub?gid=152629943&single=true&output=csv"

def get_todos():
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).date()
    tomorrow = today + timedelta(days=1)

    try:
        req = urllib.request.Request(SHEET_CSV_URL)
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))
        today_todos = []
        tomorrow_todos = []

        for row in reader:
            # 获取日期和事项内容(自动匹配列名)
            date_str = None
            item_str = None
            for key, val in row.items():
                k = key.strip().lower()
                if "日付" in k or "date" in k or "日期" in k:
                    date_str = val.strip()
                elif "内容" in k or "todo" in k or "事項" in k or "事项" in k or "content" in k:
                    item_str = val.strip()

            if not date_str or not item_str:
                continue

            try:
                # 支持多种日期格式
                for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y"]:
                    try:
                        task_date = datetime.strptime(date_str, fmt).date()
                        break
                    except:
                        continue

                if task_date == today:
                    today_todos.append(f"本日(ほんじつ): {item_str}")
                elif task_date == tomorrow:
                    tomorrow_todos.append(f"明日(あした): {item_str}")
            except:
                continue

        return today_todos + tomorrow_todos

    except Exception as e:
        print(f"表格读取失败: {e}")
        return []


def call_claude(todos):
    if todos:
        todo_str = "\n".join(f"- {t}" for t in todos)
        todo_section = f"\n5. ToDo(日本語(にほんご)に翻訳(ほんやく)):\n{todo_str}"
    else:
        todo_section = "\n5. ToDo: 本日(ほんじつ)・明日(あした)の予定(よてい)はありません"

    prompt = f"""以下の内容を日本語でまとめてください。全ての漢字に読み仮名を括弧でつけること(例:新聞(しんぶん))。記号不要。必ず全ての項目を含めること。

1. ニュース(各(かく)15文字(もじ)以内(いない)、一言(ひとこと)のみ、読み仮名(よみがな)不要(ふよう)):
   - 中国(ちゅうごく)関連(かんれん) 1件(けん)
   - 日本(にほん)関連(かんれん) 2件(けん)
   - 国際(こくさい) 2件(けん)

2. 天気(てんき)(簡潔(かんけつ)に):東京都(とうきょうと)新宿区(しんじゅくく)、気温(きおん)と降水確率(こうすいかくりつ)

3. 為替(かわせ)(簡潔(かんけつ)に):USD/JPY・CNY/JPYの現在(げんざい)レート

4. 市場(しじょう)(詳細(しょうさい)に):
   - 日経(にっけい)225・東証(とうしょう)指数(しすう)の本日(ほんじつ)寄(よ)り付(つ)き(数値(すうち)・騰落率(とうらくりつ))
   - 米国株(べいこくかぶ)(ダウ・ナスダック・S&P500)の昨夜(さくや)終値(おわりね)(数値(すうち)・騰落率(とうらくりつ))
   - 上昇(じょうしょう)・下落(げらく)した主要(しゅよう)銘柄(めいがら)やセクターを具体的(ぐたいてき)に3〜5件(けん){todo_section}"""

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{"type": "web_search_20250305", "name": "web_search"}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text_parts = [block["text"] for block in data["content"] if block.get("type") == "text"]
    result = "\n".join(text_parts).strip()
    if not result:
        result = "ブリーフィングの生成に失敗しました。"
    return result


def remove_todo(text):
    lines = text.split("\n")
    result = []
    skip = False
    for line in lines:
        if "ToDo" in line or "本日・明日" in line or "本日(ほんじつ):" in line or "明日(あした):" in line:
            skip = True
        if not skip:
            result.append(line)
    return "\n".join(result).strip()


def push_to_bark(url, title, content):
    payload = json.dumps({"title": title, "body": content}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print("Bark response:", resp.read().decode("utf-8"))


if __name__ == "__main__":
    todos = get_todos()
    print(f"今日・明日のTodo: {todos}")

    briefing = call_claude(todos)
    print("=== ブリーフィング ===")
    print(briefing)

    push_to_bark(BARK_URL, "今日(きょう)のブリーフィング", briefing)
    print("自分に送信完了")

    briefing_friend = remove_todo(briefing)
    push_to_bark(BARK_URL_FRIEND, "今日(きょう)のブリーフィング", briefing_friend)
    print("友達に送信完了")
