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
    prompt = f"""以下の内容を日本語でまとめてください。全ての漢字に読み仮名を括弧でつけること(例:新聞(しんぶん))。記号不要。1000文字以内。

1. 中国関連ニュース3件、日本関連ニュース3件、国際ニュース2件(ロイター・BBC等海外メディア視点)
2. 日経225・東証の本日寄り付き、米国株(ダウ・ナスダック・S&P500)昨夜終値、主要銘柄の動き
3. 東京都新宿区の本日天気(気温・降水確率)
4. USD/JPY・CNY/JPYの現在レート
5. 本日のToDo(日本語に翻訳して表示):
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
