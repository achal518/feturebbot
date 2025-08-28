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

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
OWNER_NAME = os.getenv("OWNER_NAME", "Achal Parvat")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "achal_parvat")

# Webhook settings
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "india_social_panel_secret_2025"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

# Server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

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
            InlineKeyboardButton(text="📜 Order History", callback_data="order_history")
        ],
        [
            InlineKeyboardButton(text="📈 Service List", callback_data="service_list"),
            InlineKeyboardButton(text="🎫 Support Tickets", callback_data="support_tickets")
        ],
        [
            InlineKeyboardButton(text="🎁 Refer & Earn", callback_data="refer_earn"),
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

def get_account_menu() -> InlineKeyboardMarkup:
    """Build my account sub-menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refill History", callback_data="refill_history"),
            InlineKeyboardButton(text="🔑 API Key", callback_data="api_key")
        ],
        [
            InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile"),
            InlineKeyboardButton(text="📊 Statistics", callback_data="user_stats")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

def get_contact_menu() -> InlineKeyboardMarkup:
    """Build contact & about menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 Owner Ke Baare Mein", callback_data="owner_info"),
            InlineKeyboardButton(text="🌐 Hamari Website", callback_data="website_info")
        ],
        [
            InlineKeyboardButton(text="💬 Support Channel", callback_data="support_channel"),
            InlineKeyboardButton(text="📜 Seva Ki Shartein (TOS)", callback_data="terms_service")
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

# ========== CALLBACK HANDLERS ==========
@dp.callback_query(F.data == "new_order")
@require_account
async def cb_new_order(callback: CallbackQuery):
    """Handle new order creation"""
    if not callback.message:
        return
        
    text = """
🚀 <b>New Order</b>

<b>Step 1:</b> Social Media Platform चुनें

🎯 <b>सभी platforms पर best quality services उपलब्ध</b>
⚡ <b>Instant start guarantee</b>
🔒 <b>100% Safe & Secure</b>
"""
    
    await callback.message.edit_text(text, reply_markup=get_category_menu())
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
@require_account
async def cb_category_select(callback: CallbackQuery):
    """Handle category selection"""
    if not callback.message:
        return
        
    category = (callback.data or "").replace("cat_", "")
    platform_names = {
        "instagram": "📷 Instagram",
        "youtube": "🎥 YouTube", 
        "facebook": "📘 Facebook",
        "twitter": "🐦 Twitter",
        "linkedin": "💼 LinkedIn",
        "tiktok": "🎵 TikTok"
    }
    
    platform = platform_names.get(category, "Unknown")
    text = f"""
{platform} <b>Services</b>

<b>Step 2:</b> Service Type चुनें

💎 <b>Premium Quality Services</b>
🚀 <b>Fast Delivery</b>
💰 <b>Best Rates in Market</b>
"""
    
    await callback.message.edit_text(text, reply_markup=get_service_menu(category))
    await callback.answer()

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
    
    await callback.message.edit_text(text, reply_markup=get_amount_selection_menu())
    await callback.answer()

@dp.callback_query(F.data == "my_account")
@require_account
async def cb_my_account(callback: CallbackQuery):
    """Handle my account dashboard"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    
    text = f"""
👤 <b>My Account Dashboard</b>

👋 <b>Welcome back, {user_data.get('full_name', user_data.get('first_name', 'User'))}!</b>

📱 <b>Phone:</b> {user_data.get('phone_number', 'Not set')}
📧 <b>Email:</b> {user_data.get('email', 'Not set')}

💰 <b>Balance:</b> {format_currency(user_data.get('balance', 0.0))}
📊 <b>Total Spent:</b> {format_currency(user_data.get('total_spent', 0.0))}
🛒 <b>Total Orders:</b> {user_data.get('orders_count', 0)}
📅 <b>Member Since:</b> {format_time(user_data.get('join_date', ''))}

🔸 <b>Account Status:</b> ✅ Active
🔸 <b>User ID:</b> <code>{user_id}</code>
"""
    
    await callback.message.edit_text(text, reply_markup=get_account_menu())
    await callback.answer()

@dp.callback_query(F.data == "refer_earn")
@require_account
async def cb_refer_earn(callback: CallbackQuery):
    """Handle referral program"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    referral_code = user_data.get('referral_code', 'ISPXXXXXX')
    
    text = f"""
🎁 <b>Refer & Earn Program</b>

💰 <b>हर successful referral पर 10% commission पाएं!</b>

🔗 <b>आपका Referral Link:</b>
<code>https://t.me/{bot.username}?start={referral_code}</code>

📋 <b>आपका Referral Code:</b>
<code>{referral_code}</code>

🎯 <b>कैसे काम करता है:</b>
1. अपना link friends को share करें
2. वे link से bot join करें
3. जब वे funds add करें, आपको 10% commission मिलेगा
4. Commission instant आपके balance में add हो जाएगा

💎 <b>Total Referrals:</b> 0
💰 <b>Total Earnings:</b> ₹0.00
"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
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
@dp.callback_query(F.data.startswith("service_"))
@require_account
async def cb_service_select(callback: CallbackQuery):
    """Handle service selection and ask for link"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    service = (callback.data or "").replace("service_", "")
    
    # Store service in temp order
    if user_id not in order_temp:
        order_temp[user_id] = {}
    order_temp[user_id]["service"] = service
    
    # Service names mapping
    service_names = {
        "ig_followers": "Instagram Followers",
        "ig_likes": "Instagram Likes", 
        "ig_views": "Instagram Views",
        "ig_comments": "Instagram Comments",
        "yt_subscribers": "YouTube Subscribers",
        "yt_likes": "YouTube Likes",
        "yt_views": "YouTube Views",
        "yt_comments": "YouTube Comments"
    }
    
    service_name = service_names.get(service, "Unknown Service")
    user_state[user_id]["current_step"] = "waiting_link"
    user_state[user_id]["data"]["service"] = service
    
    text = f"""
🔗 <b>New Order - Step 3</b>

📋 <b>Selected Service:</b> {service_name}

🔗 <b>कृपया अपना Link/URL भेजें:</b>

⚠️ <b>Example:</b>
• Instagram: https://instagram.com/username
• YouTube: https://youtube.com/channel/xyz

💬 <b>Instruction:</b> अपना profile/post link type करके भेज दें
"""
    
    await callback.message.edit_text(text)
    await callback.answer()

@dp.callback_query(F.data.startswith("amount_"))
@require_account
async def cb_amount_select(callback: CallbackQuery):
    """Handle amount selection for funds"""
    if not callback.message or not callback.from_user:
        return
        
    amount_data = (callback.data or "").replace("amount_", "")
    
    if amount_data == "custom":
        user_id = callback.from_user.id
        user_state[user_id]["current_step"] = "waiting_custom_amount"
        
        text = """
💰 <b>Custom Amount</b>

💬 <b>कृपया amount भेजें:</b>

⚠️ <b>Minimum:</b> ₹100
⚠️ <b>Maximum:</b> ₹50,000

💡 <b>Example:</b> 2500
"""
        await callback.message.edit_text(text)
    else:
        # Fixed amount selected
        amount = int(amount_data)
        transaction_id = f"TXN{int(time.time())}{random.randint(100, 999)}"
        
        text = f"""
💳 <b>Payment Details</b>

💰 <b>Amount:</b> ₹{amount:,}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📱 <b>UPI Payment:</b>
🔸 <b>UPI ID:</b> <code>indiasmm@paytm</code>
🔸 <b>Name:</b> India Social Panel

📝 <b>Payment Instructions:</b>
1. Above UPI ID पर ₹{amount:,} transfer करें
2. Transaction ID mention करें: <code>{transaction_id}</code>
3. Payment proof screenshot admin को भेजें
4. 5-10 minutes में balance add हो जाएगा

📞 <b>Support:</b> @{OWNER_USERNAME}
"""
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="add_funds")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=back_keyboard)
    
    await callback.answer()

