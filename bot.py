import os
import json
import base64
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "8785262405:AAFoluYL_MJYX44WC8ugHUzH_yDP9sFWCxM"
GITHUB_TOKEN = "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"
GITHUB_USER = "nexora-city"
GITHUB_REPO = "nexora-news"
GITHUB_FILE = "news.json"

sessions = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def get_news_json():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "User-Agent": "NexoraBot"}
    response = requests.get(url, headers=headers)
    return response.json()

def update_news_json(content, sha):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "User-Agent": "NexoraBot"}
    data = {
        "message": "Update news via Telegram bot",
        "content": base64.b64encode(json.dumps(content, ensure_ascii=False, indent=2).encode()).decode(),
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=data)
    return response.json()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.json
    if "message" not in update:
        return "ok"

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    session = sessions.get(chat_id, {})

    if text == "/start":
        send_message(chat_id, "🎮 Nexora RP News Bot!\n\nCommands:\n/addnews - News add කරන්න\n/viewnews - News බලන්න\n/deletenews - News delete කරන්න")

    elif text == "/viewnews":
        file_data = get_news_json()
        content = json.loads(base64.b64decode(file_data["content"]).decode())
        news = content["news"]
        reply = "📰 දැනට තියෙන News:\n\n"
        for i, item in enumerate(news):
            reply += f"{i+1}. {item['title']}\n"
        send_message(chat_id, reply)

    elif text == "/addnews":
        sessions[chat_id] = {"action": "add_title"}
        send_message(chat_id, "📝 News Title එක type කරන්න:")

    elif text == "/deletenews":
        file_data = get_news_json()
        content = json.loads(base64.b64decode(file_data["content"]).decode())
        news = content["news"]
        reply = "🗑️ Delete කරන number type කරන්න:\n\n"
        for i, item in enumerate(news):
            reply += f"{i+1}. {item['title']}\n"
        sessions[chat_id] = {"action": "delete_news", "sha": file_data["sha"], "news": news}
        send_message(chat_id, reply)

    elif session.get("action") == "add_title":
        sessions[chat_id]["title"] = text
        sessions[chat_id]["action"] = "add_description"
        send_message(chat_id, "📝 Description type කරන්න:")

    elif session.get("action") == "add_description":
        sessions[chat_id]["description"] = text
        sessions[chat_id]["action"] = "add_image"
        send_message(chat_id, "🖼️ Image URL paste කරන්න:")

    elif session.get("action") == "add_image":
        sessions[chat_id]["image"] = text
        file_data = get_news_json()
        content = json.loads(base64.b64decode(file_data["content"]).decode())
        new_news = {
            "title": session["title"],
            "description": session["description"],
            "image": text
        }
        content["news"].insert(0, new_news)
        result = update_news_json(content, file_data["sha"])
        if "content" in result:
            send_message(chat_id, "✅ News add කරා! 5 minutes ඇතුළත app update වෙනවා!")
        else:
            send_message(chat_id, "❌ Error! Try again.")
        sessions.pop(chat_id, None)

    elif session.get("action") == "delete_news":
        try:
            index = int(text) - 1
            news = session["news"]
            if 0 <= index < len(news):
                news.pop(index)
                content = {"news": news}
                result = update_news_json(content, session["sha"])
                if "content" in result:
                    send_message(chat_id, "✅ News delete කරා!")
                else:
                    send_message(chat_id, "❌ Error! Try again.")
            else:
                send_message(chat_id, "❌ Invalid number!")
        except:
            send_message(chat_id, "❌ Number එකක් type කරන්න!")
        sessions.pop(chat_id, None)

    return "ok"

@app.route("/")
def index():
    return "Nexora RP Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))