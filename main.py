import requests
import os
import hashlib
import difflib
import google.generativeai as genai

try:
    from google.colab import userdata
except ImportError:
    userdata = None

# 定数
GITHUB_API_URL_BASE = "https://api.github.com/repos/Altairu/sken_training_materials/contents"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PREVIOUS_HASHES_PATH = "previous_hashes.txt"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_API_KEY = userdata.get("GEMINI_API_KEY") if userdata else os.getenv("GOOGLE_API_KEY")

# AI初期化
genai.configure(api_key=GOOGLE_API_KEY)

def get_all_files_from_github(path="site"):
    files = []
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"{GITHUB_API_URL_BASE}/{path}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    contents = response.json()

    for item in contents:
        if item["type"] == "file":
            files.append(item)
        elif item["type"] == "dir":
            files.extend(get_all_files_from_github(item["path"]))
    return files

def calculate_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_previous_hashes():
    if not os.path.exists(PREVIOUS_HASHES_PATH):
        return {}
    with open(PREVIOUS_HASHES_PATH, "r", encoding="utf-8") as f:
        return dict(line.strip().split(" ", 1) for line in f)

def save_current_hashes(hashes):
    with open(PREVIOUS_HASHES_PATH, "w", encoding="utf-8") as f:
        for path, file_hash in hashes.items():
            f.write(f"{path} {file_hash}\n")

def generate_diff_summary(diff_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"""
以下は、ある技術Wikiサイトのファイル更新差分です。

この変更が「実質的な情報の追加・更新（＝利用者が読む内容の変化）」を含んでいるかを判定してください。

以下のような変更は重要ではありません：
- HTMLレイアウトや構造の変更（div, header など）
- デザイン、ナビゲーション、フッターなどの修正
- CSSや表示に関する変更
- MkDocsなど自動生成によるテンプレートの作成
- 改行、空白、インデント、スペース、句読点の修正

これらに該当する場合は、「この変更は重要ではありません」とだけ答えてください。
逆に、内容に新しい解説や資料が追加されていれば、自然な日本語で2〜4行で要約してください。

差分:
```
{diff_text[:3000]}
"""
    )

    if hasattr(response, "text"):
        return response.text.strip()
    elif hasattr(response, "candidates"):
        return response.candidates[0].content.parts[0].text.strip()
    else:
        raise ValueError("AIから有効なレスポンスが得られませんでした。")

def post_to_discord(message):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def test_network():
    try:
        response = requests.get("https://www.google.com")
        response.raise_for_status()
        print("ネットワーク接続は正常です。")
    except Exception as e:
        print(f"ネットワーク接続に問題があります: {e}")

def main():
    test_network()

    files = get_all_files_from_github("site")
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    summaries = []
    meaningful_changes = False

    for file in files:
        file_path = file["path"]
        file_content = requests.get(file["download_url"]).text
        file_hash = calculate_hash(file_content)
        current_hashes[file_path] = file_hash

        if file_path not in previous_hashes or previous_hashes[file_path] != file_hash:
            previous_content = previous_hashes.get(file_path, "")
            diff_lines = list(difflib.unified_diff(
                previous_content.splitlines(), file_content.splitlines(), lineterm="", n=2
            ))

            # 差分が小さいならスキップ（無駄なAPI呼び出しを回避）
            if len(diff_lines) < 5:
                continue

            diff_text = "\n".join(diff_lines)
            summary = generate_diff_summary(diff_text)

            if "この変更は重要ではありません" in summary:
                continue

            summaries.append(summary)
            meaningful_changes = True

    if meaningful_changes:
        message = (
            "📝 **Webサイトに変更が加えられました！**\n\n"
            + "\n".join(f"* {s}" for s in summaries)
            + "\n\n🔗 https://altairu.github.io/sken_training_materials/"
        )
        post_to_discord(message)
        save_current_hashes(current_hashes)
    else:
        print("重要な変更がなかったため、通知も保存も行いません。")

if __name__ == "__main__":
    main()