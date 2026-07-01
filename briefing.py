import os
import json
import urllib.request

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
BARK_URL = os.environ["BARK_URL"].strip()

TODO_LIST = [
    "例:メールの返信",
    "例:午後3時にミーティング",
]

def call_claude():
    todo_str = "\n".join(f"- {t}" for t in TODO_LIST)
    prompt = f"""以下の内容を日本語でまとめてください。全ての漢字に読み仮名を括弧でつけること(例:新聞(しんぶん))。記号不要。800文字以内。必ず全ての項目を含めること。

1. ニュース(ロイター・BBC等海外メディア視点):
   - 中国(ちゅうごく)関連(かんれん) 1件(けん)
   - 日本(にほん)関連(かんれん) 2件(けん)
   - 国際(こくさい) 2件(けん)

2. 市場(しじょう)(必須(ひっす)):日経(にっけい)225・東証(とうしょう)本日寄(ほんじつよ)り付(つ)き、米国株(べいこくかぶ)(ダウ・ナスダック・S&P500)昨夜終値(さくやおわりね)、主要(しゅよう)銘柄(めいがら)の動(うご)き

3. 天気(てんき)(必須(ひっす)):東京都(とうきょうと)新宿区(しんじゅくく)の本日(ほんじつ)天気(てんき)・気温(きおん)・降水確率(こうすいかくりつ)

4. 為替(かわせ)(必須(ひっす)):USD/JPY・CNY/JPYの現在(げんざい)レート

5. ToDo(必須(ひっす)、日本語(にほんご)に翻訳(ほんやく)):
{todo_str}"""

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


def push_to_bark(title, content):
    payload = json.dumps({"title": title, "body": content}).encode("utf-8")
    req = urllib.request.Request(
        BARK_URL,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print("Bark response:", resp.read().decode("utf-8"))


if __name__ == "__main__":
    briefing_text = call_claude()
    print("=== ブリーフィング ===")
    print(briefing_text)
    push_to_bark("今日(きょう)のブリーフィング", briefing_text)
