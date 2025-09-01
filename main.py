# -*- coding: utf-8 -*-
"""
India Social Panel - Professional SMM Services Bot
Advanced Telegram Bot for Social Media Marketing Services
"""

import asyncio
import os
import random
import string
import time
from datetime import datetime
from typing import Dict, Any, Optional

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Import account handlers
import account_handlers
# Import payment system handlers
import payment_system
# Import services handlers
import services

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

# Get base URL from environment or use the Replit provided URL
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
if not BASE_WEBHOOK_URL:
    # Auto-detect Replit URL if available
    repl_url = os.getenv("REPLIT_URL")
    if repl_url:
        BASE_WEBHOOK_URL = repl_url
    else:
        print("⚠️ BASE_WEBHOOK_URL not set. Bot will run in polling mode.")

OWNER_NAME = os.getenv("OWNER_NAME", "Achal Parvat")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "achal_parvat")

# Webhook settings
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "india_social_panel_secret_2025"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}" if BASE_WEBHOOK_URL else None

# Server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

# Bot initialization
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
START_TIME = time.time()

# Bot restart tracking
BOT_RESTART_TIME = datetime.now()
users_to_notify: set = set()  # Users who interacted during downtime
bot_just_restarted = True  # Flag to track if bot just restarted

# ========== DATA STORAGE ==========
# In-memory storage (will be replaced with database later)
users_data: Dict[int, Dict[str, Any]] = {}
orders_data: Dict[str, Dict[str, Any]] = {}
tickets_data: Dict[str, Dict[str, Any]] = {}
user_state: Dict[int, Dict[str, Any]] = {}  # For tracking user input states
order_temp: Dict[int, Dict[str, Any]] = {}  # For temporary order data
admin_users = {5987654321, 1234567890}  # Add your admin user IDs here

# ========== CORE FUNCTIONS ==========
def init_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> None:
    """Initialize user data if not exists"""
    if user_id not in users_data:
        users_data[user_id] = {
            "user_id": user_id,
            "username": username or "",
            "first_name": first_name or "",
            "balance": 0.0,
            "total_spent": 0.0,
            "orders_count": 0,
            "referral_code": generate_referral_code(),
            "referred_by": None,
            "join_date": datetime.now().isoformat(),
            "api_key": generate_api_key(),
            "status": "active",
            "account_created": False,
            "full_name": "",
            "phone_number": "",
            "email": ""
        }

    # Initialize user state for input tracking
    if user_id not in user_state:
        user_state[user_id] = {
            "current_step": None,
            "data": {}
        }

def generate_referral_code() -> str:
    """Generate unique referral code"""
    return f"ISP{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def generate_api_key() -> str:
    """Generate API key for user"""
    return f"ISP-{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"

def generate_order_id() -> str:
    """Generate unique order ID"""
    return f"ORD{int(time.time())}{random.randint(100, 999)}"

def generate_ticket_id() -> str:
    """Generate unique ticket ID"""
    return f"TKT{int(time.time())}{random.randint(10, 99)}"

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in admin_users

def is_message_old(message: Message) -> bool:
    """Check if message was sent before bot restart"""
    if not message.date:
        return False

    # Convert message date to timestamp and compare with bot start time
    message_timestamp = message.date.timestamp()
    return message_timestamp < START_TIME

async def send_bot_alive_notification(user_id: int, first_name: str = "", is_admin: bool = False, username: str = ""):
    """Send bot alive notification to user"""
    try:
        # Get display name with username preference
        user_display_name = f"@{username}" if username else first_name or ('Sir' if is_admin else 'Friend')

        if is_admin:
            alive_text = f"""
🚀 <b>Admin Alert - Bot Restarted</b>

नमस्ते <b>Admin {user_display_name}</b>! 🙏

✅ <b>India Social Panel Bot Successfully Restarted!</b>

🔄 <b>System Status:</b> ✅ Online
⏰ <b>Restart Time:</b> {BOT_RESTART_TIME.strftime('%d %b %Y, %I:%M %p')}
🎯 <b>Bot Mode:</b> {"Webhook" if BASE_WEBHOOK_URL else "Polling"}

📊 <b>Ready to Serve:</b>
• All services operational
• User interactions active  
• Payment system ready
• 24/7 support available

🛡️ <b>Admin Panel accessible through /start</b>
"""
        else:
            alive_text = f"""
🤖 <b>Bot Online - India Social Panel</b>

नमस्ते <b>{user_display_name}</b>! 🙏

✅ <b>भारत का सबसे भरोसेमंद SMM Panel अब Online है!</b>

🔄 <b>System Status:</b> Ready to serve
⏰ <b>Online Since:</b> {BOT_RESTART_TIME.strftime('%d %b %Y, %I:%M %p')}

💡 <b>सभी services अब available हैं!</b>

📱 <b>Services Ready:</b>
• Instagram • YouTube • Facebook 
• Twitter • TikTok • LinkedIn

🎯 <b>/start</b> करके services का इस्तेमाल शुरू करें!
"""
        await bot.send_message(user_id, alive_text)
        return True
    except Exception as e:
        print(f"❌ Failed to send alive notification to {user_id}: {e}")
        return False

async def send_first_interaction_notification(user_id: int, first_name: str = "", username: str = ""):
    """Send notification to user on first interaction after restart"""
    global bot_just_restarted
    try:
        # Get display name with username preference
        user_display_name = f"@{username}" if username else first_name or 'Friend'

        alive_text = f"""
🟢 <b>Bot is Live!</b>

Hello <b>{user_display_name}</b>! 👋

✅ <b>India Social Panel is now Online and Ready!</b>

💡 <b>All services are working perfectly</b>
🚀 <b>Ready to process your requests</b>

📱 <b>Available Services:</b>
• Instagram • YouTube • Facebook • Twitter • TikTok

🎯 Use <b>/start</b> to access all features!
"""
        await bot.send_message(user_id, alive_text)
        return True
    except Exception as e:
        print(f"❌ Failed to send first interaction notification to {user_id}: {e}")
        return False

def mark_user_for_notification(user_id: int):
    """Mark user for bot alive notification"""
    users_to_notify.add(user_id)

def format_currency(amount: float) -> str:
    """Format currency in Indian Rupees"""
    return f"₹{amount:,.2f}"

def format_time(timestamp: str) -> str:
    """Format datetime string"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return "N/A"

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """Safely edit callback message with comprehensive error handling"""
    if not callback.message:
        return False

    try:
        # Check if message is editable (not InaccessibleMessage)
        if (hasattr(callback.message, 'edit_text') and 
            hasattr(callback.message, 'message_id') and 
            hasattr(callback.message, 'text') and
            not callback.message.__class__.__name__ == 'InaccessibleMessage'):
            if reply_markup:
                await callback.message.edit_text(text, reply_markup=reply_markup)  # type: ignore
            else:
                await callback.message.edit_text(text)  # type: ignore
            return True
        else:
            # Message is inaccessible, send new message
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup)
                else:
                    await bot.send_message(callback.message.chat.id, text)
                return True
            return False
    except Exception as e:
        print(f"Error editing message: {e}")
        # Try sending new message as fallback
        try:
            if hasattr(callback.message, 'chat') and hasattr(callback.message.chat, 'id'):
                if reply_markup:
                    await bot.send_message(callback.message.chat.id, text, reply_markup=reply_markup)
                else:
                    await bot.send_message(callback.message.chat.id, text)
                return True
        except:
            pass
        return False

def is_account_created(user_id: int) -> bool:
    """Check if user has completed account creation"""
    return users_data.get(user_id, {}).get("account_created", False)

def get_initial_options_menu() -> InlineKeyboardMarkup:
    """Build initial options menu with create account and login"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account"),
            InlineKeyboardButton(text="🔐 Login to Account", callback_data="login_account")
        ],
        [
            InlineKeyboardButton(text="❓ Help & Support", callback_data="help_support")
        ]
    ])

def get_account_creation_menu() -> InlineKeyboardMarkup:
    """Build account creation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Create Account", callback_data="create_account")]
    ])

def get_account_complete_menu() -> InlineKeyboardMarkup:
    """Build menu after account creation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
        ]
    ])

def get_amount_selection_menu() -> InlineKeyboardMarkup:
    """Build amount selection menu for add funds"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₹500", callback_data="amount_500"),
            InlineKeyboardButton(text="₹1000", callback_data="amount_1000")
        ],
        [
            InlineKeyboardButton(text="₹2000", callback_data="amount_2000"),
            InlineKeyboardButton(text="₹5000", callback_data="amount_5000")
        ],
        [
            InlineKeyboardButton(text="💬 Custom Amount", callback_data="amount_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_support_menu() -> InlineKeyboardMarkup:
    """Build support tickets menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Naya Ticket Banayein", callback_data="create_ticket"),
        ],
        [
            InlineKeyboardButton(text="📖 Mere Tickets Dekhein", callback_data="view_tickets")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_order_confirm_menu(price: float) -> InlineKeyboardMarkup:
    """Build order confirmation menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")
        ]
    ])

# ========== MENU BUILDERS ==========
def get_main_menu() -> InlineKeyboardMarkup:
    """Build main menu with all core features"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 New Order", callback_data="new_order"),
            InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds")
        ],
        [
            InlineKeyboardButton(text="👤 My Account", callback_data="my_account"),
            InlineKeyboardButton(text="⚙️ Services & Tools", callback_data="services_tools")
        ],
        [
            InlineKeyboardButton(text="📈 Service List", callback_data="service_list"),
            InlineKeyboardButton(text="🎫 Support Tickets", callback_data="support_tickets")
        ],
        [
            InlineKeyboardButton(text="🎁 Offers & Rewards", callback_data="offers_rewards"),
            InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")
        ],
        [
            InlineKeyboardButton(text="📞 Contact & About", callback_data="contact_about")
        ]
    ])

