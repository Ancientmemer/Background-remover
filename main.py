import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os, json, requests
from datetime import date, datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== ENV ==================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REMOVEBG_API_KEY = os.environ.get("REMOVEBG_API_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID"))

UPI_ID = os.environ.get("UPI_ID")
OWNER_USERNAME = os.environ.get("OWNER_USERNAME")

DATA_FILE = "users.json"
CONFIG_FILE = "config.json"

# ================== UPTIME ROBOT SERVER ==================
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
# ========================================================

# ================== CONFIG ==================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"premium_mode": True}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

# ================== USER DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def register_user(user_id):
    data = load_data()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {
            "count": 0,
            "date": str(date.today())
        }
        save_data(data)

def is_premium(user):
    if "premium_until" not in user:
        return False
    return datetime.strptime(user["premium_until"], "%Y-%m-%d") >= datetime.now()

def check_limit(user_id):
    cfg = load_config()
    if not cfg["premium_mode"]:
        return True, "unlimited"

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

# ================== BOT ==================
app = Client("bg_remover_bot", API_ID, API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(_, m):
    register_user(m.from_user.id)
    cfg = load_config()

    if cfg["premium_mode"]:
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌟 Get Premium", callback_data="get_premium")]]
        )
        text = (
            "👋 Welcome!\n\n"
            "🆓 Free: 3 images/day\n"
            "🌟 Premium: Unlimited\n\n"
            "📸 Send a photo to remove background\n\n"
            "ᴩᴏᴡᴇʀᴇᴅ ʙʏ: @jb_links"
        )
    else:
        kb = None
        text = (
            "👋 Welcome!\n\n"
            "🟢 Premium mode OFF\n"
            "♾ Unlimited access for everyone\n\n"
            "📸 Send a photo to remove background\n\n"
            "ᴩᴏᴡᴇʀᴇᴅ ʙʏ: @jb_links"
        )

    await m.reply(text, reply_markup=kb)

@app.on_message(filters.command("usage"))
async def usage(_, m):
    register_user(m.from_user.id)
    cfg = load_config()

    if not cfg["premium_mode"]:
        await m.reply("🟢 Premium mode is OFF\n♾ Unlimited usage")
        return

    data = load_data()
    user = data.get(str(m.from_user.id), {})
    if is_premium(user):
        await m.reply("🌟 You are a Premium user (Unlimited)")
    else:
        left = 3 - user.get("count", 0)
        await m.reply(f"🆓 Free usage left today: {max(left,0)}")

@app.on_callback_query(filters.regex("get_premium"))
async def premium_info(_, q):
    cfg = load_config()
    if not cfg["premium_mode"]:
        await q.answer("Premium mode is OFF", show_alert=True)
        return

    text = (
        "🌟 Get Premium Access\n\n"
        "Unlimited background removals 🚀\n\n"
        f"💳 UPI ID: {UPI_ID}\n\n"
        "Steps:\n"
        "1. Pay using UPI\n"
        "2. Take screenshot\n"
        f"3. Send to @{OWNER_USERNAME}\n\n"
        "Plans:\n"
        "₹29 - 7 Days\n"
        "₹89 - 30 Days\n"
        "₹199 - 1 Year"
    )

    await q.message.reply(text)
    await q.answer()

# ================== OWNER CONTROLS ==================

@app.on_message(filters.command("set_premium") & filters.user(OWNER_ID))
async def set_premium_mode(_, m):
    try:
        mode = m.text.split()[1].lower()
        cfg = load_config()

        if mode == "on":
            cfg["premium_mode"] = True
            save_config(cfg)
            await m.reply("✅ Premium mode ON")

        elif mode == "off":
            cfg["premium_mode"] = False
            save_config(cfg)
            await m.reply("🟢 Premium mode OFF\nUnlimited access enabled")

        else:
            await m.reply("❌ Usage: /set_premium on | off")
    except:
        await m.reply("❌ Usage: /set_premium on | off")

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
        await m.reply(f"✅ Premium added till {until}")
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

# ================== STATS ==================
@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(_, m):
    data = load_data()
    await m.reply(
        f"📊 Bot Stats\n\n"
        f"👥 Total users: {len(data)}"
    )
    
# ================== USERS =====================
@app.on_message(filters.command("users") & filters.user(OWNER_ID))
async def export_users(_, m):
    data = load_data()

    if not data:
        await m.reply("❌ No users found.")
        return

    filename = "users.txt"

    with open(filename, "w") as f:
        for uid in data.keys():
            f.write(f"{uid}\n")

    await m.reply_document(
        document=filename,
        caption=f"📤 Exported users list\n👥 Total users: {len(data)}"
    )

    os.remove(filename)
    
# ================== BROADCAST ==================
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(_, m):
    if not m.reply_to_message:
        await m.reply("❌ Reply to a message to broadcast.")
        return

    data = load_data()
    users = list(data.keys())
    sent, failed = 0, 0

    await m.reply(f"📢 Broadcasting to {len(users)} users...")

    for uid in users:
        try:
            await m.reply_to_message.copy(chat_id=int(uid))
            sent += 1
        except:
            failed += 1

    await m.reply(
        f"✅ Broadcast done\n\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

# ================== IMAGE HANDLER ==================
@app.on_message(filters.photo)
async def bg_remove(_, m):
    register_user(m.from_user.id)
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
    if os.path.exists(out):
        os.remove(out)
    await msg.delete()

app.run()
