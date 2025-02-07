import os
import re
import logging
import requests, json
import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from datetime import timedelta
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_USER_ID = [8025763606, 6897739611]
BOT_TOKEN = "7418943426:AAF3k7oxYDSC_idoY-EHIKhCt6PTrPCaNuw"
API_URL = "https://terabox-player-apmf.onrender.com/generate"

api_id = "23635644"
api_hash = "467b556b4aa75087d3a0091578c88d3a"
notification = -1002266338823

MONGO_URI = "mongodb+srv://botplays90:botplays90@botplays.ycka9.mongodb.net/?retryWrites=true&w=majority&appName=botplays"
DB_NAME = "terabox_bot"
COLLECTION_NAME = "user_ids"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

app = Flask('')
@app.route('/')
def home():
    return "I am alive"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http_server)
    t.start()

# Initialize Telegram client
client = TelegramClient('bot', api_id=api_id, api_hash=api_hash).start(bot_token=BOT_TOKEN)

# Configure logging
logging.info("Bot is running...")

VALID_URL_PATTERN = r"https?://(1024terabox|teraboxapp|terabox|terafileshareapp|terafileshare|teraboxlink|terasharelink)\.com/\S+"

START_TIME = time.time()

@client.on(events.NewMessage(pattern='/start'))
async def send_welcome(event):
    user_id = event.sender_id
    username = event.sender.username
    name = event.sender.first_name
    collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

    notify_message = (
        f"<b>📢 New user started the terabox!</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Username:</b> @{username}\n\n"
    )

    await client.send_message(notification, notify_message, parse_mode="html")

    welcome_text = (
        f"✨ Hey **{name}**\n"
        f"👤**User-Id= `{user_id}`\n\n"
        "Welcome to the **TeraBox & TeraShare Stream Bot** 🎬💖\n\n"
        "Simply send me any **TeraBox** or **TeraShare** video link, and I'll generate a **direct streaming link** for you! 🎥💨\n\n"
        "Click the buttons below to connect with us! 😊👇"
    )

    buttons = [
        [Button.url("Owner🗿", "https://t.me/Nummasinghyadava9292"),
         Button.url("Channel 😁", "https://t.me/join_hyponet")]
    ]

    await event.respond(welcome_text, parse_mode="markdown", buttons=buttons)

@client.on(events.NewMessage(pattern='/users'))
async def send_user_ids(event):
    if event.sender_id not in ADMIN_USER_ID:
        return
    user_ids = [user["user_id"] for user in collection.find({}, {"_id": 0, "user_id": 1})]
    total_users = len(user_ids)
    user_list = "\n".join([f"{i + 1}) {user_id}" for i, user_id in enumerate(user_ids)])
    await event.respond(f"Total Users: {total_users}\n\n" + user_list)

@client.on(events.NewMessage(pattern='/broad'))
async def broadcast_message(event):
    if event.sender_id not in ADMIN_USER_ID:
        return
    message_to_broadcast = event.text[7:].strip()
    if not message_to_broadcast:
        await event.respond("❌ Please provide a message to broadcast.")
        return
    user_ids = [user["user_id"] for user in collection.find({}, {"_id": 0, "user_id": 1})]

    for user_id in user_ids:
        try:
            await client.send_message(user_id, message_to_broadcast)
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")

    await event.respond(f"✅ Broadcast completed. Sent to {len(user_ids)} users.")

@client.on(events.NewMessage(pattern='/uptime'))
async def send_uptime(event):
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))
    await event.respond(f"⏳ **Bot Uptime:** `{uptime_str}`", parse_mode="Markdown")

async def process_video(chat_id, video_url):
    try:
        if not re.match(VALID_URL_PATTERN, video_url):
            await client.send_message(chat_id, "❌ Please send a valid **TeraBox or TeraShare video link**.")
            return
        
        # ✅ FIX: Message ke ID ka sahi use
        processing_message = await client.send_message(chat_id, "⏳ Processing your video link... Please wait. 🚀")

        response = requests.post(API_URL, json={"video_url": video_url}, timeout=15)
        response.raise_for_status()
        data = response.json()

        # ✅ FIX: Pehle ka message delete ho
        await processing_message.delete()

        if "stream_link" in data:
            stream_link = data["stream_link"]
            buttons = [[Button.url("🎥 Watch Online", stream_link)]]
            await client.send_message(chat_id, "✅ Your streaming link is ready! Click below to watch 🎬", buttons=buttons)
        else:
            await client.send_message(chat_id, f"❌ Error: {data.get('error', 'Failed to generate the stream link.')}")

    except requests.exceptions.Timeout:
        await client.send_message(chat_id, "⚠️ The request timed out. Please try again later.")

    except requests.exceptions.RequestException as e:
        await client.send_message(chat_id, f"⚠️ API Error: {str(e)}")

    except Exception as e:
        await client.send_message(chat_id, f"⚠️ An unexpected error occurred: {str(e)}")

@client.on(events.NewMessage())
async def handle_message(event):
    video_url = event.text
    chat_id = event.chat_id
    if re.match(VALID_URL_PATTERN, video_url):
        asyncio.create_task(process_video(chat_id, video_url))

if __name__ == "__main__":
    keep_alive()
    logging.info("Starting bot polling...")
    client.run_until_disconnected()