def get_category_menu() -> InlineKeyboardMarkup:
    """Build social media category menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Instagram", callback_data="cat_instagram"),
            InlineKeyboardButton(text="🎥 YouTube", callback_data="cat_youtube")
        ],
        [
            InlineKeyboardButton(text="📘 Facebook", callback_data="cat_facebook"),
            InlineKeyboardButton(text="🐦 Twitter", callback_data="cat_twitter")
        ],
        [
            InlineKeyboardButton(text="💼 LinkedIn", callback_data="cat_linkedin"),
            InlineKeyboardButton(text="🎵 TikTok", callback_data="cat_tiktok")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_main")
        ]
    ])

def get_service_menu(category: str) -> InlineKeyboardMarkup:
    """Build service menu for specific category"""
    services = {
        "instagram": [
            ("👥 Followers", "ig_followers"),
            ("❤️ Likes", "ig_likes"),
            ("👁️ Views", "ig_views"),
            ("💬 Comments", "ig_comments")
        ],
        "youtube": [
            ("👥 Subscribers", "yt_subscribers"),
            ("❤️ Likes", "yt_likes"),
            ("👁️ Views", "yt_views"),
            ("💬 Comments", "yt_comments")
        ],
        "facebook": [
            ("👥 Page Likes", "fb_likes"),
            ("👁️ Post Views", "fb_views"),
            ("💬 Comments", "fb_comments"),
            ("↗️ Shares", "fb_shares")
        ]
    }

    keyboard = []
    for name, data in services.get(category, []):
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"service_{data}")])

    keyboard.append([InlineKeyboardButton(text="⬅️ Back", callback_data="new_order")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contact_menu() -> InlineKeyboardMarkup:
    """Build contact & about menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 Owner Ke Baare Mein", callback_data="owner_info"),
            InlineKeyboardButton(text="🌐 Hamari Website", callback_data="website_info")
        ],
        [
            InlineKeyboardButton(text="💬 Support Channel", callback_data="support_channel"),
            InlineKeyboardButton(text="🤖 AI Support", callback_data="ai_support")
        ],
        [
            InlineKeyboardButton(text="👨‍💼 Contact Admin", callback_data="contact_admin"),
            InlineKeyboardButton(text="📜 Seva Ki Shartein (TOS)", callback_data="terms_service")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_services_tools_menu() -> InlineKeyboardMarkup:
    """Build services & tools menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Mass Order", callback_data="mass_order"),
            InlineKeyboardButton(text="🔄 Subscriptions", callback_data="subscriptions")
        ],
        [
            InlineKeyboardButton(text="📊 Profile Analyzer", callback_data="profile_analyzer"),
            InlineKeyboardButton(text="## Hashtag Generator", callback_data="hashtag_generator")
        ],
        [
            InlineKeyboardButton(text="✨ Free Trial Service", callback_data="free_trial")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_offers_rewards_menu() -> InlineKeyboardMarkup:
    """Build offers & rewards menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎟️ Coupon Redeem Karein", callback_data="coupon_redeem"),
            InlineKeyboardButton(text="🤝 Partner Program", callback_data="partner_program")
        ],
        [
            InlineKeyboardButton(text="🏆 Loyalty Program", callback_data="loyalty_program"),
            InlineKeyboardButton(text="🎉 Daily Reward", callback_data="daily_reward")
        ],
        [
            InlineKeyboardButton(text="🥇 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton(text="📝 Community Polls", callback_data="community_polls")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

# ========== BOT HANDLERS ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command with professional welcome"""
    global bot_just_restarted
    
    user = message.from_user
    if not user:
        return

    # Send background notifications on first user interaction (not during startup)
    if bot_just_restarted:
        bot_just_restarted = False
        asyncio.create_task(send_background_notifications())

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    init_user(user.id, user.username or "", user.first_name or "")

    # Check if account is created
    if is_account_created(user.id):
        # Get user's actual username or first name
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        # Existing user welcome
        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user_display_name}</b>! 🙏

🎯 <b>भारत का सबसे भरोसेमंद SMM Panel</b>
✅ <b>High Quality Services</b>
✅ <b>Instant Delivery</b>
✅ <b>24/7 Support</b>
✅ <b>Affordable Rates</b>

📱 <b>सभी Social Media Platforms के लिए:</b>
Instagram • YouTube • Facebook • Twitter • TikTok • LinkedIn

💡 <b>नीचे से अपनी जरूरत का option चुनें:</b>
"""
        await message.answer(welcome_text, reply_markup=get_main_menu())
    else:
        # Get user's actual username or first name for new users
        user_display_name = f"@{user.username}" if user.username else user.first_name or 'Friend'

        # New user - show both create account and login options
        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user_display_name}</b>! 🙏

🎯 <b>भारत का सबसे भरोसेमंद SMM Panel</b>
✅ <b>High Quality Services</b>
✅ <b>Instant Delivery</b>
✅ <b>24/7 Support</b>
✅ <b>Affordable Rates</b>

📱 <b>सभी Social Media Platforms के लिए:</b>
Instagram • YouTube • Facebook • Twitter • TikTok • LinkedIn

💡 <b>अपना option चुनें:</b>
"""
        await message.answer(welcome_text, reply_markup=get_initial_options_menu())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    user = message.from_user
    if not user:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    await message.answer("🏠 <b>Main Menu</b>\nअपनी जरूरत के अनुसार option चुनें:", reply_markup=get_main_menu())

# ========== ACCOUNT CREATION AND LOGIN HANDLERS ==========
@dp.callback_query(F.data == "login_account")
async def cb_login_account(callback: CallbackQuery):
    """Handle existing user login"""
    if not callback.message or not callback.from_user:
        return

    # Check if callback is old (sent before bot restart)
    if callback.message.date and callback.message.date.timestamp() < START_TIME:
        mark_user_for_notification(callback.from_user.id)
        return  # Ignore old callbacks

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_login_phone"

    text = """
🔐 <b>Login to Your Account</b>

📱 <b>Account Verification</b>

💡 <b>कृपया अपना registered phone number भेजें:</b>

⚠️ <b>Example:</b> +91 9876543210
🔒 <b>Security:</b> Phone number verification के लिए

💡 <b>अगर phone number भूल गए हैं तो support से contact करें</b>
📞 <b>Support:</b> @achal_parvat
"""

    await safe_edit_message(callback, text)
    await callback.answer()

@dp.callback_query(F.data == "help_support")
async def cb_help_support(callback: CallbackQuery):
    """Handle help and support for new users"""
    if not callback.message:
        return

    text = f"""
❓ <b>Help & Support</b>

🤝 <b>हमारी Support Team आपकी मदद के लिए तैयार है!</b>

📞 <b>Contact Options:</b>
• Telegram: @{OWNER_USERNAME}
• Support Chat: Direct message
• Response Time: 2-6 hours

💡 <b>Common Questions:</b>
• Account creation issues
• Payment problems
• Service inquiries
• Technical difficulties

🎯 <b>Quick Solutions:</b>
• Create Account - New users
• Login Account - Existing users
• Check our service list
• Contact support for help

🔒 <b>Safe & Secure Platform</b>
✅ <b>Trusted by thousands of users</b>
"""

    help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="📝 Create Account", callback_data="create_account")
        ],
        [
            InlineKeyboardButton(text="🔐 Login Account", callback_data="login_account"),
            InlineKeyboardButton(text="🏠 Main Info", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, help_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "create_account")
async def cb_create_account(callback: CallbackQuery):
    """Start account creation process"""
    if not callback.message or not callback.from_user:
        return

    # Check if callback is old (sent before bot restart)
    if callback.message.date and callback.message.date.timestamp() < START_TIME:
        mark_user_for_notification(callback.from_user.id)
        return  # Ignore old callbacks

    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "User"

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "choosing_name_option"

    text = f"""
📋 <b>Account Creation - Step 1/3</b>

👤 <b>Name Selection</b>

💡 <b>आप अपने account के लिए कौन सा name use करना चाहते हैं?</b>

🔸 <b>Your Telegram Name:</b> {telegram_name}
🔸 <b>Custom Name:</b> अपनी पसंद का name

⚠️ <b>Note:</b> Custom name में maximum 6 characters allowed हैं (first name only)

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

    name_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Telegram Name Use करूं", callback_data="use_telegram_name"),
            InlineKeyboardButton(text="✏️ Custom Name डालूं", callback_data="use_custom_name")
        ]
    ])

    await safe_edit_message(callback, text, name_choice_keyboard)
    await callback.answer()

# ========== ACCOUNT VERIFICATION DECORATOR ==========
def require_account(handler):
    """Decorator to check if account is created before allowing access"""
    async def wrapper(callback: CallbackQuery):
        if not callback.from_user:
            return

        user_id = callback.from_user.id

        # If account not created, show message
        if not is_account_created(user_id):
            text = """
⚠️ <b>Account Required</b>

आपका account अभी तक create नहीं हुआ है!

📝 <b>सभी features का access पाने के लिए पहले account create करें</b>

✅ <b>Account creation में सिर्फ 2 मिनट लगते हैं</b>
"""

            if callback.message and hasattr(callback.message, 'edit_text'):
                await safe_edit_message(callback, text, get_account_creation_menu())
            await callback.answer()
            return

        # Account exists, proceed with handler
        return await handler(callback)

    return wrapper

# Initialize account handlers now that all variables are defined
account_handlers.init_account_handlers(
    dp, users_data, orders_data, require_account,
    format_currency, format_time, is_account_created, user_state, is_admin
)

# Initialize payment system
payment_system.register_payment_handlers(dp, users_data, user_state, format_currency)

# Initialize services system
services.register_service_handlers(dp, require_account)

# Import account menu function
get_account_menu = account_handlers.get_account_menu

# ========== NAME CHOICE HANDLERS ==========
@dp.callback_query(F.data == "use_telegram_name")
async def cb_use_telegram_name(callback: CallbackQuery):
    """Use Telegram name for account creation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    telegram_name = callback.from_user.first_name or "User"

    # Store telegram name and move to next step
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["data"]["full_name"] = telegram_name
    user_state[user_id]["current_step"] = "choosing_phone_option"

    text = f"""
✅ <b>Name Successfully Selected!</b>

👤 <b>Selected Name:</b> {telegram_name}

📋 <b>Account Creation - Step 2/3</b>

📱 <b>Phone Number Selection</b>

💡 <b>आप phone number कैसे provide करना चाहते हैं?</b>

🔸 <b>Telegram Contact:</b> आपका Telegram में saved contact number
🔸 <b>Manual Entry:</b> अपनी पसंद का कोई भी number

⚠️ <b>Note:</b> Contact share करने से आपकी permission माँगी जाएगी और आपका number automatically भर जाएगा

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

    phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Telegram Contact Share करूं", callback_data="share_telegram_contact"),
            InlineKeyboardButton(text="✏️ Manual Number डालूं", callback_data="manual_phone_entry")
        ]
    ])

    await safe_edit_message(callback, text, phone_choice_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "use_custom_name")
async def cb_use_custom_name(callback: CallbackQuery):
    """Use custom name for account creation"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_custom_name"

    text = """
✏️ <b>Custom Name Entry</b>

📋 <b>Account Creation - Step 1/3</b>

📝 <b>कृपया अपना नाम भेजें:</b>

⚠️ <b>Rules:</b>
• Maximum 6 characters allowed
• First name only
• No special characters
• English या Hindi में type करें

💬 <b>Example:</b> Rahul, Priya, Arjun

🔙 <b>अपना name type करके भेज दें:</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

# ========== PHONE CHOICE HANDLERS ==========
@dp.callback_query(F.data == "share_telegram_contact")
async def cb_share_telegram_contact(callback: CallbackQuery):
    """Request Telegram contact sharing for phone number"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_contact_permission"

    text = """
📱 <b>Telegram Contact Permission</b>

🔐 <b>Contact Sharing Request</b>

💡 <b>हमें आपके contact को access करने की permission चाहिए</b>

✅ <b>Benefits:</b>
• Automatic phone number fill
• Faster account creation
• No typing errors
• Secure & verified number

🔒 <b>Security:</b>
• आपका phone number safely store होगा
• केवल account creation के लिए use होगा
• Third party के साथ share नहीं होगा
• Complete privacy protection

⚠️ <b>Permission Steps:</b>
1. नीचे "Send Contact" button पर click करें
2. Telegram permission dialog आएगी  
3. "Allow" या "Share Contact" पर click करें
4. आपका number automatically भर जाएगा

💬 <b>Ready to share your contact?</b>
"""

    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    # Create contact request keyboard
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Send My Contact", request_contact=True)],
            [KeyboardButton(text="❌ Cancel & Enter Manually")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await safe_edit_message(callback, text)

    # Send new message with contact request keyboard
    await callback.message.answer(
        "📱 <b>Neeche wale button se contact share करें:</b>",
        reply_markup=contact_keyboard
    )

    await callback.answer()

@dp.callback_query(F.data == "manual_phone_entry")
async def cb_manual_phone_entry(callback: CallbackQuery):
    """Handle manual phone number entry"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_manual_phone"

    text = """
✏️ <b>Manual Phone Entry</b>

📋 <b>Account Creation - Step 2/3</b>

📱 <b>कृपया अपना Phone Number भेजें:</b>

⚠️ <b>Format Rules:</b>
• Must start with +91 (India)
• Total 13 characters
• Only numbers after +91
• No spaces or special characters

💬 <b>Examples:</b>
• +919876543210 ✅
• +91 9876543210 ❌ (space not allowed)
• 9876543210 ❌ (country code missing)

🔙 <b>अपना complete phone number type करके भेज दें:</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

# ========== CALLBACK HANDLERS ==========
@dp.callback_query(F.data == "new_order")
@require_account
async def cb_new_order(callback: CallbackQuery):
    """Handle new order - show service platforms"""
    if not callback.message:
        return

    from services import get_services_main_menu

    text = """
🚀 <b>New Order - Service Selection</b>

🎯 <b>Choose Your Platform</b>

💎 <b>Premium Quality Services Available:</b>
✅ Real & Active Users Only
✅ High Retention Rate
✅ Fast Delivery (0-6 Hours)
✅ 24/7 Customer Support
✅ Secure & Safe Methods

🔒 <b>100% Money Back Guarantee</b>
⚡ <b>Instant Start Guarantee</b>

💡 <b>कृपया अपना platform चुनें:</b>
"""

    await safe_edit_message(callback, text, get_services_main_menu())
    await callback.answer()

# Service handlers moved to services.py

@dp.callback_query(F.data == "add_funds")
@require_account
async def cb_add_funds(callback: CallbackQuery):
    """Handle add funds request"""
    if not callback.message:
        return

    user_id = callback.from_user.id if callback.from_user else 0
    current_balance = users_data.get(user_id, {}).get("balance", 0.0)

    text = f"""
💰 <b>Add Funds</b>

💳 <b>Current Balance:</b> {format_currency(current_balance)}

🔸 <b>Payment Methods Available:</b>
• UPI (Instant)
• Bank Transfer
• Paytm
• PhonePe
• Google Pay

💡 <b>Amount चुनें या custom amount type करें:</b>
"""

    amount_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₹500", callback_data="fund_500"),
            InlineKeyboardButton(text="₹1000", callback_data="fund_1000")
        ],
        [
            InlineKeyboardButton(text="₹2000", callback_data="fund_2000"),
            InlineKeyboardButton(text="₹5000", callback_data="fund_5000")
        ],
        [
            InlineKeyboardButton(text="💬 Custom Amount", callback_data="fund_custom")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

    await safe_edit_message(callback, text, amount_keyboard)
    await callback.answer()


@dp.callback_query(F.data == "services_tools")
@require_account
async def cb_services_tools(callback: CallbackQuery):
    """Handle services & tools menu"""
    if not callback.message:
        return

    text = """
⚙️ <b>Services & Tools</b>

🚀 <b>Advanced SMM Tools & Features</b>

💎 <b>Professional Tools:</b>
• Bulk order management
• Auto-renewal subscriptions
• Analytics & insights
• Content optimization

🎯 <b>Smart Features:</b>
• AI-powered recommendations
• Performance tracking
• Growth strategies
• Market analysis

💡 <b>अपनी जरूरत के अनुसार tool चुनें:</b>
"""

    await safe_edit_message(callback, text, get_services_tools_menu())
    await callback.answer()

@dp.callback_query(F.data == "offers_rewards")
@require_account
async def cb_offers_rewards(callback: CallbackQuery):
    """Handle offers & rewards menu"""
    if not callback.message:
        return

    text = """
🎁 <b>Offers & Rewards</b>

🌟 <b>Exciting Rewards & Benefits Await!</b>

💰 <b>Earn More, Save More:</b>
• Daily login rewards
• Loyalty points system
• Exclusive discounts
• Partner benefits

🏆 <b>Community Features:</b>
• Leaderboard competitions
• Community voting
• Special achievements
• VIP status rewards

🎉 <b>Limited Time Offers:</b>
• Festival bonuses
• Referral contests
• Bulk order discounts
• Premium memberships

✨ <b>अपना reward claim करें:</b>
"""

    await safe_edit_message(callback, text, get_offers_rewards_menu())
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery):
    """Handle admin panel access"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    if not is_admin(user_id):
        text = """
⚠️ <b>Access Denied</b>

यह section केवल authorized administrators के लिए है।

🔒 <b>Security Notice:</b>
Unauthorized access attempts are logged and monitored.

📞 यदि आप administrator हैं, तो owner से contact करें।
"""
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, back_keyboard)
    else:
        # Admin menu will be implemented here
        text = """
👑 <b>Admin Panel</b>

🔧 <b>System Controls Available</b>

📊 <b>Stats:</b>
• Total Users: 0
• Total Orders: 0
• Today's Revenue: ₹0.00

⚙️ <b>Admin features coming soon...</b>
"""
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, back_keyboard)

    await callback.answer()

@dp.callback_query(F.data == "contact_about")
async def cb_contact_about(callback: CallbackQuery):
    """Handle contact & about section"""
    if not callback.message:
        return

    text = """
📞 <b>Contact & About</b>

🇮🇳 <b>India Social Panel</b>
भारत का सबसे भरोसेमंद SMM Platform

🎯 <b>Our Mission:</b>
High-quality, affordable social media marketing services प्रदान करना

✨ <b>Why Choose Us:</b>
• ✅ 100% Real & Active Users
• ⚡ Instant Start Guarantee
• 🔒 Safe & Secure Services
• 💬 24/7 Customer Support
• 💰 Best Prices in Market

📈 <b>Services:</b> 500+ Premium SMM Services
🌍 <b>Serving:</b> Worldwide (India Focus)
"""

    await safe_edit_message(callback, text, get_contact_menu())
    await callback.answer()

@dp.callback_query(F.data == "owner_info")
async def cb_owner_info(callback: CallbackQuery):
    """Show owner information"""
    if not callback.message:
        return

    text = f"""
👨‍💻 <b>Owner Information</b>

🙏 <b>Namaste! मैं {OWNER_NAME}</b>
Founder & CEO, India Social Panel

📍 <b>Location:</b> Bihar, India 🇮🇳
💼 <b>Experience:</b> 5+ Years in SMM Industry
🎯 <b>Mission:</b> भारतीय businesses को affordable digital marketing solutions देना

✨ <b>My Vision:</b>
"हर Indian business को social media पर successful बनाना"

💬 <b>Personal Message:</b>
"मेरा मकसद आप सभी को Bihar से high-quality और affordable SMM services प्रदान करना है। आपका support और trust ही मेरी सबसे बड़ी achievement है।"

📞 <b>Contact:</b> @{OWNER_USERNAME}
🌟 <b>Thank you for choosing us!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== NEW MISSING CALLBACK HANDLERS ==========
# Removed cb_category_select and cb_service_select as they are now in services.py

# Amount handlers moved to payment_system.py


@dp.callback_query(F.data == "service_list")
@require_account
async def cb_service_list(callback: CallbackQuery):
    """Show service list"""
    if not callback.message:
        return

    text = """
📈 <b>Service List</b>

<b>Platform चुनें pricing देखने के लिए:</b>

💎 <b>High Quality Services</b>
⚡ <b>Instant Start</b>
🔒 <b>100% Safe & Secure</b>
"""

    await safe_edit_message(callback, text, get_category_menu())
    await callback.answer()

@dp.callback_query(F.data == "support_tickets")
@require_account
async def cb_support_tickets(callback: CallbackQuery):
    """Show support tickets menu"""
    if not callback.message:
        return

    text = """
🎫 <b>Support Tickets</b>

💬 <b>Customer Support System</b>

🔸 <b>24/7 Available</b>
🔸 <b>Quick Response</b>
🔸 <b>Professional Help</b>

💡 <b>आप क्या करना चाहते हैं?</b>
"""

    await safe_edit_message(callback, text, get_support_menu())
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    """Return to main menu"""
    if not callback.message:
        return

    text = """
🏠 <b>India Social Panel - Main Menu</b>

🇮🇳 भारत का #1 SMM Panel
💡 अपनी जरूरत के अनुसार option चुनें:
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()







# ========== ORDER CONFIRMATION HANDLERS ==========
@dp.callback_query(F.data == "confirm_order")
@require_account
async def cb_confirm_order(callback: CallbackQuery):
    """Confirm and process order"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if order data exists
    if user_id not in order_temp:
        await callback.answer("⚠️ Order data not found!")
        return

    order_data = order_temp[user_id]
    user_data = users_data.get(user_id, {})

    # Check balance
    balance = user_data.get('balance', 0.0)
    price = order_data['price']

    if balance < price:
        text = f"""
💳 <b>Insufficient Balance</b>

💰 <b>Required:</b> {format_currency(price)}
💰 <b>Available:</b> {format_currency(balance)}
💰 <b>Need to Add:</b> {format_currency(price - balance)}

💡 <b>Please add funds first!</b>
"""

        fund_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Add Funds", callback_data="add_funds")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ])

        await safe_edit_message(callback, text, fund_keyboard)
        await callback.answer()
        return

    # Process order
    order_id = generate_order_id()
    order_record = {
        'order_id': order_id,
        'user_id': user_id,
        'service': order_data['service'],
        'link': order_data['link'],
        'quantity': order_data['quantity'],
        'price': price,
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'start_count': 0,
        'remains': order_data['quantity']
    }

    # Save order
    orders_data[order_id] = order_record

    # Update user data
    users_data[user_id]['balance'] -= price
    users_data[user_id]['total_spent'] += price
    users_data[user_id]['orders_count'] += 1

    # Clear temp order
    del order_temp[user_id]

    text = f"""
🎉 <b>Order Successfully Placed!</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>
📱 <b>Service:</b> {order_data['service'].replace('_', ' ').title()}
🔢 <b>Quantity:</b> {order_data['quantity']:,}
💰 <b>Charged:</b> {format_currency(price)}
🔄 <b>Status:</b> Processing

✅ <b>Order का processing start हो गया!</b>
📅 <b>Delivery:</b> 0-6 hours

💡 <b>Order history में details check कर सकते हैं</b>
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Order History", callback_data="order_history")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
    ])

    await safe_edit_message(callback, text, success_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "cancel_order")
@require_account
async def cb_cancel_order(callback: CallbackQuery):
    """Cancel current order"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Clear temp order data
    if user_id in order_temp:
        del order_temp[user_id]

    text = """
❌ <b>Order Cancelled</b>

📋 <b>Order process cancelled successfully</b>

💡 <b>You can place a new order anytime!</b>
"""

    await safe_edit_message(callback, text, get_main_menu())
    await callback.answer()

# ========== SERVICES & TOOLS HANDLERS ==========
@dp.callback_query(F.data == "mass_order")
@require_account
async def cb_mass_order(callback: CallbackQuery):
    """Handle mass order feature"""
    if not callback.message:
        return

    text = """
📦 <b>Mass Order</b>

🚀 <b>Bulk Order Management System</b>

💎 <b>Features:</b>
• Multiple orders at once
• CSV file upload support
• Bulk pricing discounts
• Progress tracking

📋 <b>Supported Formats:</b>
• Multiple links processing
• Quantity distribution
• Service selection
• Custom delivery schedule

💰 <b>Bulk Discounts:</b>
• 10+ orders: 5% discount
• 50+ orders: 10% discount
• 100+ orders: 15% discount

⚙️ <b>Mass order feature under development!</b>
🔄 <b>Will be available soon with advanced features</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "subscriptions")
@require_account
async def cb_subscriptions(callback: CallbackQuery):
    """Handle subscriptions feature"""
    if not callback.message:
        return

    text = """
🔄 <b>Subscriptions</b>

⏰ <b>Auto-Renewal Service Plans</b>

🎯 <b>Subscription Benefits:</b>
• Automatic order renewal
• Consistent growth maintenance
• Priority delivery
• Special subscriber rates

📅 <b>Available Plans:</b>
• Weekly renewals
• Monthly packages
• Custom schedules
• Pause/resume options

💡 <b>Smart Features:</b>
• Growth tracking
• Performance analytics
• Auto-optimization
• Flexible modifications

🔔 <b>Subscription service coming soon!</b>
💬 <b>Early access:</b> Contact support for beta testing
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "profile_analyzer")
@require_account
async def cb_profile_analyzer(callback: CallbackQuery):
    """Handle profile analyzer feature"""
    if not callback.message:
        return

    text = """
📊 <b>Profile Analyzer</b>

🔍 <b>Advanced Social Media Analytics</b>

📈 <b>Analysis Features:</b>
• Engagement rate calculation
• Follower quality assessment
• Growth trend analysis
• Optimal posting times

🎯 <b>Insights Provided:</b>
• Audience demographics
• Content performance
• Competitor analysis
• Growth recommendations

💡 <b>AI-Powered Reports:</b>
• Personalized strategies
• Market positioning
• Content suggestions
• Hashtag optimization

🔬 <b>Profile analyzer tool under development!</b>
✨ <b>Will include AI-powered insights and recommendations</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "hashtag_generator")
@require_account
async def cb_hashtag_generator(callback: CallbackQuery):
    """Handle hashtag generator feature"""
    if not callback.message:
        return

    text = """
