import os
import json
import urllib.request
import csv
import io
import re
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


def clean(text):
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,2}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def call_claude(todos):
    if todos:
        todo_str = "\n".join(todos)
    else:
        todo_str = "なし"

    prompt = f"""今日(きょう)のブリーフィングを日本語(にほんご)で作成(さくせい)してください。
厳守(げんしゅ)ルール:
- ###/**/#などの記号(きごう)は絶対(ぜったい)に使(つか)わない
- 余分(よぶん)な空行(くうぎょう)なし
- 漢字(かんじ)には読(よ)み仮名(がな)を括弧(かっこ)でつける
- 全体(ぜんたい)600文字(もじ)以内(いない)

以下(いか)の順番(じゅんばん)で出力(しゅつりょく):

ToDo:
{todo_str}

ニュース(各(かく)10字(じ)以内(いない)):中国(ちゅうごく)1件(けん)、日本(にほん)2件(けん)、国際(こくさい)2件(けん)

天気(てんき)/為替(かわせ): 新宿区(しんじゅくく)気温(きおん)・降水(こうすい)%、USD/JPY・CNY/JPY(全部(ぜんぶ)一文(いちぶん))

株式(かぶしき)市場(しじょう)(簡潔(かんけつ)に3〜4文(ぶん)):日経(にっけい)・東証(とうしょう)寄(よ)り付(つ)き、米国株(べいこくかぶ)終値(おわりね)、主要(しゅよう)銘柄(めいがら)2〜3件(けん)"""

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
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
    return clean("\n".join(text_parts))


def remove_todo(text):
    lines = text.split("\n")
    result = [l for l in lines if "ToDo" not in l and "本日:" not in l and "明日:" not in l and "本日(ほんじつ)" not in l and "明日(あした)" not in l]
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
    print(f"Todo: {todos}")
    briefing = call_claude(todos)
    print("=== ブリーフィング ===")
    print(briefing)
    push_to_bark(BARK_URL, "今日(きょう)のブリーフィング", briefing)
    print("自分に送信完了")
    briefing_friend = remove_todo(briefing)
    push_to_bark(BARK_URL_FRIEND, "今日(きょう)のブリーフィング", briefing_friend)
    print("友達に送信完了")