@dp.callback_query(F.data == "order_history")
@require_account
async def cb_order_history(callback: CallbackQuery):
    """Show order history"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_orders = [order for order_id, order in orders_data.items() if order.get('user_id') == user_id]
    
    if not user_orders:
        text = """
📜 <b>Order History</b>

📋 <b>कोई orders नहीं मिले</b>

🚀 <b>अपना पहला order place करें और India Social Panel के premium services का मजा लें!</b>
"""
    else:
        text = "📜 <b>Order History</b>\n\n"
        for i, order in enumerate(user_orders[-5:], 1):  # Last 5 orders
            status_emoji = {"processing": "🔄", "completed": "✅", "partial": "⚡", "cancelled": "❌"}
            emoji = status_emoji.get(order.get('status', 'processing'), "🔄")
            text += f"""
{i}. <b>Order #{order.get('order_id', 'N/A')}</b>
{emoji} Status: {order.get('status', 'Processing').title()}
📱 Service: {order.get('service', 'N/A')}
💰 Amount: {format_currency(order.get('price', 0))}
📅 Date: {format_time(order.get('created_at', ''))}

"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
    await callback.answer()

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
अपनी जरूरत के अनुसार option चुनें:
"""
    
    await callback.message.edit_text(text, reply_markup=get_main_menu())
    await callback.answer()

# ========== MY ACCOUNT SUB-MENU HANDLERS ==========
@dp.callback_query(F.data == "refill_history")
@require_account
async def cb_refill_history(callback: CallbackQuery):
    """Show refill history"""
    if not callback.message or not callback.from_user:
        return
        
    text = """
🔄 <b>Refill History</b>

📋 <b>कोई refill history नहीं मिली</b>

💰 <b>पहले funds add करें और history यहां दिखेगी!</b>
"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "api_key")
@require_account
async def cb_api_key(callback: CallbackQuery):
    """Show API key"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    api_key = user_data.get('api_key', 'Not generated')
    
    text = f"""