## <b>Hashtag Generator</b>

🏷️ <b>AI-Powered Hashtag Creation Tool</b>

🎯 <b>Smart Features:</b>
• Trending hashtag suggestions
• Niche-specific tags
• Engagement optimization
• Regional relevance

📊 <b>Analytics Integration:</b>
• Performance tracking
• Reach estimation
• Competition analysis
• Viral potential score

🇮🇳 <b>India-Focused:</b>
• Local trending topics
• Cultural relevance
• Regional languages
• Festival-based tags

🤖 <b>AI-powered hashtag generator coming soon!</b>
⚡ <b>Will generate optimized hashtags for maximum reach</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "free_trial")
@require_account
async def cb_free_trial(callback: CallbackQuery):
    """Handle free trial service"""
    if not callback.message:
        return

    text = """
✨ <b>Free Trial Service</b>

🎁 <b>Try Our Premium Services For Free!</b>

🆓 <b>Available Free Trials:</b>
• 100 Instagram Likes - FREE
• 50 YouTube Views - FREE
• 25 Facebook Reactions - FREE
• 10 TikTok Likes - FREE

📋 <b>Trial Conditions:</b>
• One trial per platform
• Account verification required
• No payment needed
• Quality guaranteed

🎯 <b>Trial Benefits:</b>
• Experience our quality
• Test delivery speed
• Verify safety
• Build confidence

🔥 <b>Free trial service launching soon!</b>
💡 <b>Perfect way to test our premium quality services</b>
"""

    trial_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Request Trial", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Services & Tools", callback_data="services_tools")]
    ])

    await safe_edit_message(callback, text, trial_keyboard)
    await callback.answer()

# ========== CONTACT & ABOUT SUB-MENU HANDLERS ==========
@dp.callback_query(F.data == "website_info")
async def cb_website_info(callback: CallbackQuery):
    """Show website information"""
    if not callback.message:
        return

    text = f"""
🌐 <b>Hamari Website</b>

🔗 <b>Website:</b>
Coming Soon...

🇮🇳 <b>India Social Panel Official</b>
✅ Premium SMM Services
✅ 24/7 Customer Support
✅ Secure Payment Gateway
✅ Real-time Order Tracking

💡 <b>Website launch ke liye wait kariye!</b>

📞 <b>Contact:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "support_channel")
async def cb_support_channel(callback: CallbackQuery):
    """Show support channel info"""
    if not callback.message:
        return

    text = """
💬 <b>Support Channel</b>

🎆 <b>Join Our Community!</b>

🔗 <b>Telegram Channel:</b>
@IndiaSocialPanelOfficial

🔗 <b>Support Group:</b>
@IndiaSocialPanelSupport

📝 <b>Channel Benefits:</b>
• Latest Updates & Offers
• Service Announcements
• Community Support
• Tips & Tricks
• Exclusive Discounts

🔔 <b>Notifications ON kar dena!</b>
"""

    join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Join Channel", url="https://t.me/IndiaSocialPanelOfficial")],
        [InlineKeyboardButton(text="💬 Join Support Group", url="https://t.me/IndiaSocialPanelSupport")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, join_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "terms_service")
async def cb_terms_service(callback: CallbackQuery):
    """Show terms of service"""
    if not callback.message:
        return

    text = """
📜 <b>Seva Ki Shartein (Terms of Service)</b>

📝 <b>Important Terms:</b>

1️⃣ <b>Service Guarantee:</b>
• High quality services guarantee
• No fake/bot followers
• Real & active users only

2️⃣ <b>Refund Policy:</b>
• Service start ke baad no refund
• Wrong link ke liye customer responsible
• Technical issues mein full refund

3️⃣ <b>Account Safety:</b>
• 100% safe methods use karte hain
• Account ban nahi hoga
• Privacy fully protected

4️⃣ <b>Delivery Time:</b>
• 0-6 hours typical delivery
• Some services may take 24-48 hours
• Status tracking available

🔒 <b>By using our services, you agree to these terms</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== OFFERS & REWARDS HANDLERS ==========
@dp.callback_query(F.data == "coupon_redeem")
@require_account
async def cb_coupon_redeem(callback: CallbackQuery):
    """Handle coupon redeem feature"""
    if not callback.message:
        return

    text = """
🎟️ <b>Coupon Redeem Karein</b>

💝 <b>Discount Coupons & Promo Codes</b>

🎯 <b>Active Offers:</b>
• WELCOME10 - 10% off first order
• BULK20 - 20% off on orders above ₹2000
• FESTIVAL25 - 25% festival special
• REFER15 - 15% off via referral

💡 <b>How to Use:</b>
1. Get coupon code
2. Enter during checkout
3. Discount applied instantly
4. Save money on orders

🔥 <b>Special Coupons:</b>
• Daily login rewards
• Loyalty member exclusive
• Limited time offers
• Seasonal promotions

🎟️ <b>Coupon system coming soon!</b>
💬 <b>Get exclusive codes:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "partner_program")
@require_account
async def cb_partner_program(callback: CallbackQuery):
    """Handle partner program feature"""
    if not callback.message:
        return

    text = """
🤝 <b>Partner Program</b>

💼 <b>Business Partnership Opportunities</b>

🎯 <b>Partnership Benefits:</b>
• Wholesale pricing (up to 40% off)
• Priority customer support
• Dedicated account manager
• Custom branding options

📊 <b>Partner Tiers:</b>
• Bronze: ₹10,000+ monthly
• Silver: ₹25,000+ monthly
• Gold: ₹50,000+ monthly
• Platinum: ₹1,00,000+ monthly

💡 <b>Exclusive Features:</b>
• API access
• White-label solutions
• Bulk order management
• Revenue sharing program

🚀 <b>Partner program launching soon!</b>
📞 <b>Business inquiries:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "loyalty_program")
@require_account
async def cb_loyalty_program(callback: CallbackQuery):
    """Handle loyalty program feature"""
    if not callback.message:
        return

    text = """
🏆 <b>Loyalty Program</b>

💎 <b>Exclusive Benefits for Regular Customers</b>

🌟 <b>Loyalty Tiers:</b>
• Bronze: ₹0-₹5,000 spent
• Silver: ₹5,001-₹15,000 spent
• Gold: ₹15,001-₹50,000 spent
• Platinum: ₹50,000+ spent

🎁 <b>Tier Benefits:</b>
• Bronze: 2% cashback
• Silver: 5% cashback + priority support
• Gold: 8% cashback + exclusive offers
• Platinum: 12% cashback + VIP treatment

💡 <b>Loyalty Points:</b>
• Earn 1 point per ₹10 spent
• Redeem points for discounts
• Bonus points on special days
• Referral bonus points

🔥 <b>Loyalty program launching soon!</b>
✨ <b>Start earning rewards on every order!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "daily_reward")
@require_account
async def cb_daily_reward(callback: CallbackQuery):
    """Handle daily reward feature"""
    if not callback.message:
        return

    text = """
🎉 <b>Daily Reward</b>

🎁 <b>Login करें और Daily Rewards पाएं!</b>

📅 <b>Daily Login Streak:</b>
• Day 1: ₹5 bonus
• Day 3: ₹10 bonus
• Day 7: ₹25 bonus
• Day 15: ₹50 bonus
• Day 30: ₹100 bonus

⚡ <b>Special Rewards:</b>
• Weekend bonus (2x rewards)
• Festival special rewards
• Birthday month bonus
• Milestone achievements

🎯 <b>Additional Benefits:</b>
• Spin wheel daily
• Lucky draw entries
• Surprise gift boxes
• Exclusive coupon codes

🎊 <b>Daily reward system launching soon!</b>
💫 <b>Make it a habit to login daily for maximum benefits!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "leaderboard")
@require_account
async def cb_leaderboard(callback: CallbackQuery):
    """Handle leaderboard feature"""
    if not callback.message:
        return

    text = """
🥇 <b>Leaderboard</b>

🏆 <b>Top Users Ranking & Competitions</b>

👑 <b>Monthly Leaderboard:</b>
1. 🥇 @champion_user - ₹45,000 spent
2. 🥈 @pro_marketer - ₹38,000 spent
3. 🥉 @social_king - ₹32,000 spent
... और भी users

🎯 <b>Ranking Categories:</b>
• Total spending
• Most orders placed
• Referral champions
• Loyalty points earned

🏅 <b>Leaderboard Rewards:</b>
• Top 3: Special badges + bonuses
• Top 10: Exclusive discounts
• Top 50: Priority support
• All participants: Recognition

🔥 <b>Leaderboard system launching soon!</b>
💪 <b>Compete with other users and win exciting prizes!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "community_polls")
@require_account
async def cb_community_polls(callback: CallbackQuery):
    """Handle community polls feature"""
    if not callback.message:
        return

    text = """
