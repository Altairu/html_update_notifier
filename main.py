import requests
import os
import hashlib
import difflib
import google.generativeai as genai

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

# Google Generative AIのクライアントを初期化
genai.configure(api_key=GOOGLE_API_KEY)

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

    # モデルを指定してAIに要約を依頼
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"""
以下は、ある技術Wikiサイトにおけるファイルの更新差分です。
この変更が、利用者にとって実質的な情報の追加・変更（新しいセクションの追加、重要な情報の更新など）であるかを判定してください。

単なる改行・スペース・句読点変更・見た目の修正であれば「この変更は重要ではありません」と返答してください。
一方で、ユーザーが知るべき内容が更新されていれば、その要点を2〜4行の日本語で要約してください。

差分:
```
{diff_text[:3000]}
```
"""
    )

    # 修正: 最新の仕様に基づきレスポンスを処理
    if hasattr(response, "text"):
        return response.text.strip()
    elif hasattr(response, "candidates"):
        return response.candidates[0].content.parts[0].text.strip()
    else:
        raise ValueError("AIから有効なレスポンスが得られませんでした。")

def post_to_discord(message):
    """
    Discordに通知を送信する。
    """
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def test_network():
    """
    ネットワーク接続をテストする。
    """
    try:
        response = requests.get("https://www.google.com")
        response.raise_for_status()
        print("ネットワーク接続は正常です。")
    except Exception as e:
        print(f"ネットワーク接続に問題があります: {e}")

def main():
    # ネットワーク接続をテスト
    test_network()

    # GitHub APIからsiteディレクトリのファイルリストを取得
    files = get_github_files()
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    summaries = []  # 要約を格納するリスト

    # 差分があったファイルのみ処理
    has_changes = False
    for file in files:
        if file["type"] != "file":  # ディレクトリはスキップ
            continue

        file_path = file["path"]
        file_content = requests.get(file["download_url"]).text
        file_hash = calculate_hash(file_content)
        current_hashes[file_path] = file_hash

        # ハッシュが異なる場合は変更あり
        if file_path not in previous_hashes or previous_hashes[file_path] != file_hash:
            has_changes = True
            previous_content = previous_hashes.get(file_path, "")
            summary = generate_diff_summary(previous_content, file_content)

            # AIが「重要ではない」と判断した場合はスキップ
            if "この変更は重要ではありません" in summary:
                continue

            summaries.append(summary)  # 重要な変更のみ追加

    # 変更がない場合は終了
    if not has_changes:
        print("変更なし：Discord通知もAI呼び出しも行いません")
        return

    # 要約がある場合のみ通知
    if summaries:
        message = (
            "📝 **Webサイトに変更が加えられました！**\n\n"
            + "\n".join(f"* {s}" for s in summaries)  # 自然な文章形式で要約をリスト化
            + "\n\n🔗 https://altairu.github.io/sken_training_materials/"
        )
        post_to_discord(message)

    # 現在のハッシュを保存
    save_current_hashes(current_hashes)

if __name__ == "__main__":
    main()
