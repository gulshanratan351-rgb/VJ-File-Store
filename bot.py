import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- अपनी डिटेल्स यहाँ भरें ---
API_ID = 1234567  # अपना API ID डालें
API_HASH = "your_api_hash"  # अपना API HASH डालें
BOT_TOKEN = "your_bot_token"  # अपना बॉट टोकन डालें
DB_CHANNEL = -100123456789  # अपना चैनल ID (जहां फाइल सेव होगी)
# MongoDB URL: mongodb+srv://user:pass@cluster.mongodb.net/test
MONGODB_URI = "your_mongodb_url" 

# --- बॉट सेटअप ---
app = Client(
    "FileStoreBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    if len(message.command) > 1:
        # अगर यूजर लिंक पर क्लिक करके आया है
        file_id = int(message.command[1])
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=DB_CHANNEL,
                message_id=file_id
            )
        except Exception as e:
            await message.reply(f"Error: फाइल नहीं मिली!\n{e}")
    else:
        await message.reply("नमस्ते! मुझे कोई भी फाइल भेजें, मैं उसका Permanent Link बना दूंगा।")

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def store_file(client, message):
    # फाइल को आपके चैनल में भेजना
    sent_msg = await message.forward(DB_CHANNEL)
    
    # शेयरिंग लिंक बनाना
    bot_username = (await client.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={sent_msg.id}"
    
    # यूजर को रिप्लाई देना
    await message.reply(
        f"✅ **आपकी फाइल स्टोर हो गई है!**\n\n🔗 **लिंक:** `{share_link}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Open File 📂", url=share_link)]
        ])
    )

print("बॉट चालू हो गया है... अपना टेलीग्राम चेक करें!")
app.run()