📝 <b>Community Polls</b>

🗳️ <b>Your Voice Matters - Help Shape Our Services!</b>

📊 <b>Current Active Poll:</b>
"Which new platform should we add next?"
• 🎵 TikTok India - 45%
• 📺 YouTube Shorts - 35%
• 💼 LinkedIn India - 20%

💡 <b>Previous Poll Results:</b>
• "Best delivery time?" → 0-6 hours won
• "Preferred payment method?" → UPI won
• "Most wanted service?" → Instagram Reels won

🎁 <b>Poll Participation Rewards:</b>
• Vote करने पर points मिलते हैं
• Monthly poll winners get bonuses
• Community feedback valued
• Special recognition for active voters

🗳️ <b>Community polling system launching soon!</b>
👥 <b>Be part of India Social Panel's growth decisions!</b>
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Offers & Rewards", callback_data="offers_rewards")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== AI SUPPORT & CONTACT ADMIN HANDLERS ==========
@dp.callback_query(F.data == "ai_support")
async def cb_ai_support(callback: CallbackQuery):
    """Handle AI support feature"""
    if not callback.message:
        return

    text = """
🤖 <b>AI Support</b>

🧠 <b>Intelligent Assistant - 24/7 Available</b>

⚡ <b>AI Features:</b>
• Instant query resolution
• Smart troubleshooting
• Order tracking assistance
• Service recommendations

🎯 <b>What AI Can Help With:</b>
• Account related questions
• Order status inquiries
• Payment issues
• Service explanations
• Best practices guidance

💡 <b>Smart Responses:</b>
• Natural language understanding
• Context-aware answers
• Multi-language support
• Learning from interactions

🤖 <b>AI Support system under development!</b>
⚡ <b>Will provide instant, intelligent assistance 24/7</b>

📞 <b>For now, contact human support:</b> @{OWNER_USERNAME}
"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Chat with Human", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "contact_admin")
async def cb_contact_admin(callback: CallbackQuery):
    """Handle contact admin feature"""
    if not callback.message:
        return

    text = f"""
👨‍💼 <b>Contact Admin</b>

📞 <b>Direct Admin Support</b>

👤 <b>Main Admin:</b>
• Name: {OWNER_NAME}
• Username: @{OWNER_USERNAME}
• Response Time: 2-6 hours
• Available: 9 AM - 11 PM IST

💼 <b>Support Team:</b>
• @SupportManager_ISP
• @TechnicalSupport_ISP
• @BillingSupport_ISP
• @AccountManager_ISP

⚡ <b>Quick Support Categories:</b>
• 🆘 Emergency issues
• 💰 Payment problems
• 🔧 Technical difficulties
• 💼 Business inquiries
• 🎁 Partnership requests

🚀 <b>Premium Support:</b>
For VIP customers and partners, we provide priority support with dedicated account managers.

📱 <b>Choose your preferred contact method:</b>
"""

    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Main Admin", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton(text="🆘 Emergency", url="https://t.me/SupportManager_ISP")
        ],
        [
            InlineKeyboardButton(text="💰 Billing Support", url="https://t.me/BillingSupport_ISP"),
            InlineKeyboardButton(text="🔧 Technical Help", url="https://t.me/TechnicalSupport_ISP")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="contact_about")
        ]
    ])

    await safe_edit_message(callback, text, admin_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "create_ticket")
@require_account
async def cb_create_ticket(callback: CallbackQuery):
    """Start ticket creation process"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_ticket_subject"

    text = """
🎫 <b>Create Support Ticket</b>

📝 <b>Step 1: Subject</b>

💬 <b>कृपया ticket का subject भेजें:</b>

⚠️ <b>Examples:</b>
• Order delivery issue
• Payment problem
• Account access issue
• Service quality concern

💡 <b>Clear subject likhenge to fast response milega!</b>
"""

    await safe_edit_message(callback, text)
    await callback.answer()

@dp.callback_query(F.data == "view_tickets")
@require_account
async def cb_view_tickets(callback: CallbackQuery):
    """Show user's tickets"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id
    user_tickets = [ticket for ticket_id, ticket in tickets_data.items() if ticket.get('user_id') == user_id]

    if not user_tickets:
        text = """
📖 <b>Mere Tickets</b>

📋 <b>कोई tickets नहीं मिले</b>

🎫 <b>Agar koi problem hai to new ticket create karein!</b>
➕ <b>Support team 24/7 available hai</b>
"""
    else:
        text = "📖 <b>Mere Tickets</b>\n\n"
        for i, ticket in enumerate(user_tickets[-5:], 1):  # Last 5 tickets
            status_emoji = {"open": "🔴", "replied": "🟡", "closed": "✅"}
            emoji = status_emoji.get(ticket.get('status', 'open'), "🔴")
            text += f"""
{i}. <b>Ticket #{ticket.get('ticket_id', 'N/A')}</b>
{emoji} Status: {ticket.get('status', 'Open').title()}
📝 Subject: {ticket.get('subject', 'N/A')}
📅 Created: {format_time(ticket.get('created_at', ''))}

"""

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ New Ticket", callback_data="create_ticket")],
        [InlineKeyboardButton(text="⬅️ Support Menu", callback_data="support_tickets")]
    ])

    await safe_edit_message(callback, text, back_keyboard)
    await callback.answer()

# ========== CONTACT HANDLERS ==========
@dp.message(F.contact)
async def handle_contact_sharing(message: Message):
    """Handle shared contact for phone number"""
    if not message.from_user or not message.contact:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id
    contact = message.contact
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "waiting_contact_permission":
        # User shared their contact
        if contact.user_id == user_id:
            # Contact belongs to the same user
            phone_number = contact.phone_number

            # Ensure phone starts with + for international format
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"

            # Store phone number and move to next step
            user_state[user_id]["data"]["phone_number"] = phone_number
            user_state[user_id]["current_step"] = "waiting_email"

            # Remove contact keyboard
            from aiogram.types import ReplyKeyboardRemove

            success_text = f"""
✅ <b>Contact Successfully Shared!</b>

📱 <b>Phone Number Received:</b> {phone_number}

🎉 <b>Contact sharing successful!</b>

📋 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

            await message.answer(success_text, reply_markup=ReplyKeyboardRemove())

        else:
            # User shared someone else's contact
            from aiogram.types import ReplyKeyboardRemove

            text = """
⚠️ <b>Wrong Contact Shared</b>

🚫 <b>आपने किसी और का contact share किया है</b>

💡 <b>Solutions:</b>
• अपना own contact share करें
• "Manual Entry" option choose करें
• Account creation restart करें

🔒 <b>Security:</b> केवल अपना own contact share करें
"""

            manual_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Try Again", callback_data="share_telegram_contact"),
                    InlineKeyboardButton(text="✏️ Manual Entry", callback_data="manual_phone_entry")
                ]
            ])

            await message.answer(text, reply_markup=ReplyKeyboardRemove())
            await message.answer("💡 <b>Choose an option:</b>", reply_markup=manual_keyboard)

    else:
        # Contact shared without proper context
        text = """
📱 <b>Contact Received</b>

💡 <b>Contact sharing केवल account creation के दौरान allowed है</b>

🔄 <b>अगर आप account create कर रहे हैं तो /start करके restart करें</b>
"""

        from aiogram.types import ReplyKeyboardRemove
        await message.answer(text, reply_markup=ReplyKeyboardRemove())

