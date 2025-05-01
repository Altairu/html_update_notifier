import requests
import difflib
import os
from bs4 import BeautifulSoup
import google.generativeai as genai

# 定数
URL = "https://altairu.github.io/sken_training_materials/"
PREVIOUS_HTML_PATH = "previous.html"

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

def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

def generate_diff_summary(old, new):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY 環境変数が設定されていません。")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="models/gemini-pro")  # 修正箇所

    diff = difflib.unified_diff(
        old.splitlines(), new.splitlines(), lineterm="", n=2
    )
    diff_text = "\n".join(diff)
    prompt = f"""
以下はあるWebサイトのHTMLの変更差分です。
日本語で、どのような更新が行われたかを箇条書きで3〜5行で自然に要約してください：

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

    if current_text == previous_text:
        print("変更なし")
        return

    summary = generate_diff_summary(previous_text, current_text)
    post_to_discord(summary)
    save_current_html(current_html)

if __name__ == "__main__":
    main()
