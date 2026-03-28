import os
import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

# CONFIG
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_DB = os.environ.get("MONGO_DB")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
CHANNEL = os.environ.get("CHANNEL")  # @channelusername

# DB
mongo = MongoClient(MONGO_DB)
db = mongo["file_store"]
files = db["files"]
settings = db["settings"]

# BOT
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# AUTO DELETE TIME
def get_time():
    data = settings.find_one({"_id": "time"})
    return data["time"] if data else 300

# CHECK JOIN
async def is_joined(client, user_id):
    try:
        member = await client.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id

    # FORCE SUB CHECK
    if not await is_joined(client, user_id):
        btn = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL.replace('@','')}")],
                [InlineKeyboardButton("✅ Check Again", callback_data="checksub")]
            ]
        )
        return await message.reply("🚫 पहले channel join करो!", reply_markup=btn)

    # FILE GET
    if len(message.command) > 1:
        file_id = base64.urlsafe_b64decode(message.command[1].encode()).decode()
        msg = await message.reply_document(file_id)

        # AUTO DELETE
        time = get_time()
        await asyncio.sleep(time)
        await msg.delete()
        await message.delete()
    else:
        await message.reply("👋 Send file to store")

# CHECK BUTTON
@app.on_callback_query(filters.regex("checksub"))
async def check_sub(client, callback_query):
    user_id = callback_query.from_user.id

    if await is_joined(client, user_id):
        await callback_query.message.delete()
        await callback_query.message.reply("✅ अब access मिल गया, /start फिर से दबाओ")
    else:
        await callback_query.answer("❌ अभी join नहीं किया", show_alert=True)

# HELP
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply("""
📌 Commands:
/start - Start
/help - Help
/settime 60 - Auto delete (admin)
/batch - Batch upload (admin)

📂 Send file to store
""")

# SET TIME
@app.on_message(filters.command("settime") & filters.user(ADMIN_ID))
async def set_time(client, message):
    try:
        t = int(message.command[1])
        settings.update_one({"_id": "time"}, {"$set": {"time": t}}, upsert=True)
        await message.reply(f"✅ Time set {t} sec")
    except:
        await message.reply("❌ Use /settime 60")

# SAVE FILE
@app.on_message(filters.document | filters.video | filters.audio)
async def save_file(client, message):
    file_id = message.document.file_id if message.document else \
              message.video.file_id if message.video else \
              message.audio.file_id

    files.insert_one({"file_id": file_id})

    encoded = base64.urlsafe_b64encode(file_id.encode()).decode()
    link = f"https://t.me/{(await client.get_me()).username}?start={encoded}"

    await message.reply(f"✅ Saved!\n🔗 {link}")

# BATCH
batch_mode = {}

@app.on_message(filters.command("batch") & filters.user(ADMIN_ID))
async def batch(client, message):
    batch_mode[message.from_user.id] = True
    await message.reply("📂 Send files now")

@app.on_message(filters.document & filters.user(ADMIN_ID))
async def batch_save(client, message):
    if batch_mode.get(message.from_user.id):
        files.insert_one({"file_id": message.document.file_id})
        await message.reply("✅ Added")

@app.on_message(filters.command("stop") & filters.user(ADMIN_ID))
async def stop_batch(client, message):
    batch_mode[message.from_user.id] = False
    await message.reply("🛑 Batch stopped")

# RUN
app.run()
