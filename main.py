import requests
import difflib
import os
from bs4 import BeautifulSoup
import google.generativeai as genai

# 定数
URL = "https://altairu.github.io/sken_training_materials/"
PREVIOUS_HTML_PATH = "previous.html"
PREVIOUS_SUMMARY_PATH = "previous_summary.txt"  # 要約を保存するファイル

def get_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def load_previous_html():
    if not os.path.exists(PREVIOUS_HTML_PATH):
        return ""
    with open(PREVIOUS_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()

def save_current_html(html):
    with open(PREVIOUS_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

def load_previous_summary():
    if not os.path.exists(PREVIOUS_SUMMARY_PATH):
        return ""
    with open(PREVIOUS_SUMMARY_PATH, "r", encoding="utf-8") as f:
        return f.read()

def save_current_summary(summary):
    with open(PREVIOUS_SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(summary)

def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return " ".join(text.split())  # 空白や改行を削除して正規化

def generate_diff_summary(old, new):
    """
    HTMLの差分をAIで解析し、変更内容を要約する。
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY 環境変数が設定されていません。")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    diff = difflib.unified_diff(
        old.splitlines(), new.splitlines(), lineterm="", n=2
    )
    diff_text = "\n".join(diff)

    # AIに要約を依頼
    prompt = f"""
以下はあるWebサイトのHTMLの変更差分です。
日本語で、どのような更新が行われたかを1〜2文で自然に要約してください：

```
{diff_text[:3000]}
```
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def post_to_discord(summary):
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    message = {
        "content": f"📝 **Webサイトに変更がありました！**\n\n```\n{summary}\n```\n🔗 <{URL}>"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=message)
    response.raise_for_status()

def main():
    current_html = get_html(URL)
    previous_html = load_previous_html()
    current_text = extract_text_from_html(current_html)
    previous_text = extract_text_from_html(previous_html)

    # HTMLが同じ場合はスキップ
    if current_text == previous_text:  # 正規化されたテキストを比較
        print("HTMLに変更なし")
        return

    try:
        diff_summary = generate_diff_summary(previous_text, current_text)
        previous_summary = load_previous_summary()

        # 要約が前回と同じ場合は通知をスキップ
        if diff_summary == previous_summary:
            print("同じ要約のため通知をスキップ")
            return

        post_to_discord(diff_summary)
        save_current_summary(diff_summary)  # 新しい要約を保存
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        save_current_html(current_html)  # 必ずHTMLを保存

if __name__ == "__main__":
    main()
