
# -*- coding: utf-8 -*-
import asyncio
import os
import random
import string
import time
import json
import hashlib
import base64
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Poll, InputPollOption
)
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
OWNER_NAME = os.getenv("OWNER_NAME", "Achal")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "your_username_here")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "my_super_secret_string_12345"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 5000))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
START_TIME = time.time()

# ========== ADVANCED DATA STORAGE ==========
user_state = {}
user_data = {}
bot_stats = {"messages": 0, "commands": 0, "users": set(), "games_played": 0}

quotes_db = [
    "🌟 Success is not final, failure is not fatal. It's the courage to continue that counts.",
    "💪 Believe you can and you're halfway there. - Theodore Roosevelt",
    "🎯 The only way to do great work is to love what you do. - Steve Jobs",
    "🚀 Innovation distinguishes between a leader and a follower. - Steve Jobs",
    "✨ Your limitation—it's only your imagination.",
    "🔥 Great things never come from comfort zones.",
    "⭐ Dream it. Wish it. Do it.",
    "🌈 Success doesn't just find you. You have to go out and get it.",
    "💎 The harder you work for something, the greater you'll feel when you achieve it.",
    "🎪 Dream bigger. Do bigger.",
    "🌅 Every morning is a new opportunity to be better than yesterday.",
    "🎨 Creativity is intelligence having fun. - Albert Einstein",
    "🏆 Champions are made when nobody's watching.",
    "🔮 The future belongs to those who believe in the beauty of their dreams.",
    "💫 Be yourself; everyone else is already taken. - Oscar Wilde"
]

jokes_db = [
    "😂 Why don't scientists trust atoms? Because they make up everything!",
    "🤣 I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "😆 Why don't skeletons fight each other? They don't have the guts.",
    "🤪 What do you call a fake noodle? An impasta!",
    "😄 Why did the scarecrow win an award? He was outstanding in his field!",
    "😁 What's orange and sounds like a parrot? A carrot!",
    "🤭 Why don't eggs tell jokes? They'd crack each other up!",
    "😋 What do you call a sleeping bull? A bulldozer!",
    "🙃 Why did the math book look so sad? Because it had too many problems!",
    "😜 What do you call a bear with no teeth? A gummy bear!",
    "🤖 Why did the robot go on a diet? It had a byte problem!",
    "🎭 What do you call a fish wearing a bowtie? Sofishticated!",
    "🚗 Why don't cars ever get tired? They always have spare tires!",
    "🍕 Why did the pizza go to therapy? It had too many toppings!",
    "🐸 What do you call a frog's favorite drink? Croak-a-Cola!"
]

facts_db = [
    "🧠 Your brain uses about 20% of your body's total energy daily.",
    "🐙 Octopuses have three hearts and blue blood instead of red.",
    "🍯 Honey never spoils. Archaeologists found 3000-year-old edible honey!",
    "🦋 Butterflies taste with their feet to identify plants.",
    "🌙 A day on Venus is longer than its year (243 Earth days vs 225).",
    "🐘 Elephants can recognize themselves in mirrors, showing self-awareness.",
    "🌊 The ocean contains 99% of Earth's living space by volume.",
    "⚡ Lightning strikes Earth about 100 times every second worldwide.",
    "🎵 Listening to music can boost your immune system function.",
    "🧬 Humans share 60% of their DNA with bananas surprisingly.",
    "🦘 Kangaroos can't walk backwards due to their powerful tail.",
    "🐧 Penguins have knees hidden inside their bodies.",
    "🌍 Earth is the only planet not named after a Roman god.",
    "🦈 Sharks have been around longer than trees on Earth.",
    "🎨 The human eye can distinguish about 10 million colors."
]

riddles_db = [
    {"q": "🤔 What has keys but no locks, space but no room, and you can enter but not go inside?", "a": "keyboard"},
    {"q": "🧩 I'm tall when I'm young, short when I'm old, and every Halloween you can guess what I hold. What am I?", "a": "candle"},
    {"q": "🔍 What can travel around the world while staying in a corner?", "a": "stamp"},
    {"q": "💭 What gets wetter the more it dries?", "a": "towel"},
    {"q": "🎭 What has hands but cannot clap?", "a": "clock"},
    {"q": "🌟 I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "a": "map"},
    {"q": "🔮 What comes once in a minute, twice in a moment, but never in a thousand years?", "a": "letter m"},
    {"q": "🎪 What has a head, a tail, is brown, and has no legs?", "a": "penny"},
    {"q": "🌙 What can you catch but not throw?", "a": "cold"},
    {"q": "⭐ What runs but never walks, has a mouth but never talks?", "a": "river"}
]

trivia_questions = [
    {"q": "🌍 What is the largest planet in our solar system?", "a": "jupiter", "options": ["Mars", "Jupiter", "Saturn", "Earth"]},
    {"q": "🎨 Who painted the Mona Lisa?", "a": "leonardo da vinci", "options": ["Picasso", "Van Gogh", "Leonardo da Vinci", "Michelangelo"]},
    {"q": "🏔️ What is the highest mountain in the world?", "a": "mount everest", "options": ["K2", "Mount Everest", "Kangchenjunga", "Lhotse"]},
    {"q": "🌊 Which ocean is the largest?", "a": "pacific", "options": ["Atlantic", "Indian", "Pacific", "Arctic"]},
    {"q": "🔬 What is the chemical symbol for gold?", "a": "au", "options": ["Go", "Gd", "Au", "Ag"]}
]

fortune_messages = [
    "🔮 Today brings new opportunities! Embrace the unexpected.",
    "✨ Your kindness will return to you tenfold this week.",
    "🌟 A creative solution will solve an old problem.",
    "🎯 Focus on your goals - success is within reach.",
    "💫 Someone special thinks of you more than you know.",
    "🌈 After every storm comes a beautiful rainbow.",
    "🎪 Adventure awaits those who seek it.",
    "💎 Your unique talents will shine brightly soon.",
    "🌅 New beginnings are approaching - be ready!",
    "🦋 Transformation brings beautiful changes."
]

life_tips = [
    "💡 Start your day with gratitude - list 3 things you're thankful for.",
    "🏃‍♂️ Take a 10-minute walk daily to boost creativity and mood.",
    "📚 Read for 15 minutes before bed instead of scrolling social media.",
    "💧 Drink a glass of water first thing in the morning to hydrate your body.",
    "🧘‍♀️ Practice deep breathing: 4 seconds in, hold 4, out 4, hold 4.",
    "🤝 Compliment someone genuinely every day - it brightens both your days.",
    "📝 Write down your thoughts to clear mental clutter.",
    "🌱 Learn one new thing daily, no matter how small.",
    "😴 Maintain a consistent sleep schedule for better health.",
    "🎨 Express creativity through any medium - drawing, cooking, writing."
]

motivational_quotes = [
    "🚀 The way to get started is to quit talking and begin doing. - Walt Disney",
    "💪 It is during our darkest moments that we must focus to see the light. - Aristotle",
    "🎯 Life is what happens to you while you're busy making other plans. - John Lennon",
    "⭐ The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
    "🌟 It is never too late to be what you might have been. - George Eliot",
    "🔥 Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
    "✨ In the middle of difficulty lies opportunity. - Albert Einstein",
    "🎪 Believe you can and you're halfway there. - Theodore Roosevelt",
    "💫 Do what you can with all you have, wherever you are. - Theodore Roosevelt",
    "🌈 Turn your wounds into wisdom. - Oprah Winfrey"
]

# ========== NEW ADVANCED DATABASES ==========
# Horoscope database for mystical features
horoscope_db = {
    "aries": "🔥 आज आपकी ऊर्जा का दिन है! नए काम शुरू करने का सही समय।",
    "taurus": "🌱 धैर्य रखें, आपकी मेहनत का फल जल्दी मिलेगा।", 
    "gemini": "💬 आज संवाद और नेटवर्किंग पर फोकस करें।",
    "cancer": "🌙 परिवार के साथ समय बिताएं, खुशी मिलेगी।",
    "leo": "☀️ आज आपका आत्मविश्वास चरम पर है, नेतृत्व करें।",
    "virgo": "📋 विस्तार से काम करें, सफलता मिलेगी।",
    "libra": "⚖️ संतुलन बनाए रखें, सभी के साथ मधुर रिश्ते।",
    "scorpio": "🦂 गहरे रिसर्च का दिन है, सच्चाई सामने आएगी।",
    "sagittarius": "🏹 नई यात्रा या शिक्षा की शुरुआत करें।",
    "capricorn": "⛰️ मेहनत जारी रखें, बड़ी सफलता पास है।",
    "aquarius": "💫 अपनी अनूठी सोच से दुनिया बदलें।",
    "pisces": "🌊 अपनी भावनाओं को समझें, कलात्मक काम करें।"
}

# Virtual pets storage
virtual_pets = {}

# Daily challenges database
daily_challenges = [
    "📖 आज कम से कम 10 मिनट पढ़ें",
    "🚶 10 मिनट टहलने जाएं", 
    "💧 8 गिलास पानी पिएं",
    "📞 किसी पुराने दोस्त से बात करें",
    "🧘 5 मिनट ध्यान लगाएं",
    "📝 अपने विचार डायरी में लिखें",
    "🎵 अपना पसंदीदा गाना सुनें",
    "🙂 किसी को खुश करने का काम करें",
    "🍎 एक स्वस्थ नाश्ता करें",
    "💪 10 push-ups या योग करें"
]

# Story starters for creative writing
story_starters = [
    "एक रहस्यमय चिट्ठी मिली जिसमें लिखा था...",
    "अचानक आसमान से एक अजीब आवाज़ आई...", 
    "पुस्तकालय में एक किताब खुद से खुल गई...",
    "रात के अंधेरे में कुछ चमक रहा था...",
    "एक बूढ़े आदमी ने मुझसे कहा...",
    "जादू की दुकान में एक अजीब चीज़ दिखी...",
    "समुद्र किनारे एक बोतल मिली जिसमें...",
    "पहाड़ों से एक आवाज़ गूंज रही थी...",
    "एक सुनहरी चाबी मिली जो...",
    "अचानक मेरे कमरे में एक पोर्टल खुला..."
]

# Brain teasers database
brain_teasers_db = [
    {"q": "🧠 अगर 5 मिनट में 5 मशीनें 5 चीज़ें बनाती हैं, तो 100 मशीनें 100 चीज़ें कितने मिनट में बनाएंगी?", "a": "5"},
    {"q": "🤔 एक आदमी का वज़न 60 किलो है। उसके दोनों हाथ काट दिए जाएं तो वो कितना हल्का होगा?", "a": "6 किलो"},
    {"q": "💭 क्या चीज़ है जो टूटने से ठीक होती है?", "a": "हड्डी"},
    {"q": "🎯 अगर एक बिल्ली एक मिनट में एक चूहा पकड़ती है, तो 100 बिल्ली 100 चूहे कितने मिनट में पकड़ेंगी?", "a": "1"}
]

# Affirmations in Hindi
daily_affirmations = [
    "✨ मैं आज बेहतरीन हूं और कल भी बेहतरीन रहूंगा।",
    "🌟 मेरे पास अनंत संभावनाएं हैं।",
    "💪 मैं मजबूत, सक्षम और अद्भुत हूं।",
    "🌈 मैं खुशी और शांति का स्रोत हूं।",
    "🔥 मेरा आत्मविश्वास दिन-ब-दिन बढ़ता जा रहा है।",
    "🌱 मैं हर चुनौती से बेहतर बनकर निकलता हूं।",
    "💝 मैं प्यार पाने और देने के योग्य हूं।",
    "🎯 मेरे सपने साकार होने वाले हैं।",
    "🏆 सफलता मेरा हक है और मैं इसे पाऊंगा।",
    "🌅 हर नया दिन मेरे लिए नई खुशियां लेकर आता है।"
]

# Color personality database
color_personalities = {
    "red": "🔴 लाल रंग पसंद करने वाले ऊर्जावान, जुनूनी और नेतृत्व करने वाले होते हैं। आप में साहस और दृढ़ता है।",
    "blue": "🔵 नीला रंग शांति, विश्वास और बुद्धिमत्ता का प्रतीक है। आप भरोसेमंद और वफादार हैं।",
    "green": "🟢 हरा रंग प्रकृति, संतुलन और विकास दर्शाता है। आप दयालु और धैर्यवान हैं।",
    "yellow": "🟡 पीला रंग खुशी, रचनात्मकता और आशावाद दिखाता है। आप उत्साही और मिलनसार हैं।",
    "purple": "🟣 बैंगनी रंग रचनात्मकता और आध्यात्मिकता का प्रतीक है। आप कलात्मक और गहरे विचारक हैं।",
    "orange": "🟠 नारंगी रंग उत्साह और साहस दर्शाता है। आप हंसमुख और साहसी हैं।",
    "pink": "🌸 गुलाबी रंग प्रेम और करुणा का प्रतीक है। आप संवेदनशील और देखभाल करने वाले हैं।",
    "black": "⚫ काला रंग रहस्य और शक्ति दर्शाता है। आप मजबूत और स्वतंत्र हैं।"
}

# Achievement texts
achievement_texts = {
    "command_master": "⚡ Command Master - 50+ commands उपयोग किया",
    "level_champion": "🏆 Level Champion - Level 5 पहुंचे",
    "social_butterfly": "🦋 Social Butterfly - 10+ friends बनाए", 
    "creative_genius": "🎨 Creative Genius - 20+ stories लिखे",
    "wellness_guru": "🧘 Wellness Guru - 100+ मिनट meditation",
    "pet_lover": "🐾 Pet Lover - Pet को level 10 तक पहुंचाया",
    "trivia_master": "🧠 Trivia Master - 50+ सही जवाब"
}

# Tic Tac Toe board
ttt_board = [" "] * 9

# ========== UTILITY FUNCTIONS ==========
def ensure_user(uid: int):
    if uid not in user_state:
        user_state[uid] = {
            "echo": False, "mode": None, "design_style": None, "guess_target": None,
            "calc_mode": False, "password_length": 12, "reminder_text": None,
            "reminder_time": None, "quiz_score": 0, "quiz_question": None,
            "poll_question": None, "todo_list": [], "notes": [], "bookmarks": [],
            "profile": {"name": None, "age": None, "city": None, "bio": None, "favorite_color": None, "hobby": None},
            "settings": {"theme": "default", "notifications": True, "language": "en", "time_format": "12h"},
            "achievements": [], "level": 1, "experience": 0, "streak": 0,
            "games_played": 0, "game_wins": 0, "trivia_correct": 0, "last_active": datetime.now().isoformat(),
            "preferences": {"difficulty": "medium", "categories": ["all"]},
            "social": {"friends": [], "groups": []}, "ai_personality": "friendly",
            "mood": "happy", "meditation_time": 0, "story_count": 0, "challenge_progress": {},
            "current_challenge": None, "brain_answer": None, "math_answer": None, "ttt_turn": "X",
            "memory_sequence": [], "memory_shown": False
        }
        # Initialize pet for new user
        initialize_pet(uid)
    if uid not in user_data:
        user_data[uid] = {"join_date": datetime.now().isoformat(), "total_commands": 0, "favorite_features": []}

def calculate_level(experience: int) -> int:
    return min(100, max(1, experience // 100 + 1))

def add_experience(uid: int, amount: int = 10):
    ensure_user(uid)
    user_state[uid]["experience"] += amount
    new_level = calculate_level(user_state[uid]["experience"])
    if new_level > user_state[uid]["level"]:
        user_state[uid]["level"] = new_level
        return True  # Level up!
    return False

def format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if days > 0:
        return f"{days}d {hours:02d}h {mins:02d}m {secs:02d}s"
    return f"{hours:02d}h {mins:02d}m {secs:02d}s"

def now_ist_str() -> str:
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime("%d %B %Y, %H:%M:%S IST")

def to_fancy_text(text: str, style: str = "fancy") -> str:
    styles = {
        "fancy": "𝒻𝒶𝓃𝒸𝓎",
        "bold": "𝗯𝗼𝗹𝗱",
        "italic": "𝘪𝘵𝘢𝘭𝘪𝘤",
        "bubble": "ⓑⓤⓑⓑⓛⓔ",
        "square": "🅂🅀🅄🄰🅁🄴"
    }
    # Simplified transformation
    if style == "fancy":
        return text.replace("a", "𝒶").replace("e", "𝑒").replace("i", "𝒾").replace("o", "𝑜").replace("u", "𝓊")
    return text.upper() if style == "upper" else text

def generate_password(length: int = 12, complexity: str = "medium") -> str:
    if complexity == "simple":
        chars = string.ascii_letters + string.digits
    elif complexity == "complex":
        chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    else:  # medium
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Ensure at least one from each category
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
    ]
    
    if complexity != "simple":
        password.append(random.choice("!@#$%^&*"))
    
    # Fill the rest
    for _ in range(len(password), length):
        password.append(random.choice(chars))
    
    random.shuffle(password)
    return ''.join(password)

def calculate_expression(expr: str) -> str:
    try:
        # Safe evaluation with basic math operations
        expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")
        expr = expr.replace("√", "math.sqrt")
        
        # Only allow safe operations
        allowed_names = {"__builtins__": {}, "math": math}
        result = eval(expr, allowed_names)
        
        if isinstance(result, float):
            return f"{result:.6g}"
        return str(result)
    except:
        return "Invalid expression"

def encode_decode_text(text: str, method: str, operation: str = "encode") -> str:
    if method == "base64":
        if operation == "encode":
            return base64.b64encode(text.encode()).decode()
        else:
            try:
                return base64.b64decode(text.encode()).decode()
            except:
                return "Invalid base64"
    
    elif method == "reverse":
        return text[::-1]
    
    elif method == "caesar":
        result = ""
        shift = 3 if operation == "encode" else -3
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                result += chr((ord(char) - base + shift) % 26 + base)
            else:
                result += char
        return result
    
    elif method == "binary":
        if operation == "encode":
            return ' '.join(format(ord(char), '08b') for char in text)
        else:
            try:
                return ''.join(chr(int(byte, 2)) for byte in text.split())
            except:
                return "Invalid binary"
    
    elif method == "hex":
        if operation == "encode":
            return text.encode().hex()
        else:
            try:
                return bytes.fromhex(text).decode()
            except:
                return "Invalid hex"
    
    return text

def get_random_color() -> str:
    colors = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "🔷", "🔸", "🔹"]
    return random.choice(colors)

def create_progress_bar(percentage: int, length: int = 10) -> str:
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage}%"

