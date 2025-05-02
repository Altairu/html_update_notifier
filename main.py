import os
import requests
import hashlib
import bs4

# 定数
GITHUB_API_URL_BASE = "https://api.github.com/repos/Altairu/sken_training_materials/contents/site"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PREVIOUS_HASHES_PATH = "previous_hashes.txt"

def get_all_files_from_github(path="site"):
    files = []
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/Altairu/sken_training_materials/contents/{path}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    contents = response.json()

    for item in contents:
        if item["type"] == "file" and item["name"].endswith(".html"):
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

def extract_title_from_html(html_text, fallback_name):
    soup = bs4.BeautifulSoup(html_text, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return fallback_name

def post_to_discord(message):
    if not message.strip():
        print("空のメッセージは送信されません。")
        return

    if len(message) > 2000:
        message = message[:1997] + "..."

    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

def main():
    files = get_all_files_from_github()
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    updates = []

    for file in files:
        file_path = file["path"]
        download_url = file["download_url"]
        file_content = requests.get(download_url).text
        file_hash = calculate_hash(file_content)
        current_hashes[file_path] = file_hash

        # 新規または変更されたファイルのみ通知対象
        if file_path not in previous_hashes or previous_hashes[file_path] != file_hash:
            file_name = os.path.basename(file_path)
            title = extract_title_from_html(file_content, file_name)
            change_type = "追加" if file_path not in previous_hashes else "変更"
            updates.append(f"- **{title}**（{change_type}：`{file_path}`）")

    if updates:
        message = (
            "📝 **Webサイトに新しいページ追加または更新がありました！**\n\n"
            + "\n".join(updates)
            + "\n\n🔗 https://altairu.github.io/sken_training_materials/"
        )
        post_to_discord(message)
        save_current_hashes(current_hashes)
    else:
        print("変更されたページはありません。通知は行われません。")

if __name__ == "__main__":
    main()