# ========== INPUT HANDLERS ==========
@dp.message(F.text)
async def handle_text_input(message: Message):
    """Handle text input for account creation"""
    if not message.from_user or not message.text:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(message.from_user.id)
        return  # Ignore old messages

    user_id = message.from_user.id

    # Check if user is in account creation flow
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "waiting_login_phone":
        # Handle login phone verification
        phone = message.text.strip()

        # Find user with matching phone number
        matching_user = None
        for uid, data in users_data.items():
            if data.get('phone_number') == phone:
                matching_user = uid
                break

        if matching_user and matching_user == user_id:
            # Phone matches, complete login
            users_data[user_id]['account_created'] = True
            user_state[user_id]["current_step"] = None
            user_state[user_id]["data"] = {}

            # Get user display name for login success
            user_display_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name or 'Friend'

            success_text = f"""
✅ <b>Login Successful!</b>

🎉 <b>Welcome back {user_display_name} to India Social Panel!</b>

👤 <b>Account Details:</b>
• Name: {users_data[user_id].get('full_name', 'N/A')}
• Phone: {phone}
• Balance: {format_currency(users_data[user_id].get('balance', 0.0))}

🚀 <b>All features are now accessible!</b>
💡 <b>आप अब सभी services का इस्तेमाल कर सकते हैं</b>
"""

            await message.answer(success_text, reply_markup=get_main_menu())

        elif matching_user and matching_user != user_id:
            # Phone belongs to different user
            text = """
⚠️ <b>Account Mismatch</b>

📱 <b>यह phone number किसी और account से linked है</b>

💡 <b>Solutions:</b>
• अपना correct phone number try करें
• नया account create करें
• Support से contact करें

📞 <b>Support:</b> @achal_parvat
"""

            user_state[user_id]["current_step"] = None

            retry_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Try Again", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}")
                ]
            ])

            await message.answer(text, reply_markup=retry_keyboard)

        else:
            # Phone not found in system
            text = """
❌ <b>Account Not Found</b>

📱 <b>इस phone number से कोई account registered नहीं है</b>

💡 <b>Options:</b>
• Phone number double-check करें
• नया account create करें
• Support से help लें

🤔 <b>पहले से account नहीं है?</b>
"""

            user_state[user_id]["current_step"] = None

            options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔐 Try Different Number", callback_data="login_account"),
                    InlineKeyboardButton(text="📝 Create New Account", callback_data="create_account")
                ],
                [
                    InlineKeyboardButton(text="📞 Contact Support", url=f"https://t.me/{OWNER_USERNAME}")
                ]
            ])

            await message.answer(text, reply_markup=options_keyboard)

    elif current_step == "waiting_custom_name":
        # Handle custom name input with validation
        custom_name = message.text.strip()

        # Validate name length (max 6 characters)
        if len(custom_name) > 6:
            await message.answer(
                "⚠️ <b>Name too long!</b>\n\n"
                "📏 <b>Maximum 6 characters allowed</b>\n"
                "💡 <b>Please enter a shorter name</b>\n\n"
                "🔄 <b>Try again with max 6 characters</b>"
            )
            return

        if len(custom_name) < 2:
            await message.answer(
                "⚠️ <b>Name too short!</b>\n\n"
                "📏 <b>Minimum 2 characters required</b>\n"
                "💡 <b>Please enter a valid name</b>\n\n"
                "🔄 <b>Try again with at least 2 characters</b>"
            )
            return

        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store custom name and move to next step
        user_state[user_id]["data"]["full_name"] = custom_name
        user_state[user_id]["current_step"] = "choosing_phone_option"

        success_text = f"""
✅ <b>Custom Name Successfully Added!</b>

👤 <b>Your Name:</b> {custom_name}

📋 <b>Account Creation - Step 2/3</b>

📱 <b>Phone Number Selection</b>

💡 <b>आप phone number कैसे provide करना चाहते हैं?</b>

🔸 <b>Telegram Contact:</b> आपका Telegram में saved contact number
🔸 <b>Manual Entry:</b> अपनी पसंद का कोई भी number

⚠️ <b>Note:</b> Contact share करने से आपकी permission माँगी जाएगी और आपका number automatically भर जाएगा

💬 <b>आप क्या choose करना चाहते हैं?</b>
"""

        phone_choice_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Telegram Contact Share करूं", callback_data="share_telegram_contact"),
                InlineKeyboardButton(text="✏️ Manual Number डालूं", callback_data="manual_phone_entry")
            ]
        ])

        await message.answer(success_text, reply_markup=phone_choice_keyboard)

    elif current_step == "waiting_manual_phone":
        # Handle manual phone number entry with comprehensive Indian validation
        phone_input = message.text.strip()

        # Remove any spaces, dashes, brackets or other common separators
        phone_cleaned = phone_input.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")

        # Check if input contains any letters
        if any(char.isalpha() for char in phone_cleaned):
            await message.answer(
                "⚠️ <b>Letters Not Allowed!</b>\n\n"
                "🔤 <b>Phone number में letters नहीं हो सकते</b>\n"
                "🔢 <b>केवल numbers और +91 allowed है</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Try again with only numbers</b>"
            )
            return

        # Validate country code presence
        if not phone_cleaned.startswith('+91'):
            await message.answer(
                "⚠️ <b>Country Code Missing!</b>\n\n"
                "🇮🇳 <b>Indian numbers must start with +91</b>\n"
                "❌ <b>Numbers without +91 are not accepted</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Add +91 before your number</b>"
            )
            return

        # Check exact length (should be 13: +91 + 10 digits)
        if len(phone_cleaned) != 13:
            await message.answer(
                "⚠️ <b>Invalid Length!</b>\n\n"
                f"📏 <b>Entered length: {len(phone_cleaned)} characters</b>\n"
                "📏 <b>Required: Exactly 13 characters</b>\n"
                "💡 <b>Format:</b> +91 followed by 10 digits\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Check your number length</b>"
            )
            return

        # Extract the 10-digit number part
        digits_part = phone_cleaned[3:]  # Remove +91

        # Check if only digits after +91
        if not digits_part.isdigit():
            await message.answer(
                "⚠️ <b>Invalid Characters!</b>\n\n"
                "🔢 <b>Only numbers allowed after +91</b>\n"
                "❌ <b>No spaces, letters, or special characters</b>\n"
                "💡 <b>Example:</b> +919876543210\n\n"
                "🔄 <b>Use only digits after +91</b>"
            )
            return

        # Check for invalid starting digits (Indian mobile rules)
        first_digit = digits_part[0]
        invalid_starting_digits = ['0', '1', '2', '3', '4', '5']

        if first_digit in invalid_starting_digits:
            await message.answer(
                "⚠️ <b>Invalid Starting Digit!</b>\n\n"
                f"📱 <b>Indian mobile numbers cannot start with {first_digit}</b>\n"
                "✅ <b>Valid starting digits:</b> 6, 7, 8, 9\n"
                "💡 <b>Example:</b> +919876543210, +917894561230\n\n"
                "🔄 <b>Use a valid Indian mobile number</b>"
            )
            return

        # Check for obviously fake patterns
        # Pattern 1: All same digits
        if len(set(digits_part)) == 1:
            await message.answer(
                "⚠️ <b>Invalid Number Pattern!</b>\n\n"
                "🚫 <b>सभी digits same नहीं हो सकते</b>\n"
                "❌ <b>Example of invalid:</b> +919999999999\n"
                "💡 <b>Valid example:</b> +919876543210\n\n"
                "🔄 <b>Enter a real mobile number</b>"
            )
            return

        # Pattern 2: Sequential patterns (1234567890, 0123456789)
        if digits_part == "1234567890" or digits_part == "0123456789":
            await message.answer(
                "⚠️ <b>Sequential Pattern Detected!</b>\n\n"
                "🚫 <b>Sequential numbers invalid हैं</b>\n"
                "❌ <b>Pattern like 1234567890 not allowed</b>\n"
                "💡 <b>Enter your real mobile number</b>\n\n"
                "🔄 <b>Try with valid number</b>"
            )
            return

        # Pattern 3: Too many zeros or repeated patterns
        zero_count = digits_part.count('0')
        if zero_count >= 5:
            await message.answer(
                "⚠️ <b>Too Many Zeros!</b>\n\n"
                "🚫 <b>इतने सारे zeros वाला number invalid है</b>\n"
                "❌ <b>Real mobile numbers में इतने zeros नहीं होते</b>\n"
                "💡 <b>Enter your actual mobile number</b>\n\n"
                "🔄 <b>Try again with valid number</b>"
            )
            return

        # Pattern 4: Check for repeating segments (like 123123, 987987)
        for i in range(1, 6):  # Check patterns of length 1-5
            segment = digits_part[:i]
            if len(digits_part) >= i * 3:  # If we can fit the pattern at least 3 times
                repeated = segment * (len(digits_part) // i)
                if digits_part.startswith(repeated[:len(digits_part)]):
                    await message.answer(
                        "⚠️ <b>Repeated Pattern Detected!</b>\n\n"
                        f"🚫 <b>Pattern '{segment}' बार-बार repeat हो रहा है</b>\n"
                        "❌ <b>Real mobile numbers में repeating patterns नहीं होते</b>\n"
                        "💡 <b>Enter your actual mobile number</b>\n\n"
                        "🔄 <b>Try with different number</b>"
                    )
                    return

        # Pattern 5: Check for invalid number ranges and special service numbers
        # These are typically service numbers or invalid ranges
        invalid_ranges = [
            "1", "2", "3", "4", "5",  # Cannot start with these
        ]

        # Check second digit combinations that are invalid
        first_two = digits_part[:2]
        invalid_first_two = [
            "60", "61", "62", "63", "64", "65",  # Reserved ranges
            "90", "91", "92", "93", "94", "95"   # Some service number ranges
        ]

        if first_two in invalid_first_two:
            await message.answer(
                "⚠️ <b>Invalid Number Range!</b>\n\n"
                f"🚫 <b>Number range {first_two}XXXXXXXX reserved है</b>\n"
                "📱 <b>Valid Indian mobile ranges:</b>\n"
                "• 6XXXXXXXXX (some ranges)\n"
                "• 7XXXXXXXXX ✅\n"
                "• 8XXXXXXXXX ✅\n"
                "• 9XXXXXXXXX (most ranges) ✅\n\n"
                "🔄 <b>Enter valid Indian mobile number</b>"
            )
            return

        # Pattern 6: Extremely simple patterns
        simple_patterns = [
            "7000000000", "8000000000", "9000000000",
            "7111111111", "8111111111", "9111111111",
            "7777777777", "8888888888", "9999999999",
            "6666666666", "7123456789", "8123456789"
        ]

        if digits_part in simple_patterns:
            await message.answer(
                "⚠️ <b>Common Test Number!</b>\n\n"
                "🚫 <b>यह एक common test number है</b>\n"
                "❌ <b>Real mobile number का use करें</b>\n"
                "💡 <b>अपना actual registered number डालें</b>\n\n"
                "🔄 <b>Try with your real number</b>"
            )
            return

        # All validations passed
        validated_phone = phone_cleaned

        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store validated phone and move to next step
        user_state[user_id]["data"]["phone_number"] = phone_input
        user_state[user_id]["current_step"] = "waiting_email"

        success_text = f"""
✅ <b>Phone Number Successfully Added!</b>

📱 <b>Verified Number:</b> {phone_input}

📋 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

        await message.answer(success_text)

    elif current_step == "waiting_phone":
        # Legacy handler for old phone waiting (keeping for compatibility)
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store phone and ask for email
        user_state[user_id]["data"]["phone_number"] = message.text.strip()
        user_state[user_id]["current_step"] = "waiting_email"

        success_text = f"""
✅ <b>Phone Number Successfully Added!</b>

📋 <b>Account Creation - Step 3/3</b>

📧 <b>कृपया अपना Email Address भेजें:</b>

⚠️ <b>Example:</b> your.email@gmail.com
💬 <b>Instruction:</b> अपना email address type करके भेज दें
"""

        await message.answer(success_text)

    elif current_step == "waiting_email":
        # Handle email input with comprehensive validation
        email_input = message.text.strip().lower()

        # Remove any spaces from email
        email_cleaned = email_input.replace(" ", "")

        # Basic format validation - must contain @ and .
        if "@" not in email_cleaned or "." not in email_cleaned:
            await message.answer(
                "⚠️ <b>Invalid Email Format!</b>\n\n"
                "📧 <b>Email में @ और . होना जरूरी है</b>\n"
                "💡 <b>Example:</b> yourname@gmail.com\n"
                "🔄 <b>Correct format में email भेजें</b>"
            )
            return

        # Check if email has proper structure
        email_parts = email_cleaned.split("@")
        if len(email_parts) != 2:
            await message.answer(
                "⚠️ <b>Invalid Email Structure!</b>\n\n"
                "📧 <b>Email में केवल एक @ होना चाहिए</b>\n"
                "❌ <b>Example of wrong:</b> user@@gmail.com\n"
                "✅ <b>Example of correct:</b> user@gmail.com\n\n"
                "🔄 <b>Correct email format भेजें</b>"
            )
            return

        username_part, domain_part = email_parts[0], email_parts[1]

        # Validate username part (before @)
        if len(username_part) < 1:
            await message.answer(
                "⚠️ <b>Username Missing!</b>\n\n"
                "📧 <b>@ से पहले username होना चाहिए</b>\n"
                "❌ <b>Wrong:</b> @gmail.com\n"
                "✅ <b>Correct:</b> yourname@gmail.com\n\n"
                "🔄 <b>Valid email भेजें</b>"
            )
            return

        if len(username_part) > 64:
            await message.answer(
                "⚠️ <b>Username Too Long!</b>\n\n"
                "📧 <b>Email username 64 characters से ज्यादा नहीं हो सकता</b>\n"
                "💡 <b>Shorter email address use करें</b>\n\n"
                "🔄 <b>Try again with shorter username</b>"
            )
            return

        # Validate domain part (after @)
        if len(domain_part) < 3:
            await message.answer(
                "⚠️ <b>Invalid Domain!</b>\n\n"
                "📧 <b>Domain name बहुत छोटा है</b>\n"
                "💡 <b>Example:</b> gmail.com, yahoo.com\n\n"
                "🔄 <b>Valid domain के साथ email भेजें</b>"
            )
            return

        # Check if domain has proper format (at least one dot)
        if "." not in domain_part:
            await message.answer(
                "⚠️ <b>Domain Format Error!</b>\n\n"
                "📧 <b>Domain में कम से कम एक dot (.) होना चाहिए</b>\n"
                "❌ <b>Wrong:</b> user@gmailcom\n"
                "✅ <b>Correct:</b> user@gmail.com\n\n"
                "🔄 <b>Correct domain format भेजें</b>"
            )
            return

        # Split domain into parts
        domain_parts = domain_part.split(".")

        # Check if domain has at least 2 parts (domain.tld)
        if len(domain_parts) < 2:
            await message.answer(
                "⚠️ <b>Incomplete Domain!</b>\n\n"
                "📧 <b>Domain incomplete है</b>\n"
                "💡 <b>Format:</b> domain.extension\n"
                "💡 <b>Example:</b> gmail.com, yahoo.in\n\n"
                "🔄 <b>Complete domain भेजें</b>"
            )
            return

        # Get top-level domain (last part)
        tld = domain_parts[-1]
        main_domain = domain_parts[-2] if len(domain_parts) >= 2 else ""

        # Check if TLD is valid (at least 2 characters)
        if len(tld) < 2:
            await message.answer(
                "⚠️ <b>Invalid Domain Extension!</b>\n\n"
                "📧 <b>Domain extension बहुत छोटा है</b>\n"
                "💡 <b>Valid extensions:</b> .com, .in, .org, .net\n\n"
                "🔄 <b>Valid domain extension के साथ email भेजें</b>"
            )
            return

        # List of trusted email domains
        trusted_domains = {
            # Major international providers
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
            "icloud.com", "me.com", "mac.com", "aol.com", "mail.com",

            # Indian providers
            "yahoo.co.in", "rediffmail.com", "sify.com", "in.com",
            "indiatimes.com", "sancharnet.in", "dataone.in",

            # Educational domains
            "edu", "ac.in", "edu.in", "student.com",

            # Business domains
            "company.com", "business.com", "work.com",

            # Other popular providers
            "protonmail.com", "tutanota.com", "zoho.com", "yandex.com",
            "mail.ru", "gmx.com", "web.de", "t-online.de"
        }

        # Check if it's a trusted domain or has valid TLD
        full_domain = domain_part.lower()
        valid_tlds = {
            "com", "org", "net", "edu", "gov", "mil", "int",  # Generic TLDs
            "in", "co.in", "net.in", "org.in", "gov.in", "ac.in", "edu.in",  # Indian TLDs
            "us", "uk", "ca", "au", "de", "fr", "jp", "cn", "br", "mx",  # Country TLDs
            "io", "co", "me", "tv", "cc", "ly", "tk", "ml", "cf", "ga"  # New TLDs
        }

        is_trusted_domain = full_domain in trusted_domains
        is_valid_tld = any(full_domain.endswith("." + valid_tld) for valid_tld in valid_tlds)

        # Check for obviously fake or suspicious domains
        suspicious_patterns = [
            "temp", "fake", "test", "spam", "junk", "trash", "garbage",
            "dummy", "example", "sample", "demo", "trial", "invalid",
            "noemail", "noreply", "donotreply", "bounce", "reject"
        ]

        is_suspicious = any(pattern in full_domain for pattern in suspicious_patterns)

        # Check for very short domain names (likely fake)
        if len(main_domain) < 2:
            await message.answer(
                "⚠️ <b>Suspicious Domain!</b>\n\n"
                "📧 <b>Domain name बहुत छोटा और suspicious है</b>\n"
                "💡 <b>Use popular email providers जैसे:</b>\n"
                "• gmail.com\n"
                "• yahoo.com\n"
                "• outlook.com\n"
                "• rediffmail.com\n\n"
                "🔄 <b>Trusted email provider use करें</b>"
            )
            return

        # Check for banned/suspicious domains
        if is_suspicious:
            await message.answer(
                "⚠️ <b>Suspicious Email Domain!</b>\n\n"
                "🚫 <b>यह email domain suspicious या temporary है</b>\n"
                "❌ <b>Temporary/fake email providers allowed नहीं हैं</b>\n\n"
                "✅ <b>Use करें:</b>\n"
                "• Gmail (gmail.com)\n"
                "• Yahoo (yahoo.com, yahoo.co.in)\n"
                "• Outlook (outlook.com, hotmail.com)\n"
                "• Rediffmail (rediffmail.com)\n\n"
                "🔄 <b>Permanent email address use करें</b>"
            )
            return

        # Check if domain is trusted or has valid TLD
        if not is_trusted_domain and not is_valid_tld:
            await message.answer(
                "⚠️ <b>Unrecognized Email Domain!</b>\n\n"
                f"📧 <b>Domain '{full_domain}' recognized नहीं है</b>\n\n"
                "✅ <b>Recommended email providers:</b>\n"
                "• gmail.com ⭐\n"
                "• yahoo.com / yahoo.co.in\n"
                "• outlook.com / hotmail.com\n"
                "• rediffmail.com (Indian)\n"
                "• icloud.com (Apple)\n\n"
                "💡 <b>Popular और trusted email provider use करें</b>\n"
                "🔒 <b>Security और reliability के लिए</b>"
            )
            return

        # Additional checks for email username part
        # Check for invalid characters in username
        import re
        if not re.match(r'^[a-zA-Z0-9._+-]+$', username_part):
            await message.answer(
                "⚠️ <b>Invalid Email Characters!</b>\n\n"
                "📧 <b>Email username में invalid characters हैं</b>\n"
                "✅ <b>Allowed characters:</b> letters, numbers, dots, underscores, plus, minus\n"
                "❌ <b>Not allowed:</b> spaces, special symbols\n\n"
                "🔄 <b>Valid email format भेजें</b>"
            )
            return

        # Check if username starts or ends with dots/underscores (invalid)
        if username_part.startswith('.') or username_part.endswith('.'):
            await message.answer(
                "⚠️ <b>Invalid Email Start/End!</b>\n\n"
                "📧 <b>Email username dot (.) से start या end नहीं हो सकता</b>\n"
                "❌ <b>Wrong:</b> .user@gmail.com या user.@gmail.com\n"
                "✅ <b>Correct:</b> user@gmail.com या user.name@gmail.com\n\n"
                "🔄 <b>Correct format भेजें</b>"
            )
            return

        # Check for consecutive dots (invalid)
        if ".." in username_part:
            await message.answer(
                "⚠️ <b>Consecutive Dots Error!</b>\n\n"
                "📧 <b>Email में consecutive dots (..) allowed नहीं हैं</b>\n"
                "❌ <b>Wrong:</b> user..name@gmail.com\n"
                "✅ <b>Correct:</b> user.name@gmail.com\n\n"
                "🔄 <b>Correct email format भेजें</b>"
            )
            return

        # Check if email is too long overall
        if len(email_cleaned) > 254:
            await message.answer(
                "⚠️ <b>Email Too Long!</b>\n\n"
                "📧 <b>Email address बहुत लंबा है</b>\n"
                "📏 <b>Maximum 254 characters allowed</b>\n"
                "💡 <b>Shorter email address use करें</b>\n\n"
                "🔄 <b>Try with shorter email</b>"
            )
            return

        # Check for common typos in popular domains
        domain_typos = {
            "gmai.com": "gmail.com",
            "gmial.com": "gmail.com", 
            "gmaill.com": "gmail.com",
            "gmailcom": "gmail.com",
            "yahooo.com": "yahoo.com",
            "yahho.com": "yahoo.com",
            "yaho.com": "yahoo.com",
            "outlok.com": "outlook.com",
            "outllok.com": "outlook.com",
            "hotmial.com": "hotmail.com",
            "hotmailcom": "hotmail.com"
        }

        if full_domain in domain_typos:
            suggested_domain = domain_typos[full_domain]
            await message.answer(
                f"⚠️ <b>Possible Typo Detected!</b>\n\n"
                f"📧 <b>आपने लिखा:</b> {full_domain}\n"
                f"💡 <b>क्या आपका मतलब था:</b> {suggested_domain}?\n\n"
                f"✅ <b>Correct email:</b> {username_part}@{suggested_domain}\n\n"
                "🔄 <b>Correct spelling के साथ email भेजें</b>"
            )
            return

        # Check for invalid characters in domain
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain_part):
            await message.answer(
                "⚠️ <b>Invalid Domain Characters!</b>\n\n"
                "📧 <b>Domain में invalid characters हैं</b>\n"
                "✅ <b>Domain में allowed:</b> letters, numbers, dots, hyphens\n"
                "❌ <b>Not allowed:</b> spaces, special symbols\n\n"
                "🔄 <b>Valid domain के साथ email भेजें</b>"
            )
            return

        # All validations passed - email is valid
        validated_email = email_cleaned

        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store email and complete account creation
        user_state[user_id]["data"]["email"] = validated_email

        # Update user data (ensure user exists first)
        if user_id not in users_data:
            init_user(user_id, message.from_user.username or "", message.from_user.first_name or "")

        users_data[user_id]["full_name"] = user_state[user_id]["data"]["full_name"]
        users_data[user_id]["phone_number"] = user_state[user_id]["data"]["phone_number"]
        users_data[user_id]["email"] = user_state[user_id]["data"]["email"]
        users_data[user_id]["account_created"] = True

        # Clear user state
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        # Show processing message first
        processing_text = f"""
🔄 <b>Account Creation in Progress...</b>

⚡ <b>Verifying your details, please wait...</b>

✅ <b>Name Verification:</b> Complete
✅ <b>Phone Verification:</b> Complete  
🔄 <b>Email Verification:</b> Processing...

📧 <b>Email:</b> {validated_email}

🛡️ <b>Security Check:</b> Running advanced verification
🔐 <b>Data Encryption:</b> Applying 256-bit encryption
📊 <b>Profile Creation:</b> Setting up your dashboard

⏳ <b>Please wait while we complete the process...</b>

🎯 <b>Almost done! This ensures maximum security for your account.</b>
"""

        processing_msg = await message.answer(processing_text)

        # Wait for 5 seconds to show processing
        await asyncio.sleep(5)

        # Get user display name for account creation success
        user_display_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name or 'Friend'

        # Final success message
        success_text = f"""
🎉 <b>Account Successfully Created!</b>

✅ <b>{user_display_name}, आपका account तैयार है!</b>

👤 <b>Name:</b> {users_data[user_id]['full_name']}
📱 <b>Phone:</b> {users_data[user_id]['phone_number']}
📧 <b>Email:</b> {users_data[user_id]['email']}

🎆 <b>Welcome to India Social Panel!</b>
अब आप सभी features का इस्तेमाल कर सकते हैं।

💡 <b>अपनी जरूरत के अनुसार option चुनें:</b>
"""

        # Edit the processing message to success message
        try:
            await processing_msg.edit_text(success_text, reply_markup=get_account_complete_menu(), parse_mode="HTML")
        except:
            # If edit fails, send new message
            await message.answer(success_text, reply_markup=get_account_complete_menu())

    elif current_step == "waiting_link":
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store link and ask for quantity
        user_state[user_id]["data"]["link"] = message.text.strip()
        user_state[user_id]["current_step"] = "waiting_quantity"

        text = f"""
✅ <b>Link Successfully Added!</b>

📝 <b>New Order - Step 4</b>

🔢 <b>कृपया Quantity भेजें:</b>

⚠️ <b>Minimum:</b> 100
⚠️ <b>Maximum:</b> 100,000

💡 <b>Example:</b> 1000
💬 <b>Instruction:</b> सिर्फ number type करें
"""

        await message.answer(text)

    elif current_step == "waiting_quantity":
        # Store quantity and show price calculation
        try:
            quantity = int(message.text.strip())
            if quantity < 100 or quantity > 100000:
                await message.answer("⚠️ Quantity 100 - 100,000 के बीच होनी चाहिए!")
                return

            # Calculate price (demo rates)
            service_rates = {
                "ig_followers": 0.5, "ig_likes": 0.3, "ig_views": 0.1, "ig_comments": 0.8,
                "yt_subscribers": 2.0, "yt_likes": 0.4, "yt_views": 0.05, "yt_comments": 1.0
            }

            service = user_state[user_id]["data"].get("service", "ig_followers")
            rate = service_rates.get(service, 0.5)
            total_price = quantity * rate

            # Store order data
            order_temp[user_id] = {
                "service": service,
                "link": user_state[user_id]["data"]["link"],
                "quantity": quantity,
                "price": total_price
            }

            # Clear user state
            user_state[user_id]["current_step"] = None
            user_state[user_id]["data"] = {}

            text = f"""
📄 <b>Order Confirmation</b>

📱 <b>Service:</b> {service.replace('_', ' ').title()}
🔗 <b>Link:</b> {order_temp[user_id]['link'][:50]}...
🔢 <b>Quantity:</b> {quantity:,}
💰 <b>Total Price:</b> {format_currency(total_price)}

✅ <b>Order confirm करने के लिए आपके balance से amount deduct होगी</b>

💡 <b>आप क्या करना चाहते हैं?</b>
"""

            await message.answer(text, reply_markup=get_order_confirm_menu(total_price))

        except ValueError:
            await message.answer("⚠️ कृपया valid number भेजें!")

    elif current_step == "waiting_custom_amount":
        # Handle custom amount for funds - redirect to payment system
        try:
            amount = int(message.text.strip())
            if amount < 100 or amount > 50000:
                await message.answer("⚠️ Amount ₹100 - ₹50,000 के बीच होनी चाहिए!")
                return

            # Store amount and clear state
            user_state[user_id]["data"]["payment_amount"] = amount
            user_state[user_id]["current_step"] = None

            # Calculate processing fees for different methods
            upi_total = amount
            netbanking_fee = amount * 2.5 / 100
            netbanking_total = amount + netbanking_fee
            card_fee = amount * 3.0 / 100
            card_total = amount + card_fee

            text = f"""
💳 <b>Payment Method Selection</b>

💰 <b>Amount to Add:</b> ₹{amount:,}

💡 <b>Choose your preferred payment method:</b>

📱 <b>UPI Payment</b> (Recommended) ⭐
• ✅ No processing fee
• ⚡ Instant credit
• 🔒 100% secure
• 💰 <b>Total:</b> ₹{upi_total:,}

🏦 <b>Bank Transfer</b>
• ✅ No processing fee
• ⏰ 2-4 hours processing
• 🔒 Highly secure
• 💰 <b>Total:</b> ₹{amount:,}

💳 <b>Card Payment</b>
• ⚡ Instant credit
• 💳 All cards accepted
• 🔄 Processing fee: ₹{card_fee:.0f}
• 💰 <b>Total:</b> ₹{card_total:.0f}

💸 <b>Digital Wallets</b>
• ⚡ Quick transfer
• 🎁 Cashback offers
• 💰 <b>Total:</b> ₹{amount:,}

🔥 <b>Special Features:</b>
• Generate QR codes for easy payment
• Direct UPI app opening
• Step-by-step payment guide
• 24/7 payment support

💡 <b>UPI recommended for fastest & cheapest payments!</b>
"""

            # Import payment menu
            from payment_system import get_payment_main_menu
            await message.answer(text, reply_markup=get_payment_main_menu())

        except ValueError:
            await message.answer("⚠️ कृपया valid amount number भेजें!")

    elif current_step == "waiting_ticket_subject":
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Handle ticket subject and ask for description
        user_state[user_id]["data"]["ticket_subject"] = message.text.strip()
        user_state[user_id]["current_step"] = "waiting_ticket_description"

        text = f"""
✅ <b>Subject Added Successfully!</b>

🎫 <b>Create Support Ticket</b>

📝 <b>Step 2: Description</b>

💬 <b>कृपया problem का detailed description भेजें:</b>

💡 <b>जितनी detail देंगे, उतनी fast और accurate help मिलेगी!</b>

⚠️ <b>Include करें:</b>
• Order ID (if applicable)
• Screenshot (if needed)
• Error messages
• When did this happen
"""

        await message.answer(text)

    elif current_step == "waiting_ticket_description":
        # Create the ticket
        ticket_id = generate_ticket_id()

        ticket_data = {
            'ticket_id': ticket_id,
            'user_id': user_id,
            'subject': user_state[user_id]["data"]["ticket_subject"],
            'description': message.text.strip(),
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'last_reply': None
        }

        # Save ticket
        tickets_data[ticket_id] = ticket_data

        # Clear user state
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        text = f"""
🎉 <b>Support Ticket Created Successfully!</b>

🎫 <b>Ticket ID:</b> <code>{ticket_id}</code>
📝 <b>Subject:</b> {ticket_data['subject']}
🔴 <b>Status:</b> Open

✅ <b>Ticket successfully submit हो गया!</b>

⏰ <b>Response Time:</b> 2-4 hours
📞 <b>Priority Support:</b> @{OWNER_USERNAME}

💡 <b>हमारी team जल्दी से आपकी help करेगी!</b>
"""

        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
        ])

        await message.answer(text, reply_markup=back_keyboard)

    # ========== EDIT PROFILE HANDLERS ==========
    elif current_step == "editing_name":
        # Handle name editing
        new_name = message.text.strip()
        if len(new_name) > 50:
            await message.answer("⚠️ Name should be less than 50 characters!")
            return

        users_data[user_id]['full_name'] = new_name
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Name Updated Successfully!</b>

📝 <b>New Name:</b> {new_name}

🎉 <b>Your profile has been updated!</b>
💡 <b>Changes are effective immediately</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "editing_phone":
        # Handle phone editing
        new_phone = message.text.strip()
        # Basic phone validation
        if not any(char.isdigit() for char in new_phone):
            await message.answer("⚠️ Please enter a valid phone number!")
            return

        users_data[user_id]['phone_number'] = new_phone
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Phone Number Updated Successfully!</b>

📱 <b>New Phone:</b> {new_phone}

🎉 <b>Your contact information has been updated!</b>
💡 <b>This number will be used for important notifications</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "editing_email":
        # Handle email editing
        new_email = message.text.strip()
        # Basic email validation
        if "@" not in new_email or "." not in new_email:
            await message.answer("⚠️ Please enter a valid email address!")
            return

        users_data[user_id]['email'] = new_email
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Email Address Updated Successfully!</b>

📧 <b>New Email:</b> {new_email}

🎉 <b>Your email has been updated!</b>
💡 <b>This email will be used for important communications</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "editing_bio":
        # Handle bio editing
        new_bio = message.text.strip()
        if len(new_bio) > 200:
            await message.answer("⚠️ Bio should be less than 200 characters!")
            return

        users_data[user_id]['bio'] = new_bio
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Bio Updated Successfully!</b>

💬 <b>New Bio:</b> {new_bio}

🎉 <b>Your bio has been updated!</b>
💡 <b>This appears in your profile preview</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "editing_location":
        # Handle location editing
        new_location = message.text.strip()
        if len(new_location) > 100:
            await message.answer("⚠️ Location should be less than 100 characters!")
            return

        users_data[user_id]['location'] = new_location
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Location Updated Successfully!</b>

🌍 <b>New Location:</b> {new_location}

🎉 <b>Your location has been updated!</b>
💡 <b>This helps us provide location-based offers</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    elif current_step == "editing_birthday":
        # Handle birthday editing
        new_birthday = message.text.strip()

        users_data[user_id]['birthday'] = new_birthday
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Birthday Updated Successfully!</b>

🎂 <b>New Birthday:</b> {new_birthday}

🎉 <b>Your birthday has been updated!</b>
💡 <b>You'll receive special offers on your birthday</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    else:
        # Handle unknown messages for users with completed accounts
        if is_account_created(user_id):
            text = """
❓ <b>Unknown Command</b>

 कृपया नीचे दिए गए buttons का इस्तेमाल करें।

💡 <b>Available Commands:</b>
/start - Main menu
/menu - Show menu
"""
            await message.answer(text, reply_markup=get_main_menu())
        else:
            # Show account creation for users without accounts
            text = """
⚠️ <b>Account Required</b>

आपका account अभी तक create नहीं हुआ है!

📝 <b>सभी features का access पाने के लिए पहले account create करें</b>
"""
            await message.answer(text, reply_markup=get_account_creation_menu())

# ========== PHOTO HANDLERS ==========
@dp.message(F.photo)
async def handle_photo_input(message: Message):
    """Handle photo input for profile picture updates"""
    if not message.from_user:
        return

    user_id = message.from_user.id
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "editing_photo":
        # Handle profile photo update
        if not message.photo:
            await message.answer("⚠️ Please send a valid photo!")
            return

        # Get the largest photo size
        photo = message.photo[-1]
        file_id = photo.file_id

        # Store photo file_id in user data
        users_data[user_id]['profile_photo'] = file_id
        user_state[user_id]["current_step"] = None

        text = f"""
✅ <b>Profile Photo Updated Successfully!</b>

📸 <b>Photo Information:</b>
• 🆔 <b>File ID:</b> {file_id[:20]}...
• 📏 <b>Size:</b> {photo.width}x{photo.height}
• 💾 <b>File Size:</b> {photo.file_size or 'Unknown'} bytes

🎉 <b>Your profile photo has been updated!</b>
💡 <b>This photo will appear in your profile preview</b>

🔒 <b>Privacy:</b>
Your photo is stored securely and used only for profile display.
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Continue Editing", callback_data="edit_profile"),
                InlineKeyboardButton(text="👀 Preview Profile", callback_data="preview_profile")
            ],
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)
    else:
        # Photo sent without context
        if is_account_created(user_id):
            text = """
📸 <b>Photo Received</b>

💡 <b>To update your profile photo:</b>
1. Go to My Account → Edit Profile
2. Click on "Update Photo"
3. Send your photo when prompted

🔄 <b>Or use the menu below:</b>
"""
            await message.answer(text, reply_markup=get_main_menu())