# ========== ADVANCED KEYBOARD LAYOUTS ==========
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Games & Entertainment", callback_data="games_menu"),
         InlineKeyboardButton(text="🛠️ Advanced Tools", callback_data="tools_menu")],
        [InlineKeyboardButton(text="🎨 Text & Design Studio", callback_data="text_menu"),
         InlineKeyboardButton(text="🧠 Knowledge Center", callback_data="knowledge_menu")],
        [InlineKeyboardButton(text="💼 Productivity Suite", callback_data="productivity_menu"),
         InlineKeyboardButton(text="🔐 Security Hub", callback_data="security_menu")],
        [InlineKeyboardButton(text="👤 Profile & Social", callback_data="profile_menu"),
         InlineKeyboardButton(text="📊 Analytics & Stats", callback_data="stats_menu")],
        [InlineKeyboardButton(text="🎪 Fun & Random", callback_data="fun_menu"),
         InlineKeyboardButton(text="🤖 AI Assistant", callback_data="ai_menu")],
        [InlineKeyboardButton(text="⚙️ Settings & Config", callback_data="settings_menu"),
         InlineKeyboardButton(text="🏆 Achievements", callback_data="achievements_menu")],
        [InlineKeyboardButton(text="💡 About & Help", callback_data="about"),
         InlineKeyboardButton(text="❌ Close Menu", callback_data="close")]
    ])

