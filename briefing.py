import os
import json
import urllib.request
import urllib.parse

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BARK_URL = os.environ["BARK_URL"]

# 在这里维护你的待办事项,每天手动改这个列表即可
TODO_LIST = [
    "示例:回复客户邮件",
    "示例:下午3点开会",
]

def call_claude():
    prompt = f"""请用简洁的中文生成一份"今日简报",内容包括:
1. 今日重要财经/市场新闻摘要(2-3条)
2. 今日重要科技新闻摘要(2-3条)
3. 今日重要综合时事新闻摘要(2-3条)
4. 今天的天气情况(北京)
5. 人民币兑日元当前汇率
6. 结合以下todo清单,列出今日待办事项:
{json.dumps(TODO_LIST, ensure_ascii=False)}

请用纯文本格式输出,不要用markdown符号(不要*号、#号等),分段落即可,总长度控制在500字以内,适合手机推送通知阅读。"""

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


def push_to_bark(title, content):
    url = f"{BARK_URL}/{urllib.parse.quote(title)}/{urllib.parse.quote(content)}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        print("Bark response:", resp.read().decode("utf-8"))


if __name__ == "__main__":
    briefing_text = call_claude()
    print("=== 简报内容 ===")
    print(briefing_text)
    push_to_bark("今日简报", briefing_text)