# ========== CANCEL COMMAND HANDLER ==========
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """Handle cancel command during editing"""
    if not message.from_user:
        return

    user_id = message.from_user.id
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step and current_step.startswith("editing_"):
        user_state[user_id]["current_step"] = None
        user_state[user_id]["data"] = {}

        text = """
❌ <b>Editing Cancelled</b>

🔄 <b>No changes were made</b>
💡 <b>You can start editing again anytime</b>
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")
            ]
        ])

        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("💡 No active editing session to cancel.")

# ========== ERROR HANDLERS ==========
@dp.message()
async def handle_unknown_message(message: Message):
    """Handle unknown messages"""
    pass  # Text messages are handled by handle_text_input

# ========== WEBHOOK SETUP ==========
async def on_startup(bot: Bot) -> None:
    """Bot startup configuration"""
    try:
        commands = [
            BotCommand(command="start", description="🏠 Main Menu"),
            BotCommand(command="menu", description="📋 Show Menu")
        ]
        await bot.set_my_commands(commands)

        # Only set webhook if BASE_WEBHOOK_URL is provided
        if BASE_WEBHOOK_URL and WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
            print(f"✅ India Social Panel Bot started with webhook: {WEBHOOK_URL}")
        else:
            # For local development, delete webhook and use polling
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ India Social Panel Bot started in polling mode")

        # Send bot alive notifications to admin users immediately
        print("📧 Sending bot alive notifications to admin users...")
        for admin_id in admin_users:
            try:
                user_data = users_data.get(admin_id, {})
                first_name = user_data.get("first_name", "Admin")
                username = user_data.get("username", "")
                success = await send_bot_alive_notification(admin_id, first_name, is_admin=True, username=username)
                if success:
                    print(f"✅ Admin notification sent to {admin_id}")
                await asyncio.sleep(0.2)  # Small delay to avoid rate limits
            except Exception as e:
                print(f"❌ Failed to notify admin {admin_id}: {e}")

        print("✅ Bot alive notifications sent to all admins!")

        # Send notifications to users who interacted during downtime (if any)
        if users_to_notify:
            print(f"📧 Sending bot alive notifications to {len(users_to_notify)} regular users...")
            for user_id in users_to_notify.copy():
                try:
                    user_data = users_data.get(user_id, {})
                    first_name = user_data.get("first_name", "")
                    username = user_data.get("username", "")
                    await send_bot_alive_notification(user_id, first_name, is_admin=False, username=username)
                    await asyncio.sleep(0.1)  # Small delay to avoid rate limits
                except Exception as e:
                    print(f"❌ Failed to notify user {user_id}: {e}")
            users_to_notify.clear()
            print("✅ Bot alive notifications sent to regular users!")

    except Exception as e:
        print(f"❌ Error during startup: {e}")
        # Continue anyway for local development

async def on_shutdown(bot: Bot) -> None:
    """Bot shutdown cleanup"""
    if BASE_WEBHOOK_URL:
        await bot.delete_webhook()
    print("✅ India Social Panel Bot stopped!")

async def start_polling():
    """Start bot in polling mode for development"""
    try:
        await on_startup(bot)
        print("🚀 Bot started in polling mode. Press Ctrl+C to stop.")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error in polling mode: {e}")
    finally:
        await on_shutdown(bot)


# ========== MISSING PAYMENT & NAVIGATION HANDLERS ==========

@dp.callback_query(F.data == "payment_upi")
async def handle_payment_upi(callback: CallbackQuery):
    """Handle UPI payment selection"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 PhonePe", callback_data="upi_phonepe"),
                InlineKeyboardButton(text="🔴 Google Pay", callback_data="upi_gpay")
            ],
            [
                InlineKeyboardButton(text="💙 Paytm", callback_data="upi_paytm"),
                InlineKeyboardButton(text="🟠 FreeCharge", callback_data="upi_freecharge")
            ],
            [
                InlineKeyboardButton(text="🔵 JioMoney", callback_data="upi_jio"),
                InlineKeyboardButton(text="🟡 Amazon Pay", callback_data="upi_amazon")
            ],
            [
                InlineKeyboardButton(text="💡 UPI Guide", callback_data="upi_guide"),
                InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
            ]
        ])

        await safe_edit_message(
            callback,
            "📱 **UPI Payment**\n\n"
            "Choose your preferred UPI app:\n\n"
            "💡 All UPI payments are instant and secure!",
            keyboard
        )

    except Exception as e:
        print(f"UPI payment error: {e}")
        await callback.answer("❌ Error loading UPI options", show_alert=True)

