import os
import json
import urllib.request

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
BARK_URL = os.environ["BARK_URL"].strip()
BARK_URL_FRIEND = os.environ["BARK_URL_FRIEND"].strip()

TODO_LIST = [
    "例:メールの返信",
    "例:午後3時にミーティング",
]

def call_claude():
    todo_str = "\n".join(f"- {t}" for t in TODO_LIST)
    prompt = f"""以下の内容を日本語でまとめてください。全ての漢字に読み仮名を括弧でつけること(例:新聞(しんぶん))。記号不要。必ず全ての項目を含めること。

1. ニュース(各(かく)20文字(もじ)以内(いない)で超簡潔(ちょうかんけつ)に、タイトルのみ):
   - 中国(ちゅうごく)関連(かんれん) 1件(けん)
   - 日本(にほん)関連(かんれん) 2件(けん)
   - 国際(こくさい) 2件(けん)

2. 天気(てんき)(簡潔(かんけつ)に):東京都(とうきょうと)新宿区(しんじゅくく)、気温(きおん)と降水確率(こうすいかくりつ)

3. 為替(かわせ)(簡潔(かんけつ)に):USD/JPY・CNY/JPYの現在(げんざい)レート

4. 市場(しじょう)(詳細(しょうさい)に):
   - 日経(にっけい)225・東証(とうしょう)指数(しすう)の本日(ほんじつ)寄(よ)り付(つ)き(数値(すうち)・騰落率(とうらくりつ))
   - 米国株(べいこくかぶ)(ダウ・ナスダック・S&P500)の昨夜(さくや)終値(おわりね)(数値(すうち)・騰落率(とうらくりつ))
   - 上昇(じょうしょう)・下落(げらく)した主要(しゅよう)銘柄(めいがら)やセクターを具体的(ぐたいてき)に3〜5件(けん)

5. ToDo【TODO_START】
{todo_str}
【TODO_END】"""

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
    return "\n".join(text_parts).strip()


def remove_todo(text):
    # 去掉【TODO_START】到【TODO_END】之间的内容
    import re
    return re.sub(r'【TODO_START】.*?【TODO_END】', '', text, flags=re.DOTALL).strip()


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
    briefing = call_claude()

    if not briefing:
        briefing = "ブリーフィングの生成に失敗しました。"

    # 你的简报(含Todo)
    push_to_bark(BARK_URL, "今日(きょう)のブリーフィング", briefing)
    print("自分に送信完了")

    # 朋友的简报(去掉Todo)
    briefing_friend = remove_todo(briefing)
    push_to_bark(BARK_URL_FRIEND, "今日(きょう)のブリーフィング", briefing_friend)
    print("友達に送信完了")
