
# -*- coding: utf-8 -*-
"""
India Social Panel - Services Management
Professional Service Menu and Order Processing
"""

from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import F

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """Safely edit callback message with type checking"""
    if not callback.message or not hasattr(callback.message, 'edit_text'):
        return False
    try:
        if reply_markup:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")  # type: ignore
        else:
            await callback.message.edit_text(text, parse_mode="HTML")  # type: ignore
        return True
    except Exception as e:
        print(f"Error editing message: {e}")
        return False

# ========== SERVICE MENU BUILDERS ==========
def get_services_main_menu() -> InlineKeyboardMarkup:
    """Build main services selection menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Instagram", callback_data="service_instagram"),
            InlineKeyboardButton(text="📘 Facebook", callback_data="service_facebook")
        ],
        [
            InlineKeyboardButton(text="📞 Telegram", callback_data="service_telegram"),
            InlineKeyboardButton(text="🎥 YouTube", callback_data="service_youtube")
        ],
        [
            InlineKeyboardButton(text="💬 WhatsApp", callback_data="service_whatsapp"),
            InlineKeyboardButton(text="🎵 TikTok", callback_data="service_tiktok")
        ],
        [
            InlineKeyboardButton(text="🐦 Twitter", callback_data="service_twitter"),
            InlineKeyboardButton(text="💼 LinkedIn", callback_data="service_linkedin")
        ],
        [
            InlineKeyboardButton(text="🌟 More", callback_data="service_more")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

# ========== QUALITY SELECTION MENU ==========
def get_quality_selection_menu(platform: str, service_id: str) -> InlineKeyboardMarkup:
    """Get quality selection menu for specific package"""

    quality_options = [
        ("💎 Premium Quality", "premium", "🌟 Best results, Real users, Highest retention"),
        ("🔥 High Quality", "high", "⚡ Excellent results, Active users, High retention"),
        ("⚡ Medium Quality", "medium", "✅ Good results, Mixed users, Medium retention"),
        ("✅ Standard Quality", "standard", "💰 Fair results, Standard users, Basic retention"),
        ("💰 Basic Quality", "basic", "🔸 Budget option, Mixed quality, Low cost")
    ]

    keyboard = []

    # Add quality options
    for quality_name, quality_key, description in quality_options:
        button_text = f"{quality_name}\n{description}"
        callback_data = f"quality_{platform}_{service_id}_{quality_key}"

        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Packages", callback_data=f"service_{platform}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== SERVICE PACKAGES DATA ==========
def get_service_packages(platform: str) -> InlineKeyboardMarkup:
    """Get packages for specific platform"""

    packages = {
        "instagram": [
            ("👥 Instagram Followers", "ID:1001"),
            ("❤️ Instagram Likes", "ID:1002"),
            ("👁️ Instagram Views", "ID:1003"),
            ("📖 Instagram Story Views", "ID:1004"),
            ("💖 Instagram Story Likes", "ID:1005"),
            ("💬 Instagram Comments", "ID:1006"),
            ("📤 Instagram Shares", "ID:1007"),
            ("👥 Instagram Channel Members", "ID:1008"),
            ("💾 Instagram Saves", "ID:1009"),
            ("🔄 Instagram Auto Likes", "ID:1010"),
            ("⏰ Instagram Story Poll Votes", "ID:1011"),
            ("📊 Instagram Reel Views", "ID:1012")
        ],

        "facebook": [
            ("📄 Facebook Page Likes", "ID:2001"),
            ("❤️ Facebook Post Likes", "ID:2002"),
            ("👥 Facebook Group Members", "ID:2003"),
            ("🔴 Facebook Live Views", "ID:2004"),
            ("👁️ Facebook Video Views", "ID:2005"),
            ("💰 Facebook Monetization", "ID:2006"),
            ("💬 Facebook Comments", "ID:2007"),
            ("📤 Facebook Shares", "ID:2008"),
            ("👥 Facebook Followers", "ID:2009"),
            ("📊 Facebook Page Rating", "ID:2010"),
            ("🎯 Facebook Event Interested", "ID:2011"),
            ("⭐ Facebook Reviews", "ID:2012")
        ],

        "youtube": [
            ("👥 YouTube Subscribers", "ID:3001"),
            ("👁️ YouTube Views", "ID:3002"),
            ("❤️ YouTube Likes", "ID:3003"),
            ("💰 YouTube Monetization", "ID:3004"),
            ("💬 YouTube Comments", "ID:3005"),
            ("👎 YouTube Dislikes", "ID:3006"),
            ("📊 YouTube Watch Time", "ID:3007"),
            ("🔔 YouTube Channel Memberships", "ID:3008"),
            ("📺 YouTube Premiere Views", "ID:3009"),
            ("🎯 YouTube Shorts Views", "ID:3010"),
            ("⏰ YouTube Live Stream Views", "ID:3011"),
            ("📱 YouTube Community Post Likes", "ID:3012")
        ],

        "telegram": [
            ("👥 Telegram Channel Members", "ID:4001"),
            ("👁️ Telegram Post Views", "ID:4002"),
            ("👥 Telegram Group Members", "ID:4003"),
            ("📊 Telegram Channel Boost", "ID:4004"),
            ("💬 Telegram Comments", "ID:4005"),
            ("📤 Telegram Shares", "ID:4006"),
            ("⭐ Telegram Reactions", "ID:4007"),
            ("🔔 Telegram Poll Votes", "ID:4008"),
            ("📱 Telegram Story Views", "ID:4009"),
            ("🎯 Telegram Premium Members", "ID:4010")
        ],

        "whatsapp": [
            ("👥 WhatsApp Group Members", "ID:5001"),
            ("📊 WhatsApp Channel Subscribers", "ID:5002"),
            ("👁️ WhatsApp Status Views", "ID:5003"),
            ("📱 WhatsApp Business Reviews", "ID:5004"),
            ("💬 WhatsApp Group Activity", "ID:5005"),
            ("🔔 WhatsApp Broadcast List", "ID:5006"),
            ("⭐ WhatsApp Status Reactions", "ID:5007"),
            ("📈 WhatsApp Business Growth", "ID:5008")
        ],

        "tiktok": [
            ("👥 TikTok Followers", "ID:6001"),
            ("❤️ TikTok Likes", "ID:6002"),
            ("👁️ TikTok Views", "ID:6003"),
            ("💬 TikTok Comments", "ID:6004"),
            ("📤 TikTok Shares", "ID:6005"),
            ("💾 TikTok Saves", "ID:6006"),
            ("🔴 TikTok Live Views", "ID:6007"),
            ("🎵 TikTok Sound Usage", "ID:6008"),
            ("⏰ TikTok Story Views", "ID:6009"),
            ("🎯 TikTok Duet Views", "ID:6010")
        ],

        "twitter": [
            ("👥 Twitter Followers", "ID:7001"),
            ("❤️ Twitter Likes", "ID:7002"),
            ("🔄 Twitter Retweets", "ID:7003"),
            ("💬 Twitter Comments", "ID:7004"),
            ("👁️ Twitter Impressions", "ID:7005"),
            ("📊 Twitter Space Listeners", "ID:7006"),
            ("📱 Twitter Thread Views", "ID:7007"),
            ("🔔 Twitter Tweet Bookmarks", "ID:7008"),
            ("⭐ Twitter Poll Votes", "ID:7009"),
            ("🎯 Twitter Video Views", "ID:7010")
        ],

        "linkedin": [
            ("👥 LinkedIn Followers", "ID:8001"),
            ("❤️ LinkedIn Post Likes", "ID:8002"),
            ("💬 LinkedIn Comments", "ID:8003"),
            ("📤 LinkedIn Shares", "ID:8004"),
            ("👁️ LinkedIn Profile Views", "ID:8005"),
            ("📊 LinkedIn Company Page Follows", "ID:8006"),
            ("🎯 LinkedIn Article Views", "ID:8007"),
            ("💼 LinkedIn Skill Endorsements", "ID:8008"),
            ("⭐ LinkedIn Recommendations", "ID:8009"),
            ("📈 LinkedIn Connection Requests", "ID:8010")
        ]
    }

    keyboard = []
    platform_packages = packages.get(platform, [])

    # Add packages in rows of 1
    for package_name, service_id in platform_packages:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{package_name}\n{service_id}", 
                callback_data=f"package_{platform}_{service_id.replace('ID:', '')}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== SERVICE HANDLERS ==========

def get_instagram_services_menu() -> InlineKeyboardMarkup:
    """Build Instagram services menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Followers", callback_data="service_ig_followers"),
            InlineKeyboardButton(text="❤️ Likes", callback_data="service_ig_likes")
        ],
        [
            InlineKeyboardButton(text="👁️ Views", callback_data="service_ig_views"),
            InlineKeyboardButton(text="💬 Comments", callback_data="service_ig_comments")
        ],
        [
            InlineKeyboardButton(text="📖 Story Views", callback_data="service_ig_story_views"),
            InlineKeyboardButton(text="🎬 Reel Views", callback_data="service_ig_reel_views")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="new_order")
        ]
    ])