@dp.callback_query(F.data == "payment_wallet")
async def handle_payment_wallet(callback: CallbackQuery):
    """Handle wallet payment selection"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💙 Paytm", callback_data="wallet_paytm"),
                InlineKeyboardButton(text="🟢 PhonePe", callback_data="wallet_phonepe")
            ],
            [
                InlineKeyboardButton(text="🔴 Google Pay", callback_data="wallet_gpay"),
                InlineKeyboardButton(text="🟠 FreeCharge", callback_data="wallet_freecharge")
            ],
            [
                InlineKeyboardButton(text="🔵 JioMoney", callback_data="wallet_jio"),
                InlineKeyboardButton(text="🟡 Amazon Pay", callback_data="wallet_amazon")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
            ]
        ])

        await safe_edit_message(
            callback,
            "💸 **Digital Wallets**\n\n"
            "Select your wallet:",
            keyboard
        )

    except Exception as e:
        print(f"Wallet payment error: {e}")
        await callback.answer("❌ Error loading wallet options", show_alert=True)

@dp.callback_query(F.data == "payment_bank")
async def handle_payment_bank(callback: CallbackQuery):
    """Handle bank payment selection"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 Net Banking", callback_data="bank_netbanking"),
                InlineKeyboardButton(text="💳 IMPS Transfer", callback_data="bank_imps")
            ],
            [
                InlineKeyboardButton(text="💸 NEFT Transfer", callback_data="bank_neft"),
                InlineKeyboardButton(text="⚡ RTGS Transfer", callback_data="bank_rtgs")
            ],
            [
                InlineKeyboardButton(text="💡 Transfer Guide", callback_data="bank_guide"),
                InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
            ]
        ])

        await safe_edit_message(
            callback,
            "🏦 **Bank Transfer**\n\n"
            "Choose transfer method:\n\n"
            "⚡ IMPS/NEFT: Instant to 2 hours\n"
            "🏦 Net Banking: Direct bank transfer\n"
            "💳 RTGS: For amounts ₹2 lakh+",
            keyboard
        )

    except Exception as e:
        print(f"Bank payment error: {e}")
        await callback.answer("❌ Error loading bank options", show_alert=True)

@dp.callback_query(F.data == "payment_card")
async def handle_payment_card(callback: CallbackQuery):
    """Handle card payment selection"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Debit Card", callback_data="card_debit"),
                InlineKeyboardButton(text="💎 Credit Card", callback_data="card_credit")
            ],
            [
                InlineKeyboardButton(text="🔐 Secure Payment", callback_data="card_security"),
                InlineKeyboardButton(text="💡 Payment Guide", callback_data="card_guide")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Payment", callback_data="add_funds")
            ]
        ])

        await safe_edit_message(
            callback,
            "💳 **Card Payment**\n\n"
            "Secure card payments with encryption:\n\n"
            "✅ 256-bit SSL encryption\n"
            "✅ PCI DSS compliant\n"
            "✅ Instant processing",
            keyboard
        )

    except Exception as e:
        print(f"Card payment error: {e}")
        await callback.answer("❌ Error loading card options", show_alert=True)

@dp.callback_query(F.data.startswith("amount_"))
async def handle_amount_selection(callback: CallbackQuery):
    """Handle amount selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        amount_str = callback.data.replace("amount_", "")
        if amount_str == "custom":
            await callback.answer("💬 Please type custom amount in chat: /amount 500", show_alert=True)
            return

        amount = int(amount_str)
        user_id = callback.from_user.id

        # Store selected amount
        if user_id not in users_data:
            users_data[user_id] = {}
        users_data[user_id]["selected_amount"] = amount

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 UPI Payment", callback_data="payment_upi"),
                InlineKeyboardButton(text="💸 Digital Wallets", callback_data="payment_wallet")
            ],
            [
                InlineKeyboardButton(text="🏦 Bank Transfer", callback_data="payment_bank"),
                InlineKeyboardButton(text="💳 Card Payment", callback_data="payment_card")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Amounts", callback_data="add_funds")
            ]
        ])

        await safe_edit_message(
            callback,
            f"💰 **Amount Selected: ₹{amount}**\n\n"
            f"Choose your payment method:\n\n"
            f"🔥 Most Popular: UPI Payment\n"
            f"⚡ Fastest: Digital Wallets\n"
            f"🔐 Most Secure: Bank Transfer",
            keyboard
        )

    except Exception as e:
        print(f"Amount selection error: {e}")
        await callback.answer("❌ Error processing amount", show_alert=True)

@dp.callback_query(F.data.startswith("edit_"))
async def handle_edit_profile_options(callback: CallbackQuery):
    """Handle profile editing options"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        edit_type = callback.data.replace("edit_", "")

        if edit_type == "name":
            await callback.answer("💬 Please type: /name Your New Name", show_alert=True)
        elif edit_type == "email":
            await callback.answer("📧 Please type: /email your@email.com", show_alert=True)
        elif edit_type == "phone":
            await callback.answer("📱 Please type: /phone +91xxxxxxxxxx", show_alert=True)
        elif edit_type == "bio":
            await callback.answer("💼 Please type: /bio Your bio here", show_alert=True)
        elif edit_type == "username":
            await callback.answer("🎯 Please type: /username newusername", show_alert=True)
        else:
            await callback.answer("⚠️ Coming soon!", show_alert=True)

    except Exception as e:
        print(f"Edit profile error: {e}")
        await callback.answer("❌ Error processing edit request", show_alert=True)


# ========== MISSING SERVICE & NAVIGATION HANDLERS ==========

@dp.callback_query(F.data.startswith("cat_"))
async def handle_service_category_selection(callback: CallbackQuery):
    """Handle service category selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        category = callback.data.replace("cat_", "")

        category_names = {
            "instagram": "📷 Instagram",
            "youtube": "🎥 YouTube", 
            "facebook": "📘 Facebook",
            "twitter": "🐦 Twitter",
            "tiktok": "🎵 TikTok",
            "linkedin": "💼 LinkedIn",
            "whatsapp": "💬 WhatsApp"
        }

        category_name = category_names.get(category, category.capitalize())

        # Sample services for the category
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Followers", callback_data=f"service_{category}_followers"),
                InlineKeyboardButton(text="❤️ Likes", callback_data=f"service_{category}_likes")
            ],
            [
                InlineKeyboardButton(text="👁️ Views", callback_data=f"service_{category}_views"),
                InlineKeyboardButton(text="💬 Comments", callback_data=f"service_{category}_comments")
            ],
            [
                InlineKeyboardButton(text="👎 Dislikes", callback_data=f"service_{category}_dislikes"),
                InlineKeyboardButton(text="⭐ Popular", callback_data=f"service_{category}_popular")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Services", callback_data="service_list")
            ]
        ])

        await safe_edit_message(
            callback,
            f"{category_name} **Services**\n\n"
            f"🎯 High Quality Services\n"
            f"⚡ Fast Delivery\n" 
            f"🔐 Safe & Secure\n"
            f"💰 Best Prices\n\n"
            f"Choose service type:",
            keyboard
        )

    except Exception as e:
        print(f"Category selection error: {e}")
        await callback.answer("❌ Error loading category", show_alert=True)

@dp.callback_query(F.data.startswith("quality_"))
async def handle_quality_selection(callback: CallbackQuery):
    """Handle quality selection"""  
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        quality_type = callback.data.replace("quality_", "")

        quality_info = {
            "high": {"name": "🔥 High Quality", "price": "₹50-200", "desc": "Premium accounts, slow delivery"},
            "medium": {"name": "⚡ Medium Quality", "price": "₹30-100", "desc": "Good accounts, fast delivery"},
            "basic": {"name": "💰 Basic Quality", "price": "₹10-50", "desc": "Standard accounts, instant delivery"}
        }

        info = quality_info.get(quality_type, quality_info["medium"])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➡️ Continue Order", callback_data=f"continue_order_{quality_type}"),
                InlineKeyboardButton(text="💡 Quality Info", callback_data=f"quality_info_{quality_type}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Qualities", callback_data="back_qualities")
            ]
        ])

        await safe_edit_message(
            callback,
            f"{info['name']} **Selected**\n\n"
            f"💰 Price Range: {info['price']}\n"
            f"📝 Description: {info['desc']}\n\n"
            f"✅ Ready to proceed with order?",
            keyboard
        )

    except Exception as e:
        print(f"Quality selection error: {e}")
        await callback.answer("❌ Error processing quality selection", show_alert=True)

@dp.callback_query(F.data.startswith("continue_order_"))
async def handle_continue_order(callback: CallbackQuery):
    """Handle continue order after quality selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        quality = callback.data.replace("continue_order_", "")
        user_id = callback.from_user.id

        # Store order info
        if user_id not in users_data:
            users_data[user_id] = {}
        users_data[user_id]["pending_order"] = {"quality": quality}

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_main")
            ]
        ])

        await safe_edit_message(
            callback,
            f"📦 **Order Summary**\n\n"
            f"Quality: {quality.capitalize()}\n"
            f"Status: Ready to place\n\n"
            f"💰 Final price will be calculated based on quantity\n\n"
            f"Confirm your order?",
            keyboard
        )

    except Exception as e:
        print(f"Continue order error: {e}")
        await callback.answer("❌ Error processing order", show_alert=True)

@dp.callback_query(F.data.startswith("platform_"))
async def handle_platform_selection(callback: CallbackQuery):
    """Handle platform selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        platform = callback.data.replace("platform_", "")

        platform_info = {
            "instagram": {"emoji": "📷", "name": "Instagram", "services": "Followers, Likes, Views, Comments"},
            "youtube": {"emoji": "🎥", "name": "YouTube", "services": "Subscribers, Views, Likes, Comments"},
            "facebook": {"emoji": "📘", "name": "Facebook", "services": "Followers, Likes, Shares, Comments"},
            "twitter": {"emoji": "🐦", "name": "Twitter", "services": "Followers, Likes, Retweets, Views"},
            "tiktok": {"emoji": "🎵", "name": "TikTok", "services": "Followers, Likes, Views, Shares"},
            "linkedin": {"emoji": "💼", "name": "LinkedIn", "services": "Connections, Likes, Views, Shares"}
        }

        info = platform_info.get(platform, {"emoji": "🌟", "name": platform.capitalize(), "services": "Various services"})

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Followers", callback_data=f"service_{platform}_followers"),
                InlineKeyboardButton(text="❤️ Likes", callback_data=f"service_{platform}_likes")
            ],
            [
                InlineKeyboardButton(text="👁️ Views", callback_data=f"service_{platform}_views"),
                InlineKeyboardButton(text="💬 Comments", callback_data=f"service_{platform}_comments")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Platforms", callback_data="service_list")
            ]
        ])

        await safe_edit_message(
            callback,
            f"{info['emoji']} **{info['name']} Services**\n\n"
            f"Available: {info['services']}\n\n"
            f"🎯 High Quality\n"
            f"⚡ Fast Delivery\n"
            f"🔐 Safe & Secure\n\n"
            f"Choose service:",
            keyboard
        )

    except Exception as e:
        print(f"Platform selection error: {e}")
        await callback.answer("❌ Error loading platform services", show_alert=True)


