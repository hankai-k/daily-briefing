import os
import json
import urllib.request

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
BARK_URL = os.environ["BARK_URL"].strip()

# 待辦事項リスト(中国語や他の言語で入力してもOK、日本語に翻訳されます)
TODO_LIST = [
    "例:メールの返信",
    "例:午後3時にミーティング",
]

def call_claude():
    prompt = f"""あなたは日本語学習者向けの毎日ブリーフィングを作成するアシスタントです。
以下の内容を含む「今日のブリーフィング」を日本語で作成してください。

重要なルール:
- 全文を日本語で書くこと
- 全ての漢字に読み仮名を括弧でつけること。例:「新聞(しんぶん)」「東京(とうきょう)」
- 記号やマークダウンは使わないこと(*、#など不要)
- 待辦事項が中国語や他の言語で書かれていても必ず日本語に翻訳すること
- 全体の長さは1000文字以内にすること

内容の順番:

1. ニュース(海外メディア=ロイター、ブルームバーグ、CNN、BBC、日本経済新聞などの視点を優先):
   - 中国関連の重要ニュース 3件
   - 日本関連の重要ニュース 3件
   - 国際ニュース 2件

2. 市場まとめ:
   - 今日の日本株式市場(日経225、東証指数)の寄り付き状況
   - 昨夜の米国株式市場(ダウ、ナスダック、S&P500)の終値
   - 上昇または下落した主要銘柄やセクターも具体的に記載

3. 天気:東京都新宿区の今日の天気(気温、降水確率)

4. 為替:
   - 米ドル円(USD/JPY)の現在レート
   - 人民元円(CNY/JPY)の現在レート

5. 本日のToDo(以下のリストを日本語に翻訳して表示):
{json.dumps(TODO_LIST, ensure_ascii=False)}
"""

    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 3000,
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
        result = "ブリーフィングの生成に失敗しました。ログを確認してください。"
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
    print("=== ブリーフィング内容 ===")
    print(briefing_text)
    push_to_bark("今日(きょう)のブリーフィング", briefing_text)