def games_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Classic Dice", callback_data="game_dice"),
         InlineKeyboardButton(text="🔢 Number Puzzle", callback_data="game_guess"),
         InlineKeyboardButton(text="🧩 Brain Riddles", callback_data="game_riddle")],
        [InlineKeyboardButton(text="🎯 Trivia Challenge", callback_data="game_trivia"),
         InlineKeyboardButton(text="🎰 Lucky Slots", callback_data="game_slot"),
         InlineKeyboardButton(text="⚔️ Battle RPS", callback_data="game_rps")],
        [InlineKeyboardButton(text="🃏 Card Draw", callback_data="game_cards"),
         InlineKeyboardButton(text="🎪 Spin Wheel", callback_data="game_wheel"),
         InlineKeyboardButton(text="🔤 Word Maker", callback_data="game_words")],
        [InlineKeyboardButton(text="🏁 Racing Game", callback_data="game_race"),
         InlineKeyboardButton(text="🎳 Strike Game", callback_data="game_bowling"),
         InlineKeyboardButton(text="🎊 Party Mode", callback_data="game_party")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def tools_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Smart Calculator", callback_data="tool_calc"),
         InlineKeyboardButton(text="🔐 Password Forge", callback_data="tool_password"),
         InlineKeyboardButton(text="📏 Unit Master", callback_data="tool_convert")],
        [InlineKeyboardButton(text="🌍 World Clock", callback_data="tool_timezone"),
         InlineKeyboardButton(text="📊 Poll Builder", callback_data="tool_poll"),
         InlineKeyboardButton(text="🎲 Random Magic", callback_data="tool_random")],
        [InlineKeyboardButton(text="📱 QR Creator", callback_data="tool_qr"),
         InlineKeyboardButton(text="🔍 Text Analyzer", callback_data="tool_analyze"),
         InlineKeyboardButton(text="🌈 Color Picker", callback_data="tool_color")],
        [InlineKeyboardButton(text="📐 Math Solver", callback_data="tool_math"),
         InlineKeyboardButton(text="💱 Currency Info", callback_data="tool_currency"),
         InlineKeyboardButton(text="⏱️ Timer Pro", callback_data="tool_timer")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def text_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🅱️ Bold Style", callback_data="design_bold"),
         InlineKeyboardButton(text="𝐼 Italic Flair", callback_data="design_italic"),
         InlineKeyboardButton(text="</> Code Mode", callback_data="design_mono")],
        [InlineKeyboardButton(text="✨ Fancy Text", callback_data="design_fancy"),
         InlineKeyboardButton(text="🔄 Flip & Reverse", callback_data="design_reverse"),
         InlineKeyboardButton(text="🔤 CAPS LOCK", callback_data="design_upper")],
        [InlineKeyboardButton(text="📊 Text Stats", callback_data="text_count"),
         InlineKeyboardButton(text="🔀 Word Scrambler", callback_data="text_scramble"),
         InlineKeyboardButton(text="🎭 Case Changer", callback_data="text_case")],
        [InlineKeyboardButton(text="🔁 Echo Mirror", callback_data="toggle_echo"),
         InlineKeyboardButton(text="🎨 ASCII Art", callback_data="text_art"),
         InlineKeyboardButton(text="🌈 Rainbow Text", callback_data="text_rainbow")],
        [InlineKeyboardButton(text="📝 Text Replace", callback_data="text_replace"),
         InlineKeyboardButton(text="✂️ Text Splitter", callback_data="text_split"),
         InlineKeyboardButton(text="🔗 Text Joiner", callback_data="text_join")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def knowledge_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💭 Daily Wisdom", callback_data="knowledge_quote"),
         InlineKeyboardButton(text="🧠 Amazing Facts", callback_data="knowledge_fact"),
         InlineKeyboardButton(text="😂 Humor Zone", callback_data="knowledge_joke")],
        [InlineKeyboardButton(text="📚 Word Power", callback_data="knowledge_word"),
         InlineKeyboardButton(text="🔮 Fortune Teller", callback_data="knowledge_fortune"),
         InlineKeyboardButton(text="💡 Life Hacks", callback_data="knowledge_tips")],
        [InlineKeyboardButton(text="🌟 Motivation Boost", callback_data="knowledge_motivation"),
         InlineKeyboardButton(text="🧬 Science World", callback_data="knowledge_science"),
         InlineKeyboardButton(text="🎓 Learning Hub", callback_data="knowledge_learn")],
        [InlineKeyboardButton(text="📖 Story Time", callback_data="knowledge_story"),
         InlineKeyboardButton(text="🌍 World Facts", callback_data="knowledge_world"),
         InlineKeyboardButton(text="🎪 Did You Know?", callback_data="knowledge_trivia")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def productivity_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Smart Tasks", callback_data="prod_todo"),
         InlineKeyboardButton(text="📓 Quick Notes", callback_data="prod_notes"),
         InlineKeyboardButton(text="⏰ Reminders", callback_data="prod_reminder")],
        [InlineKeyboardButton(text="🔖 Bookmarks", callback_data="prod_bookmarks"),
         InlineKeyboardButton(text="⏱️ Pomodoro", callback_data="prod_timer"),
         InlineKeyboardButton(text="📅 Schedule", callback_data="prod_calendar")],
        [InlineKeyboardButton(text="💰 Expense Track", callback_data="prod_expense"),
         InlineKeyboardButton(text="🎯 Goal Setting", callback_data="prod_goals"),
         InlineKeyboardButton(text="📊 Progress Track", callback_data="prod_progress")],
        [InlineKeyboardButton(text="✅ Habit Builder", callback_data="prod_habits"),
         InlineKeyboardButton(text="📈 Analytics", callback_data="prod_analytics"),
         InlineKeyboardButton(text="🎨 Mind Map", callback_data="prod_mindmap")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def security_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Password Lab", callback_data="sec_password"),
         InlineKeyboardButton(text="🔒 Text Encoder", callback_data="sec_encode"),
         InlineKeyboardButton(text="🔓 Text Decoder", callback_data="sec_decode")],
        [InlineKeyboardButton(text="🛡️ Security Tips", callback_data="sec_tips"),
         InlineKeyboardButton(text="🔑 PIN Maker", callback_data="sec_pin"),
         InlineKeyboardButton(text="🎭 Name Generator", callback_data="sec_username")],
        [InlineKeyboardButton(text="🔍 Hash Creator", callback_data="sec_hash"),
         InlineKeyboardButton(text="📊 Password Check", callback_data="sec_strength"),
         InlineKeyboardButton(text="🔐 2FA Helper", callback_data="sec_2fa")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def fun_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Celebration", callback_data="fun_celebrate"),
         InlineKeyboardButton(text="🎈 Party Planner", callback_data="fun_party"),
         InlineKeyboardButton(text="🎪 Magic 8-Ball", callback_data="fun_8ball")],
        [InlineKeyboardButton(text="🌟 Compliments", callback_data="fun_compliment"),
         InlineKeyboardButton(text="🎭 Mood Boost", callback_data="fun_mood"),
         InlineKeyboardButton(text="🎨 Art Creator", callback_data="fun_art")],
        [InlineKeyboardButton(text="🎵 Music Mood", callback_data="fun_music"),
         InlineKeyboardButton(text="🌈 Color Therapy", callback_data="fun_color_therapy"),
         InlineKeyboardButton(text="🎪 Random Fun", callback_data="fun_random")],
        [InlineKeyboardButton(text="⬅️ Back to Main", callback_data="back_to_menu")]
    ])

def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]])

