import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from datetime import datetime
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
MONGO_URI = os.environ.get("MONGO_URI", "your_mongodb_uri")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "-100...")) # Jaha files store hongi
FSUB_CHANNEL_ID = int(os.environ.get("FSUB_CHANNEL_ID", "-100...")) # Force Join Channel
SUB_BOT_USER = "Aapka_Subscription_Bot_Username"

# --- DB SETUP ---
client = MongoClient(MONGO_URI)
db = client['all_in_one_bot'] 
users_col = db['users'] 
settings_col = db['settings']

app = Client("advanced_file_store", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPERS ---
def get_config():
    conf = settings_col.find_one({"id": "bot_config"})
    return conf if conf else {"delete_time": 60}

def is_prime(user_id):
    if user_id == ADMIN_ID: return True
    user = users_col.find_one({"user_id": user_id})
    return user and user.get('expiry', 0) > datetime.now().timestamp()

async def auto_delete(message, t):
    await asyncio.sleep(t)
    try: await message.delete()
    except: pass

# --- FORCE SUBSCRIBE CHECK ---
async def check_fsub(client, message):
    try:
        await client.get_chat_member(FSUB_CHANNEL_ID, message.from_user.id)
        return True
    except:
        btn = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/your_channel_link")]]
        await message.reply_text("❌ Pehle hamare channel ko join karein!", reply_markup=InlineKeyboardMarkup(btn))
        return False

# --- COMMANDS ---

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await check_fsub(client, message): return
    
    text = message.text.split()
    if len(text) > 1:
        if not is_prime(message.from_user.id):
            btn = [[InlineKeyboardButton("💳 Buy Prime Access", url=f"https://t.me/{SUB_BOT_USER}")]]
            return await message.reply_text("❌ Ye file Prime members ke liye hai. Subscription lein.", reply_markup=InlineKeyboardMarkup(btn))
        
        try:
            conf = get_config()
            f_id = int(text[1])
            sent = await client.copy_message(message.chat.id, DB_CHANNEL_ID, f_id)
            warn = await message.reply_text(f"⚠️ Ye file {conf['delete_time']}s mein delete ho jayegi!")
            asyncio.create_task(auto_delete(sent, conf['delete_time']))
            asyncio.create_task(auto_delete(warn, conf['delete_time']))
        except: await message.reply_text("File Not Found!")
        return
    await message.reply_text("👋 Bot is Online!\n\n/batch - Create Batch\n/broadcast - Send Message to All\n/setdelete - Change Timer")

@app.on_message(filters.command("setdelete") & filters.user(ADMIN_ID))
async def set_timer(client, message):
    try:
        t = int(message.text.split()[1])
        settings_col.update_one({"id": "bot_config"}, {"$set": {"delete_time": t}}, upsert=True)
        await message.reply_text(f"✅ Timer set to {t} seconds.")
    except: await message.reply_text("Use: `/setdelete 60`")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast(client, message):
    users = users_col.find({})
    for user in users:
        try: await message.reply_to_message.copy(user['user_id'])
        except: pass
    await message.reply_text("✅ Broadcast Done!")

@app.on_message(filters.user(ADMIN_ID) & (filters.video | filters.document))
async def save_file(client, message):
    db_msg = await message.copy(DB_CHANNEL_ID)
    bot_un = (await client.get_me()).username
    await message.reply_text(f"✅ **Link:** `https://t.me/{bot_un}?start={db_msg.id}`")

# --- WEB SERVER ---
web = Flask('')
@web.route('/')
def home(): return "Running"
def run(): web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    Thread(target=run).start()
    app.run()