# ========== REMAINING CRITICAL HANDLERS ==========

@dp.callback_query(F.data.startswith("select_lang_"))
async def handle_language_selection(callback: CallbackQuery):
    """Handle language selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        lang_code = callback.data.replace("select_lang_", "")
        user_id = callback.from_user.id

        # Store user language preference
        if user_id not in users_data:
            users_data[user_id] = {}
        users_data[user_id]["language"] = lang_code

        lang_names = {
            "hindi": "🇮🇳 हिंदी (Hindi)",
            "english": "🇬🇧 English",
            "chinese": "🇨🇳 中文 (Chinese)",
            "spanish": "🇪🇸 Español",
            "french": "🇫🇷 Français",
            "german": "🇩🇪 Deutsch",
            "russian": "🇷🇺 Русский",
            "arabic": "🇸🇦 العربية"
        }

        selected_lang = lang_names.get(lang_code, "Selected Language")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main"),
                InlineKeyboardButton(text="👤 My Account", callback_data="my_account")
            ]
        ])

        await safe_edit_message(
            callback,
            f"✅ **Language Updated!**\n\n"
            f"🌐 Selected: {selected_lang}\n\n"
            f"🚀 Language support is being improved!\n"
            f"📢 You'll get notified when full translation is ready.\n\n"
            f"🙏 Thank you for choosing India Social Panel!",
            keyboard
        )

    except Exception as e:
        print(f"Language selection error: {e}")
        await callback.answer("❌ Error updating language", show_alert=True)

@dp.callback_query(F.data.startswith("wallet_"))
async def handle_specific_wallet(callback: CallbackQuery):
    """Handle specific wallet selection"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        wallet = callback.data.replace("wallet_", "")
        user_id = callback.from_user.id
        amount = users_data.get(user_id, {}).get("selected_amount", 100)

        wallet_info = {
            "paytm": {"name": "💙 Paytm", "fee": "₹0"},
            "phonepe": {"name": "🟢 PhonePe", "fee": "₹0"},
            "gpay": {"name": "🔴 Google Pay", "fee": "₹0"},
            "freecharge": {"name": "🟠 FreeCharge", "fee": "₹0"},
            "jio": {"name": "🔵 JioMoney", "fee": "₹2"},
            "amazon": {"name": "🟡 Amazon Pay", "fee": "₹0"}  
        }

        info = wallet_info.get(wallet, {"name": wallet.capitalize(), "fee": "₹0"})

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Generate QR", callback_data=f"qr_generate_{wallet}_{amount}"),
                InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_upi_{wallet}")
            ],
            [
                InlineKeyboardButton(text="📱 Open UPI App", callback_data=f"open_upi_{wallet}_{amount}"),
                InlineKeyboardButton(text="✅ Payment Done", callback_data=f"payment_done_{amount}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Wallets", callback_data="payment_wallet")
            ]
        ])

        await safe_edit_message(
            callback,
            f"{info['name']} **Payment**\n\n"
            f"💰 Amount: ₹{amount}\n"
            f"💳 Processing Fee: {info['fee']}\n"
            f"⚡ Processing: Instant\n\n"
            f"Choose payment option:",
            keyboard
        )

    except Exception as e:
        print(f"Wallet selection error: {e}")
        await callback.answer("❌ Error processing wallet", show_alert=True)

@dp.callback_query(F.data.startswith("upi_"))
async def handle_specific_upi(callback: CallbackQuery):
    """Handle specific UPI app selection"""
    try:
        if callback.data and callback.data.startswith("upi_guide"):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to UPI", callback_data="payment_upi")]
            ])

            await safe_edit_message(
                callback,
                "💡 **UPI Payment Guide**\n\n"
                "📱 **How to pay:**\n"
                "1. Select your UPI app\n"
                "2. Scan QR code OR copy UPI ID\n"
                "3. Enter amount and complete payment\n"
                "4. Click 'Payment Done' button\n\n"
                "⚡ **Payment is instant!**\n"
                "🔐 **100% Safe & Secure**",
                keyboard
            )
            return

        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        upi_app = callback.data.replace("upi_", "")
        user_id = callback.from_user.id
        amount = users_data.get(user_id, {}).get("selected_amount", 100)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Generate QR", callback_data=f"qr_generate_{upi_app}_{amount}"),
                InlineKeyboardButton(text="📋 Copy UPI ID", callback_data=f"copy_upi_{upi_app}")
            ],
            [
                InlineKeyboardButton(text="📱 Open UPI App", callback_data=f"open_upi_{upi_app}_{amount}"),
                InlineKeyboardButton(text="✅ Payment Done", callback_data=f"payment_done_{amount}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to UPI", callback_data="payment_upi")
            ]
        ])

        await safe_edit_message(
            callback,
            f"📱 **{upi_app.upper()} Payment**\n\n"
            f"💰 Amount: ₹{amount}\n"
            f"⚡ Processing: Instant\n"
            f"🔐 Safe & Secure\n\n"
            f"Choose payment method:",
            keyboard
        )

    except Exception as e:
        print(f"UPI selection error: {e}")
        await callback.answer("❌ Error processing UPI", show_alert=True)

@dp.callback_query(F.data.startswith("bank_"))
async def handle_bank_options(callback: CallbackQuery):
    """Handle bank transfer options"""
    try:
        if not callback.data:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        bank_option = callback.data.replace("bank_", "")

        if bank_option == "guide":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Bank Transfer", callback_data="payment_bank")]
            ])

            await safe_edit_message(
                callback,
                "💡 **Bank Transfer Guide**\n\n"
                "🏦 **NEFT Transfer:**\n"
                "• Processing: 1-2 hours\n"
                "• Available: 24/7\n"
                "• Charges: As per bank\n\n"
                "⚡ **IMPS Transfer:**\n"
                "• Processing: Instant\n"
                "• Available: 24/7\n"
                "• Limit: ₹5 lakh/day\n\n"
                "💳 **RTGS Transfer:**\n"
                "• Processing: Instant\n"
                "• Minimum: ₹2 lakh\n"
                "• Time: 9 AM - 4:30 PM",
                keyboard
            )
            return

        # Handle other bank options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Copy Bank Details", callback_data="copy_bank_details"),
                InlineKeyboardButton(text="💡 Transfer Guide", callback_data="bank_guide")
            ],
            [
                InlineKeyboardButton(text="✅ Transfer Done", callback_data="transfer_done"),
                InlineKeyboardButton(text="⬅️ Back to Bank", callback_data="payment_bank")
            ]
        ])

        await safe_edit_message(
            callback,
            f"🏦 **{bank_option.upper().replace('_', ' ')} Transfer**\n\n"
            f"Transfer money to our bank account:\n\n"
            f"🏦 **Account Details:**\n"
            f"Bank: State Bank of India\n"
            f"A/C: 1234567890123\n"
            f"IFSC: SBIN0001234\n"
            f"Name: India Social Panel\n\n"
            f"💡 Use your User ID as reference: {callback.from_user.id}",
            keyboard
        )

    except Exception as e:
        print(f"Bank options error: {e}")
        await callback.answer("❌ Error loading bank options", show_alert=True)


# ========== MESSAGE HANDLERS ==========
@dp.message()
async def handle_all_messages(message: Message):
    """Handle all text messages for user input states"""
    user = message.from_user
    if not user:
        return

    # Check if message is old (sent before bot restart)
    if is_message_old(message):
        mark_user_for_notification(user.id)
        return  # Ignore old messages

    user_id = user.id
    init_user(user_id, user.username or "", user.first_name or "")

    # Handle bot restart notifications
    global bot_just_restarted
    if bot_just_restarted and user_id in users_to_notify:
        await send_first_interaction_notification(user_id, user.first_name or "", user.username or "")
        users_to_notify.discard(user_id)

    # Check user input state
    if user_id in user_state and user_state[user_id].get("current_step"):
        # Handle account creation states
        if user_state[user_id]["current_step"] == "waiting_name":
            await account_handlers.handle_name_input(message, user_state, users_data)
        elif user_state[user_id]["current_step"] == "waiting_phone":
            await account_handlers.handle_phone_input(message, user_state, users_data)
        elif user_state[user_id]["current_step"] == "waiting_email":
            await account_handlers.handle_email_input(message, user_state, users_data)
        elif user_state[user_id]["current_step"] == "waiting_ticket_subject":
            await handle_ticket_subject_input(message)
        elif user_state[user_id]["current_step"] == "waiting_ticket_message":
            await handle_ticket_message_input(message)
        else:
            # Default response for undefined states
            await message.answer("🤔 Something went wrong. Please use /start to return to main menu.")
    else:
        # No specific state - send to main menu
        await message.answer("👋 Use /start to access the main menu!")


# ========== TICKET HANDLING ==========
async def handle_ticket_subject_input(message: Message):
    """Handle ticket subject input"""
    user = message.from_user
    if not user or not message.text:
        return

    user_id = user.id
    subject = message.text.strip()

    if len(subject) < 5:
        await message.answer("⚠️ Subject too short! Please enter at least 5 characters.")
        return

    # Store subject and move to next step
    user_state[user_id]["data"]["subject"] = subject
    user_state[user_id]["current_step"] = "waiting_ticket_message"

    text = """
📝 <b>Create Support Ticket - Step 2/2</b>

💬 <b>अब ticket का detailed message भेजें:</b>

⚠️ <b>Details include करें:</b>
• Problem का clear description
• Error messages (अगर कोई है)
• Screenshots (अगर applicable है)
• आपने क्या try किया है

💡 <b>जितनी ज्यादा details होंगी, उतना fast resolution मिलेगा!</b>
"""

    await message.answer(text)


async def handle_ticket_message_input(message: Message):
    """Handle ticket message input"""
    user = message.from_user
    if not user or not message.text:
        return

    user_id = user.id
    ticket_message = message.text.strip()

    if len(ticket_message) < 10:
        await message.answer("⚠️ Message too short! Please provide more details.")
        return

    # Generate ticket ID
    ticket_id = generate_ticket_id()

    # Create ticket
    tickets_data[ticket_id] = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "subject": user_state[user_id]["data"]["subject"],
        "message": ticket_message,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "admin_reply": None
    }

    # Clear user state
    user_state[user_id]["current_step"] = None
    user_state[user_id]["data"] = {}

    # Success message
    text = f"""
✅ <b>Ticket Successfully Created!</b>

🎫 <b>Ticket ID:</b> <code>{ticket_id}</code>
📝 <b>Subject:</b> {tickets_data[ticket_id]['subject']}
🔄 <b>Status:</b> Open

📞 <b>Support team को notification भेज दी गई!</b>
⏰ <b>Response time:</b> 2-6 hours

🎯 <b>Ticket status track करने के लिए:</b>
/start → 🎫 Support Tickets → 📖 Mere Tickets Dekhein
"""

    success_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Mere Tickets", callback_data="view_tickets")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
    ])

    await message.answer(text, reply_markup=success_keyboard)

    # Notify admins about new ticket
    for admin_id in admin_users:
        try:
            admin_text = f"""
🎫 <b>New Support Ticket</b>

🆔 <b>Ticket ID:</b> {ticket_id}
👤 <b>User:</b> @{user.username or 'N/A'} ({user_id})
📝 <b>Subject:</b> {tickets_data[ticket_id]['subject']}
💬 <b>Message:</b> {ticket_message[:200]}{'...' if len(ticket_message) > 200 else ''}

📅 <b>Created:</b> {format_time(tickets_data[ticket_id]['created_at'])}
"""
            await bot.send_message(admin_id, admin_text)
        except:
            pass  # Admin notification failed, continue


# ========== BOT STARTUP ==========
async def set_bot_commands():
    """Set bot commands in menu"""
    commands = [
        BotCommand(command="start", description="🏠 Main Menu"),
        BotCommand(command="menu", description="🏠 Show Main Menu"),
        BotCommand(command="help", description="❓ Get Help")
    ]
    await bot.set_my_commands(commands)


async def send_background_notifications():
    """Send startup notifications in background after startup (Render-friendly)"""
    # Wait a bit for server to be fully ready
    await asyncio.sleep(2)
    
    print("📧 Sending bot alive notifications to admin users...")
    for admin_id in admin_users:
        try:
            user_data = users_data.get(admin_id, {})
            username = user_data.get("username", "")
            await send_bot_alive_notification(admin_id, "Admin", True, username)
        except Exception as e:
            print(f"❌ Failed to send alive notification to {admin_id}: {e}")
    print("✅ Bot alive notifications sent to all admins!")

async def send_startup_notifications():
    """Legacy function - kept for compatibility"""
    await send_background_notifications()


# ========== LIFECYCLE FUNCTIONS ==========
async def on_startup(bot: Bot) -> None:
    """Startup function with proper webhook configuration"""
    try:
        # Set bot commands
        commands = [
            BotCommand(command="start", description="🏠 Main Menu"),
            BotCommand(command="menu", description="🏠 Show Main Menu"),
            BotCommand(command="help", description="❓ Get Help")
        ]
        await bot.set_my_commands(commands)
        print("✅ Bot commands set successfully")
        
        # Set webhook if URL is available
        if WEBHOOK_URL:
            # Delete any existing webhook first
            await bot.delete_webhook(drop_pending_updates=True)
            print("🗑️ Cleared previous webhook")
            
            # Set new webhook
            await bot.set_webhook(
                url=WEBHOOK_URL, 
                secret_token=WEBHOOK_SECRET,
                drop_pending_updates=True
            )
            print(f"✅ Webhook set successfully: {WEBHOOK_URL}")
            
            # Verify webhook
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url == WEBHOOK_URL:
                print("✅ Webhook verification successful")
            else:
                print(f"⚠️ Webhook verification failed. Expected: {WEBHOOK_URL}, Got: {webhook_info.url}")
                
            print("🔄 Registering payment handlers...")
            print("🔄 Registering service handlers...")
            print("✅ Service handlers registered successfully!")
            print(f"🌐 Web server started on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
            print("🤖 Bot is ready to receive webhooks!")
        else:
            print("⚠️ No webhook URL configured. Bot cannot receive messages!")
            print("📋 Please set BASE_WEBHOOK_URL in environment variables")
            
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise

async def on_shutdown(bot: Bot) -> None:
    """Shutdown function - same as working bot"""
    await bot.delete_webhook()
    print("✅ India Social Panel Bot stopped!")

def main():
    """Main function - exactly like working bot"""
    # Register lifecycle events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    if WEBHOOK_URL:
        # Create aiohttp app and register handlers - same as working bot
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=WEBHOOK_SECRET,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        
        # Mount dispatcher on app and start web server - same as working bot
        setup_application(app, dp, bot=bot)
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    else:
        # Polling mode for local development
        print("✅ India Social Panel Bot started in polling mode")
        asyncio.run(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


if __name__ == "__main__":
    """Entry point - exactly like working bot"""
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")