# ========== WELCOME & START HANDLERS ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    ensure_user(message.from_user.id)
    bot_stats["users"].add(message.from_user.id)
    
    uid = message.from_user.id
    level_up = add_experience(uid, 20)
    
    welcome_text = f"""
🚀 <b>Welcome to Ultimate Advanced Bot!</b> 🚀
👋 <i>Hello {message.from_user.first_name}!</i>

✨ <b>Your All-in-One Digital Companion</b> ✨

🎯 <b>🔥 100+ AMAZING FEATURES 🔥</b>

🎮 <b>Entertainment Hub:</b>
• 15+ Interactive Games • Trivia Challenges
• Lucky Slots • Card Games • Racing & More!

🛠️ <b>Power Tools:</b>
• Smart Calculator • Password Generator
• QR Creator • Unit Converter • World Clock

🎨 <b>Creative Studio:</b>
• Text Designer • ASCII Art • Rainbow Text
• Case Changer • Word Scrambler • Echo Mode

🧠 <b>Knowledge Base:</b>
• Daily Quotes • Fun Facts • Jokes
• Life Tips • Fortune Telling • Science Facts

💼 <b>Productivity Suite:</b>
• Smart Tasks • Quick Notes • Reminders
• Habit Tracker • Goal Setting • Analytics

🔐 <b>Security Center:</b>
• Advanced Encryption • Password Strength
• Hash Generator • 2FA Helper • Security Tips

📊 <b>Your Progress:</b>
• Level: {user_state[uid]['level']} 
• Experience: {user_state[uid]['experience']} XP
{'🎉 LEVEL UP! +20 XP' if level_up else ''}

🌟 <b>Special Features:</b>
• AI Personality • Achievement System
• Social Functions • Custom Themes
• Progress Tracking • And Much More!

💡 <i>Tip: Each action earns XP and unlocks achievements!</i>
"""
    
    await message.answer(welcome_text, reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
📚 <b>Ultimate Bot - Complete Guide</b>

🎯 <b>Quick Commands:</b>
/start - Launch main interface
/help - Show this comprehensive guide
/menu - Quick access to all features
/profile - View your profile & stats
/achievements - See your progress
/cancel - Stop current operation

🎮 <b>Games & Entertainment:</b>
• 🎲 Dice Games • 🔢 Number Puzzles
• 🧩 Brain Riddles • 🎯 Trivia Challenges
• 🎰 Slot Machines • ⚔️ Rock Paper Scissors
• 🃏 Card Games • 🎪 Spin Wheel
• 🏁 Racing Games • 🎳 Bowling

🛠️ <b>Professional Tools:</b>
• 🧮 Advanced Calculator with functions
• 🔐 Password Generator (3 complexity levels)
• 📏 Unit Converter (length, weight, temp)
• 🌍 World Clock & Timezone
• 📱 QR Code Generator
• 📊 Poll & Survey Creator

🎨 <b>Text & Design Features:</b>
• Bold, Italic, Monospace formatting
• Fancy Unicode text transformation
• Text reversal and case conversion
• Word count and text analysis
• ASCII art generation
• Rainbow colored text
• Text encryption/decryption

🧠 <b>Knowledge & Learning:</b>
• Daily inspirational quotes
• Amazing fun facts database
• Joke collection for entertainment
• Life tips and productivity hacks
• Fortune telling and predictions
• Science facts and trivia
• Motivational content

💼 <b>Productivity Suite:</b>
• Smart to-do list management
• Quick note-taking system
• Reminder and alert system
• Bookmark organization
• Habit tracking system
• Goal setting and progress
• Time management tools

🔐 <b>Security & Privacy:</b>
• Military-grade password generation
• Text encoding (Base64, Caesar, Binary)
• Hash generation (MD5, SHA256)
• Password strength analysis
• Two-factor authentication helper
• Security best practices guide

📊 <b>Analytics & Stats:</b>
• Personal usage statistics
• Bot performance metrics
• Achievement tracking
• Experience point system
• Level progression
• Usage patterns analysis

🏆 <b>Achievement System:</b>
Unlock achievements by:
• Using different features
• Reaching milestones
• Completing challenges
• Maintaining streaks
• Helping others

🎪 <b>Fun & Random Features:</b>
• Magic 8-Ball predictions
• Compliment generator
• Mood booster messages
• Color therapy
• Party celebration mode
• Random fun activities

🤖 <b>AI Assistant:</b>
• Personalized responses
• Learning from interactions
• Context awareness
• Smart suggestions
• Adaptive behavior

<i>🌟 Made with ❤️ for ultimate user experience!</i>
"""
    await message.answer(help_text, reply_markup=main_menu())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 <b>Main Control Center</b>\nChoose your adventure:", reply_markup=main_menu())

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = None
    await message.answer("✅ <b>Operation Cancelled!</b>\n\n🏠 Returning to main menu...", reply_markup=main_menu())

@dp.message(Command("achievements"))
async def cmd_achievements(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    
    achievements = user_state[uid]["achievements"]
    level = user_state[uid]["level"]
    experience = user_state[uid]["experience"]
    
    # Calculate achievements
    possible_achievements = [
        "🎮 Game Master - Play 10 games",
        "📝 Text Wizard - Use 5 text features", 
        "🛠️ Tool Expert - Use 8 different tools",
        "🧠 Knowledge Seeker - Access knowledge 15 times",
        "💼 Productivity Pro - Complete 20 tasks",
        "🔐 Security Guardian - Use security features 10 times",
        "🌟 Social Butterfly - Interact 50 times",
        "🏆 Level Champion - Reach level 10",
        "⚡ Speed User - Use bot for 7 consecutive days",
        "🎯 Perfectionist - Complete all tutorials"
    ]
    
    unlocked = len(achievements)
    total = len(possible_achievements)
    progress = create_progress_bar(unlocked * 100 // total)
    
    achievements_text = f"""
🏆 <b>Your Achievements</b>

📊 <b>Progress Overview:</b>
• Level: {level} 🌟
• Experience: {experience} XP ⚡
• Unlocked: {unlocked}/{total} 🎯
{progress}

🎖️ <b>Available Achievements:</b>
"""
    
    for i, achievement in enumerate(possible_achievements):
        status = "✅" if i < unlocked else "🔒"
        achievements_text += f"{status} {achievement}\n"
    
    achievements_text += f"\n💡 <i>Keep using the bot to unlock more achievements!</i>"
    
    await message.answer(achievements_text, reply_markup=main_menu())

# ========== CALLBACK HANDLERS ==========
@dp.callback_query(F.data == "back_to_menu")
async def cb_back_menu(cb: CallbackQuery):
    uid = cb.from_user.id
    level = user_state[uid]["level"] if uid in user_state else 1
    
    await cb.message.edit_text(f"🏠 <b>Main Control Center</b>\n\n👤 Level {level} User\n🎯 Choose your next adventure:", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "close")
async def cb_close(cb: CallbackQuery):
    goodbye_msgs = [
        "👋 Thanks for using Ultimate Bot!",
        "✨ See you soon, champion!",
        "🚀 Keep exploring and growing!",
        "🌟 You're awesome! Come back anytime!",
        "💫 Until next time, stay amazing!"
    ]
    
    try:
        await cb.message.delete()
    except:
        await cb.message.edit_text(f"{random.choice(goodbye_msgs)}\n\n💡 Use /start to return anytime!")
    await cb.answer("Bot closed! Use /start to reopen.")

# ========== GAMES MENU HANDLERS ==========
@dp.callback_query(F.data == "games_menu")
async def cb_games_menu(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    games_played = user_state[uid]["games_played"]
    
    await cb.message.edit_text(f"🎮 <b>Ultimate Gaming Hub</b>\n\n🏆 Games Played: {games_played}\n🎯 Choose your game:", reply_markup=games_menu())
    await cb.answer()

@dp.callback_query(F.data == "game_dice")
async def cb_dice(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    await cb.answer()
    dice_msg = await bot.send_dice(chat_id=cb.message.chat.id, emoji="🎲")
    value = dice_msg.dice.value
    
    user_state[uid]["games_played"] += 1
    add_experience(uid, 15)
    
    result_messages = {
        1: "😅 Oops! Better luck next time!",
        2: "😐 Not bad! Keep trying!",
        3: "😊 Good roll! Getting better!",
        4: "😄 Great roll! You're on fire!",
        5: "🤩 Excellent! Almost perfect!",
        6: "🎉 JACKPOT! AMAZING! 🎊"
    }
    
    rewards = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25, 6: 50}
    reward = rewards[value]
    
    result_text = f"""
🎲 <b>Dice Game Result</b>

🎯 <b>You rolled: {value}</b>
{result_messages[value]}

🏆 <b>Rewards:</b>
• +{reward} XP Points
• +1 Game Played

🎮 <b>Stats:</b>
• Total Games: {user_state[uid]['games_played']}
• Level: {user_state[uid]['level']}
"""
    
    dice_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Roll Again", callback_data="game_dice"),
         InlineKeyboardButton(text="🎮 Other Games", callback_data="games_menu")],
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back_to_menu")]
    ])
    
    await bot.send_message(cb.message.chat.id, result_text, reply_markup=dice_kb)

@dp.callback_query(F.data == "game_trivia")
async def cb_trivia(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    question_data = random.choice(trivia_questions)
    user_state[uid]["mode"] = "trivia"
    user_state[uid]["trivia_answer"] = question_data["a"].lower()
    user_state[uid]["trivia_options"] = question_data["options"]
    
    # Create option buttons
    option_buttons = []
    for i, option in enumerate(question_data["options"]):
        option_buttons.append([InlineKeyboardButton(text=f"{chr(65+i)}. {option}", callback_data=f"trivia_{i}")])
    
    option_buttons.append([InlineKeyboardButton(text="⬅️ Back to Games", callback_data="games_menu")])
    trivia_kb = InlineKeyboardMarkup(inline_keyboard=option_buttons)
    
    trivia_text = f"""
🎯 <b>Trivia Challenge!</b>

❓ <b>Question:</b>
{question_data['q']}

🤔 <b>Choose your answer:</b>
"""
    
    await cb.message.edit_text(trivia_text, reply_markup=trivia_kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("trivia_"))
async def cb_trivia_answer(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    selected_option = int(cb.data.split("_")[1])
    correct_answer = user_state[uid]["trivia_answer"]
    options = user_state[uid]["trivia_options"]
    
    selected_text = options[selected_option].lower()
    is_correct = correct_answer in selected_text.lower()
    
    user_state[uid]["mode"] = None
    user_state[uid]["games_played"] += 1
    
    if is_correct:
        user_state[uid]["trivia_correct"] += 1
        add_experience(uid, 30)
        result_text = f"""
✅ <b>CORRECT!</b> 🎉

🎯 <b>Answer:</b> {options[selected_option]}
🏆 <b>Rewards:</b> +30 XP, +1 Correct Answer

📊 <b>Your Stats:</b>
• Correct Answers: {user_state[uid]['trivia_correct']}
• Games Played: {user_state[uid]['games_played']}
• Level: {user_state[uid]['level']}

🌟 <i>Great knowledge! Keep it up!</i>
"""
    else:
        add_experience(uid, 10)
        result_text = f"""
❌ <b>Not Quite Right!</b>

🎯 <b>Correct Answer:</b> {correct_answer.title()}
💪 <b>Consolation:</b> +10 XP for trying

📊 <b>Your Stats:</b>
• Correct Answers: {user_state[uid]['trivia_correct']}
• Games Played: {user_state[uid]['games_played']}
• Level: {user_state[uid]['level']}

💡 <i>Don't give up! Knowledge comes with practice!</i>
"""
    
    result_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Another Question", callback_data="game_trivia"),
         InlineKeyboardButton(text="🎮 Other Games", callback_data="games_menu")],
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await cb.message.edit_text(result_text, reply_markup=result_kb)
    await cb.answer()

@dp.callback_query(F.data == "game_slot")
async def cb_slot(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    # Enhanced slot machine with more symbols
    symbols = ["🍎", "🍊", "🍋", "🍇", "🍓", "🥝", "🍒", "💎", "🔔", "⭐", "7️⃣", "💰"]
    slot1, slot2, slot3 = [random.choice(symbols) for _ in range(3)]
    
    user_state[uid]["games_played"] += 1
    
    # Calculate winnings
    if slot1 == slot2 == slot3:
        if slot1 == "💰":
            result = "💰💰💰 MEGA JACKPOT! 💰💰💰"
            points = 1000
            xp = 100
        elif slot1 == "💎":
            result = "💎💎💎 DIAMOND JACKPOT! 💎💎💎"
            points = 500
            xp = 75
        elif slot1 == "7️⃣":
            result = "7️⃣7️⃣7️⃣ LUCKY SEVENS! 7️⃣7️⃣7️⃣"
            points = 250
            xp = 50
        else:
            result = "🎉 TRIPLE MATCH! Amazing! 🎉"
            points = 100
            xp = 30
    elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
        result = "🎊 DOUBLE MATCH! Good job! 🎊"
        points = 25
        xp = 15
    else:
        result = "😅 No match! Try again! 😅"
        points = 5
        xp = 5
    
    add_experience(uid, xp)
    
    slot_text = f"""
🎰 <b>ULTIMATE SLOT MACHINE</b> 🎰

🎲 <b>Result:</b>
┌─────────────┐
│  {slot1} │ {slot2} │ {slot3}  │
└─────────────┘

{result}

🏆 <b>Winnings:</b>
• Points: {points} 💰
• Experience: +{xp} XP ⚡

📊 <b>Your Progress:</b>
• Games Played: {user_state[uid]['games_played']}
• Current Level: {user_state[uid]['level']}
• Total XP: {user_state[uid]['experience']}
"""
    
    slot_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Spin Again!", callback_data="game_slot"),
         InlineKeyboardButton(text="🎮 Other Games", callback_data="games_menu")],
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await cb.message.edit_text(slot_text, reply_markup=slot_kb)
    await cb.answer()

# ========== TOOLS MENU HANDLERS ==========
@dp.callback_query(F.data == "tools_menu")
async def cb_tools_menu(cb: CallbackQuery):
    await cb.message.edit_text("🛠️ <b>Advanced Tools Hub</b>\n\n⚡ Professional-grade utilities at your fingertips!\n\n🎯 Select a tool:", reply_markup=tools_menu())
    await cb.answer()

@dp.callback_query(F.data == "tool_password")
async def cb_password_advanced(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    # Generate multiple password types
    simple_pass = generate_password(8, "simple")
    medium_pass = generate_password(12, "medium") 
    complex_pass = generate_password(16, "complex")
    memorable_pass = f"{random.choice(['Sun', 'Moon', 'Star', 'Fire', 'Ocean'])}{random.randint(100,999)}!"
    
    add_experience(uid, 10)
    
    password_text = f"""
🔐 <b>Advanced Password Generator</b>

🔹 <b>Simple (8 chars - Letters & Numbers):</b>
<code>{simple_pass}</code>

🔸 <b>Medium (12 chars - With Symbols):</b>
<code>{medium_pass}</code>

🔺 <b>Complex (16 chars - Maximum Security):</b>
<code>{complex_pass}</code>

🎯 <b>Memorable (Easy to remember):</b>
<code>{memorable_pass}</code>

🛡️ <b>Security Tips:</b>
• Use different passwords for each account
• Change passwords every 3-6 months
• Enable 2FA when possible
• Never share passwords via text/email
• Use a password manager

💡 <b>Strength Indicators:</b>
• Simple: ⭐⭐ (Basic security)
• Medium: ⭐⭐⭐ (Good security)
• Complex: ⭐⭐⭐⭐⭐ (Maximum security)

🎉 <i>+10 XP earned for using security tools!</i>
"""
    
    password_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Generate New", callback_data="tool_password"),
         InlineKeyboardButton(text="📊 Check Strength", callback_data="sec_strength")],
        [InlineKeyboardButton(text="🛠️ More Tools", callback_data="tools_menu"),
         InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await cb.message.edit_text(password_text, reply_markup=password_kb)
    await cb.answer()

# ========== MISSING UTILITY FUNCTIONS ==========
def add_experience(uid: int, xp: int):
    """Add experience points and handle level ups"""
    ensure_user(uid)
    user_state[uid]["experience"] = user_state[uid].get("experience", 0) + xp
    
    # Level up calculation
    current_level = user_state[uid].get("level", 1)
    required_xp = current_level * 100
    
    if user_state[uid]["experience"] >= required_xp:
        user_state[uid]["level"] = current_level + 1
        user_state[uid]["experience"] = 0
        return True  # Level up occurred
    return False

def generate_password(length: int, complexity: str = "medium") -> str:
    """Enhanced password generator with different complexity levels"""
    if complexity == "simple":
        chars = string.ascii_letters + string.digits
    elif complexity == "complex":
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_+=[]{}|;:,.<>?"
    else:  # medium
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
    
    return ''.join(random.choices(chars, k=length))

# ========== NEW HELPER FUNCTIONS ==========
def calculate_pet_status(pet_data: dict) -> dict:
    """Calculate pet status based on time and actions"""
    current_time = time.time()
    
    # Decrease stats over time
    last_update = pet_data.get('last_update', current_time)
    time_diff = (current_time - last_update) / 3600  # hours
    
    pet_data['hunger'] = max(0, pet_data.get('hunger', 50) - time_diff * 5)
    pet_data['energy'] = max(0, pet_data.get('energy', 100) - time_diff * 3)
    pet_data['happiness'] = max(0, pet_data.get('happiness', 75) - time_diff * 2)
    pet_data['last_update'] = current_time
    
    return pet_data

def generate_daily_affirmation() -> str:
    """Generate daily affirmation"""
    return random.choice(daily_affirmations)

def generate_story_prompt(starter: str) -> str:
    """Generate creative story prompts"""
    elements = ["सुनहरी", "रहस्यमय", "जादुई", "चमकता", "डरावना", "खूबसूरत"]
    characters = ["राजकुमार", "परी", "जादूगर", "डकैत", "साधु", "व्यापारी"]
    places = ["महल", "जंगल", "गुफा", "नदी", "पहाड़", "गांव"]
    
    element = random.choice(elements)
    character = random.choice(characters)
    place = random.choice(places)
    
    return f"{starter} एक {element} {character} {place} में मिला..."

def get_achievement_text(achievement_id: str) -> str:
    """Get achievement text"""
    return achievement_texts.get(achievement_id, f"🏆 {achievement_id} Achievement")

def get_color_personality(color: str) -> str:
    """Get color personality description"""
    return color_personalities.get(color, "🎨 आप एक अनूठे व्यक्तित्व के मालिक हैं!")

def generate_brain_teaser() -> dict:
    """Generate brain teaser"""
    return random.choice(brain_teasers_db)

def generate_meditation_guide(duration: int) -> str:
    """Generate meditation guide based on duration"""
    guides = {
        5: "🧘 <b>5 मिनट मेडिटेशन</b>\n\n🌸 आराम से बैठें और आंखें बंद करें\n🌊 गहरी सांस लें... छोड़ें...\n💭 अपने मन को शांत करें\n\n⏰ 5 मिनट बाद धीरे से आंखें खोलें",
        15: "🧘 <b>15 मिनट मेडिटेशन</b>\n\n🪷 सुखासन में बैठें\n🌬️ सांस पर ध्यान दें\n🎵 मन में शांत संगीत सुनें\n✨ सकारात्मक विचार लाएं\n\n⏰ 15 मिनट का गहरा अभ्यास",
        30: "🧘 <b>30 मिनट गहरा मेडिटेशन</b>\n\n🕯️ शांत वातावरण बनाएं\n💫 पूर्ण एकाग्रता\n🌊 मन की सभी लहरों को शांत करें\n🙏 आभार व्यक्त करें\n\n⏰ 30 मिनट का संपूर्ण अनुभव"
    }
    return guides.get(duration, guides[5])

def get_mood_emoji(mood: str) -> str:
    """Get emoji for mood"""
    mood_emojis = {
        "happy": "😊", "sad": "😢", "excited": "🤩", 
        "calm": "😌", "angry": "😠", "sleepy": "😴"
    }
    return mood_emojis.get(mood, "😊")

def to_fullwidth(text: str) -> str:
    """Convert text to fullwidth characters"""
    result = ""
    for char in text:
        if 'a' <= char <= 'z':
            result += chr(ord(char) - ord('a') + ord('ａ'))
        elif 'A' <= char <= 'Z':
            result += chr(ord(char) - ord('A') + ord('Ａ'))
        elif '0' <= char <= '9':
            result += chr(ord(char) - ord('0') + ord('０'))
        else:
            result += char
    return result

# ========== MISSING MENU FUNCTIONS ==========
def mystical_menu():
    """Create mystical features menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 राशिफल", callback_data="mystical_horoscope"),
         InlineKeyboardButton(text="🥠 भाग्य कुकी", callback_data="mystical_fortune")],
        [InlineKeyboardButton(text="🎱 Magic 8 Ball", callback_data="mystical_8ball"),
         InlineKeyboardButton(text="🎨 रंग थेरेपी", callback_data="mystical_color")],
        [InlineKeyboardButton(text="🔢 लकी नंबर", callback_data="mystical_lucky"),
         InlineKeyboardButton(text="🌙 सपनों की व्याख्या", callback_data="mystical_dreams")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

def pet_menu():
    """Create virtual pet menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ पेट देखें", callback_data="pet_view"),
         InlineKeyboardButton(text="🍖 खाना दें", callback_data="pet_feed")],
        [InlineKeyboardButton(text="🎾 खेलें", callback_data="pet_play"),
         InlineKeyboardButton(text="😴 सुलाएं", callback_data="pet_sleep")],
        [InlineKeyboardButton(text="🎓 ट्रेनिंग", callback_data="pet_train"),
         InlineKeyboardButton(text="🛁 नहलाएं", callback_data="pet_clean")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

def wellness_menu():
    """Create wellness menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ सकारात्मक विचार", callback_data="wellness_affirmations"),
         InlineKeyboardButton(text="🧘 मेडिटेशन", callback_data="wellness_meditation")],
        [InlineKeyboardButton(text="😊 मूड ट्रैकर", callback_data="wellness_mood"),
         InlineKeyboardButton(text="💪 फिटनेस टिप्स", callback_data="wellness_fitness")],
        [InlineKeyboardButton(text="😴 नींद गाइड", callback_data="wellness_sleep"),
         InlineKeyboardButton(text="🌬️ सांस की तकनीक", callback_data="wellness_breathing")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

def creative_menu():
    """Create creative zone menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 कहानी जेनरेटर", callback_data="creative_story"),
         InlineKeyboardButton(text="✍️ राइटिंग प्रॉम्प्ट", callback_data="creative_prompt")],
        [InlineKeyboardButton(text="🎵 गाने के बोल", callback_data="creative_lyrics"),
         InlineKeyboardButton(text="💌 प्रेम पत्र", callback_data="creative_love_letter")],
        [InlineKeyboardButton(text="🎭 चरित्र निर्माण", callback_data="creative_character"),
         InlineKeyboardButton(text="🎨 कला प्रेरणा", callback_data="creative_art")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

def achievements_menu():
    """Create achievements menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 मेरे बैजेस", callback_data="ach_view"),
         InlineKeyboardButton(text="📊 प्रगति देखें", callback_data="ach_progress")],
        [InlineKeyboardButton(text="🎯 दैनिक लक्ष्य", callback_data="ach_daily_goals"),
         InlineKeyboardButton(text="📈 आंकड़े", callback_data="ach_stats")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

def challenges_menu():
    """Create challenges menu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ आज का चैलेंज", callback_data="challenge_daily"),
         InlineKeyboardButton(text="🧠 ब्रेन ट्रेनिंग", callback_data="challenge_brain")],
        [InlineKeyboardButton(text="📊 प्रगति देखें", callback_data="challenge_progress"),
         InlineKeyboardButton(text="🏅 साप्ताहिक क्वेस्ट", callback_data="challenge_weekly")],
        [InlineKeyboardButton(text="⬅️ मुख्य मेन्यू", callback_data="back_to_menu")]
    ])

# ========== PET INITIALIZATION ==========
def initialize_pet(uid: int):
    """Initialize virtual pet for user"""
    if uid not in virtual_pets:
        pet_types = ["🐱", "🐶", "🐰", "🦊", "🐼", "🐸", "🐧", "🦄"]
        pet_names = ["Buddy", "Luna", "Max", "Bella", "Charlie", "Lucy", "Rocky", "Daisy"]
        
        virtual_pets[uid] = {
            "name": random.choice(pet_names),
            "type": random.choice(pet_types),
            "level": 1,
            "exp": 0,
            "happiness": 75,
            "hunger": 50,
            "energy": 100,
            "last_fed": time.time(),
            "last_played": time.time(),
            "last_update": time.time()
        }
    return virtual_pets[uid]

# ========== NEW MYSTICAL FEATURES ==========
@dp.callback_query(F.data == "mystical_menu")
async def cb_mystical_menu(cb: CallbackQuery):
    await cb.message.edit_text("🔮 <b>रहस्यमय संसार में आपका स्वागत है!</b>\nअपना भाग्य जानिए:", reply_markup=mystical_menu())
    await cb.answer()

@dp.callback_query(F.data == "mystical_horoscope")
async def cb_horoscope(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = "horoscope"
    
    horoscope_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♈ मेष", callback_data="horo_aries"),
         InlineKeyboardButton(text="♉ वृषभ", callback_data="horo_taurus"),
         InlineKeyboardButton(text="♊ मिथुन", callback_data="horo_gemini")],
        [InlineKeyboardButton(text="♋ कर्क", callback_data="horo_cancer"),
         InlineKeyboardButton(text="♌ सिंह", callback_data="horo_leo"),
         InlineKeyboardButton(text="♍ कन्या", callback_data="horo_virgo")],
        [InlineKeyboardButton(text="♎ तुला", callback_data="horo_libra"),
         InlineKeyboardButton(text="♏ वृश्चिक", callback_data="horo_scorpio"),
         InlineKeyboardButton(text="♐ धनु", callback_data="horo_sagittarius")],
        [InlineKeyboardButton(text="♑ मकर", callback_data="horo_capricorn"),
         InlineKeyboardButton(text="♒ कुंभ", callback_data="horo_aquarius"),
         InlineKeyboardButton(text="♓ मीन", callback_data="horo_pisces")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="mystical_menu")]
    ])
    
    await cb.message.edit_text("🔮 <b>राशिफल</b>\n\nअपनी राशि चुनें:", reply_markup=horoscope_kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("horo_"))
async def cb_horo_result(cb: CallbackQuery):
    sign = cb.data.split("_")[1]
    prediction = horoscope_db.get(sign, "🌟 आज आपका दिन शानदार होगा!")
    add_experience(cb.from_user.id, 5)
    
    text = f"🔮 <b>आज का राशिफल</b>\n\n{prediction}\n\n📫 <i>कल फिर आएं नया राशिफल जानने के लिए!</i>"
    await cb.message.edit_text(text, reply_markup=mystical_menu())
    await cb.answer()

@dp.callback_query(F.data == "mystical_fortune")
async def cb_fortune(cb: CallbackQuery):
    fortunes = [
        "🥠 आज कुछ खुशखबरी मिलेगी!",
        "🌟 एक नया अवसर आपका इंतज़ार कर रहा है!",
        "💫 आपकी मेहनत जल्दी रंग लाएगी!",
        "🎯 जो सोचा है वो पूरा होगा!",
        "🌈 खुशियों का बादल आप पर बरसेगा!",
        "⚡ आपकी एनर्जी आज बहुत पॉज़िटिव है!",
        "🎪 कोई सरप्राइज़ मिलने वाला है!",
        "🔥 आपका आत्मविश्वास चरम पर है!"
    ]
    
    fortune = random.choice(fortunes)
    add_experience(cb.from_user.id, 5)
    text = f"🥠 <b>आज का फॉर्च्यून कुकी</b>\n\n{fortune}\n\n✨ <i>हर दिन नया भाग्य जानने आएं!</i>"
    await cb.message.edit_text(text, reply_markup=mystical_menu())
    await cb.answer()

# ========== VIRTUAL PET SYSTEM ==========
@dp.callback_query(F.data == "pet_menu")
async def cb_pet_menu(cb: CallbackQuery):
    await cb.message.edit_text("🐾 <b>वर्चुअल पेट सिस्टम</b>\n\nअपने डिजिटल दोस्त का ख्याल रखें:", reply_markup=pet_menu())
    await cb.answer()

@dp.callback_query(F.data == "pet_view")
async def cb_pet_view(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    if uid not in virtual_pets:
        initialize_pet(uid)
    pet = calculate_pet_status(virtual_pets[uid])
    
    happiness_bar = "❤️" * (pet["happiness"] // 10) + "🤍" * (10 - pet["happiness"] // 10)
    hunger_bar = "🍖" * (pet["hunger"] // 10) + "⚪" * (10 - pet["hunger"] // 10)
    energy_bar = "⚡" * (pet["energy"] // 10) + "⚪" * (10 - pet["energy"] // 10)
    
    text = f"""🐾 <b>आपका पेट: {pet['name']}</b> {pet['type']}

📊 <b>स्टेटस:</b>
😊 खुशी: {happiness_bar} ({pet['happiness']}%)
🍖 भूख: {hunger_bar} ({pet['hunger']}%)
⚡ एनर्जी: {energy_bar} ({pet['energy']}%)
🏆 लेवल: {pet['level']} (EXP: {pet['exp']}/100)

💭 <i>{pet['name']} आपको देखकर खुश है!</i>"""
    
    await cb.message.edit_text(text, reply_markup=pet_menu())
    await cb.answer()

@dp.callback_query(F.data == "pet_feed")
async def cb_pet_feed(cb: CallbackQuery):
    uid = cb.from_user.id
    pet = virtual_pets[uid]
    
    if pet["hunger"] >= 90:
        text = f"🐾 <b>{pet['name']}</b> का पेट भरा है!\n\n😋 <i>बाद में खिलाएं!</i>"
    else:
        pet["hunger"] = min(100, pet["hunger"] + 25)
        pet["happiness"] = min(100, pet["happiness"] + 10)
        pet["exp"] = min(100, pet["exp"] + 5)
        pet["last_fed"] = time.time()
        add_experience(uid, 10)
        
        if pet["exp"] >= 100:
            pet["level"] += 1
            pet["exp"] = 0
            text = f"🍖 <b>{pet['name']}</b> को खाना दिया!\n\n🎉 लेवल अप! अब लेवल {pet['level']} है!"
        else:
            text = f"🍖 <b>{pet['name']}</b> को खाना दिया!\n\n😋 वो बहुत खुश है! (+5 EXP)"
    
    await cb.message.edit_text(text, reply_markup=pet_menu())
    await cb.answer()

# ========== WELLNESS & MEDITATION ==========
@dp.callback_query(F.data == "wellness_menu")
async def cb_wellness_menu(cb: CallbackQuery):
    await cb.message.edit_text("🧘 <b>वेलनेस & मेडिटेशन</b>\n\nअपनी मानसिक शांति पाएं:", reply_markup=wellness_menu())
    await cb.answer()

@dp.callback_query(F.data == "wellness_affirmations")
async def cb_affirmations(cb: CallbackQuery):
    affirmation = generate_daily_affirmation()
    add_experience(cb.from_user.id, 8)
    text = f"✨ <b>आज का सकारात्मक विचार</b>\n\n{affirmation}\n\n🌅 <i>इसे अपने दिल में बसा लें और खुश रहें!</i>"
    await cb.message.edit_text(text, reply_markup=wellness_menu())
    await cb.answer()

# ========== CREATIVE ZONE ==========
@dp.callback_query(F.data == "creative_menu")
async def cb_creative_menu(cb: CallbackQuery):
    await cb.message.edit_text("🎨 <b>क्रिएटिव ज़ोन</b>\n\nअपनी कलात्मकता का प्रदर्शन करें:", reply_markup=creative_menu())
    await cb.answer()

@dp.callback_query(F.data == "creative_story")
async def cb_story_generator(cb: CallbackQuery):
    uid = cb.from_user.id
    starter = random.choice(story_starters)
    story = generate_story_prompt(starter)
    add_experience(uid, 15)
    user_state[uid]["story_count"] += 1
    
    text = f"📖 <b>आपकी कहानी #{user_state[uid]['story_count']}</b>\n\n{story}\n\n✍️ <i>इसे आगे बढ़ाएं और अपनी कल्पना का उपयोग करें!</i>"
    
    story_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 नई कहानी", callback_data="creative_story"),
         InlineKeyboardButton(text="✍️ राइटिंग प्रॉम्प्ट", callback_data="creative_prompt")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="creative_menu")]
    ])
    
    await cb.message.edit_text(text, reply_markup=story_kb)
    await cb.answer()

# ========== ACHIEVEMENTS SYSTEM ==========
@dp.callback_query(F.data == "achievements_menu")
async def cb_achievements_menu(cb: CallbackQuery):
    await cb.message.edit_text("🏆 <b>अचीवमेंट्स & बैजेस</b>\n\nआपकी सफलताएं:", reply_markup=achievements_menu())
    await cb.answer()

@dp.callback_query(F.data == "ach_view")
async def cb_view_achievements(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    user_achievements = user_state[uid].get("achievements", [])
    total_commands = user_data[uid].get("total_commands", 0)
    level = user_state[uid].get("level", 1)
    
    # Check for new achievements
    new_achievements = []
    if total_commands >= 50 and "command_master" not in user_achievements:
        user_achievements.append("command_master")
        new_achievements.append("⚡ Command Master")
    
    if level >= 5 and "level_champion" not in user_achievements:
        user_achievements.append("level_champion")
        new_achievements.append("🏆 Level Champion")
    
    # Display achievements
    if user_achievements:
        text = "🏆 <b>आपकी अचीवमेंट्स:</b>\n\n"
        for ach in user_achievements:
            text += f"✅ {get_achievement_text(ach)}\n\n"
    else:
        text = "📝 <b>अभी तक कोई अचीवमेंट नहीं</b>\n\n🎯 <i>बॉट का इस्तेमाल करके बैजेस जीतें!</i>"
    
    if new_achievements:
        text += f"\n🎉 <b>नए बैजेस अनलॉक:</b>\n" + "\n".join(new_achievements)
    
    user_state[uid]["achievements"] = user_achievements
    await cb.message.edit_text(text, reply_markup=achievements_menu())
    await cb.answer()

# ========== MORE ADVANCED GAMES ==========
@dp.callback_query(F.data == "game_ttt")
async def cb_tic_tac_toe(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    # Reset board
    global ttt_board
    ttt_board = [" "] * 9
    user_state[uid]["ttt_turn"] = "X"
    
    ttt_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ttt_board[0] or "⬜", callback_data="ttt_0"),
         InlineKeyboardButton(text=ttt_board[1] or "⬜", callback_data="ttt_1"),
         InlineKeyboardButton(text=ttt_board[2] or "⬜", callback_data="ttt_2")],
        [InlineKeyboardButton(text=ttt_board[3] or "⬜", callback_data="ttt_3"),
         InlineKeyboardButton(text=ttt_board[4] or "⬜", callback_data="ttt_4"),
         InlineKeyboardButton(text=ttt_board[5] or "⬜", callback_data="ttt_5")],
        [InlineKeyboardButton(text=ttt_board[6] or "⬜", callback_data="ttt_6"),
         InlineKeyboardButton(text=ttt_board[7] or "⬜", callback_data="ttt_7"),
         InlineKeyboardButton(text=ttt_board[8] or "⬜", callback_data="ttt_8")],
        [InlineKeyboardButton(text="🔄 नया गेम", callback_data="game_ttt"),
         InlineKeyboardButton(text="⬅️ वापस", callback_data="games_menu")]
    ])
    
    await cb.message.edit_text("⭕ <b>Tic Tac Toe</b>\n\n🎯 आप X हैं, बॉट O है!\nअपनी चाल चुनें:", reply_markup=ttt_kb)
    await cb.answer()

@dp.callback_query(F.data == "mystical_8ball")
async def cb_8ball(cb: CallbackQuery):
    answers = [
        "🎱 हां, बिल्कुल!",
        "🎱 नहीं, ऐसा नहीं लगता!",
        "🎱 शायद, कोशिश करके देखें!",
        "🎱 जरूर, समय आने पर!",
        "🎱 इसमें संदेह है!",
        "🎱 अभी नहीं, बाद में!",
        "🎱 भविष्य धुंधला है!",
        "🎱 बहुत अच्छे संकेत हैं!"
    ]
    
    answer = random.choice(answers)
    add_experience(cb.from_user.id, 5)
    text = f"🔮 <b>Magic 8 Ball</b>\n\nआपका सवाल: ?\n\n{answer}\n\n🎯 <i>कोई और सवाल पूछना चाहते हैं?</i>"
    await cb.message.edit_text(text, reply_markup=mystical_menu())
    await cb.answer()

@dp.callback_query(F.data == "mystical_color")
async def cb_color_therapy(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    color_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 लाल", callback_data="color_red"),
         InlineKeyboardButton(text="🔵 नीला", callback_data="color_blue")],
        [InlineKeyboardButton(text="🟢 हरा", callback_data="color_green"),
         InlineKeyboardButton(text="🟡 पीला", callback_data="color_yellow")],
        [InlineKeyboardButton(text="🟣 बैंगनी", callback_data="color_purple"),
         InlineKeyboardButton(text="🟠 नारंगी", callback_data="color_orange")],
        [InlineKeyboardButton(text="🩷 गुलाबी", callback_data="color_pink"),
         InlineKeyboardButton(text="⚫ काला", callback_data="color_black")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="mystical_menu")]
    ])
    
    await cb.message.edit_text("🎨 <b>कलर थेरेपी</b>\n\nआज आपका पसंदीदा रंग कौन सा है?", reply_markup=color_kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("color_"))
async def cb_color_result(cb: CallbackQuery):
    color = cb.data.split("_")[1]
    result = get_color_personality(color)
    add_experience(cb.from_user.id, 8)
    
    text = f"🎨 <b>आपका कलर पर्सनैलिटी</b>\n\n{result}\n\n🌈 <i>रंग आपकी मनोदशा को दर्शाते हैं!</i>"
    await cb.message.edit_text(text, reply_markup=mystical_menu())
    await cb.answer()

@dp.callback_query(F.data == "mystical_lucky")
async def cb_lucky_number(cb: CallbackQuery):
    lucky_nums = []
    for _ in range(5):
        lucky_nums.append(random.randint(1, 99))
    
    add_experience(cb.from_user.id, 5)
    
    text = f"🧿 <b>आपके लकी नंबर</b>\n\n🎯 आज के विशेष नंबर:\n" + ", ".join([f"**{num}**" for num in lucky_nums])
    text += f"\n\n🌟 <i>इन नंबरों से आज कुछ अच्छा हो सकता है!</i>"
    await cb.message.edit_text(text, reply_markup=mystical_menu())
    await cb.answer()

# ========== DAILY CHALLENGES ==========
@dp.callback_query(F.data == "challenges_menu")
async def cb_challenges_menu(cb: CallbackQuery):
    await cb.message.edit_text("⚡ <b>डेली चैलेंजेस</b>\n\nहर दिन नए कार्य पूरे करें:", reply_markup=challenges_menu())
    await cb.answer()

@dp.callback_query(F.data == "challenge_daily")
async def cb_daily_challenge(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    today_challenge = random.choice(daily_challenges)
    progress = user_state[uid].get("challenge_progress", {})
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    if today_date in progress:
        text = f"✅ <b>आज का चैलेंज पूरा हो गया!</b>\n\n🏆 **{progress[today_date]}**\n\n🎉 कल नया चैलेंज मिलेगा!"
    else:
        user_state[uid]["current_challenge"] = today_challenge
        text = f"⚡ <b>आज का चैलेंज</b>\n\n{today_challenge}\n\n🎯 <i>इसे पूरा करके XP जीतें!</i>"
    
    challenge_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 प्रोग्रेस देखें", callback_data="challenge_progress"),
         InlineKeyboardButton(text="🧠 ब्रेन ट्रेनिंग", callback_data="challenge_brain")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="challenges_menu")]
    ])
    
    await cb.message.edit_text(text, reply_markup=challenge_kb)
    await cb.answer()

@dp.callback_query(F.data == "challenge_brain")
async def cb_brain_training(cb: CallbackQuery):
    teaser = generate_brain_teaser()
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = "brain_teaser"
    user_state[uid]["brain_answer"] = teaser["a"]
    
    text = f"🧠 <b>ब्रेन ट्रेनिंग</b>\n\n{teaser['q']}\n\n💭 <i>अपना जवाब भेजें!</i>"
    await cb.message.edit_text(text, reply_markup=challenges_menu())
    await cb.answer()

# ========== MORE WELLNESS FEATURES ==========
@dp.callback_query(F.data == "wellness_meditation")
async def cb_meditation(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    meditation_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧘‍♀️ 5 मिनट", callback_data="med_5"),
         InlineKeyboardButton(text="🧘‍♂️ 15 मिनट", callback_data="med_15")],
        [InlineKeyboardButton(text="🧘 30 मिनट", callback_data="med_30"),
         InlineKeyboardButton(text="🔉️ गाइडेड", callback_data="med_guided")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="wellness_menu")]
    ])
    
    await cb.message.edit_text("🧘 <b>मेडिटेशन टाइम</b>\n\nकितने मिनट का सेशन चाहिए?", reply_markup=meditation_kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("med_"))
async def cb_meditation_start(cb: CallbackQuery):
    duration_map = {"med_5": 5, "med_15": 15, "med_30": 30}
    
    if cb.data == "med_guided":
        guide = "🧘 <b>गाइडेड मेडिटेशन</b>\n\n🌸 आराम से बैठें\n👁️ आंखें बंद करें\n🌬️ गहरी सांस लें\n💭 मन को शांत करें\n✨ सकारात्मक सोचें\n\n🎯 <i>10 मिनट बाद वापस आएं!</i>"
        add_experience(cb.from_user.id, 20)
    else:
        duration = duration_map[cb.data]
        guide = generate_meditation_guide(duration)
        user_state[cb.from_user.id]["meditation_time"] = user_state[cb.from_user.id].get("meditation_time", 0) + duration
        add_experience(cb.from_user.id, duration * 2)
    
    await cb.message.edit_text(guide, reply_markup=wellness_menu())
    await cb.answer()

@dp.callback_query(F.data == "wellness_mood")
async def cb_mood_tracker(cb: CallbackQuery):
    mood_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 खुश", callback_data="mood_happy"),
         InlineKeyboardButton(text="😢 उदास", callback_data="mood_sad")],
        [InlineKeyboardButton(text="🤩 उत्साहित", callback_data="mood_excited"),
         InlineKeyboardButton(text="😌 शांत", callback_data="mood_calm")],
        [InlineKeyboardButton(text="😠 गुस्सा", callback_data="mood_angry"),
         InlineKeyboardButton(text="😴 सुस्त", callback_data="mood_sleepy")],
        [InlineKeyboardButton(text="⬅️ वापस", callback_data="wellness_menu")]
    ])
    
    await cb.message.edit_text("😊 <b>मूड ट्रैकर</b>\n\nआज आपका मूड कैसा है?", reply_markup=mood_kb)
    await cb.answer()

@dp.callback_query(F.data.startswith("mood_"))
async def cb_mood_set(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    mood = cb.data.split("_")[1]
    user_state[uid]["mood"] = mood
    
    mood_responses = {
        "happy": "😊 बहुत अच्छा! खुशी बांटते रहें!",
        "sad": "😢 कोई बात नहीं, कल बेहतर होगा!",
        "excited": "🤩 वाह! आपकी energy देखकर खुशी हुई!",
        "calm": "😌 शांति बहुत अच्छी चीज है!",
        "angry": "😠 गुस्सा छोड़ें, खुश रहें!",
        "sleepy": "😴 आराम जरूरी है, अच्छी नींद लें!"
    }
    
    emoji = get_mood_emoji(mood)
    response = mood_responses.get(mood, "🌟 आपका मूड नोट कर लिया!")
    add_experience(uid, 5)
    
    text = f"{emoji} <b>मूड अपडेट</b>\n\n{response}\n\n📊 <i>आप रोज अपना मूड ट्रैक कर सकते हैं!</i>"
    await cb.message.edit_text(text, reply_markup=wellness_menu())
    await cb.answer()

# ========== MORE CREATIVE FEATURES ==========
@dp.callback_query(F.data == "creative_prompt")
async def cb_writing_prompt(cb: CallbackQuery):
    prompts = [
        "✍️ एक ऐसे व्यक्ति के बारे में लिखें जो समय यात्रा कर सकता है",
        "📚 एक जादुई किताब की कहानी जो सच हो जाती है",
        "🌙 एक ऐसी रात का वर्णन करें जहां चांद गायब हो गया",
        "🎭 दो अलग दुनिया के लोगों की मुलाकात",
        "🗝️ एक रहस्यमय चाबी जो किसी भी दरवाजे को खोल सकती है",
        "🎨 एक कलाकार जिसकी पेंटिंग्स जीवंत हो जाती हैं",
        "🌟 सितारों से गिरा एक संदेश",
        "🦋 तितलियों की भाषा समझने वाला बच्चा"
    ]
    
    prompt = random.choice(prompts)
    add_experience(cb.from_user.id, 10)
    
    text = f"✍️ <b>राइटिंग प्रॉम्प्ट</b>\n\n{prompt}\n\n🎨 <i>इस विषय पर कुछ रचनात्मक लिखें!</i>"
    await cb.message.edit_text(text, reply_markup=creative_menu())
    await cb.answer()

@dp.callback_query(F.data == "creative_lyrics")
async def cb_song_lyrics(cb: CallbackQuery):
    themes = ["प्रेम", "दोस्ती", "सफलता", "सपने", "खुशी", "उम्मीद", "यादें", "मंजिल"]
    theme = random.choice(themes)
    
    lyrics_template = f"🎵 <b>गाने का विषय: {theme}</b>\n\n🎼 **पहली लाइन:**\n{theme} के बारे में...\n\n🎤 <i>आगे की लाइनें आप लिखें और अपना गाना पूरा करें!</i>"
    
    add_experience(cb.from_user.id, 12)
    await cb.message.edit_text(lyrics_template, reply_markup=creative_menu())
    await cb.answer()

# ========== MORE PET FEATURES ==========
@dp.callback_query(F.data == "pet_play")
async def cb_pet_play(cb: CallbackQuery):
    uid = cb.from_user.id
    pet = virtual_pets[uid]
    
    if pet["energy"] < 20:
        text = f"🐾 <b>{pet['name']}</b> बहुत थका है!\n\n💤 <i>पहले आराम करने दें!</i>"
    else:
        pet["energy"] = max(0, pet["energy"] - 15)
        pet["happiness"] = min(100, pet["happiness"] + 15)
        pet["exp"] = min(100, pet["exp"] + 8)
        pet["last_played"] = time.time()
        add_experience(uid, 8)
        
        games = ["फ्रिसबी", "गेंद", "छुपन-छुपाई", "रेसिंग", "ट्रिक्स"]
        game = random.choice(games)
        
        text = f"🎾 <b>{pet['name']}</b> के साथ {game} खेली!\n\n🤩 वो बहुत मजे कर रहा है! (+8 EXP)"
    
    await cb.message.edit_text(text, reply_markup=pet_menu())
    await cb.answer()

@dp.callback_query(F.data == "pet_sleep")
async def cb_pet_sleep(cb: CallbackQuery):
    uid = cb.from_user.id
    pet = virtual_pets[uid]
    
    pet["energy"] = min(100, pet["energy"] + 30)
    pet["happiness"] = min(100, pet["happiness"] + 5)
    add_experience(uid, 5)
    
    sleep_messages = [
        f"💤 {pet['name']} आराम से सो रहा है!",
        f"😴 {pet['name']} प्यारे सपने देख रहा है!",
        f"🛏️ {pet['name']} को अच्छी नींद आई!"
    ]
    
    text = f"{random.choice(sleep_messages)}\n\n⚡ एनर्जी रिस्टोर हो गई! (+30 Energy)"
    await cb.message.edit_text(text, reply_markup=pet_menu())
    await cb.answer()

# ========== MORE GAMES ==========
@dp.callback_query(F.data == "game_memory")
async def cb_memory_game(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    # Generate memory sequence
    sequence = [random.choice(["🔴", "🟢", "🔵", "🟡"]) for _ in range(4)]
    user_state[uid]["memory_sequence"] = sequence
    user_state[uid]["memory_shown"] = True
    
    sequence_text = " ".join(sequence)
    
    text = f"🧠 <b>मेमोरी गेम</b>\n\n🎯 इस सीक्वेंस को याद करें:\n\n{sequence_text}\n\n⏰ <i>5 सेकंड में गायब हो जाएगा!</i>"
    
    memory_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ तैयार हूं!", callback_data="memory_start"),
         InlineKeyboardButton(text="⬅️ वापस", callback_data="games_menu")]
    ])
    
    await cb.message.edit_text(text, reply_markup=memory_kb)
    await cb.answer()

@dp.callback_query(F.data == "game_math")
async def cb_math_challenge(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    
    # Generate math problem
    num1 = random.randint(10, 99)
    num2 = random.randint(10, 99)
    operations = ["+", "-", "×"]
    op = random.choice(operations)
    
    if op == "+":
        answer = num1 + num2
    elif op == "-":
        answer = num1 - num2
    else:  # ×
        answer = num1 * num2
    
    user_state[uid]["mode"] = "math_challenge"
    user_state[uid]["math_answer"] = answer
    
    text = f"🧮 <b>मैथ चैलेंज</b>\n\n❓ **{num1} {op} {num2} = ?**\n\n🎯 <i>जल्दी से जवाब दें!</i>"
    await cb.message.edit_text(text, reply_markup=games_menu())
    await cb.answer()

@dp.callback_query(F.data == "game_tod")
async def cb_truth_dare(cb: CallbackQuery):
    truths = [
        "🤔 आपका सबसे बड़ा डर क्या है?",
        "💭 आपको कौन सा सुपरपावर चाहिए?",
        "🎵 आपका फेवरेट गाना कौन सा है?",
        "🍕 आपकी मनपसंद डिश क्या है?",
        "🌟 आपका बचपन का हीरो कौन है?"
    ]
    
    dares = [
        "🎭 अपना फेवरेट डांस स्टेप करें!",
        "🎤 कोई गाना गुनगुनाएं!",
        "😄 अपनी सबसे फनी फोटो भेजें!",
        "🤸 10 जंपिंग जैक्स करें!",
        "📞 किसी दोस्त को कॉल करें!"
    ]
    
    choice = random.choice(["truth", "dare"])
    
    if choice == "truth":
        question = random.choice(truths)
        text = f"🔍 <b>Truth</b>\n\n{question}\n\n💭 <i>सच्चा जवाब दें!</i>"
    else:
        challenge = random.choice(dares)
        text = f"🎪 <b>Dare</b>\n\n{challenge}\n\n🎯 <i>चैलेंज कंप्लीट करें!</i>"
    
    add_experience(cb.from_user.id, 10)
    
    tod_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 अगला राउंड", callback_data="game_tod"),
         InlineKeyboardButton(text="⬅️ वापस", callback_data="games_menu")]
    ])
    
    await cb.message.edit_text(text, reply_markup=tod_kb)
    await cb.answer()

# ========== MISSING HANDLERS ==========
async def handle_advanced_text_design(message: Message, uid: int, text: str):
    """Handle advanced text design with multiple styles"""
    user_state[uid]["mode"] = None
    style = user_state[uid].get("design_style", "bold")
    
    if style == "bold":
        result = f"<b>{text}</b>"
    elif style == "italic":
        result = f"<i>{text}</i>"
    elif style == "mono":
        result = f"<code>{text}</code>"
    elif style == "fancy":
        result = to_fullwidth(text)
    elif style == "reverse":
        result = text[::-1]
    elif style == "upper":
        result = text.upper()
    else:
        result = text
    
    add_experience(uid, 8)
    
    design_text = f"🎨 <b>Text Design Result</b>\n\n📝 **Original:** {text}\n✨ **Styled:** {result}\n\n🏆 <i>+8 XP for creativity!</i>"
    
    design_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Try Another Style", callback_data="text_menu"),
         InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await message.answer(design_text, reply_markup=design_kb)

async def handle_advanced_todo(message: Message, uid: int, text: str):
    """Handle advanced todo operations"""
    user_state[uid]["mode"] = None
    
    if text.startswith("/add "):
        task = text[5:]
        user_state[uid]["todo_list"].append(task)
        response = f"✅ Task added: {task}"
    elif text.startswith("/done "):
        try:
            index = int(text[6:]) - 1
            if 0 <= index < len(user_state[uid]["todo_list"]):
                completed_task = user_state[uid]["todo_list"].pop(index)
                response = f"🎉 Completed: {completed_task}"
                add_experience(uid, 15)
            else:
                response = "❌ Invalid task number"
        except ValueError:
            response = "❌ Please provide a valid number"
    else:
        user_state[uid]["todo_list"].append(text)
        response = f"📝 Added to your todo list: {text}"
        add_experience(uid, 5)
    
    todo_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(user_state[uid]["todo_list"])])
    
    if todo_list:
        full_response = f"{response}\n\n📋 **Your Todo List:**\n{todo_list}\n\n💡 **Commands:**\n• `/add [task]` - Add new task\n• `/done [number]` - Complete task"
    else:
        full_response = f"{response}\n\n📋 **Your todo list is empty!**\n\n💡 Type a task to add it to your list."
    
    todo_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Add More Tasks", callback_data="prod_todo"),
         InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await message.answer(full_response, reply_markup=todo_kb)

# ========== MORE MISSING HANDLERS ==========
async def handle_guess_game(message: Message, uid: int, text: str):
    """Handle guess number game"""
    try:
        guess = int(text)
        target = user_state[uid]["guess_target"]
        
        if guess == target:
            user_state[uid]["mode"] = None
            user_state[uid]["game_wins"] += 1
            add_experience(uid, 25)
            await message.answer(f"🎉 <b>बधाई हो! सही अनुमान!</b>\n\n🎯 Number था: {target}\n🏆 +25 XP मिले!\n\n🎮 दूसरा गेम खेलना चाहते हैं?", reply_markup=games_menu())
        elif guess < target:
            await message.answer(f"📈 <b>ऊपर की तरफ!</b>\n\n🎯 {guess} से बड़ा number है।\n💡 दोबारा try करें!")
        else:
            await message.answer(f"📉 <b>नीचे की तरफ!</b>\n\n🎯 {guess} से छोटा number है।\n💡 दोबारा try करें!")
    except ValueError:
        await message.answer("❌ <b>कृपया valid number डालें!</b>\n\n🔢 Example: 50")

# ========== MESSAGE HANDLERS ==========
@dp.message(F.text)
async def handle_text_messages(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    
    bot_stats["messages"] += 1
    user_data[uid]["total_commands"] = user_data[uid].get("total_commands", 0) + 1
    user_state[uid]["last_active"] = datetime.now().isoformat()
    
    text = message.text.strip()
    mode = user_state[uid].get("mode")
    
    # Add small XP for interaction
    add_experience(uid, 2)
    
    # Handle different modes
    if mode == "guess":
        await handle_guess_game(message, uid, text)
    elif mode == "calculator":
        await handle_advanced_calculator(message, uid, text)
    elif mode == "design":
        await handle_advanced_text_design(message, uid, text)
    elif mode == "todo":
        await handle_advanced_todo(message, uid, text)
    elif mode == "brain_teaser":
        await handle_brain_teaser_answer(message, uid, text)
    elif mode == "math_challenge":
        await handle_math_challenge_answer(message, uid, text)
    elif user_state[uid]["echo"]:
        await message.answer(f"🔁 <b>Echo Mirror:</b> ✨{text}✨\n\n💡 <i>Echo mode is active! Use /menu to change settings.</i>")
    else:
        # Smart response based on user input
        await handle_smart_response(message, uid, text)

async def handle_brain_teaser_answer(message: Message, uid: int, text: str):
    """Handle brain teaser answers"""
    user_state[uid]["mode"] = None
    correct_answer = user_state[uid].get("brain_answer", "")
    
    if text.lower().strip() == correct_answer.lower().strip():
        add_experience(uid, 20)
        await message.answer(f"🧠 <b>शानदार! बिल्कुल सही!</b>\n\n✅ सही जवाब: {correct_answer}\n🏆 +20 XP मिले!\n\n🎯 <i>आप वाकई तेज़ हैं!</i>", reply_markup=challenges_menu())
    else:
        add_experience(uid, 5)
        await message.answer(f"🤔 <b>अच्छी कोशिश!</b>\n\n✅ सही जवाब: {correct_answer}\n🏆 +5 XP मिले कोशिश के लिए!\n\n💡 <i>अगली बार ज़रूर सही होगा!</i>", reply_markup=challenges_menu())

async def handle_math_challenge_answer(message: Message, uid: int, text: str):
    """Handle math challenge answers"""
    try:
        answer = int(text)
        correct_answer = user_state[uid].get("math_answer", 0)
        user_state[uid]["mode"] = None
        
        if answer == correct_answer:
            add_experience(uid, 15)
            await message.answer(f"🧮 <b>Perfect! बिल्कुल सही!</b>\n\n✅ जवाब: {correct_answer}\n🏆 +15 XP मिले!\n\n🎯 <i>Math में आप expert हैं!</i>", reply_markup=games_menu())
        else:
            add_experience(uid, 3)
            await message.answer(f"📊 <b>गलत, लेकिन कोशिश अच्छी थी!</b>\n\n✅ सही जवाब: {correct_answer}\n🏆 +3 XP मिले कोशिश के लिए!\n\n💪 <i>अभ्यास से आप बेहतर होंगे!</i>", reply_markup=games_menu())
    except ValueError:
        await message.answer("❌ <b>कृपया valid number डालें!</b>\n\n🔢 Example: 25")

async def handle_smart_response(message: Message, uid: int, text: str):
    """Enhanced smart response system"""
    text_lower = text.lower()
    
    greetings = ["hello", "hi", "hey", "good morning", "good evening"]
    questions = ["how are you", "what can you do", "help me"]
    
    if any(greeting in text_lower for greeting in greetings):
        responses = [
            f"👋 Hello {message.from_user.first_name}! Ready for some amazing features?",
            "🌟 Hi there! I'm here to make your day awesome!",
            "✨ Hey! What incredible thing shall we do today?",
            "🚀 Greetings! Let's explore my 100+ features together!"
        ]
        await message.answer(random.choice(responses), reply_markup=main_menu())
    
    elif any(question in text_lower for question in questions):
        await message.answer("🤖 <b>I'm your ultimate digital assistant!</b>\n\n💪 I can help you with games, tools, productivity, security, and so much more!\n\n🎯 Use the menu to explore all features:", reply_markup=main_menu())
    
    else:
        motivational_responses = [
            "🌟 That's interesting! Use /menu to discover amazing features!",
            "💫 I love chatting with you! Check out my incredible tools!",
            "✨ Thanks for sharing! Let me show you what I can do!",
            "🎯 Great message! Ready to explore 100+ features?",
            "🚀 Awesome! Let's make something amazing happen!"
        ]
        await message.answer(random.choice(motivational_responses), reply_markup=main_menu())

async def handle_advanced_calculator(message: Message, uid: int, text: str):
    """Enhanced calculator with advanced functions"""
    result = calculate_expression(text)
    user_state[uid]["mode"] = None
    add_experience(uid, 15)
    
    if result != "Invalid expression":
        calc_text = f"""
🧮 <b>Smart Calculator Result</b>

📝 <b>Expression:</b> <code>{text}</code>
🎯 <b>Result:</b> <code>{result}</code>
⚡ <b>Calculation Type:</b> {get_calculation_type(text)}

💡 <b>Available Functions:</b>
• Basic: +, -, ×, ÷
• Advanced: ^(power), √(square root)
• Functions: sin, cos, tan, log

🏆 <b>Reward:</b> +15 XP for using tools!

🎯 <b>Your Progress:</b>
• Level: {user_state[uid]['level']}
• Total XP: {user_state[uid]['experience']}
"""
    else:
        calc_text = f"""
❌ <b>Calculation Error</b>

📝 <b>Expression:</b> {text}
🔍 <b>Issue:</b> Invalid mathematical expression

💡 <b>Examples of valid expressions:</b>
• Simple: 2 + 2, 10 × 5
• Advanced: 2^3, √16
• Complex: (8 + 4) × 2 - 5

🎯 Try again with a valid expression!
"""
    
    calc_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Calculate Again", callback_data="tool_calc"),
         InlineKeyboardButton(text="🛠️ More Tools", callback_data="tools_menu")],
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_menu")]
    ])
    
    await message.answer(calc_text, reply_markup=calc_kb)

def get_calculation_type(expression: str) -> str:
    """Determine the type of calculation"""
    if "√" in expression or "math.sqrt" in expression:
        return "Square Root Calculation"
    elif "^" in expression or "**" in expression:
        return "Power Calculation"  
    elif any(op in expression for op in ["sin", "cos", "tan", "log"]):
        return "Trigonometric/Logarithmic"
    elif any(op in expression for op in ["×", "*", "÷", "/"]):
        return "Multiplication/Division"
    else:
        return "Basic Arithmetic"

# ========== WEBHOOK SETUP ==========
async def on_startup(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="🚀 Launch the ultimate bot"),
        BotCommand(command="help", description="📚 Complete feature guide"),
        BotCommand(command="menu", description="📋 Access main control center"),
        BotCommand(command="profile", description="👤 View your progress & stats"),
        BotCommand(command="achievements", description="🏆 See your achievements"),
        BotCommand(command="cancel", description="❌ Cancel current operation")
    ]
    await bot.set_my_commands(commands)
    await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    print(f"✅ Ultimate Bot webhook set to: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    print("✅ Ultimate Bot webhook deleted.")

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
