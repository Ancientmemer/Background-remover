import os, json, requests
from datetime import date, datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID"))

UPI_ID = os.environ.get("UPI_ID")
QR_IMAGE_URL = os.environ.get("UPI_QR_URL")
OWNER_USERNAME = os.environ.get("OWNER_USERNAME")

DATA_FILE = "users.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def is_premium(user):
    if "premium_until" not in user:
        return False
    return datetime.strptime(user["premium_until"], "%Y-%m-%d") >= datetime.now()

def check_limit(user_id):
    data = load_data()
    today = str(date.today())
    uid = str(user_id)

    user = data.get(uid, {"count": 0, "date": today})

    if is_premium(user):
        return True, "premium"

    if user.get("date") != today:
        user["count"] = 0
        user["date"] = today

    if user["count"] >= 3:
        return False, "limit"

    user["count"] += 1
    data[uid] = user
    save_data(data)
    return True, f"{3 - user['count']} left"

app = Client("bg_remover_bot", API_ID, API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(_, m):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🌟 Get Premium", callback_data="get_premium")]]
    )
    await m.reply(
        "👋 Welcome!\n\n"
        "🆓 Free: 3 images/day\n"
        "🌟 Premium: Unlimited\n\n"
        "📸 Send a photo to remove background",
        reply_markup=kb
    )

@app.on_message(filters.command("usage"))
async def usage(_, m):
    data = load_data()
    user = data.get(str(m.from_user.id), {})
    if is_premium(user):
        await m.reply("🌟 You are a **Premium user** (Unlimited)")
    else:
        left = 3 - user.get("count", 0)
        await m.reply(f"🆓 Free usage left today: **{max(left,0)}**")

@app.on_callback_query(filters.regex("get_premium"))
async def premium_info(_, q):
    text = (
        "🌟 **Get Premium Access**\n\n"
        "Unlimited background removals 🚀\n\n"
        f"💳 **UPI ID:** `{UPI_ID}`\n\n"
        "📌 **Steps:**\n"
        "1️⃣ Make payment using the UPI ID / QR code\n"
        "2️⃣ Take a screenshot of payment\n"
        f"3️⃣ Send the screenshot to 👉 @{OWNER_USERNAME}\n\n"
        "⏳ Premium will be activated after verification\n\n"
        "🌟 Premium Plans 🌟\n\n"
        "🌟 ₹29 - 7 Days\n"
        "🌟 ₹89 - 30 Days\n"
        "🌟 ₹199 - 1 Year"
    )
    await q.message.reply_photo(QR_IMAGE_URL, caption=text)
    await q.answer()

@app.on_message(filters.command("premium") & filters.user(OWNER_ID))
async def add_premium(_, m):
    try:
        _, uid, days = m.text.split()
        days = int(days)
        data = load_data()
        until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        user = data.get(uid, {})
        user["premium_until"] = until
        data[uid] = user
        save_data(data)
        await m.reply(f"✅ Premium added till **{until}**")
    except:
        await m.reply("❌ Usage: /premium <user_id> <days>")

@app.on_message(filters.command("unpremium") & filters.user(OWNER_ID))
async def remove_premium(_, m):
    try:
        uid = m.text.split()[1]
        data = load_data()
        if uid in data and "premium_until" in data[uid]:
            del data[uid]["premium_until"]
            save_data(data)
        await m.reply("❌ Premium removed")
    except:
        await m.reply("❌ Usage: /unpremium <user_id>")

@app.on_message(filters.photo)
async def bg_remove(_, m):
    allowed, status = check_limit(m.from_user.id)
    if not allowed:
        await m.reply("🚫 Daily limit reached.\n🌟 Get Premium for unlimited usage.")
        return

    msg = await m.reply("⏳ Removing background...")
    photo = await m.download()
    out = "output.png"

    with open(photo, "rb") as img:
        r = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img},
            headers={"X-Api-Key": REMOVEBG_API_KEY},
        )

    if r.status_code == 200:
        open(out, "wb").write(r.content)
        await m.reply_document(out, caption="✅ Background removed")
    else:
        await m.reply("❌ Failed")

    os.remove(photo)
    if os.path.exists(out): os.remove(out)
    await msg.delete()

app.run()
