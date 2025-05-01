import requests
import os
import hashlib
import difflib

try:
    from google.colab import userdata  # Google Colab環境用
except ImportError:
    userdata = None

# 定数
GITHUB_API_URL = "https://api.github.com/repos/Altairu/sken_training_materials/contents/site"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub Actionsで提供されるトークン
PREVIOUS_HASHES_PATH = "previous_hashes.txt"  # ファイルのハッシュを保存するファイル
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_API_KEY = userdata.get("GEMINI_API_KEY") if userdata else os.getenv("GOOGLE_API_KEY")  # AI用APIキー

def get_github_files():
    """
    GitHub APIを使用してsiteディレクトリ内のファイルリストを取得する。
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def calculate_hash(content):
    """
    ファイル内容のハッシュを計算する。
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_previous_hashes():
    """
    前回のファイルハッシュを読み込む。
    """
    if not os.path.exists(PREVIOUS_HASHES_PATH):
        return {}
    with open(PREVIOUS_HASHES_PATH, "r", encoding="utf-8") as f:
        return dict(line.strip().split(" ", 1) for line in f)

def save_current_hashes(hashes):
    """
    現在のファイルハッシュを保存する。
    """
    with open(PREVIOUS_HASHES_PATH, "w", encoding="utf-8") as f:
        for path, file_hash in hashes.items():
            f.write(f"{path} {file_hash}\n")

def generate_diff_summary(old_content, new_content):
    """
    ファイルの差分をAIで解析し、変更内容を要約する。
    """
    if not GOOGLE_API_KEY:
        raise EnvironmentError("GOOGLE_API_KEY 環境変数が設定されていません。")

    # 差分を生成
    diff = difflib.unified_diff(
        old_content.splitlines(), new_content.splitlines(), lineterm="", n=2
    )
    diff_text = "\n".join(diff)

    # AIに要約を依頼
    prompt = f"""
以下はあるファイルの変更差分です。
日本語で、どのような更新が行われたかを1〜2文で自然に要約してください：

```
{diff_text[:3000]}
```
"""
    # AIリクエスト（仮の関数、実際にはGoogle Generative AIライブラリを使用）
    response = requests.post(
        "https://api.generativeai.google.com/v1beta/generate",
        headers={"Authorization": f"Bearer {GOOGLE_API_KEY}"},  # GOOGLE_API_KEYを使用
        json={"prompt": prompt}
    )
    response.raise_for_status()
    return response.json()["text"].strip()

def post_to_discord(message):
    """
    Discordに通知を送信する。
    """
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def main():
    # GitHub APIからsiteディレクトリのファイルリストを取得
    files = get_github_files()
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    changes = []

    for file in files:
        if file["type"] != "file":  # ディレクトリはスキップ
            continue

        file_path = file["path"]
        file_content = requests.get(file["download_url"]).text
        file_hash = calculate_hash(file_content)
        current_hashes[file_path] = file_hash

        # ハッシュが異なる場合は変更あり
        if file_path not in previous_hashes or previous_hashes[file_path] != file_hash:
            previous_content = previous_hashes.get(file_path, "")
            summary = generate_diff_summary(previous_content, file_content)
            changes.append(f"**{file_path}**\n{summary}")

    # 変更がある場合のみ通知
    if changes:
        message = "以下のファイルが更新されました:\n" + "\n\n".join(changes)
        post_to_discord(message)

    # 現在のハッシュを保存
    save_current_hashes(current_hashes)

if __name__ == "__main__":
    main()