def get_youtube_services_menu() -> InlineKeyboardMarkup:
    """Build YouTube services menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Subscribers", callback_data="service_yt_subscribers"),
            InlineKeyboardButton(text="❤️ Likes", callback_data="service_yt_likes")
        ],
        [
            InlineKeyboardButton(text="👁️ Views", callback_data="service_yt_views"),
            InlineKeyboardButton(text="💬 Comments", callback_data="service_yt_comments")
        ],
        [
            InlineKeyboardButton(text="👎 Dislikes", callback_data="service_yt_dislikes"),
            InlineKeyboardButton(text="⏰ Watch Time", callback_data="service_yt_watchtime")
        ],
        [
            InlineKeyboardButton(text="⬅️ Back", callback_data="new_order")
        ]
    ])

def register_service_handlers(dp, require_account):
    """Register all service-related handlers"""

    print("🔄 Registering service handlers...")

    @dp.callback_query(F.data.startswith("platform_"))
    async def cb_platform_select(callback: CallbackQuery):
        """Handle platform selection"""
        if not callback.message:
            return

        platform = (callback.data or "").replace("platform_", "")

        if platform == "instagram":
            text = """
📷 <b>Instagram Services</b>

🌟 <b>Premium Instagram Growth Services</b>

✅ <b>High Quality Features:</b>
• Real & Active Users Only
• Instant Start (0-30 minutes)
• High Retention Rate (90%+)
• Safe & Secure Methods
• 24/7 Customer Support

