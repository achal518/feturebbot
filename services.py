
# -*- coding: utf-8 -*-
"""
India Social Panel - Services Management
Professional Service Menu and Order Processing
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import F

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
def register_service_handlers(dp, require_account):
    """Register service handlers"""

    # Service platform handlers
    @dp.callback_query(F.data.startswith("service_"))
    @require_account
    async def cb_service_handler(callback: CallbackQuery):
        """Handle service selection - Show packages"""
        if not callback.message:
            return

        service = (callback.data or "").replace("service_", "")

        # Service names mapping
        service_names = {
            "instagram": "📷 Instagram",
            "facebook": "📘 Facebook",
            "telegram": "📞 Telegram",
            "youtube": "🎥 YouTube",
            "whatsapp": "💬 WhatsApp",
            "tiktok": "🎵 TikTok",
            "twitter": "🐦 Twitter",
            "linkedin": "💼 LinkedIn",
            "more": "🌟 More Services"
        }

        service_name = service_names.get(service, "🌟 Service")

        if service == "more":
            text = f"""
🌟 <b>More Services</b>

🚀 <b>Additional platforms coming soon!</b>

📱 <b>Upcoming Services:</b>
• Pinterest
• Snapchat 
• Reddit
• Discord
• Twitch
• And many more...

💡 <b>Request your favorite platform in support!</b>
"""
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")]
            ])

            await callback.message.edit_text(text, reply_markup=back_keyboard)
        else:
            text = f"""
{service_name} <b>Services</b>

🎯 <b>Select Your Package:</b>

💎 <b>Premium Quality Features:</b>
✅ Real & Active Users Only
✅ High Retention Rate  
✅ Fast Delivery (0-6 Hours)
✅ 24/7 Customer Support
✅ Secure & Safe Methods

🔒 <b>100% Money Back Guarantee</b>
⚡ <b>Instant Start Guarantee</b>

💡 <b>कृपया अपना package चुनें:</b>
"""

            await callback.message.edit_text(text, reply_markup=get_service_packages(service))

        await callback.answer()

    # Package selection handlers
    @dp.callback_query(F.data.startswith("package_"))
    @require_account
    async def cb_package_handler(callback: CallbackQuery):
        """Handle package selection - Show quality options"""
        if not callback.message:
            return

        # Parse package data
        package_data = (callback.data or "").replace("package_", "")
        parts = package_data.split("_")

        if len(parts) >= 2:
            platform = parts[0]
            service_id = parts[1]

            service_names = {
                "instagram": "📷 Instagram",
                "facebook": "📘 Facebook", 
                "telegram": "📞 Telegram",
                "youtube": "🎥 YouTube",
                "whatsapp": "💬 WhatsApp",
                "tiktok": "🎵 TikTok",
                "twitter": "🐦 Twitter",
                "linkedin": "💼 LinkedIn"
            }

            platform_name = service_names.get(platform, platform.title())

            text = f"""
{platform_name} <b>Package Selected</b>

🆔 <b>Service ID:</b> {service_id}

💎 <b>Quality Selection</b>

🎯 <b>अपनी जरूरत के अनुसार quality चुनें:</b>

💡 <b>Higher quality = Better results + More cost</b>
🔒 <b>All qualities are 100% safe & secure</b>
"""

            # Create quality selection menu
            quality_keyboard = get_quality_selection_menu(platform, service_id)

        else:
            text = """
⚠️ <b>Package Error</b>

🔄 <b>Please try selecting again</b>
"""
            quality_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")]
            ])

        await callback.message.edit_text(text, reply_markup=quality_keyboard)
        await callback.answer()

    # Quality selection handlers
    @dp.callback_query(F.data.startswith("quality_"))
    @require_account
    async def cb_quality_handler(callback: CallbackQuery):
        """Handle quality selection with dynamic configuration"""
        if not callback.message:
            return

        # Parse quality data
        quality_data = (callback.data or "").replace("quality_", "")
        parts = quality_data.split("_")

        # Debug information
        print(f"Quality handler debug: quality_data='{quality_data}', parts={parts}")

        if len(parts) >= 3:
            platform = parts[0]
            service_id = parts[1] 
            quality = parts[2]

            try:
                # Import and get dynamic package configuration
                from python_config import get_package_config
                config = get_package_config(platform, service_id, quality)

                # Get the automatically generated unique description
                description = config['description']

                # Show the unique description for this combination
                text = description

                # Add order action buttons
                text += f"""

🛒 <b>Order Details:</b>
💰 <b>Rate per unit:</b> ₹{config['rate']:.2f}
📊 <b>Min quantity:</b> {config['min_quantity']:,}
📊 <b>Max quantity:</b> {config['max_quantity']:,}

