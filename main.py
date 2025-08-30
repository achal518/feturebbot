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
import uuid
from datetime import datetime, timedelta
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

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")  # Optional for local development
OWNER_NAME = os.getenv("OWNER_NAME", "Achal Parvat")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "achal_parvat")

# Webhook settings (only if webhook URL provided)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "india_social_panel_secret_2025"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}" if BASE_WEBHOOK_URL else None

# Server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 5000))

# Bot initialization
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
START_TIME = time.time()

# ========== DATA STORAGE ==========
# In-memory storage (will be replaced with database later)
users_data: Dict[int, Dict[str, Any]] = {}
orders_data: Dict[str, Dict[str, Any]] = {}
tickets_data: Dict[str, Dict[str, Any]] = {}
user_state: Dict[int, Dict[str, Any]] = {}  # For tracking user input states
order_temp: Dict[int, Dict[str, Any]] = {}  # For temporary order data
admin_users = {123456789}  # Add your admin user ID here

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

def is_account_created(user_id: int) -> bool:
    """Check if user has completed account creation"""
    return users_data.get(user_id, {}).get("account_created", False)

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
    user = message.from_user
    if not user:
        return

    init_user(user.id, user.username or "", user.first_name or "")

    # Check if account is created
    if is_account_created(user.id):
        # Existing user welcome
        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user.first_name or 'Friend'}</b>! 🙏

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
        # New user - account creation required
        welcome_text = f"""
🇮🇳 <b>स्वागत है India Social Panel में!</b>

नमस्ते <b>{user.first_name or 'Friend'}</b>! 🙏

🎯 <b>भारत का सबसे भरोसेमंद SMM Panel</b>
✅ <b>High Quality Services</b>
✅ <b>Instant Delivery</b>
✅ <b>24/7 Support</b>
✅ <b>Affordable Rates</b>

📱 <b>सभी Social Media Platforms के लिए:</b>
Instagram • YouTube • Facebook • Twitter • TikTok • LinkedIn

⚠️ <b>सभी features का इस्तेमाल करने के लिए पहले Account Create करें:</b>
"""
        await message.answer(welcome_text, reply_markup=get_account_creation_menu())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    await message.answer("🏠 <b>Main Menu</b>\nअपनी जरूरत के अनुसार option चुनें:", reply_markup=get_main_menu())

# ========== ACCOUNT CREATION HANDLERS ==========
@dp.callback_query(F.data == "create_account")
async def cb_create_account(callback: CallbackQuery):
    """Start account creation process"""
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Initialize user state if not exists
    if user_id not in user_state:
        user_state[user_id] = {"current_step": None, "data": {}}

    user_state[user_id]["current_step"] = "waiting_name"

    text = """
📋 <b>Account Creation - Step 1/3</b>

📝 <b>कृपया अपना पूरा नाम भेजें:</b>

⚠️ <b>Example:</b> Rahul Kumar
💬 <b>Instruction:</b> अपना full name type करके भेज दें
"""

    await callback.message.edit_text(text)
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

            if callback.message:
                await callback.message.edit_text(text, reply_markup=get_account_creation_menu())
            await callback.answer()
            return

        # Account exists, proceed with handler
        return await handler(callback)

    return wrapper

# Initialize account handlers now that all variables are defined
account_handlers.init_account_handlers(
    dp, users_data, orders_data, require_account,
    format_currency, format_time, is_account_created, user_state
)

# Initialize payment system
payment_system.register_payment_handlers(dp, users_data, user_state, format_currency)

# Import account menu function
get_account_menu = account_handlers.get_account_menu

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

    await callback.message.edit_text(text, reply_markup=get_services_main_menu())
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

    await callback.message.edit_text(text, reply_markup=amount_keyboard)
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

    await callback.message.edit_text(text, reply_markup=get_services_tools_menu())
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

    await callback.message.edit_text(text, reply_markup=get_offers_rewards_menu())
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

        await callback.message.edit_text(text, reply_markup=back_keyboard)
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

        await callback.message.edit_text(text, reply_markup=back_keyboard)

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

    await callback.message.edit_text(text, reply_markup=get_contact_menu())
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=get_category_menu())
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

    await callback.message.edit_text(text, reply_markup=get_support_menu())
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

    await callback.message.edit_text(text, reply_markup=get_main_menu())
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

        await callback.message.edit_text(text, reply_markup=fund_keyboard)
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

    await callback.message.edit_text(text, reply_markup=success_keyboard)
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

    await callback.message.edit_text(text, reply_markup=get_main_menu())
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=trial_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=join_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

    await callback.message.edit_text(text, reply_markup=admin_keyboard)
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

    await callback.message.edit_text(text)
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

    await callback.message.edit_text(text, reply_markup=back_keyboard)
    await callback.answer()

# ========== INPUT HANDLERS ==========
@dp.message(F.text)
async def handle_text_input(message: Message):
    """Handle text input for account creation"""
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id

    # Check if user is in account creation flow
    current_step = user_state.get(user_id, {}).get("current_step")

    if current_step == "waiting_name":
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store name and ask for phone
        user_state[user_id]["data"]["full_name"] = message.text.strip()
        user_state[user_id]["current_step"] = "waiting_phone"

        success_text = f"""
✅ <b>Name Successfully Added!</b>

📋 <b>Account Creation - Step 2/3</b>

📱 <b>कृपया अपना Phone Number भेजें:</b>

⚠️ <b>Example:</b> +91 9876543210
💬 <b>Instruction:</b> अपना mobile number type करके भेज दें
"""

        await message.answer(success_text)

    elif current_step == "waiting_phone":
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
        # Initialize user state if not exists
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store email and complete account creation
        user_state[user_id]["data"]["email"] = message.text.strip()

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

        success_text = f"""
🎉 <b>Account Successfully Created!</b>

✅ <b>आपका account तैयार है!</b>

👤 <b>Name:</b> {users_data[user_id]['full_name']}
📱 <b>Phone:</b> {users_data[user_id]['phone_number']}
📧 <b>Email:</b> {users_data[user_id]['email']}

🎆 <b>Welcome to India Social Panel!</b>
अब आप सभी features का इस्तेमाल कर सकते हैं।

💡 <b>अपनी जरूरत के अनुसार option चुनें:</b>
"""

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
        if BASE_WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
            print(f"✅ India Social Panel Bot started with webhook: {WEBHOOK_URL}")
        else:
            # For local development, delete webhook and use polling
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ India Social Panel Bot started in polling mode")
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

def main():
    """Main application entry point"""
    # Register service handlers
    from services import register_service_handlers
    register_service_handlers(dp, require_account)

    # Register lifecycle events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Check if we should use webhook or polling
    if BASE_WEBHOOK_URL:
        # Production mode with webhook
        app = web.Application()
        webhook_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=WEBHOOK_SECRET,
        )
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    else:
        # Development mode with polling
        print("🔄 Starting bot in polling mode...")
        asyncio.run(start_polling())

if __name__ == "__main__":
    main()