💰 <b>Competitive Pricing:</b>
• Followers: ₹0.50 per follower
• Likes: ₹0.30 per like
• Views: ₹0.10 per view
• Comments: ₹0.80 per comment

💡 <b>अपनी जरूरत की service चुनें:</b>
"""
            await safe_edit_message(callback, text, get_instagram_services_menu())

        elif platform == "youtube":
            text = """
🎥 <b>YouTube Services</b>

🚀 <b>Professional YouTube Growth Services</b>

✅ <b>Premium Features:</b>
• Real Subscribers & Views
• Instant Delivery
• High Retention Guarantee
• AdSense Safe Methods
• Monetization Friendly

💰 <b>Best Pricing:</b>
• Subscribers: ₹2.00 per subscriber
• Views: ₹0.05 per view
• Likes: ₹0.40 per like
• Comments: ₹1.00 per comment

🎯 <b>YouTube के लिए service select करें:</b>
"""
            await safe_edit_message(callback, text, get_youtube_services_menu())

        else:
            text = f"""
🚀 <b>{platform.title()} Services</b>

🔧 <b>Services Coming Soon!</b>

💡 <b>{platform.title()} services are under development</b>

⚡ <b>Available Soon:</b>
• High-quality {platform} services
• Competitive pricing
• Instant delivery
• 24/7 support

📞 <b>For early access, contact:</b> @achal_parvat
"""

            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")]
            ])

            await safe_edit_message(callback, text, back_keyboard)

        await callback.answer()

# Export functions for main.py
__all__ = ['register_service_handlers', 'get_services_main_menu']