🔑 <b>Your API Key</b>

📝 <b>API Key:</b>
<code>{api_key}</code>

💡 <b>Usage:</b>
• Developers के लिए API access
• Automatic order placement
• Bulk operations

🔒 <b>Security:</b> इस key को secret रखें!

📜 <b>API Documentation:</b>
Coming soon...
"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "edit_profile")
@require_account
async def cb_edit_profile(callback: CallbackQuery):
    """Show edit profile options"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    
    text = f"""
✏️ <b>Edit Profile</b>

👤 <b>Current Details:</b>
📝 <b>Name:</b> {user_data.get('full_name', 'Not set')}
📱 <b>Phone:</b> {user_data.get('phone_number', 'Not set')}
📧 <b>Email:</b> {user_data.get('email', 'Not set')}

💡 <b>Profile editing feature coming soon!</b>
🔧 <b>Contact admin for profile changes</b>

📞 <b>Support:</b> @{OWNER_USERNAME}
"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "user_stats")
@require_account
async def cb_user_stats(callback: CallbackQuery):
    """Show user statistics"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
    user_data = users_data.get(user_id, {})
    
    # Calculate stats
    user_orders = [order for order in orders_data.values() if order.get('user_id') == user_id]
    completed_orders = [order for order in user_orders if order.get('status') == 'completed']
    
    text = f"""
📈 <b>Your Statistics</b>

💰 <b>Financial:</b>
• Current Balance: {format_currency(user_data.get('balance', 0.0))}
• Total Spent: {format_currency(user_data.get('total_spent', 0.0))}
• Total Refilled: {format_currency(0.0)}

🛍 <b>Orders:</b>
• Total Orders: {len(user_orders)}
• Completed: {len(completed_orders)}
• Success Rate: {(len(completed_orders)/len(user_orders)*100) if user_orders else 0:.1f}%

📅 <b>Account:</b>
• Member Since: {format_time(user_data.get('join_date', ''))}
• Referrals: 0
• Tier: Bronze
"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ My Account", callback_data="my_account")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard)
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

@dp.callback_query(F.data == "create_ticket")
@require_account
async def cb_create_ticket(callback: CallbackQuery):
    """Start ticket creation process"""
    if not callback.message or not callback.from_user:
        return
        
    user_id = callback.from_user.id
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

🎫 <b>अगर कोई problem है तो new ticket create करें!</b>
➕ <b>Support team 24/7 available है</b>
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
        # Store email and complete account creation
        user_state[user_id]["data"]["email"] = message.text.strip()
        
        # Update user data
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
        # Handle custom amount for funds
        try:
            amount = int(message.text.strip())
            if amount < 100 or amount > 50000:
                await message.answer("⚠️ Amount ₹100 - ₹50,000 के बीच होनी चाहिए!")
                return
                
            transaction_id = f"TXN{int(time.time())}{random.randint(100, 999)}"
            user_state[user_id]["current_step"] = None
            
            text = f"""
💳 <b>Payment Details</b>

💰 <b>Amount:</b> ₹{amount:,}
🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>

📱 <b>UPI Payment:</b>
🔸 <b>UPI ID:</b> <code>indiasmm@paytm</code>
🔸 <b>Name:</b> India Social Panel

📝 <b>Payment Instructions:</b>
1. Above UPI ID पर ₹{amount:,} transfer करें
2. Transaction ID mention करें: <code>{transaction_id}</code>
3. Payment proof screenshot admin को भेजें
4. 5-10 minutes में balance add हो जाएगा

📞 <b>Support:</b> @{OWNER_USERNAME}
"""
            
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="add_funds")],
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
            ])
            
            await message.answer(text, reply_markup=back_keyboard)
            
        except ValueError:
            await message.answer("⚠️ कृपया valid amount number भेजें!")
            
    elif current_step == "waiting_ticket_subject":
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
        
        ticket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 My Tickets", callback_data="view_tickets")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_main")]
        ])
        
        await message.answer(text, reply_markup=ticket_keyboard)
        
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

# ========== ERROR HANDLERS ==========
@dp.message()
async def handle_unknown_message(message: Message):
    """Handle unknown messages"""
    pass  # Text messages are handled by handle_text_input

# ========== WEBHOOK SETUP ==========
async def on_startup(bot: Bot) -> None:
    """Bot startup configuration"""
    commands = [
        BotCommand(command="start", description="🏠 Main Menu"),
        BotCommand(command="menu", description="📋 Show Menu")
    ]
    await bot.set_my_commands(commands)
    await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    print(f"✅ India Social Panel Bot started! Webhook: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot) -> None:
    """Bot shutdown cleanup"""
    await bot.delete_webhook()
    print("✅ India Social Panel Bot stopped!")

def main():
    """Main application entry point"""
    # Register lifecycle events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Create aiohttp app
    app = web.Application()
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    
    # Setup and run
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