💡 <b>Ready to place order?</b>
📝 Click continue to enter link and quantity
"""

                order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➡️ Continue Order", callback_data=f"order_{platform}_{service_id}_{quality}")],
                    [InlineKeyboardButton(text="⬅️ Back to Qualities", callback_data=f"package_{platform}_{service_id}")]
                ])

            except Exception as e:
                # Debug error and show fallback
                print(f"Error in quality handler: {e}")
                text = f"""
⚠️ <b>Configuration Error</b>

Debug Info:
• Platform: {platform}
• Service ID: {service_id}
• Quality: {quality}
• Error: {str(e)}

🔄 <b>Please try again or contact support</b>

📞 <b>Support:</b> @achal_parvat
"""
                order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Back to Package", callback_data=f"package_{platform}_{service_id}")]
                ])
        else:
            text = f"""
⚠️ <b>Selection Error</b>

Invalid data received: {quality_data}
Expected format: platform_serviceid_quality

🔄 <b>Please try selecting again</b>
"""
            order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Services", callback_data="new_order")]
            ])

        await callback.message.edit_text(text, reply_markup=order_keyboard)
        await callback.answer()

# Function will be called from main.py to register handlers
# -*- coding: utf-8 -*-
"""
Services Module - India Social Panel
All service-related functionality and handlers
"""

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

def get_services_main_menu() -> InlineKeyboardMarkup:
    """Build services platform selection menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Instagram", callback_data="platform_instagram"),
            InlineKeyboardButton(text="🎥 YouTube", callback_data="platform_youtube")
        ],
        [
            InlineKeyboardButton(text="📘 Facebook", callback_data="platform_facebook"),
            InlineKeyboardButton(text="🐦 Twitter", callback_data="platform_twitter")
        ],
        [
            InlineKeyboardButton(text="💼 LinkedIn", callback_data="platform_linkedin"),
            InlineKeyboardButton(text="🎵 TikTok", callback_data="platform_tiktok")
        ],
        [
            InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_main")
        ]
    ])

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
            await callback.message.edit_text(text, reply_markup=get_instagram_services_menu())
            
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
            await callback.message.edit_text(text, reply_markup=get_youtube_services_menu())
            
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
            
            await callback.message.edit_text(text, reply_markup=back_keyboard)

        await callback.answer()

    @dp.callback_query(F.data.startswith("service_"))
    async def cb_service_select(callback: CallbackQuery):
        """Handle service selection and start order process"""
        if not callback.message or not callback.from_user:
            return

        service = (callback.data or "").replace("service_", "")
        user_id = callback.from_user.id

        # Initialize user state if not exists
        from main import user_state
        if user_id not in user_state:
            user_state[user_id] = {"current_step": None, "data": {}}

        # Store selected service and ask for link
        user_state[user_id]["data"]["service"] = service
        user_state[user_id]["current_step"] = "waiting_link"

        # Service information
        service_info = {
            "ig_followers": ("Instagram Followers", "₹0.50", "Real & Active followers"),
            "ig_likes": ("Instagram Likes", "₹0.30", "High-quality likes"),
            "ig_views": ("Instagram Views", "₹0.10", "Instant video views"),
            "ig_comments": ("Instagram Comments", "₹0.80", "Real user comments"),
            "ig_story_views": ("Instagram Story Views", "₹0.15", "Story engagement"),
            "ig_reel_views": ("Instagram Reel Views", "₹0.08", "Reel video views"),
            "yt_subscribers": ("YouTube Subscribers", "₹2.00", "Real subscribers"),
            "yt_likes": ("YouTube Likes", "₹0.40", "Video likes"),
            "yt_views": ("YouTube Views", "₹0.05", "High retention views"),
            "yt_comments": ("YouTube Comments", "₹1.00", "Custom comments"),
            "yt_dislikes": ("YouTube Dislikes", "₹0.50", "Video dislikes"),
            "yt_watchtime": ("YouTube Watch Time", "₹0.20", "Genuine watch time")
        }

        service_name, price, description = service_info.get(service, ("Service", "₹0.00", "Description"))

        text = f"""
🚀 <b>New Order - {service_name}</b>

📱 <b>Service Selected:</b> {service_name}
💰 <b>Price:</b> {price} per unit
📋 <b>Description:</b> {description}

🔗 <b>Step 3: Please send your link</b>

💬 <b>Send the link for this service:</b>

⚠️ <b>Examples:</b>
• Instagram: https://instagram.com/username
• YouTube: https://youtube.com/watch?v=VIDEO_ID
• Facebook: https://facebook.com/page_name

💡 <b>Paste the correct link और send करें</b>
"""

        await callback.message.edit_text(text)
        await callback.answer()

# Export functions for main.py
__all__ = ['register_service_handlers', 'get_services_main_menu']
