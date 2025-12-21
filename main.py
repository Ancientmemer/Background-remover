import os
import requests
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY")

app = Client(
    "bg_remover_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "👋 Hello!\n\n"
        "📸 Send me a photo\n"
        "🎯 I will remove the background for you"
    )

@app.on_message(filters.photo)
async def remove_bg(client, message):
    msg = await message.reply("⏳ Removing background...")

    photo_path = await message.download()
    output_path = "output.png"

    with open(photo_path, "rb") as img:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVEBG_API_KEY},
        )

    if response.status_code == 200:
        with open(output_path, "wb") as out:
            out.write(response.content)

        await message.reply_document(output_path, caption="✅ Background removed")
    else:
        await message.reply("❌ Failed to remove background")

    await msg.delete()
    os.remove(photo_path)
    if os.path.exists(output_path):
        os.remove(output_path)

app.run()
