import asyncio
import json
import logging
import os
import random
import re
import signal
import unicodedata
import time as pytime
from datetime import datetime, time, timedelta
from logging.handlers import RotatingFileHandler
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.ext import ApplicationHandlerStop

# 🔴 توکن باتت رو اینجا بذار
TOKEN = "8122230876:AAHVnsvD3dw_z7PKi0sh7BxaR-3wiUDA5Bk"
ADMIN_ACTIVATION_CODE = "12345678901234567890"
ADMIN_IDS = {6930517587}
SUPPORT_ADMIN_ID = 6930517587
PRIMARY_ADMIN_ID = SUPPORT_ADMIN_ID
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "bot.log")
USER_DATA_FILE = os.path.join(BASE_DIR, "user_data.json")
PENDING_PAYMENTS_FILE = os.path.join(BASE_DIR, "pending_payments.json")
CLAN_DATA_FILE = os.path.join(BASE_DIR, "clan_data.json")
COIN_TRANSFER_DAILY_LIMIT = 1000
DUEL_DAILY_LIMIT = 2
HIGH_RANK_THRESHOLD = 12000
LOW_RANK_CAP_THRESHOLD = 2000
GOLD_MINE_BASE_RATE = 100
GOLD_MINE_MAX_HOURS = 3
GOLD_MINE_MAX_LEVEL = 30
GEM_MINE_REWARD = 2
GEM_MINE_COOLDOWN = timedelta(hours=24)
GEM_MINE_MIN_LEVEL = 10
ATLAS_BASE_PRICE = 50
ATLAS_PRICE_STEP = 0
ATLAS_DAMAGE_MIN = 16
ATLAS_DAMAGE_MAX = 20
QADR_PRICE = 30
QADR_DAMAGE_MIN = 10
QADR_DAMAGE_MAX = 13
KHEIBAR_PRICE = 60
KHEIBAR_DAMAGE_MIN = 20
KHEIBAR_DAMAGE_MAX = 25
SAJJIL_PRICE = 130
SAJJIL_DAMAGE_MIN = 50
SAJJIL_DAMAGE_MAX = 60
SHAHAB_PRICE = 150
SHAHAB_DAMAGE_MIN = 60
SHAHAB_DAMAGE_MAX = 70
TUFAN_PRICE = 420
TUFAN_DAMAGE_MIN = 120
TUFAN_DAMAGE_MAX = 130
ALMAS_PRICE = 480
ALMAS_DAMAGE_MIN = 145
ALMAS_DAMAGE_MAX = 160
KHORRAMSHAHR_PRICE = 380
KHORRAMSHAHR_DAMAGE_MIN = 100
KHORRAMSHAHR_DAMAGE_MAX = 120
EMAD_PRICE = 100
EMAD_DAMAGE_MIN = 38
EMAD_DAMAGE_MAX = 45
TIRBAR_PRICE = 100
CHEMICAL_PRICE = 400
NUCLEAR_PRICE_COINS = 2000
NUCLEAR_PRICE_GEMS = 1
SHIELD_PACKS = [
    {"label": "برنز", "hours": 1, "gems": 18},
    {"label": "نقره", "hours": 2, "gems": 21},
    {"label": "طلا", "hours": 3, "gems": 24},
    {"label": "الماس", "hours": 8, "gems": 40},
]
REQUIRED_SUBSCRIPTIONS = [
    {
        "chat_id": -1003330828421,  # آیدی عددی کانال/گروه اول
        "link": "https://t.me/SolarWar_Game",
        "label": "کانال",
    },
    {
        "chat_id": -1003616173276,  # آیدی عددی کانال/گروه دوم
        "link": "https://t.me/SolarWar_Gap",
        "label": "گروه",
    },
]
DEFENSE_ITEMS = [
    {"key": "tirbar_defense", "label": "تیر بار", "price": 100, "level": 1, "chance": 20},
    {"key": "aegis_defense", "label": "ایجیس", "price": 300, "level": 3, "chance": 30},
    {"key": "panster_defense", "label": "پانستر", "price": 800, "level": 7, "chance": 40},
    {"key": "arrow_defense", "label": "ارو", "price": 1500, "level": 10, "chance": 55},
    {"key": "hq9_defense", "label": "اچ‌کیو-9", "price": 2300, "level": 13, "chance": 60},
    {"key": "s400_defense", "label": "اس 400", "price": 3000, "level": 15, "chance": 70},
    {"key": "hq22_defense", "label": "اچ‌کیو-22", "price": 5000, "level": 18, "chance": 80},
]
CLAN_CREATE_COST = 3000
CLAN_LEVEL_COSTS = {2: 10000, 3: 15000, 4: 25000, 5: 50000}
CLAN_TANK_PURCHASE_COST = 100000
CLAN_TANK_LEVEL_COSTS = {2: 50000, 3: 100000, 4: 150000, 5: 200000}
CLAN_WAR_TEAM_SIZE = 10
CLAN_WAR_ATTACKS_PER_USER = 5
CLAN_CASTLE_MAX_LEVEL = 10
CLAN_CASTLE_LEVEL_COST = 10000
CLAN_CASTLE_DAMAGE_MIN_PER_LEVEL = 15
CLAN_CASTLE_DAMAGE_MAX_PER_LEVEL = 20
CLAN_WAR_PREP_MINUTES = 15
CLAN_WAR_DURATION_MINUTES = 30
AMERICA_WHEEL_COIN_COST = 1000
LEVEL_PASS_MAX_LEVEL = 40
LEVEL_PASS_EXP_PER_LEVEL = 100
MISSILE_EXP_VALUES = {
    "atlas_missiles": 1,
    "emad_missiles": 2,
    "kheibar_missiles": 2,
    "sajjil_missiles": 2,
    "shahab_missiles": 2,
    "khorramshahr_missiles": 3,
    "tufan_missiles": 3,
    "almas_missiles": 3,
    "chemical_missiles": 4,
    "nuclear_missiles": 5,
    "redline_missiles": 5,
}
AMERICA_WHEEL_GEM_COST = 5
REDLINE_WHEEL_REWARDS = [
    {"label": "ردلاین (3 عدد)", "type": "redline_missiles", "amount": 3},
    {"label": "4000 سکه", "type": "coins", "amount": 4000},
    {"label": "ردلاین (1 عدد)", "type": "redline_missiles", "amount": 1},
    {"label": "عماد (5 عدد)", "type": "emad_missiles", "amount": 5},
    {"label": "اطلس (5 عدد)", "type": "atlas_missiles", "amount": 5},
    {"label": "200 سکه", "type": "coins", "amount": 200},
    {"label": "تیر بار (1 عدد)", "type": "tirbar_defense", "amount": 1},
]
REDLINE_WHEEL_CHANCES = [1, 2, 4, 10, 15, 25, 35]
AMERICA_WHEEL_REWARDS = [
    "200 سکه",
    "عماد (3 عدد)",
    "ذوالفقار (3 عدد)",
    "500 سکه",
    "F-16 (1 عدد)",
    "F-35 (1 عدد)",
    "F-22 (1 عدد)",
    "فتاح (5 عدد)",
]
LOOT_BOX_MESSAGE_THRESHOLD = 200
LOOT_BOX_DAILY_LIMIT = 20
LOOT_BOX_REWARDS = [
    {"type": "coins", "label": "سکه", "min": 100, "max": 500},
    {"type": "atlas_missiles", "label": "اطلس", "min": 3, "max": 5},
    {"type": "emad_missiles", "label": "عماد", "min": 1, "max": 3},
    {"type": "khorramshahr_missiles", "label": "خرمشهر", "min": 1, "max": 2},
    {"type": "chemical_missiles", "label": "شیمیایی", "min": 1, "max": 2},
]

ZARINPAL_MERCHANT_ID = "YOUR_MERCHANT_ID"
ZARINPAL_CALLBACK_URL = "https://YOUR_DOMAIN/verify"
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_GATEWAY_URL = "https://www.zarinpal.com/pg/StartPay/"
PAYMENT_CARD_NUMBER = "6063731176689694"
PAYMENT_CARD_OWNER = "اسدیان"

TOPUP_PACKS = [
    (20000, "بسته ۲۰ هزار تومان"),
    (50000, "بسته ۵۰ هزار تومان"),
    (100000, "بسته ۱۰۰ هزار تومان"),
    (200000, "بسته ۲۰۰ هزار تومان"),
]
GEM_PACKS = [
    {"gems": 10, "price": 5000},
    {"gems": 25, "price": 12500},
    {"gems": 50, "price": 25000},
    {"gems": 100, "price": 50000},
    {"gems": 200, "price": 95000},
    {"gems": 500, "price": 230000},
    {"gems": 1000, "price": 450000},
    {"gems": 2500, "price": 1100000},
]
COIN_PACKS = [
    {"coins": 10000, "price": 5000},
    {"coins": 20000, "price": 10000},
    {"coins": 60000, "price": 30000},
    {"coins": 240000, "price": 120000},
    {"coins": 400000, "price": 200000},
]
SPECIAL_PACKS = []
BUNDLE_PACKS = []

user_data_store = {}
gift_codes = {}
pending_payments = {}
clan_data_store = {}
clan_war_sessions = {}
clan_war_queue: list[dict] = []
telegram_app = None
group_message_counts = {}
loot_boxes = {}
duel_sessions: dict[str, dict] = {}
duel_requests: dict[str, dict] = {}
_USER_LAST_SAVE = 0.0
USER_SAVE_MIN_INTERVAL = 2.0

LEAGUE_TIERS = [
    (0, "🎗 تازه‌کار"),
    (100, "🏵 باتجربه"),
    (500, "🥉 برنزی"),
    (1000, "🥈 نقره‌ای"),
    (1700, "🥇 طلایی"),
    (3000, "💠 پلاتینیوم"),
    (5000, "🏆 قهرمانان"),
    (8000, "👻 ارواح"),
    (12000, "🐉 دراگون"),
    (17000, "❄️ آیس"),
    (23000, "🌪 طوفان"),
    (30000, "🌪 طوفان"),
    (38000, "⚔ تایتان"),
    (47000, "🔮 کریستال"),
]

CRYSTAL_DAILY_ATTACK_LIMIT = 30
CRYSTAL_LEAGUE_NAME = "🔮 کریستال"

STARPASS_COST = 50
STARPASS_RESET_TIME = time(3, 30)
STARPASS_REWARDS = [
    {"day": 1, "label": "15 عماد", "missiles": {"emad_missiles": 15}},
    {"day": 2, "label": "400 اس", "coins": 400},
    {"day": 3, "label": "2000 سکه", "coins": 2000},
    {"day": 4, "label": "100 تجربه", "experience": 100},
    {"day": 5, "label": "10 خرمشهر", "missiles": {"khorramshahr_missiles": 10}},
    {"day": 6, "label": "5 ردلاین", "missiles": {"redline_missiles": 5}},
    {"day": 7, "label": "10 اچ‌کیو-9", "defenses": {"hq9_defense": 10}},
    {"day": 8, "label": "5 هسته‌ای", "missiles": {"nuclear_missiles": 5}},
    {"day": 9, "label": "10000 سکه", "coins": 10000},
    {"day": 10, "label": "تایتل SolarVIP", "title": "SolarVIP"},
]
STARPASS_CHAT_STICKERS = [
    ("🔥 استیکر آتش", "🔥"),
    ("❄️ استیکر یخ", "❄️"),
    ("⚡ استیکر برق", "⚡"),
    ("⭐ استیکر ستاره", "⭐"),
    ("💎 استیکر الماس", "💎"),
    ("🌟 استیکر پریمیوم", "🌟"),
    ("👑 استیکر تاج", "👑"),
    ("🚀 استیکر موشک", "🚀"),
    ("🎖️ استیکر مدال", "🎖️"),
]

GLOBAL_ATTACK_COOLDOWN_SECONDS = 90
GLOBAL_ATTACK_REROLL_COST = 10
NOT_AVAILABLE_TEXT = "این منو وجود نداره."
DUEL_DURATION = timedelta(minutes=5)
DUEL_REQUEST_TIMEOUT = timedelta(minutes=2)
MISSILE_CATEGORIES = [
    ("کروز 🧨", [("قدر", "qadr_missiles"), ("اطلس", "atlas_missiles"), ("خیبرشکن", "kheibar_missiles")]),
    (
        "بالستیک 🧨",
        [
            ("عماد", "emad_missiles"),
            ("سجیل", "sajjil_missiles"),
            ("شهاب", "shahab_missiles"),
            ("پاتریوت", "patriot_missiles"),
        ],
    ),
    ("هایپرسونیک 🧨", [("خرمشهر", "khorramshahr_missiles"), ("طوفان", "tufan_missiles"), ("الماس", "almas_missiles")]),
    ("شیمیایی 🧨", [("شیمیایی", "chemical_missiles")]),
    ("هسته‌ای 🧨", [("هسته‌ای", "nuclear_missiles")]),
]

CUSTOM_MISSILE_CATEGORIES = [
    ("کاستوم ها 🧨", [("رد لاین", "redline_missiles")]),
]
MISSILE_NAME_TO_KEY = {
    label: key
    for _, items in (MISSILE_CATEGORIES + CUSTOM_MISSILE_CATEGORIES)
    for label, key in items
}
MISSILE_DAMAGE_BY_NAME = {
    "قدر": (QADR_DAMAGE_MIN, QADR_DAMAGE_MAX),
    "اطلس": (ATLAS_DAMAGE_MIN, ATLAS_DAMAGE_MAX),
    "خیبرشکن": (KHEIBAR_DAMAGE_MIN, KHEIBAR_DAMAGE_MAX),
    "خرمشهر": (KHORRAMSHAHR_DAMAGE_MIN, KHORRAMSHAHR_DAMAGE_MAX),
    "عماد": (EMAD_DAMAGE_MIN, EMAD_DAMAGE_MAX),
    "سجیل": (SAJJIL_DAMAGE_MIN, SAJJIL_DAMAGE_MAX),
    "شهاب": (SHAHAB_DAMAGE_MIN, SHAHAB_DAMAGE_MAX),
    "طوفان": (TUFAN_DAMAGE_MIN, TUFAN_DAMAGE_MAX),
    "الماس": (ALMAS_DAMAGE_MIN, ALMAS_DAMAGE_MAX),
    "شیمیایی": (110, 120),
    "هسته‌ای": (400, 400),
    "رد لاین": (600, 700),
}
MISSILE_REWARD_BY_NAME = {
    "قدر": (15, 20),
    "اطلس": (30, 35),
    "خیبرشکن": (40, 45),
    "خرمشهر": (250, 300),
    "عماد": (60, 70),
    "سجیل": (90, 110),
    "شهاب": (120, 130),
    "طوفان": (300, 330),
    "الماس": (350, 400),
    "شیمیایی": (250, 300),
    "هسته‌ای": (500, 600),
    "رد لاین": (800, 1000),
}
MISSILE_DAMAGE_BY_KEY = {
    key: MISSILE_DAMAGE_BY_NAME[label]
    for label, key in MISSILE_NAME_TO_KEY.items()
    if label in MISSILE_DAMAGE_BY_NAME
}
MISSILE_REWARD_BY_KEY = {
    key: MISSILE_REWARD_BY_NAME[label]
    for label, key in MISSILE_NAME_TO_KEY.items()
    if label in MISSILE_REWARD_BY_NAME
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def load_user_data_store() -> None:
    global user_data_store
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
            if isinstance(stored, dict):
                user_data_store = stored
            else:
                user_data_store = {}
    except FileNotFoundError:
        user_data_store = {}


def save_user_data_store(force: bool = False) -> None:
    global _USER_LAST_SAVE
    now = pytime.time()
    if not force and (now - _USER_LAST_SAVE) < USER_SAVE_MIN_INTERVAL:
        return
    with open(USER_DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(user_data_store, handle, ensure_ascii=False, indent=2)
    _USER_LAST_SAVE = now


def setup_logging() -> None:
    logger = logging.getLogger()
    if logger.handlers:
        return
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def load_pending_payments() -> None:
    global pending_payments
    try:
        with open(PENDING_PAYMENTS_FILE, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
            if isinstance(stored, dict):
                pending_payments = stored
            else:
                pending_payments = {}
    except FileNotFoundError:
        pending_payments = {}


def save_pending_payments() -> None:
    with open(PENDING_PAYMENTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(pending_payments, handle, ensure_ascii=False, indent=2)


def load_clan_data_store() -> None:
    global clan_data_store
    try:
        with open(CLAN_DATA_FILE, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
            if isinstance(stored, dict):
                clan_data_store = stored
            else:
                clan_data_store = {}
    except FileNotFoundError:
        clan_data_store = {}


def save_clan_data_store() -> None:
    with open(CLAN_DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(clan_data_store, handle, ensure_ascii=False, indent=2)


def get_user_record(user_id: int) -> dict:
    key = str(user_id)
    is_new_record = key not in user_data_store
    record = user_data_store.setdefault(
        key,
        {
            "id": user_id,
            "coins": 0,
            "toman": 0,
            "gems": 0,
            "level": 1,
            "experience": 0,
            "experience_needed": 100,
            "rank": 0,
            "highest_rank": 0,
            "league": "🎗 تازه‌کار",
            "shield_active": False,
            "shield_until": None,
            "missiles": 0,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "banned": False,
            "banned_until": None,
            "last_daily_reward": None,
            "display_name": "کاربر",
            "starpass_active": False,
            "starpass_day": 1,
            "starpass_last_claim": None,
            "last_global_attack_open": None,
            "atlas_missiles": 0,
            "atlas_level": 1,
            "krooz_missiles": 0,
            "ballistic_missiles": 0,
            "hypersonic_missiles": 0,
            "khorramshahr_missiles": 0,
            "emad_missiles": 0,
            "chemical_missiles": 0,
            "nuclear_missiles": 0,
            "redline_missiles": 0,
            "qadr_missiles": 0,
            "kheibar_missiles": 0,
            "sajjil_missiles": 0,
            "shahab_missiles": 0,
            "tufan_missiles": 0,
            "almas_missiles": 0,
            "patriot_missiles": 0,
            "tirbar_defense": 0,
            "aegis_defense": 0,
            "panster_defense": 0,
            "arrow_defense": 0,
            "hq9_defense": 0,
            "s400_defense": 0,
            "hq22_defense": 0,
            "active_defense": None,
            "daily_coin_transfer": 0,
            "daily_duels_started": 0,
            "last_duel_day": None,
            "last_coin_transfer_date": None,
            "last_attack_from": None,
            "revenge_available": False,
            "chat_sticker": None,
            "last_group_chat_id": None,
            "daily_attacks_done": 0,
            "daily_attacks_received": 0,
            "last_attack_day": None,
            "gold_mine_level": 1,
            "gold_mine_last_collect": None,
            "gold_mine_stored": 0,
            "gem_mine_last_collect": None,
            "daily_boxes_opened": 0,
            "last_box_open_date": None,
            "available_titles": [],
            "selected_title": None,
            "inviter_id": None,
            "inviter_rewarded": False,
            "clan_id": None,
            "clan_war_id": None,
            "clan_war_attacks_left": 0,
            "admin_protection": is_admin(user_id),
            "revenge_targets": [],
            "last_group_attack": None,
            "level_pass_level": 1,
            "level_pass_exp": 0,
            "level_pass_exp_needed": level_pass_exp_needed(1),
            "first_start_completed": False,
    },
)
    defaults = {
        "id": user_id,
        "coins": 0,
        "toman": 0,
        "gems": 0,
        "level": 1,
        "experience": 0,
        "experience_needed": 100,
        "rank": 0,
        "highest_rank": 0,
        "league": "🎗 تازه‌کار",
        "shield_active": False,
        "shield_until": None,
        "missiles": 0,
        "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "banned": False,
        "banned_until": None,
        "last_daily_reward": None,
        "display_name": "کاربر",
        "starpass_active": False,
        "starpass_day": 1,
        "starpass_last_claim": None,
        "last_global_attack_open": None,
        "atlas_missiles": 0,
        "atlas_level": 1,
        "krooz_missiles": 0,
        "ballistic_missiles": 0,
        "hypersonic_missiles": 0,
        "khorramshahr_missiles": 0,
        "emad_missiles": 0,
        "chemical_missiles": 0,
        "nuclear_missiles": 0,
        "redline_missiles": 0,
        "qadr_missiles": 0,
        "kheibar_missiles": 0,
        "sajjil_missiles": 0,
        "shahab_missiles": 0,
        "tufan_missiles": 0,
        "almas_missiles": 0,
        "patriot_missiles": 0,
        "tirbar_defense": 0,
        "aegis_defense": 0,
        "panster_defense": 0,
        "arrow_defense": 0,
        "hq9_defense": 0,
        "s400_defense": 0,
        "hq22_defense": 0,
        "active_defense": None,
        "daily_coin_transfer": 0,
        "daily_duels_started": 0,
        "last_duel_day": None,
        "last_coin_transfer_date": None,
        "last_attack_from": None,
        "revenge_available": False,
        "chat_sticker": None,
        "last_group_chat_id": None,
        "daily_attacks_done": 0,
        "daily_attacks_received": 0,
        "last_attack_day": None,
        "gold_mine_level": 1,
        "gold_mine_last_collect": None,
        "gold_mine_stored": 0,
        "gem_mine_last_collect": None,
        "daily_boxes_opened": 0,
        "last_box_open_date": None,
        "available_titles": [],
        "selected_title": None,
        "inviter_id": None,
        "inviter_rewarded": False,
        "clan_id": None,
        "clan_war_id": None,
        "clan_war_attacks_left": 0,
        "admin_protection": is_admin(user_id),
        "revenge_targets": [],
        "last_group_attack": None,
        "level_pass_level": 1,
        "level_pass_exp": 0,
        "level_pass_exp_needed": level_pass_exp_needed(1),
        "first_start_completed": False,
    }
    needs_save = is_new_record
    for key, value in defaults.items():
        if key not in record:
            record[key] = value
            needs_save = True
    if "level_pass_level" not in record:
        record["level_pass_level"] = 1
        needs_save = True
    if "level_pass_exp" not in record:
        record["level_pass_exp"] = 0
        needs_save = True
    if "level_pass_exp_needed" not in record:
        record["level_pass_exp_needed"] = level_pass_exp_needed(record.get("level_pass_level", 1))
        needs_save = True
    if not is_new_record and "first_start_completed" not in record:
        record["first_start_completed"] = True
        needs_save = True
    if "admin_protection" not in record and is_admin(user_id):
        record["admin_protection"] = True
        needs_save = True
    user_data_store[key] = record
    if needs_save:
        save_user_data_store()
    return record


def sanitize_display_name(name: str | None) -> str:
    cleaned = (name or "").strip()
    return cleaned if cleaned else "کاربر"


def update_user_profile(user_id: int, display_name: str) -> dict:
    record = get_user_record(user_id)
    record["display_name"] = sanitize_display_name(display_name)
    record["id"] = user_id
    save_user_data_store()
    return record


def display_name_with_sticker(record: dict, fallback: str = "کاربر") -> str:
    name = record.get("display_name") or fallback
    sticker = record.get("chat_sticker")
    return f"{name} {sticker}" if sticker else name


def stylize_title(text: str) -> str:
    return text


def display_name_with_title(record: dict, fallback: str = "کاربر") -> str:
    base = display_name_with_sticker(record, fallback)
    title = record.get("selected_title")
    if not title:
        return base
    return f"{base}\n{stylize_title(title)}"


def format_titles_quote(record: dict) -> str:
    titles = record.get("available_titles") or []
    if not titles:
        return ""
    lines = [f"> {stylize_title(title)}" for title in titles]
    return "\n\n" + "\n".join(lines)


def append_titles_as_quote(user_id: int, text: str) -> str:
    if text is None:
        return text
    if not isinstance(user_id, int) or user_id <= 0:
        return text
    record = user_data_store.get(str(user_id)) or get_user_record(user_id)
    quote_block = format_titles_quote(record)
    if not quote_block:
        return text
    return f"{text}{quote_block}"


def should_protect_content(chat_id: int | None) -> bool:
    return False


_original_send_message = Bot.send_message
_original_reply_text = Message.reply_text


async def send_message_with_titles(self: Bot, *args, **kwargs):
    chat_id = kwargs.get("chat_id")
    if chat_id is None and args:
        chat_id = args[0]
    if should_protect_content(chat_id):
        kwargs.setdefault("protect_content", True)
    return await _original_send_message(self, *args, **kwargs)


Bot.send_message = send_message_with_titles


async def reply_text_with_protection(self: Message, *args, **kwargs):
    chat_id = getattr(self, "chat_id", None)
    if should_protect_content(chat_id):
        kwargs.setdefault("protect_content", True)
    return await _original_reply_text(self, *args, **kwargs)


Message.reply_text = reply_text_with_protection


async def is_user_in_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except Exception:
        return False
    if member.status in {"left", "kicked"}:
        return False
    if member.status == "restricted":
        is_member = getattr(member, "is_member", True)
        return bool(is_member)
    return True


async def chat_member_status(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> str:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except Exception:
        return "left"
    status = getattr(member, "status", None)
    if status in {"left", "kicked"}:
        return "left"
    if status == "restricted":
        is_member = getattr(member, "is_member", True)
        return "restricted" if is_member else "left"
    return "ok"


def display_name_with_tag(record: dict, fallback: str = "کاربر") -> str:
    base = display_name_with_sticker(record, fallback)
    clan_id = record.get("clan_id")
    if not clan_id:
        return base
    clan = clan_data_store.get(str(clan_id))
    tag = clan.get("tag") if clan else None
    return f"{base} {tag}" if tag else base


def display_name_with_league(record: dict, fallback: str = "کاربر") -> str:
    name = display_name_with_tag(record, fallback)
    league = record.get("league")
    return f"{name} {league}" if league else name


def is_admin_protection_enabled(record: dict) -> bool:
    if not record:
        return False
    if not is_admin(int(record.get("id", 0))):
        return False
    return record.get("admin_protection", False)


async def notify_primary_admin_of_action(
    context: ContextTypes.DEFAULT_TYPE, actor_id: int, message: str
) -> None:
    if PRIMARY_ADMIN_ID is None or actor_id == PRIMARY_ADMIN_ID:
        return
    try:
        await context.bot.send_message(chat_id=PRIMARY_ADMIN_ID, text=message)
    except Exception:
        return


def format_title_quote(record: dict) -> str:
    title = record.get("selected_title")
    if not title:
        return ""
    return f"\n> {stylize_title(title)}"


def reply_user_id(update: Update) -> int | None:
    if update is None or update.message is None or update.message.reply_to_message is None:
        return None
    if update.message.reply_to_message.from_user is None:
        return None
    return update.message.reply_to_message.from_user.id


async def is_user_subscribed(
    context: ContextTypes.DEFAULT_TYPE, chat_id_or_username, user_id: int
) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id_or_username, user_id=user_id)
    except Exception:
        # اگر بات دسترسی به چت ندارد (مثلاً ادمین نیست یا چت خصوصی است) بررسی را رد می‌کنیم
        return True
    return member.status not in {"left", "kicked"}


async def ensure_required_memberships(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    via_callback: bool = False,
) -> bool:
    user = update.effective_user
    if user is None:
        return False
    missing = []
    for sub in REQUIRED_SUBSCRIPTIONS:
        chat_id = sub.get("chat_id")
        if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
            chat_id = int(chat_id)
        username = sub.get("username") or sub.get("link")
        target = chat_id if chat_id is not None else username
        if target is None:
            continue
        if not await is_user_subscribed(context, target, user.id):
            missing.append(sub)
    if not missing:
        return False
    buttons = []
    for sub in missing:
        link = sub.get("link") or ""
        label = sub.get("label", "کانال/گروه")
        buttons.append([InlineKeyboardButton(f"عضویت در {label}", url=link)])
    buttons.append([InlineKeyboardButton("✅ عضو شدم", callback_data="check_subs")])
    text_lines = ["🔒 برای استفاده از ربات باید عضو شوید و سپس دکمه «عضو شدم» را بزنید:"]
    for sub in missing:
        text_lines.append(f"- {sub.get('label', 'کانال/گروه')}")
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
    if update.message:
        await update.message.reply_text("\n".join(text_lines), reply_markup=reply_markup)
    elif update.callback_query:
        if via_callback:
            await update.callback_query.answer("عضویت‌ها را بررسی کنید.", show_alert=True)
            try:
                await update.callback_query.edit_message_text(
                    "\n".join(text_lines), reply_markup=reply_markup
                )
            except Exception:
                pass
        else:
            await update.callback_query.answer("\n".join(text_lines), show_alert=True)
    return True


async def membership_message_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await ensure_required_memberships(update, context):
        raise ApplicationHandlerStop


async def membership_callback_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await ensure_required_memberships(update, context, via_callback=True):
        raise ApplicationHandlerStop


async def check_subscriptions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None:
        return
    if await ensure_required_memberships(update, context, via_callback=True):
        return
    await update.callback_query.answer("✅ عضویت تأیید شد.")
    try:
        await update.callback_query.edit_message_text(
            "✅ عضویت شما تأیید شد. می‌توانید از منوها استفاده کنید.",
            reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
        )
    except Exception:
        pass


def add_revenge_target(defender_record: dict, attacker_id: int) -> None:
    targets = defender_record.setdefault("revenge_targets", [])
    targets.append(attacker_id)
    if len(targets) > 20:
        targets.pop(0)
    defender_record["revenge_available"] = bool(targets)


def remove_single_revenge_target(record: dict, target_id: int) -> None:
    targets = record.get("revenge_targets", [])
    for idx, value in enumerate(targets):
        if value == target_id:
            targets.pop(idx)
            break
    record["revenge_available"] = bool(targets)


def is_private_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type == "private"


def is_group_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.type in {"group", "supergroup"}


def update_last_group_chat(record: dict, chat_id: int) -> None:
    if not record or not chat_id:
        return
    record["last_group_chat_id"] = chat_id


async def reject_if_not_private(update: Update) -> bool:
    if is_private_chat(update):
        return False
    if update.message:
        await update.message.reply_text("⛔️ این منو فقط در پیوی ربات فعال است.")
    return True


async def reject_if_not_group(update: Update) -> bool:
    if is_group_chat(update):
        return False
    if update.message:
        await update.message.reply_text("⛔️ حمله فقط در گروه قابل انجام است.")
    elif update.callback_query:
        await update.callback_query.answer("⛔️ حمله فقط در گروه قابل انجام است.", show_alert=True)
    return True


def check_ban_status(record: dict) -> bool:
    if record.get("banned"):
        return True
    banned_until = record.get("banned_until")
    if not banned_until:
        return False
    now = datetime.now()
    banned_until_time = datetime.fromisoformat(banned_until)
    if now < banned_until_time:
        return True
    record["banned_until"] = None
    save_user_data_store()
    return False


async def reject_if_banned(
    update: Update, context: ContextTypes.DEFAULT_TYPE, alert: bool = False
) -> bool:
    user = update.effective_user
    if user is None:
        return False
    record = get_user_record(user.id)
    if not check_ban_status(record):
        return False
    message = "⛔️ شما بن هستید و اجازه استفاده از ربات را ندارید."
    if update.callback_query and alert:
        await update.callback_query.answer(message, show_alert=True)
    elif update.message:
        await update.message.reply_text(message)
    return True


def update_league(record: dict) -> None:
    current_rank = record.get("rank", 0)
    league = LEAGUE_TIERS[0][1]
    for threshold, name in LEAGUE_TIERS:
        if current_rank >= threshold:
            league = name
    record["league"] = league
    if current_rank > record.get("highest_rank", 0):
        record["highest_rank"] = current_rank


def reset_purchase_flags(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_generic_missile_quantity"] = False
    context.user_data["awaiting_khorramshahr_quantity"] = False
    context.user_data["awaiting_emad_quantity"] = False
    context.user_data["awaiting_tirbar_quantity"] = False
    context.user_data["awaiting_defense_quantity"] = False
    context.user_data["awaiting_chemical_quantity"] = False
    context.user_data["awaiting_nuclear_quantity"] = False
    context.user_data["awaiting_topup_receipt"] = False


def reset_clan_prompt_flags(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_clan_remove_member"] = False
    context.user_data["awaiting_clan_leader_change"] = False
    context.user_data["awaiting_clan_sub_leader"] = False
    context.user_data.pop("clan_war_selection", None)
    context.user_data.pop("awaiting_clan_war_attack", None)


def format_owned_missiles(record: dict) -> str:
    lines = ["موشک‌ها:"]
    for title, items in MISSILE_CATEGORIES:
        owned_items = []
        for label, key in items:
            count = record.get(key, 0)
            if count > 0:
                owned_items.append(f"• {label}: {count}")
        if owned_items:
            lines.append(title)
            lines.extend(owned_items)
    for title, items in CUSTOM_MISSILE_CATEGORIES:
        owned_items = []
        for label, key in items:
            count = record.get(key, 0)
            if count > 0:
                owned_items.append(f"• {label}: {count}")
        if owned_items:
            lines.append(title)
            lines.extend(owned_items)
    if len(lines) == 1:
        return "موشکی ندارید."
    return "\n".join(lines)


def format_owned_defenses(record: dict) -> str:
    lines = ["پدافندها:"]
    for item in DEFENSE_ITEMS:
        count = record.get(item["key"], 0)
        if count > 0:
            lines.append(f"• {item['label']} 🛡️: {count}")
    active = record.get("active_defense")
    active_item = next((item for item in DEFENSE_ITEMS if item["key"] == active), None)
    active_label = f"{active_item['label']} 🛡️" if active_item else "هیچ"
    lines.append(f"• پدافند فعال: {active_label}")
    if len(lines) == 2 and lines[1].endswith("هیچ"):
        return "پدافندی ندارید."
    return "\n".join(lines)


def owned_missile_choices(record: dict) -> dict:
    choices = {}
    for label, key in MISSILE_NAME_TO_KEY.items():
        if record.get(key, 0) > 0:
            choices[label] = key
    return choices


def level_pass_exp_needed(level: int) -> int:
    if level <= 0:
        return LEVEL_PASS_EXP_PER_LEVEL
    return LEVEL_PASS_EXP_PER_LEVEL + (level - 1) * 10


def normalize_missile_name(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def find_missile_key(name: str) -> str | None:
    normalized = normalize_missile_name(name)
    normalized_compact = normalized.replace(" ", "")
    for label, key in MISSILE_NAME_TO_KEY.items():
        if normalized == label or normalized_compact == label.replace(" ", ""):
            return key
    return None


def missile_damage(name: str, missile_key: str | None = None) -> int:
    if missile_key and missile_key in MISSILE_DAMAGE_BY_KEY:
        low, high = MISSILE_DAMAGE_BY_KEY[missile_key]
        return random.randint(low, high)
    normalized = (name or "").replace(" ", "").replace("‌", "")
    for label, damage_range in MISSILE_DAMAGE_BY_NAME.items():
        if label.replace(" ", "").replace("‌", "") == normalized:
            return random.randint(*damage_range)
    return random.randint(ATLAS_DAMAGE_MIN, ATLAS_DAMAGE_MAX)


def missile_reward_range(name: str, missile_key: str | None = None) -> tuple[int, int]:
    if missile_key and missile_key in MISSILE_REWARD_BY_KEY:
        return MISSILE_REWARD_BY_KEY[missile_key]
    normalized = (name or "").replace(" ", "").replace("‌", "")
    for label, reward_range in MISSILE_REWARD_BY_NAME.items():
        if label.replace(" ", "").replace("‌", "") == normalized:
            return reward_range
    return MISSILE_REWARD_BY_NAME["اطلس"]


def calculate_attack_reward(defender: dict, reward_range: tuple[int, int]) -> int:
    base_reward = random.randint(*reward_range)
    defender_coins = defender.get("coins", 0)
    if defender_coins >= base_reward:
        return base_reward
    return int(defender_coins * 0.75)


def calculate_rank_transfer(attacker: dict, defender: dict, damage: int) -> tuple[int, int]:
    base_gain = max(1, damage // 5)
    defender_rank = defender.get("rank", 0)
    attacker_rank = attacker.get("rank", 0)
    attacker_gain = base_gain
    return adjust_rank_transfer_for_high_rank(attacker_rank, defender_rank, attacker_gain)


def adjust_rank_transfer_for_high_rank(
    attacker_rank: int, defender_rank: int, attacker_gain: int
) -> tuple[int, int]:
    if attacker_rank >= HIGH_RANK_THRESHOLD and defender_rank < LOW_RANK_CAP_THRESHOLD:
        if defender_rank <= 0:
            return 0, 0
        capped_gain = max(1, attacker_gain // 2)
        defender_loss = min(defender_rank, capped_gain)
        return capped_gain, defender_loss
    defender_loss = min(defender_rank, attacker_gain) if defender_rank > 0 else 0
    return attacker_gain, defender_loss


def calculate_rank_transfer_for_missile(
    attacker: dict, defender: dict, missile_name: str, damage: int
) -> tuple[int, int]:
    if "هسته‌ای" in missile_name:
        attacker_gain = random.randint(130, 150)
        defender_rank = defender.get("rank", 0)
        attacker_rank = attacker.get("rank", 0)
        return adjust_rank_transfer_for_high_rank(attacker_rank, defender_rank, attacker_gain)
    if "رد لاین" in missile_name:
        attacker_gain = random.randint(150, 200)
        defender_rank = defender.get("rank", 0)
        attacker_rank = attacker.get("rank", 0)
        return adjust_rank_transfer_for_high_rank(attacker_rank, defender_rank, attacker_gain)
    return calculate_rank_transfer(attacker, defender, damage)


def level_pass_reward_for_level(level: int) -> dict:
    if 1 <= level <= 5:
        return {"coins": 1000}
    if 5 < level <= 10:
        return {"khorramshahr_missiles": 10}
    if 10 < level <= 15:
        return {"chemical_missiles": 10}
    if 15 < level <= 25:
        return {"almas_missiles": 15}
    if 25 < level <= 30:
        return {"redline_missiles": 1}
    if 30 < level <= 35:
        return {"nuclear_missiles": 2}
    if 35 < level <= 40:
        return {"redline_missiles": 2}
    return {}


def apply_level_pass_reward(record: dict, reward: dict) -> None:
    for key, amount in reward.items():
        if key == "coins":
            record["coins"] = record.get("coins", 0) + amount
        elif key in record:
            record[key] = record.get(key, 0) + amount


def add_level_pass_exp(record: dict, missile_key: str | None) -> None:
    if missile_key is None:
        return
    if record.get("level_pass_level", 1) >= LEVEL_PASS_MAX_LEVEL:
        return
    gain = MISSILE_EXP_VALUES.get(missile_key, 1)
    record["level_pass_exp"] = record.get("level_pass_exp", 0) + gain
    exp_needed = max(1, record.get("level_pass_exp_needed", level_pass_exp_needed(record.get("level_pass_level", 1))))
    leveled = False
    while (
        record["level_pass_exp"] >= exp_needed
        and record.get("level_pass_level", 1) < LEVEL_PASS_MAX_LEVEL
    ):
        record["level_pass_exp"] -= exp_needed
        record["level_pass_level"] = record.get("level_pass_level", 1) + 1
        record["level_pass_exp_needed"] = level_pass_exp_needed(record["level_pass_level"])
        reward = level_pass_reward_for_level(record["level_pass_level"])
        apply_level_pass_reward(record, reward)
        leveled = True
    if leveled:
        save_user_data_store()


def level_pass_status_text(record: dict) -> str:
    level = record.get("level_pass_level", 1)
    exp = record.get("level_pass_exp", 0)
    needed = max(1, record.get("level_pass_exp_needed", LEVEL_PASS_EXP_PER_LEVEL))
    next_level = level + 1 if level < LEVEL_PASS_MAX_LEVEL else LEVEL_PASS_MAX_LEVEL
    reward = level_pass_reward_for_level(next_level) if level < LEVEL_PASS_MAX_LEVEL else {}
    reward_text = "ندارد"
    if reward:
        parts = []
        for key, amount in reward.items():
            label = key
            if key == "coins":
                label = "سکه"
            parts.append(f"{amount} {label}")
        reward_text = "، ".join(parts)
    return (
        "🚀 لول آپ پس\n"
        f"🔢 لول: {level}/{LEVEL_PASS_MAX_LEVEL}\n"
        f"📈 اکسپی: {exp}/{needed}\n"
        f"🎁 جایزه لول بعد ({next_level}): {reward_text}"
    )


def level_pass_reward_for_level(level: int) -> dict:
    if 1 <= level <= 5:
        return {"coins": 1000}
    if 5 < level <= 10:
        return {"khorramshahr_missiles": 10}
    if 10 < level <= 15:
        return {"chemical_missiles": 10}
    if 15 < level <= 25:
        return {"almas_missiles": 15}
    if 25 < level <= 30:
        return {"redline_missiles": 1}
    if 30 < level <= 35:
        return {"nuclear_missiles": 2}
    if 35 < level <= 40:
        return {"redline_missiles": 2}
    return {}


def apply_level_pass_reward(record: dict, reward: dict) -> None:
    for key, amount in reward.items():
        if key == "coins":
            record["coins"] = record.get("coins", 0) + amount
        elif key in record:
            record[key] = record.get(key, 0) + amount


def add_level_pass_exp(record: dict, missile_key: str | None) -> None:
    if missile_key is None:
        return
    if record.get("level_pass_level", 1) >= LEVEL_PASS_MAX_LEVEL:
        return
    gain = MISSILE_EXP_VALUES.get(missile_key, 1)
    record["level_pass_exp"] = record.get("level_pass_exp", 0) + gain
    exp_needed = max(1, record.get("level_pass_exp_needed", LEVEL_PASS_EXP_PER_LEVEL))
    leveled = False
    while record["level_pass_exp"] >= exp_needed and record.get("level_pass_level", 1) < LEVEL_PASS_MAX_LEVEL:
        record["level_pass_exp"] -= exp_needed
        record["level_pass_level"] = record.get("level_pass_level", 1) + 1
        record["level_pass_exp_needed"] = LEVEL_PASS_EXP_PER_LEVEL
        reward = level_pass_reward_for_level(record["level_pass_level"])
        apply_level_pass_reward(record, reward)
        leveled = True
    if leveled:
        save_user_data_store()


def missile_experience(name: str) -> int:
    if "رد لاین" in name:
        return 50
    if "هسته‌ای" in name:
        return 50
    if "شیمیایی" in name:
        return 20
    if "هایمرسونیک" in name or "خرمشهر" in name or "طوفان" in name or "الماس" in name:
        return 15
    if "بالستیک" in name or "عماد" in name or "سجیل" in name or "شهاب" in name:
        return 10
    return 5


def apply_experience(record: dict, amount: int) -> bool:
    if amount <= 0:
        return False
    starting_level = record.get("level", 1)
    record["experience"] = record.get("experience", 0) + amount
    while record["experience"] >= record["experience_needed"]:
        record["experience"] -= record["experience_needed"]
        record["level"] = record.get("level", 1) + 1
        record["experience_needed"] += 100
    return starting_level < 3 <= record.get("level", 1)


def generate_clan_code(length: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(alphabet) for _ in range(length))
        if code not in clan_data_store:
            return code


def get_clan_capacity(level: int) -> int:
    return max(1, level) * 10


def get_clan_for_user(record: dict) -> dict | None:
    clan_id = record.get("clan_id")
    if not clan_id:
        return None
    clan = clan_data_store.get(str(clan_id))
    if clan:
        clan.setdefault("tank_level", 0)
        clan.setdefault("castle_level", 0)
        clan.setdefault("cups", 0)
        clan.setdefault("sub_leaders", [])
    return clan


def user_is_clan_leader(record: dict, clan: dict | None) -> bool:
    if not clan:
        return False
    return clan.get("leader_id") == record.get("id")


def user_is_sub_leader(record: dict, clan: dict | None) -> bool:
    if not clan:
        return False
    return record.get("id") in clan.get("sub_leaders", [])


def clan_tank_bonus(record: dict) -> int:
    clan = get_clan_for_user(record)
    if not clan:
        return 0
    level = min(5, max(0, clan.get("tank_level", 0)))
    return level * 20


def clan_castle_reduction(defender: dict) -> int:
    clan = get_clan_for_user(defender)
    if not clan:
        return 0
    level = min(CLAN_CASTLE_MAX_LEVEL, max(0, clan.get("castle_level", 0)))
    if level <= 0:
        return 0
    low = level * CLAN_CASTLE_DAMAGE_MIN_PER_LEVEL
    high = level * CLAN_CASTLE_DAMAGE_MAX_PER_LEVEL
    return random.randint(low, high)


def normalize_sort_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", name or "")
    normalized = normalized.replace("ي", "ی").replace("ك", "ک")
    return normalized.casefold().strip()


def calculate_attack_damage(
    attacker: dict,
    defender: dict,
    missile_name: str,
    blocked: bool,
    missile_key: str | None = None,
    include_clan_bonus: bool = False,
) -> int:
    if blocked:
        return 0
    damage = missile_damage(missile_name, missile_key)
    if include_clan_bonus:
        damage += clan_tank_bonus(attacker)
    return damage


def pick_clan_war_opponent(current_clan_id: str) -> dict | None:
    candidates = []
    for clan_id, clan in clan_data_store.items():
        if clan_id == current_clan_id:
            continue
        members = clan.get("members", [])
        if len(members) >= CLAN_WAR_TEAM_SIZE:
            if any(get_user_record(int(member_id)).get("clan_war_id") for member_id in members):
                continue
            candidates.append(clan)
    if not candidates:
        return None
    return random.choice(candidates)


def get_active_clan_war_for_user(user_id: int) -> dict | None:
    record = get_user_record(user_id)
    war_id = record.get("clan_war_id")
    if not war_id:
        return None
    war = clan_war_sessions.get(war_id)
    if not war or war.get("completed"):
        record["clan_war_id"] = None
        record["clan_war_attacks_left"] = 0
        return None
    return war


def war_started_at(war: dict) -> datetime | None:
    started_at = war.get("started_at") or war.get("starts_at")
    if not started_at:
        return None
    try:
        return datetime.fromisoformat(started_at)
    except ValueError:
        return None


def ensure_war_started(war: dict) -> None:
    starts_at = war.get("starts_at")
    if not starts_at:
        if war.get("started_at") is None:
            war["started_at"] = datetime.now().isoformat()
        return
    try:
        starts_dt = datetime.fromisoformat(starts_at)
    except ValueError:
        return
    if war.get("started_at") is None and datetime.now() >= starts_dt:
        war["started_at"] = starts_at


def war_has_expired(war: dict) -> bool:
    started = war_started_at(war)
    if not started:
        return False
    return datetime.now() - started >= timedelta(minutes=CLAN_WAR_DURATION_MINUTES)


def remove_clan_from_queue(clan_id: str) -> None:
    global clan_war_queue
    clan_war_queue = [item for item in clan_war_queue if item.get("clan_id") != clan_id]


async def queue_clan_war_request(
    context: ContextTypes.DEFAULT_TYPE,
    clan: dict,
    team: list[int],
    reply_target,
) -> str:
    remove_clan_from_queue(str(clan.get("id")))
    now = datetime.now()
    # purge invalid queue entries
    valid_queue = []
    for item in clan_war_queue:
        opp = clan_data_store.get(str(item.get("clan_id")))
        if opp and len(opp.get("members", [])) >= CLAN_WAR_TEAM_SIZE:
            valid_queue.append(item)
    clan_war_queue.clear()
    clan_war_queue.extend(valid_queue)
    opponent_entry = None
    for item in clan_war_queue:
        if item.get("clan_id") != str(clan.get("id")):
            opponent_entry = item
            break
    if opponent_entry is None:
        clan_war_queue.append(
            {
                "clan_id": str(clan.get("id")),
                "team": team,
                "requested_at": now.isoformat(),
            }
        )
        return "⏳ کلن شما در صف وار قرار گرفت. منتظر حریف باشید."
    clan_war_queue.remove(opponent_entry)
    opponent_clan = clan_data_store.get(str(opponent_entry.get("clan_id")))
    if not opponent_clan:
        return "❌ کلن حریف یافت نشد. دوباره تلاش کنید."
    opponent_team = opponent_entry.get("team", [])
    if len(opponent_team) != CLAN_WAR_TEAM_SIZE:
        return "❌ اعضای حریف کامل نبود."
    starts_at = now + timedelta(minutes=CLAN_WAR_PREP_MINUTES)
    ok, war_id = await start_clan_war_session(
        context,
        clan,
        opponent_clan,
        team,
        opponent_team,
        starts_at=starts_at,
    )
    if not ok:
        return war_id
    message = (
        "✅ کلن وار زمان‌بندی شد.\n"
        f"کد وار: {war_id}\n"
        f"⏳ شروع حدود {CLAN_WAR_PREP_MINUTES} دقیقه دیگر.\n"
        f"حریف: {opponent_clan.get('name', 'نامشخص')}"
    )
    try:
        await reply_target.reply_text(message)
    except Exception:
        pass
    return "کلن وار در انتظار شروع است."


def maybe_reward_inviter(record: dict) -> bool:
    inviter_id = record.get("inviter_id")
    if not inviter_id or record.get("inviter_rewarded"):
        return False
    if inviter_id == record.get("id"):
        record["inviter_rewarded"] = True
        return False
    inviter_record = get_user_record(int(inviter_id))
    inviter_record["gems"] += 3
    record["inviter_rewarded"] = True
    return True


def resolve_defense(defender: dict, missile_name: str) -> tuple[bool, str]:
    normalized = normalize_missile_name(missile_name)
    if "رد لاین" in normalized or "ردلاین" in normalized:
        return False, "🚀 پدافند روی رد لاین اثر ندارد."
    if "هسته‌ای" in normalized:
        return False, "☢️ پدافند روی موشک هسته‌ای اثر ندارد."
    active_defense = defender.get("active_defense")
    active_item = next((item for item in DEFENSE_ITEMS if item["key"] == active_defense), None)
    if not active_item:
        return False, "⚠️ مدافع پدافند فعال نداشت..."
    if defender.get(active_item["key"], 0) <= 0:
        defender["active_defense"] = None
        return False, "⚠️ مدافع پدافندی نداشت..."
    chance = active_item["chance"]
    if (
        "هایمرسونیک" in missile_name
        or "خرمشهر" in missile_name
        or "طوفان" in missile_name
        or "الماس" in missile_name
    ):
        chance = max(1, chance // 2)
    if random.randint(1, 100) <= chance:
        defender[active_item["key"]] -= 1
        if defender.get(active_item["key"], 0) <= 0:
            defender["active_defense"] = None
        return True, f"🛡️ موشک توسط پدافند {active_item['label']} مهار شد."
    defender[active_item["key"]] -= 1
    if defender.get(active_item["key"], 0) <= 0:
        defender["active_defense"] = None
    return False, "⚠️ پدافند نتوانست موشک را مهار کند."


def is_shield_active(record: dict) -> bool:
    shield_until = record.get("shield_until")
    if not shield_until:
        record["shield_active"] = False
        return False
    try:
        until = datetime.fromisoformat(shield_until)
    except ValueError:
        record["shield_active"] = False
        record["shield_until"] = None
        save_user_data_store()
        return False
    if datetime.now() >= until:
        record["shield_active"] = False
        record["shield_until"] = None
        save_user_data_store()
        return False
    record["shield_active"] = True
    return True


def shield_remaining_text(record: dict) -> str:
    shield_until = record.get("shield_until")
    if not shield_until:
        return ""
    try:
        until = datetime.fromisoformat(shield_until)
    except Exception:
        return ""
    remaining = until - datetime.now()
    minutes = max(0, int(remaining.total_seconds() // 60))
    seconds = max(0, int(remaining.total_seconds() % 60))
    return f"{minutes} دقیقه و {seconds} ثانیه"


def generate_gift_code(length: int = 8) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(length))


def normalize_gift_code(code: str) -> str:
    return re.sub(r"\s+", "", code).upper()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    reset_clan_prompt_flags(context)
    if await ensure_required_memberships(update, context):
        return
    if await reject_if_not_private(update):
        return
    if update.effective_user is not None:
        record = get_user_record(update.effective_user.id)
        if context.args:
            token = context.args[0]
            if (
                token.startswith("ref_")
                and record.get("inviter_id") is None
                and not record.get("first_start_completed")
            ):
                inviter_text = token.replace("ref_", "", 1)
                if inviter_text.isdigit():
                    inviter_id = int(inviter_text)
                    if inviter_id != update.effective_user.id:
                        record["inviter_id"] = inviter_id
                        record["inviter_rewarded"] = False
                        rewarded = maybe_reward_inviter(record)
                        save_user_data_store()
                        if rewarded:
                            await notify_primary_admin_of_action(
                                context,
                                inviter_id,
                                (
                                    "📢 دعوت موفق ثبت شد.\n"
                                    f"دعوت‌کننده: {inviter_id}\n"
                                    f"کاربر جدید: {record.get('id')}"
                                ),
                            )
                            await notify_user(
                                context,
                                inviter_id,
                                (
                                    "🎉 دعوت موفق!\n"
                                    f"کاربر {display_name_with_sticker(record, 'کاربر')} با لینک شما وارد شد.\n"
                                    "3 جم به شما داده شد."
                                ),
                            )
        update_user_profile(
            update.effective_user.id,
            update.effective_user.first_name or "کاربر",
        )
        record["first_start_completed"] = True
        save_user_data_store()
    reply_markup = main_menu_markup(update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(
        "سلام! خوش اومدی 👋\n"
        "برای تست بگو /start رو زدی و بات آماده‌ست.",
        reply_markup=reply_markup,
    )


def build_invite_link(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    username = getattr(context.bot, "username", None)
    if not username:
        return ""
    return f"https://t.me/{username}?start=ref_{user_id}"


async def invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    link = build_invite_link(context, update.effective_user.id)
    if not link:
        await update.message.reply_text("❌ نام کاربری ربات تنظیم نشده است.")
        return
    await update.message.reply_text(
        "🔗 لینک دعوت شما:\n"
        f"{link}\n\n"
        "با رسیدن دعوت‌شده به لول 3، 3 جم دریافت می‌کنید.",
    )


def main_menu_markup(user_id: int | None = None) -> ReplyKeyboardMarkup:
    keyboard = [
        ["حمله جهانی 🌐"],
        ["رنکینگ 🏆", "دارایی 📦", "فروشگاه 🛒"],
        ["گردونه 🎡", "جایزه روزانه 🎁", "معدن طلا ⛏️"],
        ["معدن جم 💎", "تبادل سکه 💸", "کلن 👥"],
        ["راهنما ❓", "پدافند ها 🛡️"],
        ["پشتیبانی 📞", "سولارپس ⭐", "خرید آیتم 💳"],
        ["شخصی سازی 🎨"],
    ]
    if user_id is not None and is_admin(user_id):
        keyboard.append(["پنل ادمین 🛠️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def starpass_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["دریافت جوایز 🎁", "خرید سولارپس 🛒"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def starpass_purchase_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                f"خرید سولارپس ({STARPASS_COST} جم) 💎",
                callback_data="starpass_purchase_confirm",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def wheel_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [["رد لاین 🔴"], ["بازگشت به منوی اصلی ↩️"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def shop_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["افزایش موجودی 🔁"],
        ["پک های ویژه 💥", "پک های جم 💎"],
        ["پک های سکه 💰", "خرید لول ⏫"],
        ["باندل ها 🥷"],
        ["خروج از خرید ◀️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def pack_choice_markup(pack_labels: list[str]) -> ReplyKeyboardMarkup:
    rows = []
    row = []
    for label in pack_labels:
        row.append(label)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(["بازگشت به دسته ها ◀️"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def coin_pack_choice_markup() -> ReplyKeyboardMarkup:
    labels = pack_labels(COIN_PACKS, "coins", "سکه")
    return pack_choice_markup(labels)


def store_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["موشک 🚀"],
        ["پدافند 🛡️"],
        ["سپر 🛡️"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def shield_shop_markup() -> ReplyKeyboardMarkup:
    keyboard = [[f"💎 {pack['gems']} - {pack['label']}"] for pack in SHIELD_PACKS]
    keyboard.append(["بازگشت به منوی فروشگاه ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def coin_transfer_markup() -> ReplyKeyboardMarkup:
    keyboard = [["بازگشت به منوی اصلی ↩️"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def gold_mine_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["جمع‌آوری سکه 💰", "ارتقای معدن ⛏️"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def gem_mine_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["جمع‌آوری جم 💎"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def ranking_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("صفحه قبلی ⬅️", callback_data="ranking_prev"),
            InlineKeyboardButton("صفحه بعدی ➡️", callback_data="ranking_next"),
        ],
        [InlineKeyboardButton("کلن ها 👥", callback_data="ranking_clans")],
    ]
    return InlineKeyboardMarkup(keyboard)


def revenge_inline_markup(attacker_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("انتقام ⚔️", callback_data=f"revenge_{attacker_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_attack_report(
    attacker: dict,
    defender: dict,
    missile_name: str,
    damage: int,
    attacker_coin_delta: int,
    defender_coin_delta: int,
    attacker_rank_delta: int,
    defender_rank_delta: int,
    timestamp: datetime,
    defense_note: str,
) -> str:
    attacker_name = display_name_with_sticker(attacker, "کاربر")
    defender_name = display_name_with_sticker(defender, "کاربر")
    attacker_league = attacker.get("league", "🎗 تازه‌کار")
    defender_league = defender.get("league", "🎗 تازه‌کار")
    attacker_title_line = format_title_quote(attacker)
    defender_title_line = format_title_quote(defender)
    return (
        "🚀💥 حمله موفق! 💥🚀\n\n"
        f"👤 مهاجم: {attacker_name} ({attacker_league}){attacker_title_line}\n"
        f"🛡️ مدافع: {defender_name} ({defender_league}){defender_title_line}\n\n"
        f"نوع موشک: {missile_name}🚀\n"
        f"دمیج واردشده: {damage} 💢\n\n"
        f"{defense_note}\n\n"
        f"💰 سکه‌ها: 🟢 +{attacker_coin_delta} برای مهاجم | 🔴 -{defender_coin_delta} برای مدافع\n"
        f"🏆 رنک:⬆️ +{attacker_rank_delta} برای مهاجم | ➖ -{defender_rank_delta} برای مدافع\n\n"
        f"⏰ تاریخ و ساعت: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )


def format_defense_report(
    attacker: dict,
    defender: dict,
    missile_name: str,
    damage: int,
    defender_coin_loss: int,
    attacker_rank_delta: int,
    defender_rank_delta: int,
    timestamp: datetime,
) -> str:
    attacker_name = display_name_with_sticker(attacker, "کاربر")
    attacker_title_line = format_title_quote(attacker)
    return (
        "❌ به شما حمله شد!\n\n"
        f"⚔ حمله‌کننده: {attacker_name}{attacker_title_line}\n"
        f"🆔 آیدی حمله‌کننده: {attacker.get('id', 'نامشخص')}\n"
        f"🚀/✈️ سلاح: {missile_name}\n"
        f"💢 دمیج: {damage}\n"
        f"💰 سکه از دست رفته: {defender_coin_loss}\n"
        f"🏆 رنک: ⬆️ +{attacker_rank_delta} برای مهاجم | ➖ -{defender_rank_delta} برای مدافع\n"
        f"⏰ {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )


def format_clan_war_attack_report(
    attacker: dict,
    clan_name: str,
    missile_name: str,
    damage: int,
    attacks_left: int,
    timestamp: datetime,
) -> str:
    attacker_name = display_name_with_sticker(attacker, "کاربر")
    attacker_title_line = format_title_quote(attacker)
    return (
        "⚔️ حمله کلن وار\n\n"
        f"👤 مهاجم: {attacker_name}{attacker_title_line}\n"
        f"🏰 کلن: {clan_name}\n"
        f"🚀 موشک: {missile_name}\n"
        f"💢 دمیج: {damage}\n"
        f"🔁 حمله باقی‌مانده: {attacks_left}\n"
        f"⏰ {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )


def missiles_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["کروز 🚀", "بالستیک 🚀"],
        ["هایپرسونیک 🚀", "شیمیایی 🚀"],
        ["هسته‌ای 🚀"],
        ["بازگشت به منوی فروشگاه ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def clan_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["جستجو کلن 🔍", "ساخت کلن 🏗️"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def clan_panel_markup(is_manager: bool, is_leader: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [["اعضا 👥", "ترک کلن 🚪"]]
    if is_leader:
        keyboard.append(["درخواست‌ها 📩", "ارتقا کلن ⬆️"])
        keyboard.append(["تنظیم تگ 🏷️", "پاک کردن تگ ❌"])
        keyboard.append(["تغییر لیدر 👑", "ساب لیدر 👥"])
        keyboard.append(["تانک کلن 🪖"])
        keyboard.append(["قلعه کلن 🏰"])
    if is_manager:
        keyboard.append(["کلن وار ⚔️"])
    keyboard.append(["بازگشت به منوی اصلی ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def clan_war_menu_markup(is_leader: bool, has_active_war: bool) -> ReplyKeyboardMarkup:
    keyboard = []
    if has_active_war:
        keyboard.append(["حمله در وار ⚔️"])
    elif is_leader:
        keyboard.append(["شروع کلن وار ⚔️"])
    keyboard.append(["بازگشت به منوی کلن ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def clan_war_selection_markup(
    member_ids: list[int], selected: set[int]
) -> InlineKeyboardMarkup:
    buttons = []
    for member_id in member_ids:
        record = get_user_record(int(member_id))
        name = display_name_with_sticker(record, "کاربر")
        prefix = "✅" if member_id in selected else "⬜️"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{prefix} {name}",
                    callback_data=f"clan_war_pick_{member_id}",
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                "شروع وار ✅",
                callback_data="clan_war_confirm",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def clan_members_markup(is_leader: bool) -> ReplyKeyboardMarkup:
    keyboard = []
    if is_leader:
        keyboard.append(["حذف عضو ➖"])
    keyboard.append(["بازگشت به منوی کلن ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def clan_requests_markup(requests: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for req in requests:
        user_id = req.get("user_id")
        name = req.get("name", "کاربر")
        buttons.append(
            [
                InlineKeyboardButton(
                    f"✅ {name}",
                    callback_data=f"clan_accept_{user_id}",
                ),
                InlineKeyboardButton(
                    "❌ رد",
                    callback_data=f"clan_reject_{user_id}",
                ),
            ]
        )
    return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([])


def customization_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [
        ["افکت های حمله ✨", "تایتل ها 🎗️"],
        ["چت استیکر ⭐"],
        ["بازگشت به منوی اصلی ↩️"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def title_menu_markup(titles: list[str]) -> ReplyKeyboardMarkup:
    rows = []
    row = []
    for title in titles:
        row.append(title)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(["حذف تایتل ❌"])
    rows.append(["بازگشت به شخصی سازی ↩️"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def chat_sticker_menu_markup() -> ReplyKeyboardMarkup:
    keyboard = [[label] for label, _ in STARPASS_CHAT_STICKERS]
    keyboard.append(["حذف استیکر ❌"])
    keyboard.append(["بازگشت به شخصی سازی ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def defense_status_menu_markup(record: dict) -> ReplyKeyboardMarkup:
    keyboard = []
    for item in DEFENSE_ITEMS:
        if record.get(item["key"], 0) > 0:
            keyboard.append([f"فعال کردن {item['label']} 🛡️"])
    keyboard.append(["غیرفعال کردن پدافند ❌"])
    keyboard.append(["بازگشت به منوی اصلی ↩️"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def help_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("حمله 🚀", callback_data="help_attack"),
            InlineKeyboardButton("پدافند 🛡️", callback_data="help_defense"),
        ],
        [
            InlineKeyboardButton("سپر 🛡️", callback_data="help_shield"),
            InlineKeyboardButton("حمله جهانی 🌐", callback_data="help_global_attack"),
        ],
        [
            InlineKeyboardButton("انتقام 🗡️", callback_data="help_revenge"),
            InlineKeyboardButton("موشک‌ها 🧨", callback_data="help_missiles"),
        ],
        [
            InlineKeyboardButton("جنگنده‌ها ✈️", callback_data="help_fighters"),
            InlineKeyboardButton("معدن طلا ⛏️", callback_data="help_mine"),
        ],
        [
            InlineKeyboardButton("لول و تجربه 📈", callback_data="help_level"),
            InlineKeyboardButton("کلن 👥", callback_data="help_clan"),
        ],
        [
            InlineKeyboardButton("رنکینگ و لیگ‌ها 🏆", callback_data="help_ranking"),
            InlineKeyboardButton("کلن وار ⚔️", callback_data="help_clan_war"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def safe_edit_message(
    query,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    current_text = getattr(query.message, "text", None)
    current_markup = query.message.reply_markup
    if current_text == text and current_markup == reply_markup:
        return
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception:
        return


def help_menu_text() -> str:
    return (
        "📖 راهنما\n\n"
        "این یک بازی استراتژیک تلگرامی است که در آن با حمله به دیگران، "
        "دفاع از خود، جمع‌آوری منابع (سکه و جم) و رقابت در رنکینگ جهانی، "
        "به قوی‌ترین بازیکن تبدیل می‌شوید!\n\n"
        "### 🏠 منوهای اصلی:\n"
        "- 🛒 فروشگاه: خرید موشک، پدافند و سپر.\n"
        "- 📦 دارایی: مشاهده موجودی موشک‌ها، پدافندها، سکه، جم و غیره.\n"
        "- 🏆 رنکینگ: جایگاه شما و دیگران در لیست جهانی.\n"
        "- 🛡️ پدافند: مدیریت و انتخاب پدافند فعال.\n"
        "- 🌐 حمله جهانی: جستجوی حریف تصادفی و حمله.\n"
        "- 🎁 جایزه روزانه: دریافت جوایز روزانه.\n"
        "- ⛏️ معدن طلا: تولید خودکار سکه.\n"
        "- 👥 کلن: ایجاد یا پیوستن به کلن برای رقابت گروهی.\n"
        "- ⚔️ کلن وار: رقابت ۱۰ در ۱۰ بین کلن‌ها.\n\n"
        "### 💡 نکات کلی:\n"
        "- حمله فقط به کاربران واقعی انجام می‌شود (نه ربات‌ها یا گروه‌ها).\n"
        "- امکان حمله به ادمین‌های محافظت‌شده وجود ندارد.\n"
        "- ادمین‌ها می‌توانند لول، رنگ، سکه، جم و غیره را تنظیم کنند.\n"
        "- برای جزئیات هر بخش، از دکمه‌های زیر انتخاب کنید.\n\n"
        "🔻 بخش مورد نظر را انتخاب کنید:"
    )




def create_payment_request(user_id: int, amount_toman: int) -> tuple[bool, str]:
    if ZARINPAL_MERCHANT_ID == "YOUR_MERCHANT_ID":
        return False, "❌ مرچنت آیدی زرین‌پال تنظیم نشده است."
    amount_rial = amount_toman * 10
    payload = {
        "merchant_id": ZARINPAL_MERCHANT_ID,
        "amount": amount_rial,
        "callback_url": f"{ZARINPAL_CALLBACK_URL}?user_id={user_id}",
        "description": "افزایش موجودی ربات",
    }
    try:
        response = requests.post(ZARINPAL_REQUEST_URL, json=payload, timeout=15)
        data = response.json()
    except Exception:
        return False, "❌ خطا در اتصال به زرین‌پال."
    if data.get("data", {}).get("code") != 100:
        return False, "❌ خطا در ساخت لینک پرداخت."
    authority = data["data"]["authority"]
    pending_payments[authority] = {
        "user_id": user_id,
        "amount_toman": amount_toman,
        "created_at": datetime.now().isoformat(),
    }
    save_pending_payments()
    return True, f"{ZARINPAL_GATEWAY_URL}{authority}"


def redline_wheel_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("۱ بار 🎰", callback_data="wheel_redline_spin_1"),
            InlineKeyboardButton("۱۰ بار 🎰", callback_data="wheel_redline_spin_10"),
        ],
        [
            InlineKeyboardButton(
                f"{AMERICA_WHEEL_COIN_COST} سکه 💰",
                callback_data="wheel_redline_pay_coins",
            ),
            InlineKeyboardButton(
                f"{AMERICA_WHEEL_GEM_COST} جم 💎",
                callback_data="wheel_redline_pay_gems",
            ),
        ],
        [InlineKeyboardButton("لغو ❌", callback_data="wheel_redline_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def redline_wheel_text() -> str:
    rewards_lines = "\n".join(f"• {reward['label']}" for reward in REDLINE_WHEEL_REWARDS)
    return (
        "🎡 گردونه: رد لاین 🔴\n\n"
        "💰 هزینه: ۱۰۰۰ سکه یا 💎 ۵ جم\n\n"
        "🎁 آیتم‌های ممکن:\n"
        f"{rewards_lines}\n\n"
        "🔻 انتخاب کنید"
    )


async def wheel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        "🎡 گردونه‌ها:\n"
        "یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=wheel_menu_markup(),
    )


async def wheel_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    text = (update.message.text or "").strip()
    if text == "رد لاین 🔴":
        context.user_data["redline_wheel_payment"] = None
        await update.message.reply_text(
            redline_wheel_text(),
            reply_markup=redline_wheel_markup(),
        )
        return
    await update.message.reply_text(NOT_AVAILABLE_TEXT, reply_markup=wheel_menu_markup())


async def redline_wheel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context, alert=True):
        return
    if not is_private_chat(update):
        await update.callback_query.answer(
            "⛔️ این منو فقط در پیوی ربات فعال است.", show_alert=True
        )
        return
    query = update.callback_query
    await query.answer()
    if query.data == "wheel_redline_cancel":
        context.user_data["redline_wheel_payment"] = None
        await safe_edit_message(query, "بازگشت به منوی گردونه 👇")
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="گردونه‌ها:",
            reply_markup=wheel_menu_markup(),
        )
        return
    if query.data == "wheel_redline_pay_coins":
        context.user_data["redline_wheel_payment"] = "coins"
        await safe_edit_message(query, redline_wheel_text(), redline_wheel_markup())
        return
    if query.data == "wheel_redline_pay_gems":
        context.user_data["redline_wheel_payment"] = "gems"
        await safe_edit_message(query, redline_wheel_text(), redline_wheel_markup())
        return
    payment = context.user_data.get("redline_wheel_payment")
    if payment not in {"coins", "gems"}:
        await safe_edit_message(query, "اول روش پرداخت رو انتخاب کن.", redline_wheel_markup())
        return
    record = get_user_record(update.effective_user.id)
    spins = 1 if query.data == "wheel_redline_spin_1" else 10
    if payment == "coins":
        total_coins = AMERICA_WHEEL_COIN_COST * spins
        if record["coins"] < total_coins:
            await safe_edit_message(query, "❌ سکه کافی ندارید.")
            return
        record["coins"] -= total_coins
    else:
        total_gems = AMERICA_WHEEL_GEM_COST * spins
        if record["gems"] < total_gems:
            await safe_edit_message(query, "❌ جم کافی ندارید.")
            return
        record["gems"] -= total_gems
    save_user_data_store()
    weights = (
        REDLINE_WHEEL_CHANCES
        if len(REDLINE_WHEEL_CHANCES) == len(REDLINE_WHEEL_REWARDS)
        else None
    )
    rewards = random.choices(REDLINE_WHEEL_REWARDS, weights=weights, k=spins)
    for reward in rewards:
        reward_type = reward["type"]
        amount = reward["amount"]
        if reward_type == "coins":
            record["coins"] = record.get("coins", 0) + amount
        elif reward_type == "tirbar_defense":
            record["tirbar_defense"] = record.get("tirbar_defense", 0) + (amount * 10)
        elif any(reward_type == item["key"] for item in DEFENSE_ITEMS):
            record[reward_type] = record.get(reward_type, 0) + (amount * 10)
        else:
            record[reward_type] = record.get(reward_type, 0) + amount
            record["missiles"] = record.get("missiles", 0) + amount
    save_user_data_store()
    if spins == 1:
        result_text = f"🎉 نتیجه گردونه رد لاین:\n{rewards[0]['label']}"
    else:
        reward_lines = "\n".join(
            f"{index + 1}. {item['label']}" for index, item in enumerate(rewards)
        )
        result_text = "🎉 نتیجه ۱۰ بار گردونه رد لاین:\n" f"{reward_lines}"
    context.user_data["redline_wheel_payment"] = None
    await safe_edit_message(query, result_text)


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["coin_transfer_target_id"] = None
    context.user_data["awaiting_global_attack_missile"] = False
    context.user_data["awaiting_clan_create_name"] = False
    context.user_data["awaiting_clan_search_code"] = False
    context.user_data["awaiting_clan_tag"] = False
    context.user_data["awaiting_clan_remove_member"] = False
    context.user_data["awaiting_nuclear_quantity"] = False
    await update.message.reply_text(
        "بازگشت به منوی اصلی 👇",
        reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
    )


async def assets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    reset_purchase_flags(context)
    user = update.effective_user
    record = update_user_profile(user.id, user.first_name or "کاربر")
    update_league(record)
    save_user_data_store()
    shield_status = "دارد" if is_shield_active(record) else "ندارد"
    missiles_lines = format_owned_missiles(record)
    defenses_lines = format_owned_defenses(record)
    display_name = display_name_with_sticker(record, user.first_name or "کاربر")
    await update.message.reply_text(
        "🧨👤 کاربر: "
        f"{display_name}\n"
        f"🔢 آیدی عددی: {user.id}\n"
        f"📆 تاریخ عضویت: {record['join_date']}\n\n"
        f"🔼 سطح: {record['level']}\n"
        f"⭐ تجربه: {record['experience']}/{record['experience_needed']}\n"
        f"💰 سکه: {record['coins']}\n"
        f"💵 تومان: {record['toman']}\n"
        f"🏆 رنک: {record['rank']}\n"
        f"🏵 بالاترین رنک: {record['highest_rank']}\n"
        f"💎 جم: {record['gems']}\n"
        f"🏅 لیگ: {record['league']}\n\n"
        f"🛡️ سپر فعال: {shield_status}\n\n"
        "📦 دارایی:\n"
        f"{missiles_lines}\n"
        f"{defenses_lines}",
    )


def get_leaderboard() -> list[dict]:
    unique_records: dict[int | str, dict] = {}
    changed = False
    for key, player in user_data_store.items():
        pid = player.get("id")
        if pid is None:
            try:
                pid = int(key)
            except Exception:
                pid = key
        sanitized_name = sanitize_display_name(player.get("display_name"))
        if player.get("display_name") != sanitized_name:
            player["display_name"] = sanitized_name
            changed = True
        existing = unique_records.get(pid)
        if existing is None:
            unique_records[pid] = player
        else:
            existing_rank = existing.get("rank", 0)
            player_rank = player.get("rank", 0)
            if player_rank > existing_rank:
                unique_records[pid] = player
            elif player_rank == existing_rank and player.get("highest_rank", 0) > existing.get(
                "highest_rank", 0
            ):
                unique_records[pid] = player
    if changed:
        save_user_data_store()
    return sorted(
        unique_records.values(),
        key=lambda item: (
            -item.get("rank", 0),
            normalize_sort_name(item.get("display_name") or "کاربر"),
        ),
    )


def format_ranking_text(record: dict, page: int = 1) -> str:
    leaderboard = get_leaderboard()
    page_size = 10
    total_pages = max(1, (len(leaderboard) + page_size - 1) // page_size)
    safe_page = max(1, min(page, total_pages))
    start_index = (safe_page - 1) * page_size
    end_index = start_index + page_size
    top_players = leaderboard[start_index:end_index]
    lines = []
    for index, player in enumerate(top_players, start=start_index + 1):
        name = display_name_with_league(player, "کاربر")
        name = f"\u200f{name}"
        score = player.get("rank", 0)
        lines.append(f"{index}. {name} - ⭐ {score}")
    ranking_text = "\n".join(lines) if lines else "هنوز بازیکنی ثبت نشده."
    return (
        "🏆 لیست برترین بازیکن‌ها\n"
        f"امتیاز شما: {record.get('rank', 0)}\n\n"
        "🔮رنکینگ👇\n"
        f"{ranking_text}\n\n"
        f"صفحه {safe_page} از {total_pages}"
    )


def format_clan_ranking_text(page: int = 1) -> str:
    clans = list(clan_data_store.values())
    for clan in clans:
        clan.setdefault("cups", 0)
    def sort_key(item: dict) -> tuple[int, str]:
        name = item.get("name") or "کلن"
        return (-item.get("cups", 0), normalize_sort_name(name))
    leaderboard = sorted(clans, key=sort_key)
    page_size = 10
    total_pages = max(1, (len(leaderboard) + page_size - 1) // page_size)
    safe_page = max(1, min(page, total_pages))
    start_index = (safe_page - 1) * page_size
    end_index = start_index + page_size
    top_clans = leaderboard[start_index:end_index]
    lines = []
    for index, clan in enumerate(top_clans, start=start_index + 1):
        name = clan.get("name", "نامشخص")
        cups = clan.get("cups", 0)
        lines.append(f"{index}. {name} - 🏆 {cups}")
    ranking_text = "\n".join(lines) if lines else "هنوز کلنی ثبت نشده."
    return (
        "🏆 لیست برترین کلن‌ها\n\n"
        "🔮رنکینگ👇\n"
        f"{ranking_text}\n\n"
        f"صفحه {safe_page} از {total_pages}"
    )


async def ranking_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    context.user_data["ranking_page"] = 1
    context.user_data["ranking_mode"] = "players"
    record = update_user_profile(
        update.effective_user.id,
        update.effective_user.first_name or "کاربر",
    )
    update_league(record)
    save_user_data_store()
    await update.message.reply_text(
        format_ranking_text(record, context.user_data["ranking_page"]),
        reply_markup=ranking_menu_markup(),
    )


async def ranking_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context, alert=True):
        return
    if not is_private_chat(update):
        await update.callback_query.answer(
            "⛔️ این منو فقط در پیوی ربات فعال است.", show_alert=True
        )
        return
    query = update.callback_query
    await query.answer()
    record = update_user_profile(
        update.effective_user.id,
        update.effective_user.first_name or "کاربر",
    )
    update_league(record)
    save_user_data_store()
    page = context.user_data.get("ranking_page", 1)
    mode = context.user_data.get("ranking_mode", "players")
    if query.data == "ranking_prev":
        page = max(1, page - 1)
        context.user_data["ranking_page"] = page
        await safe_edit_message(
            query,
            format_clan_ranking_text(page) if mode == "clans" else format_ranking_text(record, page),
            reply_markup=ranking_menu_markup(),
        )
        return
    if query.data == "ranking_clans":
        context.user_data["ranking_page"] = 1
        context.user_data["ranking_mode"] = "clans"
        await safe_edit_message(
            query,
            format_clan_ranking_text(1),
            reply_markup=ranking_menu_markup(),
        )
        return
    if query.data == "ranking_next":
        page = page + 1
        context.user_data["ranking_page"] = page
        await safe_edit_message(
            query,
            format_clan_ranking_text(page) if mode == "clans" else format_ranking_text(record, page),
            reply_markup=ranking_menu_markup(),
        )
        return
    await safe_edit_message(
        query,
        NOT_AVAILABLE_TEXT,
        reply_markup=ranking_menu_markup(),
    )


async def rank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    parts = (update.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("فرمت: /rank_info <شماره رتبه> (مثلاً /rank_info 1)")
        return
    try:
        position = int(parts[1])
    except ValueError:
        await update.message.reply_text("شماره رتبه باید عدد باشد.")
        return
    if position <= 0:
        await update.message.reply_text("شماره رتبه باید بزرگ‌تر از صفر باشد.")
        return
    leaderboard = get_leaderboard()
    if not leaderboard:
        await update.message.reply_text("رنکینگ خالی است.")
        return
    if position > len(leaderboard):
        await update.message.reply_text("این رتبه در لیست وجود ندارد.")
        return
    player = leaderboard[position - 1]
    name = display_name_with_sticker(player, "کاربر")
    league = player.get("league", "🎗 تازه‌کار")
    await update.message.reply_text(
        "ℹ️ جزئیات بازیکن رنکینگ\n\n"
        f"🏅 رتبه: {position}\n"
        f"👤 نام: \u200f{name}\n"
        f"🆔 آیدی: {player.get('id', 'نامشخص')}\n"
        f"🏆 رنک: {player.get('rank', 0)} (بالاترین: {player.get('highest_rank', 0)})\n"
        f"🔼 لول: {player.get('level', 1)} | لیگ: {league}\n"
        f"💰 سکه: {player.get('coins', 0)} | 💎 جم: {player.get('gems', 0)}",
        reply_markup=ranking_menu_markup(),
    )


async def clan_info_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if len(context.args) < 1:
        await update.message.reply_text("فرمت: /clan_info <clan_id>")
        return
    clan_id = context.args[0].upper()
    clan = clan_data_store.get(clan_id)
    if not clan:
        await update.message.reply_text("❌ کلنی با این آیدی پیدا نشد.")
        return
    members = clan.get("members", [])
    subs = clan.get("sub_leaders") or []
    await update.message.reply_text(
        "ℹ️ اطلاعات کلن\n"
        f"نام: {clan.get('name', '---')}\n"
        f"کد/آیدی: {clan.get('id') or clan.get('code')}\n"
        f"تگ: {clan.get('tag') or 'ندارد'}\n"
        f"لیدر: {clan.get('leader_id')}\n"
        f"ساب‌لیدرها: {', '.join(map(str, subs)) if subs else 'ندارد'}\n"
        f"اعضا: {len(members)}\n"
        f"کاپ‌ها: {clan.get('cups', 0)}"
    )


async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_support_message"] = True
    await update.message.reply_text("✉️ پیامت رو بفرست تا به پشتیبانی ارسال بشه.")


async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        help_menu_text(),
        reply_markup=help_menu_markup(),
    )


async def help_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None:
        return
    if await reject_if_banned(update, context, alert=True):
        return
    await update.callback_query.answer()
    help_texts = {
        "help_attack": (
            "🚀 راهنمای حمله\n\n"
            "• برای حمله در گپ روی پیام طرف مقابل رپلای بزنید و بنویسید:\n"
            "حمله <نام موشک>\n"
            "• برای حمله جهانی از منوی حمله جهانی استفاده کنید.\n"
            "• برای انتقام از دکمه انتقام در پیام دفاعی استفاده کنید."
        ),
        "help_global_attack": (
            "🌐 راهنمای حمله جهانی\n\n"
            "1) از منوی اصلی وارد حمله جهانی شوید.\n"
            "2) حریف نمایش داده می‌شود.\n"
            "3) با دکمه «حمله» وارد مرحله انتخاب موشک شوید.\n"
            "4) نام موشک را ارسال کنید تا نتیجه نمایش داده شود."
        ),
        "help_revenge": (
            "⚔️ راهنمای انتقام\n\n"
            "وقتی به شما حمله شود، در پیام دفاعی دکمه «انتقام» نمایش داده می‌شود.\n"
            "با زدن دکمه، نام موشک را ارسال کنید تا انتقام ثبت شود."
        ),
        "help_clan": (
            "👥 راهنمای کلن\n\n"
            "• با پرداخت ۳۰۰۰ سکه کلن بسازید.\n"
            "• با وارد کردن کد کلن درخواست عضویت بدهید.\n"
            "• لیدر می‌تواند اعضا را مدیریت و کلن را ارتقا دهد."
        ),
        "help_clan_war": (
            "⚔️ راهنمای کلن وار\n\n"
            "• فقط لیدر می‌تواند وار را شروع کند.\n"
            f"• هر وار با {CLAN_WAR_TEAM_SIZE} نفر از هر کلن شروع می‌شود.\n"
            f"• هر نفر {CLAN_WAR_ATTACKS_PER_USER} حمله دارد.\n"
            "• برای حمله از منوی کلن وار در پیوی استفاده کنید.\n"
            "• برنده بر اساس بیشترین دمیج کلن تعیین می‌شود."
        ),
        "help_defense": "🛡️ راهنمای پدافند\n\nپدافند فعال را از منوی پدافند انتخاب کنید.",
        "help_shield": (
            "🛡️ راهنمای سپر\n\n"
            "با خرید سپر از فروشگاه، تا زمان پایان سپر کسی نمی‌تواند به شما حمله کند."
        ),
        "help_missiles": "🧨 راهنمای موشک‌ها\n\nاز فروشگاه موشک بخرید و در حملات استفاده کنید.",
        "help_level": "📈 لول و تجربه\n\nبا حمله و فعالیت، تجربه می‌گیرید و لول بالا می‌رود.",
        "help_ranking": "🏆 رنکینگ\n\nجایگاه شما و دیگر بازیکن‌ها در لیست جهانی نمایش داده می‌شود.",
        "help_fighters": "✈️ جنگنده‌ها\n\nدر صورت فعال بودن، از فروشگاه تهیه کنید.",
        "help_mine": "⛏️ معدن طلا\n\nبا ارتقا معدن، سکه بیشتری تولید کنید.",
    }
    text = help_texts.get(update.callback_query.data, NOT_AVAILABLE_TEXT)
    await safe_edit_message(
        update.callback_query,
        text,
        reply_markup=help_menu_markup(),
    )


async def topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    await update.message.reply_text(
        "💳 افزایش موجودی\n"
        f"💼 موجودی شما: {record['toman']} تومان\n\n"
        "برای شارژ، مبلغ را به شماره کارت زیر واریز کنید و سپس عکس رسید را ارسال کنید:\n"
        f"💳 شماره کارت: {PAYMENT_CARD_NUMBER}\n"
        f"👤 به نام: {PAYMENT_CARD_OWNER}\n\n"
        "بعد از واریز، از منوی زیر رسید را ارسال کنید.",
        reply_markup=ReplyKeyboardMarkup(
            [["ارسال رسید 🧾"], ["بازگشت به منوی اصلی ↩️"]],
            resize_keyboard=True,
        ),
    )


async def topup_receipt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    context.user_data["awaiting_topup_receipt"] = True
    await update.message.reply_text(
        "🧾 لطفاً عکس یا فایل رسید پرداخت را ارسال کنید.",
        reply_markup=ReplyKeyboardMarkup([["بازگشت به منوی اصلی ↩️"]], resize_keyboard=True),
    )


async def handle_topup_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_topup_receipt"):
        return
    if await reject_if_not_private(update):
        return
    user = update.effective_user
    context.user_data["awaiting_topup_receipt"] = False
    admin_id = PRIMARY_ADMIN_ID or SUPPORT_ADMIN_ID or next(iter(ADMIN_IDS), None)
    if admin_id is None:
        await update.message.reply_text("❌ ادمین برای بررسی یافت نشد.")
        return
    await context.bot.forward_message(
        chat_id=admin_id,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )
    await context.bot.send_message(
        chat_id=admin_id,
        text=(
            "🧾 رسید شارژ جدید\n"
            f"👤 کاربر: {user.first_name or 'کاربر'}\n"
            f"🆔 آیدی: {user.id}"
        ),
    )
    await update.message.reply_text("✅ رسید شما ثبت شد. بعد از بررسی موجودی شارژ می‌شود.")


async def handle_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_support_message"):
        return
    context.user_data["awaiting_support_message"] = False
    user = update.effective_user
    message_text = update.message.text or ""
    admin_id = SUPPORT_ADMIN_ID or next(iter(ADMIN_IDS), None)
    if admin_id is None or admin_id == 0:
        await update.message.reply_text("❌ آیدی پشتیبانی تنظیم نشده است.")
        return
    await context.bot.forward_message(
        chat_id=admin_id,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )
    await context.bot.send_message(
        chat_id=admin_id,
        text=(
            "📨 پیام جدید پشتیبانی\n"
            f"👤 کاربر: {user.first_name or 'کاربر'}\n"
            f"🆔 آیدی: {user.id}\n"
            f"💬 پیام: {message_text}"
        ),
    )
    await update.message.reply_text("✅ پیامت به پشتیبانی ارسال شد.")


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_private_chat(update):
        return
    if await reject_if_banned(update, context):
        return
    if update.message.text and update.message.text.startswith("/"):
        reset_clan_prompt_flags(context)
    if await ensure_required_memberships(update, context):
        return
    if context.user_data.get("awaiting_support_message"):
        await handle_support_message(update, context)
        return
    if context.user_data.get("awaiting_revenge_attack"):
        await handle_revenge_attack(update, context)
        return
    if context.user_data.get("awaiting_global_attack_missile"):
        await handle_global_attack_missile(update, context)
        return
    if context.user_data.get("awaiting_clan_war_attack"):
        await handle_clan_war_attack(update, context)
        return
    if context.user_data.get("awaiting_topup_receipt"):
        await handle_topup_receipt(update, context)
        return
    if context.user_data.get("awaiting_atlas_quantity"):
        await handle_atlas_quantity(update, context)
        return
    if context.user_data.get("awaiting_generic_missile_quantity"):
        await handle_generic_missile_quantity(update, context)
        return
    if context.user_data.get("awaiting_khorramshahr_quantity"):
        await handle_khorramshahr_quantity(update, context)
        return
    if context.user_data.get("awaiting_emad_quantity"):
        await handle_emad_quantity(update, context)
        return
    if context.user_data.get("awaiting_tirbar_quantity"):
        await handle_tirbar_quantity(update, context)
        return
    if context.user_data.get("awaiting_defense_quantity"):
        await handle_defense_quantity(update, context)
        return
    if context.user_data.get("awaiting_chemical_quantity"):
        await handle_chemical_quantity(update, context)
        return
    if context.user_data.get("awaiting_nuclear_quantity"):
        await handle_nuclear_quantity(update, context)
        return
    if context.user_data.get("awaiting_pack_category"):
        await handle_pack_purchase(update, context)
        return
    if context.user_data.get("awaiting_clan_create_name"):
        await handle_clan_create(update, context)
        return
    if context.user_data.get("awaiting_clan_search_code"):
        await handle_clan_search(update, context)
        return
    if context.user_data.get("awaiting_clan_tag"):
        await handle_clan_tag(update, context)
        return
    if context.user_data.get("awaiting_clan_remove_member"):
        await handle_clan_remove_member(update, context)
        return
    if context.user_data.get("awaiting_clan_leader_change"):
        await handle_clan_leader_change(update, context)
        return
    if context.user_data.get("awaiting_clan_sub_leader"):
        await handle_clan_sub_leader(update, context)
        return
    if context.user_data.get("awaiting_title_choice"):
        await handle_title_choice(update, context)
        return
    message_text = (update.message.text or "").strip()
    if message_text == ADMIN_ACTIVATION_CODE:
        ADMIN_IDS.add(update.effective_user.id)
        await update.message.reply_text("✅ شما ادمین شدید.")
        return
    if message_text:
        code = normalize_gift_code(message_text)
        if code in gift_codes:
            await redeem_gift_code_for_user(update, context, code)
            return
    if context.user_data.get("awaiting_coin_transfer_target") or context.user_data.get(
        "awaiting_coin_transfer_amount"
    ):
        await handle_coin_transfer_input(update, context)


def reset_daily_transfer_if_needed(record: dict, today: str) -> None:
    if record.get("last_coin_transfer_date") != today:
        record["daily_coin_transfer"] = 0
        record["last_coin_transfer_date"] = today


def reset_daily_boxes_if_needed(record: dict, today: str) -> None:
    if record.get("last_box_open_date") != today:
        record["daily_boxes_opened"] = 0
        record["last_box_open_date"] = today


def reset_daily_attack_limits_if_needed(record: dict, today: str) -> None:
    if record.get("last_attack_day") != today:
        record["daily_attacks_done"] = 0
        record["daily_attacks_received"] = 0
        record["last_attack_day"] = today


def reset_daily_duel_limits_if_needed(record: dict, today: str) -> None:
    if record.get("last_duel_day") != today:
        record["daily_duels_started"] = 0
        record["last_duel_day"] = today


def is_crystal_league(record: dict) -> bool:
    return record.get("league") == CRYSTAL_LEAGUE_NAME


def can_crystal_attack_today(attacker: dict, defender: dict, today: str) -> tuple[bool, str | None]:
    reset_daily_attack_limits_if_needed(attacker, today)
    reset_daily_attack_limits_if_needed(defender, today)
    if is_crystal_league(attacker) and attacker.get("daily_attacks_done", 0) >= CRYSTAL_DAILY_ATTACK_LIMIT:
        return False, "❌ سهمیه حمله روزانه لیگ کریستال شما تمام شده است."
    if is_crystal_league(defender) and defender.get("daily_attacks_received", 0) >= CRYSTAL_DAILY_ATTACK_LIMIT:
        return False, "❌ سهمیه دریافت حمله روزانه این بازیکن در لیگ کریستال تمام شده است."
    return True, None


def apply_crystal_attack_limits(attacker: dict, defender: dict) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    reset_daily_attack_limits_if_needed(attacker, today)
    reset_daily_attack_limits_if_needed(defender, today)
    if is_crystal_league(attacker):
        attacker["daily_attacks_done"] = attacker.get("daily_attacks_done", 0) + 1
    if is_crystal_league(defender):
        defender["daily_attacks_received"] = defender.get("daily_attacks_received", 0) + 1


def duel_key(chat_id: int, user_a: int, user_b: int) -> str:
    left, right = sorted([user_a, user_b])
    return f"{chat_id}:{left}:{right}"


def duel_request_key(chat_id: int, user_a: int, user_b: int) -> str:
    left, right = sorted([user_a, user_b])
    return f"{chat_id}:{left}:{right}"


def user_in_active_duel(user_id: int) -> bool:
    now = datetime.now()
    for duel in duel_sessions.values():
        if duel["ends_at"] <= now:
            continue
        if user_id in duel["participants"]:
            return True
    return False


def get_duel_between(chat_id: int, user_a: int, user_b: int) -> dict | None:
    key = duel_key(chat_id, user_a, user_b)
    duel = duel_sessions.get(key)
    if duel and duel["ends_at"] > datetime.now():
        return duel
    return None


def is_duel_attack_allowed(chat_id: int, attacker_id: int, defender_id: int) -> bool:
    if not user_in_active_duel(attacker_id) and not user_in_active_duel(defender_id):
        return True
    duel = get_duel_between(chat_id, attacker_id, defender_id)
    return duel is not None


def add_duel_damage(chat_id: int, attacker_id: int, defender_id: int, damage: int) -> None:
    duel = get_duel_between(chat_id, attacker_id, defender_id)
    if duel is None:
        return
    duel["damage"][attacker_id] = duel["damage"].get(attacker_id, 0) + damage


def get_duel_request(chat_id: int, user_a: int, user_b: int) -> dict | None:
    key = duel_request_key(chat_id, user_a, user_b)
    request = duel_requests.get(key)
    if request and request["expires_at"] > datetime.now():
        return request
    duel_requests.pop(key, None)
    return None


def clear_duel_request(chat_id: int, user_a: int, user_b: int) -> None:
    key = duel_request_key(chat_id, user_a, user_b)
    duel_requests.pop(key, None)


def pick_loot_box_reward() -> tuple[str, str, int]:
    reward = random.choice(LOOT_BOX_REWARDS)
    amount = random.randint(reward["min"], reward["max"])
    return reward["type"], reward["label"], amount


def apply_loot_box_reward(record: dict, reward_type: str, amount: int) -> None:
    if reward_type == "coins":
        record["coins"] = record.get("coins", 0) + amount
        return
    record[reward_type] = record.get(reward_type, 0) + amount
    record["missiles"] = record.get("missiles", 0) + amount


def update_gold_mine_storage(record: dict, now: datetime) -> None:
    level = max(1, record.get("gold_mine_level", 1))
    hourly_rate = GOLD_MINE_BASE_RATE * level
    max_capacity = hourly_rate * GOLD_MINE_MAX_HOURS
    last_collect = record.get("gold_mine_last_collect")
    if not last_collect:
        record["gold_mine_last_collect"] = now.isoformat()
        return
    last_time = datetime.fromisoformat(last_collect)
    elapsed_hours = max(0, (now - last_time).total_seconds() / 3600)
    accrued = int(elapsed_hours * hourly_rate)
    current = record.get("gold_mine_stored", 0)
    new_total = min(current + accrued, max_capacity)
    if new_total != current:
        record["gold_mine_stored"] = new_total
        record["gold_mine_last_collect"] = now.isoformat()


def gold_mine_upgrade_cost(level: int) -> int:
    return 1000 * level


def gem_mine_time_remaining(record: dict, now: datetime) -> timedelta:
    last_collect = record.get("gem_mine_last_collect")
    if not last_collect:
        return timedelta(0)
    try:
        last_time = datetime.fromisoformat(last_collect)
    except ValueError:
        return timedelta(0)
    elapsed = now - last_time
    remaining = GEM_MINE_COOLDOWN - elapsed
    return remaining if remaining > timedelta(0) else timedelta(0)


def parse_positive_int(value: str) -> int | None:
    cleaned = re.sub(r"[^\d]", "", value)
    if not cleaned:
        return None
    amount = int(cleaned)
    return amount if amount > 0 else None


def atlas_unit_price(level: int) -> int:
    return ATLAS_BASE_PRICE


def atlas_total_cost(start_level: int, quantity: int) -> int:
    if quantity <= 0:
        return 0
    first_price = atlas_unit_price(start_level)
    return int(quantity * (2 * first_price + (quantity - 1) * ATLAS_PRICE_STEP) / 2)


def atlas_max_buy(coins: int, start_level: int) -> int:
    total = 0
    level = start_level
    while True:
        price = atlas_unit_price(level)
        if total + price > coins:
            break
        total += price
        level += 1
    return level - start_level


GENERIC_MISSILE_SHOP = {
    "قدر": {"key": "qadr_missiles", "price": QADR_PRICE, "level": 1},
    "خیبرشکن": {"key": "kheibar_missiles", "price": KHEIBAR_PRICE, "level": 6},
    "سجیل": {"key": "sajjil_missiles", "price": SAJJIL_PRICE, "level": 8},
    "شهاب": {"key": "shahab_missiles", "price": SHAHAB_PRICE, "level": 10},
    "طوفان": {"key": "tufan_missiles", "price": TUFAN_PRICE, "level": 13},
    "الماس": {"key": "almas_missiles", "price": ALMAS_PRICE, "level": 15},
}


async def gold_mine_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    now = datetime.now()
    update_gold_mine_storage(record, now)
    save_user_data_store()
    level = max(1, record.get("gold_mine_level", 1))
    hourly_rate = GOLD_MINE_BASE_RATE * level
    stored = record.get("gold_mine_stored", 0)
    next_cost = gold_mine_upgrade_cost(level) if level < GOLD_MINE_MAX_LEVEL else None
    await update.message.reply_text(
        "⛏ معدن طلا\n"
        f"سطح معدن: {level}\n"
        f"سکه‌های آماده جمع‌آوری: {stored}\n"
        f"تولید هر ساعت: {hourly_rate} سکه\n"
        f"حداکثر نگهداری: {hourly_rate * GOLD_MINE_MAX_HOURS} سکه\n"
        f"{'هزینه ارتقا به سطح ' + str(level + 1) + ': ' + str(next_cost) + ' سکه' if next_cost is not None else '✅ معدن در بالاترین سطح است.'}\n\n"
        "🔻 از منو انتخاب کنید",
        reply_markup=gold_mine_menu_markup(),
    )


async def gold_mine_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    now = datetime.now()
    update_gold_mine_storage(record, now)
    collected = record.get("gold_mine_stored", 0)
    if collected <= 0:
        await update.message.reply_text(
            "❌ سکه‌ای برای جمع‌آوری موجود نیست.",
            reply_markup=gold_mine_menu_markup(),
        )
        return
    record["coins"] += collected
    record["gold_mine_stored"] = 0
    record["gold_mine_last_collect"] = now.isoformat()
    save_user_data_store()
    await update.message.reply_text(
        f"✅ {collected} سکه از معدن جمع‌آوری شد.",
        reply_markup=gold_mine_menu_markup(),
    )


async def gold_mine_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    level = max(1, record.get("gold_mine_level", 1))
    if level >= GOLD_MINE_MAX_LEVEL:
        await update.message.reply_text(
            "✅ معدن شما به سقف لول رسیده است.",
            reply_markup=gold_mine_menu_markup(),
        )
        return
    cost = gold_mine_upgrade_cost(level)
    if record["coins"] < cost:
        await update.message.reply_text(
            "❌ سکه کافی برای ارتقا ندارید.",
            reply_markup=gold_mine_menu_markup(),
        )
        return
    record["coins"] -= cost
    record["gold_mine_level"] = level + 1
    now = datetime.now()
    update_gold_mine_storage(record, now)
    save_user_data_store()
    await update.message.reply_text(
        f"✅ معدن به سطح {level + 1} ارتقا یافت!",
        reply_markup=gold_mine_menu_markup(),
    )


async def gem_mine_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if record.get("level", 1) < GEM_MINE_MIN_LEVEL:
        await update.message.reply_text(
            "❌ برای استفاده از معدن جم باید لول ۱۰ یا بالاتر باشید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    now = datetime.now()
    remaining = gem_mine_time_remaining(record, now)
    if remaining == timedelta(0):
        status = "✅ اکنون می‌توانید جم برداشت کنید."
    else:
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes = remainder // 60
        status = f"⏳ زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه"
    await update.message.reply_text(
        "💎 معدن جم\n\n"
        f"پاداش هر ۲۴ ساعت: {GEM_MINE_REWARD} جم\n"
        f"{status}",
        reply_markup=gem_mine_menu_markup(),
    )


async def gem_mine_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if record.get("level", 1) < GEM_MINE_MIN_LEVEL:
        await update.message.reply_text(
            "❌ برای استفاده از معدن جم باید لول ۱۰ یا بالاتر باشید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    now = datetime.now()
    remaining = gem_mine_time_remaining(record, now)
    if remaining > timedelta(0):
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes = remainder // 60
        await update.message.reply_text(
            "⏳ هنوز زمان برداشت نرسیده است.\n"
            f"زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه",
            reply_markup=gem_mine_menu_markup(),
        )
        return
    record["gems"] = record.get("gems", 0) + GEM_MINE_REWARD
    record["gem_mine_last_collect"] = now.isoformat()
    save_user_data_store()
    await update.message.reply_text(
        f"✅ {GEM_MINE_REWARD} جم دریافت کردید!",
        reply_markup=gem_mine_menu_markup(),
    )


async def group_loot_box_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_chat is None:
        return
    if not is_group_chat(update):
        return
    if update.message.text is None:
        return
    if update.effective_user is not None:
        record = get_user_record(update.effective_user.id)
        update_last_group_chat(record, update.effective_chat.id)
    chat_id = update.effective_chat.id
    group_message_counts[chat_id] = group_message_counts.get(chat_id, 0) + 1
    if group_message_counts[chat_id] < LOOT_BOX_MESSAGE_THRESHOLD:
        return
    group_message_counts[chat_id] = 0
    box_id = uuid4().hex[:12]
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("باز کردن 🎁", callback_data=f"box_open_{box_id}")]]
    )
    sent = await update.message.reply_text(
        "✨🎁 جعبه شانسی آماده‌ست!\n"
        "اولین نفری که بازش کنه، جایزه می‌گیره.",
        reply_markup=keyboard,
    )
    loot_boxes[box_id] = {
        "chat_id": chat_id,
        "message_id": sent.message_id,
        "opened": False,
    }


async def loot_box_open_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    query = update.callback_query
    box_id = query.data.replace("box_open_", "")
    box_info = loot_boxes.get(box_id)
    if not box_info:
        await query.answer("⛔️ این جعبه معتبر نیست.", show_alert=True)
        return
    if box_info.get("opened"):
        await query.answer("✅ این جعبه قبلاً باز شده است.", show_alert=True)
        return
    record = get_user_record(update.effective_user.id)
    today = datetime.now().date().isoformat()
    reset_daily_boxes_if_needed(record, today)
    if record.get("daily_boxes_opened", 0) >= LOOT_BOX_DAILY_LIMIT:
        await query.answer("❌ سقف روزانه باز کردن جعبه‌ها تکمیل شده است.", show_alert=True)
        return
    reward_type, reward_label, amount = pick_loot_box_reward()
    apply_loot_box_reward(record, reward_type, amount)
    record["daily_boxes_opened"] = record.get("daily_boxes_opened", 0) + 1
    record["last_box_open_date"] = today
    save_user_data_store()
    box_info["opened"] = True
    winner_name = display_name_with_sticker(
        record, update.effective_user.first_name or "کاربر"
    )
    await query.answer()
    await query.edit_message_text(
        "🎁 جعبه شانسی باز شد!\n"
        f"👤 برنده: {winner_name}\n"
        f"🏆 جایزه: {amount} {reward_label}",
        reply_markup=None,
    )


async def coin_transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_coin_transfer_target"] = True
    record = get_user_record(update.effective_user.id)
    today = datetime.now().date().isoformat()
    reset_daily_transfer_if_needed(record, today)
    remaining = COIN_TRANSFER_DAILY_LIMIT - record.get("daily_coin_transfer", 0)
    await update.message.reply_text(
        "💸 تبادل سکه\n"
        "آیدی عددی گیرنده را وارد کنید:\n"
        f"سقف انتقال امروز: {COIN_TRANSFER_DAILY_LIMIT} سکه\n"
        f"باقی‌مانده امروز: {remaining} سکه",
        reply_markup=coin_transfer_markup(),
    )


async def handle_coin_transfer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    message_text = (update.message.text or "").strip()
    if context.user_data.get("awaiting_coin_transfer_target"):
        if not message_text.isdigit():
            await update.message.reply_text("❌ فقط آیدی عددی وارد کنید.")
            return
        target_id = int(message_text)
        if target_id == update.effective_user.id:
            await update.message.reply_text("❌ نمی‌توانید به خودتان انتقال دهید.")
            return
        context.user_data["coin_transfer_target_id"] = target_id
        context.user_data["awaiting_coin_transfer_target"] = False
        context.user_data["awaiting_coin_transfer_amount"] = True
        await update.message.reply_text(
            "💸 تعداد سکه برای انتقال را وارد کنید:",
            reply_markup=coin_transfer_markup(),
        )
        return
    if context.user_data.get("awaiting_coin_transfer_amount"):
        if not message_text.isdigit():
            await update.message.reply_text("❌ فقط عدد وارد کنید.")
            return
        amount = int(message_text)
        if amount <= 0:
            await update.message.reply_text("❌ مقدار باید بیشتر از صفر باشد.")
            return
        record = get_user_record(update.effective_user.id)
        today = datetime.now().date().isoformat()
        reset_daily_transfer_if_needed(record, today)
        remaining = COIN_TRANSFER_DAILY_LIMIT - record.get("daily_coin_transfer", 0)
        if amount > remaining:
            await update.message.reply_text(
                f"❌ فقط {remaining} سکه تا پایان امروز می‌توانید انتقال دهید."
            )
            return
        if record["coins"] < amount:
            await update.message.reply_text("❌ سکه کافی ندارید.")
            return
        target_id = context.user_data.get("coin_transfer_target_id")
        if not target_id:
            await update.message.reply_text("❌ آیدی گیرنده مشخص نیست. دوباره تلاش کنید.")
            return
        target_record = get_user_record(int(target_id))
        record["coins"] -= amount
        target_record["coins"] += amount
        record["daily_coin_transfer"] += amount
        save_user_data_store()
        context.user_data["awaiting_coin_transfer_amount"] = False
        context.user_data["coin_transfer_target_id"] = None
        await notify_user(
            context,
            int(target_id),
            (
                "💸 انتقال سکه\n"
                f"👤 فرستنده: {update.effective_user.id}\n"
                f"💰 مبلغ: {amount} سکه"
            ),
        )
        await update.message.reply_text(
            f"✅ انتقال {amount} سکه به {target_id} انجام شد.",
            reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
        )


def can_open_global_attack(record: dict, now: datetime) -> tuple[bool, int]:
    last_open = record.get("last_global_attack_open")
    if not last_open:
        return True, 0
    last_time = datetime.fromisoformat(last_open)
    elapsed = (now - last_time).total_seconds()
    if elapsed >= GLOBAL_ATTACK_COOLDOWN_SECONDS:
        return True, 0
    return False, int(GLOBAL_ATTACK_COOLDOWN_SECONDS - elapsed)


def available_leagues_for_attack(current_league: str) -> list[str]:
    seen = set()
    ordered = []
    for _, league in LEAGUE_TIERS:
        if league not in seen:
            ordered.append(league)
            seen.add(league)
    if current_league not in seen:
        return [current_league]
    index = ordered.index(current_league)
    choices = {ordered[index]}
    if index > 0:
        choices.add(ordered[index - 1])
    if index + 1 < len(ordered):
        choices.add(ordered[index + 1])
    return list(choices)


def pick_random_opponent(user_id: int, leagues: list[str]) -> dict | None:
    league_choices = set(leagues)
    candidates = [
        player
        for key, player in user_data_store.items()
        if key != str(user_id)
        and player.get("league") in league_choices
        and player.get("id") != user_id
        and not is_admin_protection_enabled(player)
    ]
    if not candidates:
        return None
    return random.choice(candidates)


def render_opponent_message(opponent: dict, league: str) -> str:
    name = opponent.get("display_name", "کاربر")
    user_id = opponent.get("id", opponent.get("user_id", "نامشخص"))
    rank = opponent.get("rank", 0)
    coins = opponent.get("coins", 0)
    league = opponent.get("league", league)
    return (
        "🌐 حمله جهانی\n"
        "🌐 حریف پیشنهادی\n\n"
        f"👤 نام: {name}\n"
        f"🆔 آیدی: {user_id}\n"
        f"⭐ رنک: {rank} - {league}\n"
        f"💰 سکه‌های او: {coins}\n\n"
        "🔻 برای حمله یا جایگزین کردن حریف یکی از دکمه‌ها را بزنید.\n"
        "⏳ این پیشنهاد تا ۳ ثانیه معتبر است."
    )


def global_attack_inline_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                f"بعدی ({GLOBAL_ATTACK_REROLL_COST} سکه) ➡️",
                callback_data="global_attack_reroll",
            ),
            InlineKeyboardButton("حمله ⚔️", callback_data="global_attack_start"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def global_attack_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    update_league(record)
    now = datetime.now()
    allowed, remaining = can_open_global_attack(record, now)
    if not allowed:
        await update.message.reply_text(
            f"⏳ {remaining} ثانیه دیگر نمی‌توانید حمله کنید."
        )
        return
    record["last_global_attack_open"] = now.isoformat()
    save_user_data_store()

    allowed_leagues = available_leagues_for_attack(record["league"])
    opponent = pick_random_opponent(update.effective_user.id, allowed_leagues)
    if opponent is None:
        await update.message.reply_text(
            "برای لیگ شما فعلاً حریفی پیدا نشد.",
            reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
        )
        return
    context.user_data["current_opponent"] = opponent
    context.user_data["awaiting_global_attack_missile"] = False
    await update.message.reply_text(
        render_opponent_message(opponent, record["league"]),
        reply_markup=global_attack_inline_markup(),
    )


async def global_attack_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context, alert=True):
        return
    if not is_private_chat(update):
        await update.callback_query.answer(
            "⛔️ این منو فقط در پیوی ربات فعال است.", show_alert=True
        )
        return
    query = update.callback_query
    await query.answer()
    record = get_user_record(update.effective_user.id)
    update_league(record)
    if query.data == "global_attack_reroll":
        if record["coins"] < GLOBAL_ATTACK_REROLL_COST:
            await query.message.reply_text("❌ سکه کافی برای تعویض حریف ندارید.")
            return
        allowed_leagues = available_leagues_for_attack(record["league"])
        opponent = pick_random_opponent(update.effective_user.id, allowed_leagues)
        if opponent is None:
            await query.message.reply_text(
                "برای لیگ شما فعلاً حریفی پیدا نشد.",
                reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
            )
            return
        record["coins"] -= GLOBAL_ATTACK_REROLL_COST
        save_user_data_store()
        context.user_data["current_opponent"] = opponent
        await query.edit_message_text(
            render_opponent_message(opponent, record["league"]),
            reply_markup=global_attack_inline_markup(),
        )
        return
    opponent = context.user_data.get("current_opponent")
    if opponent is None:
        await query.message.reply_text("حریف انتخاب نشده. دوباره حمله جهانی را باز کنید.")
        return
    opponent_id = opponent.get("id") if isinstance(opponent, dict) else None
    if opponent_id == update.effective_user.id:
        await query.message.reply_text("❌ نمی‌توانید به خودتان حمله کنید.")
        return
    choices = owned_missile_choices(record)
    if not choices:
        await query.message.reply_text("❌ موشکی برای حمله ندارید.")
        return
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_revenge_attack"] = False
    context.user_data["awaiting_global_attack_missile"] = True
    await query.edit_message_text(
        "⚔️ حمله جهانی\n"
        "اسم موشک را بنویسید تا حمله انجام شود.\n\n"
        f"موشک‌های شما:\n{format_owned_missiles(record)}"
    )


async def handle_global_attack_missile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_global_attack_missile"):
        return
    missile_name = (update.message.text or "").strip()
    if not missile_name:
        await update.message.reply_text("❌ اسم موشک را وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    opponent = context.user_data.get("current_opponent")
    opponent_id = opponent.get("id") if isinstance(opponent, dict) else None
    if opponent_id is None or opponent_id == update.effective_user.id:
        context.user_data["awaiting_global_attack_missile"] = False
        await update.message.reply_text("❌ حریف معتبر نیست. دوباره حمله جهانی را باز کنید.")
        return
    opponent_record = get_user_record(int(opponent_id))
    if is_admin_protection_enabled(opponent_record):
        context.user_data["awaiting_global_attack_missile"] = False
        await update.message.reply_text("❌ نمی‌توانید به این ادمین محافظت‌شده حمله کنید.")
        return
    if user_in_active_duel(record.get("id")) or user_in_active_duel(int(opponent_id)):
        context.user_data["awaiting_global_attack_missile"] = False
        await update.message.reply_text("⛔️ یکی از شما در دوئل فعال است.")
        return
    update_league(record)
    update_league(opponent_record)
    today = datetime.now().strftime("%Y-%m-%d")
    allowed, limit_message = can_crystal_attack_today(record, opponent_record, today)
    if not allowed:
        context.user_data["awaiting_global_attack_missile"] = False
        await update.message.reply_text(limit_message)
        return
    if is_shield_active(opponent_record):
        context.user_data["awaiting_global_attack_missile"] = False
        remaining = shield_remaining_text(opponent_record)
        note = f" ({remaining})" if remaining else ""
        await update.message.reply_text(f"❌ این بازیکن سپر فعال دارد{note}.")
        return
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await update.message.reply_text("❌ موشک مورد نظر یافت نشد.")
        return
    if record.get(missile_key, 0) <= 0:
        await update.message.reply_text("❌ از این موشک موجودی ندارید.")
        return
    record[missile_key] -= 1
    if record.get("missiles", 0) > 0:
        record["missiles"] -= 1
    context.user_data["awaiting_global_attack_missile"] = False
    blocked, defense_note = resolve_defense(opponent_record, missile_name)
    reward = 0 if blocked else calculate_attack_reward(opponent_record, missile_reward_range(missile_name, missile_key))
    if reward:
        record["coins"] += reward
        opponent_record["coins"] = max(0, opponent_record.get("coins", 0) - reward)
    damage = calculate_attack_damage(record, opponent_record, missile_name, blocked, missile_key)
    if blocked:
        rank_gain, rank_loss = 0, 0
    else:
        rank_gain, rank_loss = calculate_rank_transfer_for_missile(
            record, opponent_record, missile_name, damage
        )
        record["rank"] = record.get("rank", 0) + rank_gain
        opponent_record["rank"] = max(0, opponent_record.get("rank", 0) - rank_loss)
    apply_crystal_attack_limits(record, opponent_record)
    leveled_to_three = apply_experience(record, missile_experience(missile_name))
    update_league(record)
    opponent_record["last_attack_from"] = update.effective_user.id
    add_revenge_target(opponent_record, update.effective_user.id)
    update_league(opponent_record)
    if leveled_to_three:
        maybe_reward_inviter(record)
    save_user_data_store()
    report = format_defense_report(
        attacker=record,
        defender=opponent_record,
        missile_name=missile_name,
        damage=damage,
        defender_coin_loss=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
    )
    await context.bot.send_message(
        chat_id=opponent_id,
        text=report,
        reply_markup=revenge_inline_markup(update.effective_user.id),
    )
    attack_report = format_attack_report(
        attacker=record,
        defender=opponent_record,
        missile_name=missile_name,
        damage=damage,
        attacker_coin_delta=reward,
        defender_coin_delta=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
        defense_note=defense_note,
    )
    await update.message.reply_text(
        attack_report,
        reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
    )


async def finish_duel_by_key(bot: Bot, key: str | None) -> None:
    if not key:
        return
    duel = duel_sessions.pop(key, None)
    if duel is None:
        return
    chat_id = duel["chat_id"]
    participants = duel["participants"]
    damage = duel["damage"]
    user_a, user_b = participants
    record_a = get_user_record(user_a)
    record_b = get_user_record(user_b)
    name_a = display_name_with_sticker(record_a, "کاربر")
    name_b = display_name_with_sticker(record_b, "کاربر")
    damage_a = damage.get(user_a, 0)
    damage_b = damage.get(user_b, 0)
    if damage_a == damage_b:
        result_text = (
            "⏱ دوئل تمام شد!\n"
            f"دمیج {name_a}: {damage_a}\n"
            f"دمیج {name_b}: {damage_b}\n"
            "نتیجه: مساوی"
        )
        await bot.send_message(chat_id=chat_id, text=result_text)
        if PRIMARY_ADMIN_ID is not None:
            try:
                await bot.send_message(chat_id=PRIMARY_ADMIN_ID, text=f"نتیجه دوئل:\n{result_text}")
            except Exception:
                pass
        return
    winner_id, loser_id = (user_a, user_b) if damage_a > damage_b else (user_b, user_a)
    loser_record = get_user_record(loser_id)
    winner_record = get_user_record(winner_id)
    winner_name = display_name_with_sticker(winner_record, "کاربر")
    loser_name = display_name_with_sticker(loser_record, "کاربر")
    transfer = min(1000, loser_record.get("rank", 0))
    loser_record["rank"] = max(0, loser_record.get("rank", 0) - transfer)
    winner_record["rank"] = winner_record.get("rank", 0) + transfer
    update_league(loser_record)
    update_league(winner_record)
    save_user_data_store()
    result_text = (
        "⏱ دوئل تمام شد!\n"
        f"دمیج {winner_name}: {damage.get(winner_id, 0)}\n"
        f"دمیج {loser_name}: {damage.get(loser_id, 0)}\n"
        f"🏆 برنده: {winner_name}\n"
        f"🏆 رنک انتقالی: {transfer}"
    )
    await bot.send_message(chat_id=chat_id, text=result_text)
    if PRIMARY_ADMIN_ID is not None:
        try:
            await bot.send_message(chat_id=PRIMARY_ADMIN_ID, text=f"نتیجه دوئل:\n{result_text}")
        except Exception:
            pass


async def finish_duel(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data if context.job else None
    if not isinstance(job_data, dict):
        return
    key = job_data.get("key")
    await finish_duel_by_key(context.bot, key)


async def schedule_duel_finish(application, key: str) -> None:
    await asyncio.sleep(DUEL_DURATION.total_seconds())
    await finish_duel_by_key(application.bot, key)


async def start_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_group(update):
        return
    if await reject_if_banned(update, context):
        return
    if update.message.reply_to_message is None or update.message.reply_to_message.from_user is None:
        await update.message.reply_text("❌ برای شروع دوئل باید روی پیام طرف مقابل رپلای کنید.")
        return
    opponent = update.message.reply_to_message.from_user
    if opponent.is_bot or (context.bot and opponent.id == context.bot.id):
        await update.message.reply_text("❌ نمی‌توانید با ربات دوئل کنید.")
        return
    if opponent.id == update.effective_user.id:
        await update.message.reply_text("❌ نمی‌توانید با خودتان دوئل کنید.")
        return
    if user_in_active_duel(update.effective_user.id) or user_in_active_duel(opponent.id):
        await update.message.reply_text("❌ یکی از شما در دوئل فعال است.")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    requester_record = get_user_record(update.effective_user.id)
    reset_daily_duel_limits_if_needed(requester_record, today)
    if requester_record.get("daily_duels_started", 0) >= DUEL_DAILY_LIMIT:
        await update.message.reply_text("❌ سقف دوئل روزانه شما پر شده است.")
        return
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    duel_key_value = duel_key(chat_id, update.effective_user.id, opponent.id)
    if duel_key_value in duel_sessions:
        await update.message.reply_text("❌ دوئل بین شما در حال اجراست.")
        return
    if get_duel_request(chat_id, update.effective_user.id, opponent.id):
        await update.message.reply_text("❌ درخواست دوئل قبلاً ارسال شده است.")
        return
    request_key = duel_request_key(chat_id, update.effective_user.id, opponent.id)
    duel_requests[request_key] = {
        "chat_id": chat_id,
        "from_id": update.effective_user.id,
        "to_id": opponent.id,
        "expires_at": datetime.now() + DUEL_REQUEST_TIMEOUT,
    }
    accept_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ قبول دوئل",
                    callback_data=f"duel_accept:{request_key}",
                ),
                InlineKeyboardButton(
                    "❌ رد دوئل",
                    callback_data=f"duel_reject:{request_key}",
                ),
            ]
        ]
    )
    await update.message.reply_text(
        "⚔️ درخواست دوئل ارسال شد.\n"
        "حریف باید دکمه قبول را بزند.",
        reply_markup=accept_markup,
    )


async def duel_request_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    query = update.callback_query
    data = query.data or ""
    if not data.startswith("duel_"):
        return
    parts = data.split(":", 1)
    if len(parts) != 2:
        await query.answer("درخواست نامعتبر است.", show_alert=True)
        return
    action, request_key = parts
    request = duel_requests.get(request_key)
    if request is None or request["expires_at"] <= datetime.now():
        duel_requests.pop(request_key, None)
        await query.answer("درخواست دوئل منقضی شد.", show_alert=True)
        return
    if update.effective_user.id != request["to_id"]:
        await query.answer("این درخواست برای شما نیست.", show_alert=True)
        return
    if action == "duel_reject":
        clear_duel_request(request["chat_id"], request["from_id"], request["to_id"])
        await query.edit_message_text("❌ درخواست دوئل رد شد.")
        return
    if user_in_active_duel(request["from_id"]) or user_in_active_duel(request["to_id"]):
        clear_duel_request(request["chat_id"], request["from_id"], request["to_id"])
        await query.edit_message_text("❌ یکی از شما در دوئل فعال است.")
        return
    chat_id = request["chat_id"]
    duel_key_value = duel_key(chat_id, request["from_id"], request["to_id"])
    if duel_key_value in duel_sessions:
        clear_duel_request(request["chat_id"], request["from_id"], request["to_id"])
        await query.edit_message_text("❌ دوئل بین شما در حال اجراست.")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    requester_record = get_user_record(request["from_id"])
    reset_daily_duel_limits_if_needed(requester_record, today)
    if requester_record.get("daily_duels_started", 0) >= DUEL_DAILY_LIMIT:
        clear_duel_request(request["chat_id"], request["from_id"], request["to_id"])
        await query.edit_message_text("❌ سقف دوئل روزانه طرف مقابل پر شده است.")
        return
    ends_at = datetime.now() + DUEL_DURATION
    requester_record["daily_duels_started"] = requester_record.get("daily_duels_started", 0) + 1
    requester_record["last_duel_day"] = today
    duel_sessions[duel_key_value] = {
        "chat_id": chat_id,
        "participants": (request["from_id"], request["to_id"]),
        "damage": {request["from_id"]: 0, request["to_id"]: 0},
        "ends_at": ends_at,
    }
    clear_duel_request(request["chat_id"], request["from_id"], request["to_id"])
    if context.job_queue is not None:
        context.job_queue.run_once(finish_duel, when=DUEL_DURATION, data={"key": duel_key_value})
    elif context.application is not None and hasattr(context.application, "create_task"):
        context.application.create_task(schedule_duel_finish(context.application, duel_key_value))
    await query.edit_message_text(
        "⚔️ دوئل شروع شد!\n"
        f"⏳ مدت: {int(DUEL_DURATION.total_seconds() // 60)} دقیقه\n"
        "در این مدت فقط می‌توانید به همدیگر حمله کنید."
    )


async def group_attack_by_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_group(update):
        return
    if await reject_if_banned(update, context):
        return
    text = (update.message.text or "").strip()
    if not text.startswith("حمله "):
        return
    missile_name = text.replace("حمله", "", 1).strip()
    if not missile_name:
        await update.message.reply_text("❌ اسم موشک را وارد کنید.")
        return
    if update.message.reply_to_message is None or update.message.reply_to_message.from_user is None:
        await update.message.reply_text("❌ برای حمله باید روی پیام کاربر رپلای کنید.")
        return
    target_user = update.message.reply_to_message.from_user
    if target_user.is_bot or (context.bot and target_user.id == context.bot.id):
        await update.message.reply_text("❌ نمی‌توانید به ربات‌ها حمله کنید.")
        return
    if target_user.id == update.effective_user.id:
        await update.message.reply_text("❌ نمی‌توانید به خودتان حمله کنید.")
        return
    target_record = get_user_record(target_user.id)
    member_status = await chat_member_status(context, update.effective_chat.id, target_user.id)
    if member_status == "left":
        await update.message.reply_text("❌ این کاربر در این گروه نیست، نمی‌توانید به او حمله کنید.")
        return
    if member_status == "restricted":
        await update.message.reply_text("❌ این کاربر سکوت است و نمی‌توانید به او حمله کنید.")
        return
    if is_admin_protection_enabled(target_record):
        await update.message.reply_text("❌ نمی‌توانید به این ادمین محافظت‌شده حمله کنید.")
        return
    if not is_duel_attack_allowed(update.effective_chat.id, update.effective_user.id, target_user.id):
        await update.message.reply_text("⛔️ یکی از شما در دوئل فعال است و نمی‌توانید حمله کنید.")
        return
    attacker_record = get_user_record(update.effective_user.id)
    update_league(attacker_record)
    update_league(target_record)
    duel = get_duel_between(update.effective_chat.id, update.effective_user.id, target_user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    if duel is None:
        allowed, limit_message = can_crystal_attack_today(attacker_record, target_record, today)
        if not allowed:
            await update.message.reply_text(limit_message)
            return
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await update.message.reply_text("❌ موشک مورد نظر یافت نشد.")
        return
    if attacker_record.get(missile_key, 0) <= 0:
        await update.message.reply_text("❌ از این موشک موجودی ندارید.")
        return
    defender_record = target_record
    now = datetime.now()
    last_attack_time = attacker_record.get("last_group_attack")
    if last_attack_time:
        try:
            last_dt = datetime.fromisoformat(last_attack_time)
            delta = (now - last_dt).total_seconds()
            if delta < 3:
                await update.message.reply_text("⏳ بین حملات گروهی حداقل ۳ ثانیه فاصله بگذارید.")
                return
        except Exception:
            pass
    attacker_record["last_group_attack"] = now.isoformat()
    attacker_record[missile_key] -= 1
    if attacker_record.get("missiles", 0) > 0:
        attacker_record["missiles"] -= 1
    if is_shield_active(defender_record):
        remaining = shield_remaining_text(defender_record)
        note = f" ({remaining})" if remaining else ""
        await update.message.reply_text(f"❌ این بازیکن سپر فعال دارد{note}.")
        return
    blocked, defense_note = resolve_defense(defender_record, missile_name)
    reward = 0 if blocked else calculate_attack_reward(defender_record, missile_reward_range(missile_name, missile_key))
    if reward:
        attacker_record["coins"] += reward
        defender_record["coins"] = max(0, defender_record.get("coins", 0) - reward)
    damage = calculate_attack_damage(attacker_record, defender_record, missile_name, blocked, missile_key)
    if blocked:
        rank_gain, rank_loss = 0, 0
    else:
        rank_gain, rank_loss = calculate_rank_transfer_for_missile(
            attacker_record, defender_record, missile_name, damage
        )
        attacker_record["rank"] = attacker_record.get("rank", 0) + rank_gain
        defender_record["rank"] = max(0, defender_record.get("rank", 0) - rank_loss)
    add_duel_damage(update.effective_chat.id, attacker_record.get("id"), defender_record.get("id"), damage)
    if duel is None:
        apply_crystal_attack_limits(attacker_record, defender_record)
    leveled_to_three = apply_experience(attacker_record, missile_experience(missile_name))
    update_league(attacker_record)
    defender_record["last_attack_from"] = update.effective_user.id
    add_revenge_target(defender_record, update.effective_user.id)
    update_league(defender_record)
    if leveled_to_three:
        maybe_reward_inviter(attacker_record)
    save_user_data_store()
    report = format_attack_report(
        attacker=attacker_record,
        defender=defender_record,
        missile_name=missile_name,
        damage=damage,
        attacker_coin_delta=reward,
        defender_coin_delta=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
        defense_note=defense_note,
    )
    await update.message.reply_text(report)
    defense_report = format_defense_report(
        attacker=attacker_record,
        defender=defender_record,
        missile_name=missile_name,
        damage=damage,
        defender_coin_loss=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
    )
    await notify_user(
        context,
        target_user.id,
        defense_report,
        reply_markup=revenge_inline_markup(update.effective_user.id),
    )


async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    await update.message.reply_text(
        "🛍 خرید آیتم | استاروار\n"
        f"💼 موجودی اعتبار شما: {record['toman']} تومان\n\n"
        "برای خرید از دکمه‌های پایین (کیبورد معمولی) استفاده کن.\n"
        "برای شارژ اعتبار، دکمهٔ افزایش موجودی را بزن.",
        reply_markup=shop_menu_markup(),
    )


def format_toman(amount: int) -> str:
    return f"{amount:,}"


def log_admin_action(user_id: int, admin_id: int, action: str) -> None:
    record = get_user_record(user_id)
    history = record.setdefault("admin_history", [])
    history.append(
        {
            "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "admin_id": admin_id,
            "action": action,
        }
    )
    if len(history) > 50:
        record["admin_history"] = history[-50:]


def pack_labels(packs: list[dict], value_key: str, label_prefix: str) -> list[str]:
    labels = []
    for pack in packs:
        labels.append(f"{label_prefix} {pack[value_key]} 🛒")
    return labels


def find_pack_by_label(
    label: str, packs: list[dict], value_key: str, label_prefix: str
) -> dict | None:
    for pack in packs:
        if label == f"{label_prefix} {pack[value_key]} 🛒":
            return pack
    return None


def find_shield_pack_by_label(label: str) -> dict | None:
    for pack in SHIELD_PACKS:
        if label == f"💎 {pack['gems']} - {pack['label']}":
            return pack
    return None


async def shield_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    await update.message.reply_text(
        "🛡️ فروشگاه سپرها\n"
        f"💎 جم‌های شما: {record['gems']}\n\n"
        "سپر مورد نظر را انتخاب کنید:",
        reply_markup=shield_shop_markup(),
    )


async def shield_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    text = (update.message.text or "").strip()
    pack = find_shield_pack_by_label(text)
    if not pack:
        return
    record = get_user_record(update.effective_user.id)
    cost = pack["gems"]
    if record.get("gems", 0) < cost:
        await update.message.reply_text("❌ جم کافی برای خرید سپر ندارید.")
        return
    now = datetime.now()
    base_time = now
    if is_shield_active(record):
        shield_until = record.get("shield_until")
        if shield_until:
            base_time = datetime.fromisoformat(shield_until)
    record["gems"] -= cost
    record["shield_active"] = True
    record["shield_until"] = (base_time + timedelta(hours=pack["hours"])).isoformat()
    save_user_data_store()
    await update.message.reply_text(
        "✅ سپر فعال شد.\n"
        f"⏳ مدت: {pack['hours']} ساعت\n"
        f"💎 هزینه: {cost} جم",
        reply_markup=store_menu_markup(),
    )


async def gem_packs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if not GEM_PACKS:
        await update.message.reply_text(
            "فعلاً پک جم فعالی نداریم.",
            reply_markup=shop_menu_markup(),
        )
        return
    context.user_data["awaiting_pack_category"] = "gems"
    labels = pack_labels(GEM_PACKS, "gems", "جم")
    pack_lines = "\n".join(
        f"• {pack['gems']} جم — {format_toman(pack['price'])} تومان"
        for pack in GEM_PACKS
    )
    await update.message.reply_text(
        "💎 پک های جم\n"
        f"اعتبار شما: {format_toman(record['toman'])} تومان\n\n"
        f"{pack_lines}\n\n"
        "برای خرید یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=pack_choice_markup(labels),
    )


async def special_packs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    if not SPECIAL_PACKS:
        await update.message.reply_text(
            "فعلاً پک ویژه‌ای برای خرید نیست.",
            reply_markup=shop_menu_markup(),
        )
        return
    context.user_data["awaiting_pack_category"] = "special"
    labels = [pack["label"] for pack in SPECIAL_PACKS]
    pack_lines = "\n".join(
        f"• {pack['label']} — {format_toman(pack['price'])} تومان"
        for pack in SPECIAL_PACKS
    )
    await update.message.reply_text(
        "💥 پک های ویژه\n"
        f"{pack_lines}\n\n"
        "برای خرید یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=pack_choice_markup(labels),
    )


async def bundle_packs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    if not BUNDLE_PACKS:
        await update.message.reply_text(
            "فعلاً باندلی برای خرید نیست.",
            reply_markup=shop_menu_markup(),
        )
        return
    context.user_data["awaiting_pack_category"] = "bundle"
    labels = [pack["label"] for pack in BUNDLE_PACKS]
    pack_lines = "\n".join(
        f"• {pack['label']} — {format_toman(pack['price'])} تومان"
        for pack in BUNDLE_PACKS
    )
    await update.message.reply_text(
        "🥷 باندل ها\n"
        f"{pack_lines}\n\n"
        "برای خرید یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=pack_choice_markup(labels),
    )


def apply_pack_to_record(record: dict, pack: dict) -> None:
    if pack.get("gems"):
        record["gems"] += pack["gems"]
    if pack.get("coins"):
        record["coins"] += pack["coins"]
    if pack.get("missiles"):
        for key, count in pack["missiles"].items():
            record[key] = record.get(key, 0) + count
            record["missiles"] += count
    if pack.get("defenses"):
        for key, count in pack["defenses"].items():
            record[key] = record.get(key, 0) + count


async def handle_pack_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    category = context.user_data.get("awaiting_pack_category")
    if not category:
        return
    message_text = (update.message.text or "").strip()
    if message_text == "بازگشت به دسته ها ◀️":
        context.user_data["awaiting_pack_category"] = None
        await update.message.reply_text(
            "بازگشت به دسته ها 👇",
            reply_markup=shop_menu_markup(),
        )
        return
    if category == "gems":
        pack = find_pack_by_label(message_text, GEM_PACKS, "gems", "جم")
    elif category == "special":
        pack = next((item for item in SPECIAL_PACKS if item["label"] == message_text), None)
    else:
        pack = next((item for item in BUNDLE_PACKS if item["label"] == message_text), None)
    if pack is None:
        await update.message.reply_text("❌ گزینه نامعتبر است.")
        return
    record = get_user_record(update.effective_user.id)
    price = pack["price"]
    if record["toman"] < price:
        await update.message.reply_text("❌ اعتبار کافی ندارید.")
        return
    record["toman"] -= price
    apply_pack_to_record(record, pack)
    save_user_data_store()
    context.user_data["awaiting_pack_category"] = None
    await update.message.reply_text(
        "✅ خرید با موفقیت انجام شد و آیتم‌ها فعال شدند.",
        reply_markup=shop_menu_markup(),
    )


async def handle_clan_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_create_name"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی اصلی ↩️":
        context.user_data["awaiting_clan_create_name"] = False
        await back_to_main_menu(update, context)
        return
    name = text
    if not name:
        await update.message.reply_text("❌ نام کلن را وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    if record.get("clan_id"):
        context.user_data["awaiting_clan_create_name"] = False
        await update.message.reply_text("❌ شما عضو کلن هستید.")
        return
    if record.get("coins", 0) < CLAN_CREATE_COST:
        context.user_data["awaiting_clan_create_name"] = False
        await update.message.reply_text(f"❌ {CLAN_CREATE_COST} سکه نیاز دارید.")
        return
    clan_id = generate_clan_code()
    clan_data_store[clan_id] = {
        "id": clan_id,
        "name": name,
        "code": clan_id,
        "leader_id": update.effective_user.id,
        "sub_leaders": [],
        "members": [update.effective_user.id],
        "level": 1,
        "tank_level": 0,
        "castle_level": 0,
        "cups": 0,
        "tag": None,
        "requests": [],
    }
    record["coins"] -= CLAN_CREATE_COST
    record["clan_id"] = clan_id
    save_user_data_store()
    save_clan_data_store()
    context.user_data["awaiting_clan_create_name"] = False
    await update.message.reply_text(
        "✅ کلن ساخته شد!\n"
        f"کد کلن شما: {clan_id}",
        reply_markup=clan_panel_markup(True, True),
    )


async def handle_clan_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_search_code"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی اصلی ↩️":
        context.user_data["awaiting_clan_search_code"] = False
        await back_to_main_menu(update, context)
        return
    code = text.upper()
    if not code:
        await update.message.reply_text("❌ کد کلن را وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    if record.get("clan_id"):
        context.user_data["awaiting_clan_search_code"] = False
        await update.message.reply_text("❌ شما عضو کلن هستید.")
        return
    clan = clan_data_store.get(code)
    if not clan:
        await update.message.reply_text("❌ کلنی با این کد پیدا نشد.")
        return
    member_ids = clan.get("members", [])
    if update.effective_user.id in member_ids:
        context.user_data["awaiting_clan_search_code"] = False
        await update.message.reply_text("❌ شما عضو این کلن هستید.")
        return
    requests = clan.setdefault("requests", [])
    if any(req.get("user_id") == update.effective_user.id for req in requests):
        await update.message.reply_text("✅ درخواست شما قبلاً ارسال شده است.")
        return
    capacity = get_clan_capacity(clan.get("level", 1))
    if len(member_ids) >= capacity:
        await update.message.reply_text("❌ ظرفیت کلن کامل است.")
        return
    requests.append(
        {
            "user_id": update.effective_user.id,
            "name": update.effective_user.first_name or "کاربر",
        }
    )
    save_clan_data_store()
    context.user_data["awaiting_clan_search_code"] = False
    await update.message.reply_text("✅ درخواست عضویت ارسال شد.")
    await notify_user(
        context,
        clan.get("leader_id"),
        (
            "📩 درخواست عضویت جدید\n"
            f"نام: {update.effective_user.first_name or 'کاربر'}\n"
            f"آیدی: {update.effective_user.id}"
        ),
    )
    await notify_user(
        context,
        clan.get("leader_id"),
        "برای تایید یا رد درخواست از دکمه‌های زیر استفاده کنید.",
    )
    try:
        await context.bot.send_message(
            chat_id=clan.get("leader_id"),
            text=f"درخواست‌های کلن {clan.get('name')}:",
            reply_markup=clan_requests_markup(requests),
        )
    except Exception:
        pass


async def handle_clan_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_tag"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی کلن ↩️":
        context.user_data["awaiting_clan_tag"] = False
        await clan_menu(update, context)
        return
    tag = text
    if not tag:
        await update.message.reply_text("❌ تگ را وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        context.user_data["awaiting_clan_tag"] = False
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        context.user_data["awaiting_clan_tag"] = False
        await update.message.reply_text("❌ فقط لیدر می‌تواند تگ تنظیم کند.")
        return
    clan["tag"] = tag
    save_clan_data_store()
    context.user_data["awaiting_clan_tag"] = False
    await update.message.reply_text("✅ تگ کلن ثبت شد.")


async def handle_clan_remove_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_remove_member"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی کلن ↩️":
        context.user_data["awaiting_clan_remove_member"] = False
        await clan_menu(update, context)
        return
    if not text.isdigit():
        await update.message.reply_text("❌ فقط آیدی عددی وارد کنید.")
        return
    member_id = int(text)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        context.user_data["awaiting_clan_remove_member"] = False
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        context.user_data["awaiting_clan_remove_member"] = False
        await update.message.reply_text("❌ فقط لیدر می‌تواند عضو حذف کند.")
        return
    if member_id == record.get("id"):
        await update.message.reply_text("❌ نمی‌توانید خودتان را حذف کنید.")
        return
    member_record = get_user_record(member_id)
    if get_active_clan_war_for_user(member_id):
        await update.message.reply_text("❌ این عضو در کلن وار فعال است و نمی‌توان حذفش کرد.")
        return
    members = clan.get("members", [])
    if member_id not in members:
        await update.message.reply_text("❌ این آیدی در کلن نیست.")
        return
    members.remove(member_id)
    subs = clan.get("sub_leaders", [])
    if member_id in subs:
        subs.remove(member_id)
    member_record["clan_id"] = None
    save_user_data_store()
    save_clan_data_store()
    context.user_data["awaiting_clan_remove_member"] = False
    await update.message.reply_text("✅ عضو از کلن حذف شد.")


async def clan_leader_change_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    reset_clan_prompt_flags(context)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند لیدر را تغییر دهد.")
        return
    context.user_data["awaiting_clan_leader_change"] = True
    await update.message.reply_text(
        "👑 تغییر لیدر\n"
        "آیدی عددی عضو جدید لیدر را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup([["بازگشت به منوی کلن ↩️"]], resize_keyboard=True),
    )


async def handle_clan_leader_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_leader_change"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی کلن ↩️":
        context.user_data["awaiting_clan_leader_change"] = False
        await clan_menu(update, context)
        return
    if not text.isdigit():
        await update.message.reply_text("❌ آیدی باید عددی باشد.")
        return
    new_leader_id = int(text)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        context.user_data["awaiting_clan_leader_change"] = False
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        context.user_data["awaiting_clan_leader_change"] = False
        await update.message.reply_text("❌ فقط لیدر می‌تواند لیدر را تغییر دهد.")
        return
    members = clan.get("members", [])
    if new_leader_id not in members:
        await update.message.reply_text("❌ این کاربر عضو کلن نیست.")
        return
    if new_leader_id == record.get("id"):
        await update.message.reply_text("❌ همین الان لیدر هستید.")
        return
    clan["leader_id"] = new_leader_id
    sub_leaders = clan.setdefault("sub_leaders", [])
    if new_leader_id in sub_leaders:
        sub_leaders.remove(new_leader_id)
    if record.get("id") not in members:
        members.append(record.get("id"))
    save_clan_data_store()
    context.user_data["awaiting_clan_leader_change"] = False
    await update.message.reply_text("✅ لیدر جدید تنظیم شد.", reply_markup=clan_panel_markup(False, False))
    await notify_user(
        context,
        new_leader_id,
        "👑 شما به عنوان لیدر جدید کلن منصوب شدید.",
    )


async def clan_sub_leader_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    reset_clan_prompt_flags(context)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند ساب‌لیدر را تعیین کند.")
        return
    context.user_data["awaiting_clan_sub_leader"] = True
    subs = clan.get("sub_leaders", [])
    await update.message.reply_text(
        "👥 مدیریت ساب‌لیدر\n"
        "آیدی عضو موردنظر را ارسال کنید.\n"
        "اگر عضو ساب‌لیدر باشد حذف می‌شود؛ اگر نباشد و ظرفیت خالی باشد اضافه می‌شود.\n"
        f"ساب‌لیدرهای فعلی: {', '.join(map(str, subs)) if subs else 'ندارد'}",
        reply_markup=ReplyKeyboardMarkup([["بازگشت به منوی کلن ↩️"]], resize_keyboard=True),
    )


async def handle_clan_sub_leader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_clan_sub_leader"):
        return
    text = (update.message.text or "").strip()
    if text == "بازگشت به منوی کلن ↩️":
        context.user_data["awaiting_clan_sub_leader"] = False
        await clan_menu(update, context)
        return
    if not text.isdigit():
        await update.message.reply_text("❌ آیدی باید عددی باشد.")
        return
    member_id = int(text)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        context.user_data["awaiting_clan_sub_leader"] = False
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        context.user_data["awaiting_clan_sub_leader"] = False
        await update.message.reply_text("❌ فقط لیدر می‌تواند ساب‌لیدر را تعیین کند.")
        return
    members = clan.get("members", [])
    if member_id not in members:
        await update.message.reply_text("❌ این کاربر عضو کلن نیست.")
        return
    if member_id == clan.get("leader_id"):
        await update.message.reply_text("❌ لیدر نمی‌تواند ساب‌لیدر باشد.")
        return
    subs = clan.setdefault("sub_leaders", [])
    if member_id in subs:
        subs.remove(member_id)
        save_clan_data_store()
        context.user_data["awaiting_clan_sub_leader"] = False
        await update.message.reply_text("✅ این عضو از ساب‌لیدرها حذف شد.")
        return
    if len(subs) >= 2:
        await update.message.reply_text("❌ حداکثر 2 ساب‌لیدر می‌توانید داشته باشید.")
        return
    subs.append(member_id)
    save_clan_data_store()
    context.user_data["awaiting_clan_sub_leader"] = False
    await update.message.reply_text("✅ این عضو به عنوان ساب‌لیدر ثبت شد.")


async def clan_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    query = update.callback_query
    await query.answer()
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await query.edit_message_text("❌ کلن یافت نشد.")
        return
    data = query.data
    is_leader = user_is_clan_leader(record, clan)
    is_sub_leader = user_is_sub_leader(record, clan)
    if not is_leader and not (data.startswith("clan_war_") and is_sub_leader):
        await query.edit_message_text("❌ فقط لیدر می‌تواند این عملیات را انجام دهد.")
        return
    if data.startswith("clan_accept_"):
        if not is_leader:
            await query.edit_message_text("❌ فقط لیدر می‌تواند درخواست‌ها را مدیریت کند.")
            return
        user_id = int(data.replace("clan_accept_", ""))
        requests = clan.get("requests", [])
        clan["requests"] = [req for req in requests if req.get("user_id") != user_id]
        member_ids = clan.get("members", [])
        capacity = get_clan_capacity(clan.get("level", 1))
        if len(member_ids) >= capacity:
            await query.edit_message_text("❌ ظرفیت کلن کامل است.")
            save_clan_data_store()
            return
        if user_id not in member_ids:
            member_ids.append(user_id)
        user_record = get_user_record(user_id)
        user_record["clan_id"] = clan.get("id")
        save_user_data_store()
        save_clan_data_store()
        await query.edit_message_text("✅ عضو جدید اضافه شد.")
        await notify_user(
            context,
            user_id,
            f"✅ درخواست شما برای کلن {clan.get('name')} تایید شد.",
        )
        return
    if data.startswith("clan_reject_"):
        if not is_leader:
            await query.edit_message_text("❌ فقط لیدر می‌تواند درخواست‌ها را مدیریت کند.")
            return
        user_id = int(data.replace("clan_reject_", ""))
        requests = clan.get("requests", [])
        clan["requests"] = [req for req in requests if req.get("user_id") != user_id]
        save_clan_data_store()
        await query.edit_message_text("❌ درخواست رد شد.")
        await notify_user(
            context,
            user_id,
            f"❌ درخواست شما برای کلن {clan.get('name')} رد شد.",
        )
        return
    if data.startswith("clan_war_pick_") or data == "clan_war_confirm":
        selection = context.user_data.get("clan_war_selection")
        if not selection or selection.get("clan_id") != clan.get("id"):
            await query.edit_message_text("❌ انتخاب اعضای وار منقضی شده است.")
            return
        members = selection.get("members", [])
        selected = set(selection.get("selected", set()))
        if data.startswith("clan_war_pick_"):
            member_id = int(data.replace("clan_war_pick_", ""))
            if member_id not in members:
                await query.answer("این عضو در لیست نیست.")
                return
            if member_id in selected:
                selected.remove(member_id)
            else:
                if len(selected) >= CLAN_WAR_TEAM_SIZE:
                    await query.answer(f"فقط {CLAN_WAR_TEAM_SIZE} نفر را می‌توانید انتخاب کنید.")
                    return
                selected.add(member_id)
            selection["selected"] = selected
            context.user_data["clan_war_selection"] = selection
            selection_text = (
                "✋ انتخاب اعضای کلن وار\n"
                f"اعضای انتخاب‌شده: {len(selected)}/{CLAN_WAR_TEAM_SIZE}"
            )
            await safe_edit_message(
                query,
                selection_text,
                reply_markup=clan_war_selection_markup(members, selected),
            )
            return
        if len(selected) != CLAN_WAR_TEAM_SIZE:
            await query.answer(f"باید دقیقاً {CLAN_WAR_TEAM_SIZE} نفر را انتخاب کنید.")
            return
        members_in_clan = clan.get("members", [])
        if any(member_id not in members_in_clan for member_id in selected):
            await query.edit_message_text("❌ یکی از اعضا دیگر در کلن نیست.")
            context.user_data.pop("clan_war_selection", None)
            return
        if any(get_user_record(int(member_id)).get("clan_war_id") for member_id in selected):
            await query.edit_message_text("❌ یکی از اعضا در وار دیگری است.")
            context.user_data.pop("clan_war_selection", None)
            return
        result_message = await queue_clan_war_request(
            context,
            clan,
            list(selected),
            query.message,
        )
        context.user_data.pop("clan_war_selection", None)
        if result_message:
            await query.edit_message_text(result_message)
        return


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ فقط ادمین‌ها دسترسی دارند.")
        return
    await update.message.reply_text(
        "🛠 پنل ادمین\n\n"
        "/set_coins <user_id> <amount>\n"
        "/set_toman <user_id> <amount>\n"
        "/set_gems <user_id> <amount>\n"
        "/set_level <user_id> <level>\n"
        "/set_rank <user_id> <rank>\n"
        "/adjust_balance <user_id> <coins_delta> [gems_delta]\n"
        "/give_missile <user_id> <missile_name> <count>\n"
        "/ban <user_id> <minutes>\n"
        "/bang <user_id>\n"
        "/unban <user_id>\n"
        "/add_admin <user_id>\n"
        "/remove_admin <user_id>\n"
        "/give_title <user_id> <title>\n"
        "/reset_user <user_id>\n"
        "/reset_all_assets\n"
        "/reset_solarpass <user_id>\n"
        "/reset_solarpass_all\n"
        "/admin_history <user_id>\n"
        "/set_mine_level <user_id> <level>\n"
        "/remove_missile <user_id> <missile_name> <count>\n"
        "/grant_solarpass <user_id>\n"
        "/admin_protection_on\n"
        "/admin_protection_off\n"
        "/list_assets\n"
        "/reset_caps\n"
        "/create_gift <uses> <amount>\n"
        "/redeem <code>\n"
        "/broadcast <message>"
    )


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    message = " ".join(context.args).strip()
    if not message and update.message.reply_to_message is not None:
        reply = update.message.reply_to_message
        message = (reply.text or reply.caption or "").strip()
    if not message:
        await admin_only_reply(update, "فرمت: /broadcast <message> (یا ریپلای بدون آرگومان)")
        return
    sent = 0
    failed = 0
    for record in user_data_store.values():
        user_id = record.get("id")
        if user_id is None:
            continue
        try:
            await context.bot.send_message(chat_id=int(user_id), text=message)
            sent += 1
        except Exception:
            failed += 1
    log_admin_action(update.effective_user.id, update.effective_user.id, "ارسال پیام همگانی")
    await admin_only_reply(update, f"✅ پیام ارسال شد. موفق: {sent} | ناموفق: {failed}")


async def store_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    await update.message.reply_text(
        "🛒 به فروشگاه خوش آمدید!\n\n"
        f"💰 سکه‌های شما: {record['coins']}\n"
        f"💎 جم‌های شما: {record['gems']}\n"
        f"⭐ لول شما: {record['level']}\n\n"
        "🔻 نوع خرید را انتخاب کنید:",
        reply_markup=store_menu_markup(),
    )


async def missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    reset_purchase_flags(context)
    await update.message.reply_text(
        "🚀 دسته موشکی مورد نظر را انتخاب کنید:",
        reply_markup=missiles_menu_markup(),
    )


async def defense_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    reset_purchase_flags(context)
    context.user_data["defense_key"] = None
    context.user_data["defense_price"] = None
    context.user_data["defense_label"] = None
    record = get_user_record(update.effective_user.id)
    available = [
        item for item in DEFENSE_ITEMS if record.get("level", 1) >= item["level"]
    ]
    rows = [[f"{item['label']} 🛡️ - {item['price']}"] for item in available]
    rows.append(["بازگشت به منوی فروشگاه ↩️"])
    await update.message.reply_text(
        "🛡️ فروشگاه پدافند\n"
        f"💰 سکه‌های شما: {record['coins']}\n"
        f"⭐ لول شما: {record['level']}\n\n"
        "🔻 پدافند مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )


async def defense_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    reset_purchase_flags(context)
    context.user_data["defense_key"] = None
    context.user_data["defense_price"] = None
    context.user_data["defense_label"] = None
    record = get_user_record(update.effective_user.id)
    active = record.get("active_defense")
    active_item = next((item for item in DEFENSE_ITEMS if item["key"] == active), None)
    active_label = f"{active_item['label']} 🛡️" if active_item else "هیچ"
    counts = "\n".join(
        f"• {item['label']} 🛡️: {record.get(item['key'], 0)}"
        for item in DEFENSE_ITEMS
        if record.get(item["key"], 0) > 0
    )
    counts_text = counts if counts else "• هیچ پدافندی ندارید."
    await update.message.reply_text(
        "🛡️ پدافندهای شما:\n"
        f"{counts_text}\n"
        f"• پدافند فعال: {active_label}\n\n"
        "از منو انتخاب کنید:",
        reply_markup=defense_status_menu_markup(record),
    )


async def defense_activate_tirbar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if record.get("tirbar_defense", 0) <= 0:
        await update.message.reply_text("❌ تیر بار ندارید.")
        return
    record["active_defense"] = "tirbar_defense"
    save_user_data_store()
    await update.message.reply_text("✅ پدافند تیر بار فعال شد.")


async def defense_activate_generic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    text = (update.message.text or "").strip()
    label = text.replace("فعال کردن", "").replace("🛡️", "").strip()
    item = next((entry for entry in DEFENSE_ITEMS if entry["label"] == label), None)
    if not item:
        return
    record = get_user_record(update.effective_user.id)
    if record.get(item["key"], 0) <= 0:
        await update.message.reply_text("❌ این پدافند را ندارید.")
        return
    record["active_defense"] = item["key"]
    save_user_data_store()
    await update.message.reply_text(f"✅ پدافند {item['label']} فعال شد.")


async def defense_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_banned(update, context):
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    record["active_defense"] = None
    save_user_data_store()
    await update.message.reply_text("✅ پدافند غیرفعال شد.")


async def hypersonic_missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id) if update.effective_user else None
    if record and record.get("level", 1) < 7:
        await update.message.reply_text(
            "❌ برای دسترسی به موشک‌های هایپرسونیک باید حداقل لول 7 باشید.",
            reply_markup=missiles_menu_markup(),
        )
        return
    items = []
    if record and record.get("level", 1) >= 7:
        items.append(f"خرمشهر 💰 {KHORRAMSHAHR_PRICE}")
    if record and record.get("level", 1) >= 13:
        items.append(f"طوفان 💰 {TUFAN_PRICE}")
    if record and record.get("level", 1) >= 15:
        items.append(f"الماس 💰 {ALMAS_PRICE}")
    rows = [[item] for item in items]
    rows.append(["بازگشت به منوی فروشگاه ↩️"])
    await update.message.reply_text(
        "🛒 فروشگاه موشک‌های هایپرسونیک 🚀\n"
        f"💰 سکه‌های شما: {record['coins'] if record else 0}\n\n"
        "🔻 موشک مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )


async def ballistic_missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id) if update.effective_user else None
    if record and record.get("level", 1) < 3:
        await update.message.reply_text(
            "❌ برای دسترسی به موشک‌های بالستیک باید حداقل لول 3 باشید.",
            reply_markup=missiles_menu_markup(),
        )
        return
    items = []
    if record and record.get("level", 1) >= 3:
        items.append(f"عماد 💰 {EMAD_PRICE}")
    if record and record.get("level", 1) >= 8:
        items.append(f"سجیل 💰 {SAJJIL_PRICE}")
    if record and record.get("level", 1) >= 10:
        items.append(f"شهاب 💰 {SHAHAB_PRICE}")
    rows = [[item] for item in items]
    rows.append(["بازگشت به منوی فروشگاه ↩️"])
    await update.message.reply_text(
        "🛒 فروشگاه موشک‌های بالستیک 🚀\n"
        f"💰 سکه‌های شما: {record['coins'] if record else 0}\n\n"
        "🔻 موشک مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )


async def chemical_missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id) if update.effective_user else None
    if record and record.get("level", 1) < 10:
        await update.message.reply_text(
            "❌ برای دسترسی به موشک‌های شیمیایی باید حداقل لول 10 باشید.",
            reply_markup=missiles_menu_markup(),
        )
        return
    await update.message.reply_text(
        "🛒 فروشگاه موشک‌های شیمیایی 🚀\n"
        f"💰 سکه‌های شما: {record['coins'] if record else 0}\n"
        f"💵 قیمت شیمیایی: {CHEMICAL_PRICE} سکه\n\n"
        "🔻 موشک مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [[f"شیمیایی 💰 {CHEMICAL_PRICE}"], ["بازگشت به منوی فروشگاه ↩️"]],
            resize_keyboard=True,
        ),
    )


async def nuclear_missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id) if update.effective_user else None
    if record and record.get("level", 1) < 20:
        await update.message.reply_text(
            "❌ برای دسترسی به موشک‌های هسته‌ای باید حداقل لول 20 باشید.",
            reply_markup=missiles_menu_markup(),
        )
        return
    await update.message.reply_text(
        "🛒 فروشگاه موشک‌های هسته‌ای 🚀\n"
        f"💰 سکه‌های شما: {record['coins'] if record else 0}\n"
        f"💎 جم‌های شما: {record['gems'] if record else 0}\n"
        f"💵 قیمت هسته‌ای: {NUCLEAR_PRICE_COINS} سکه + {NUCLEAR_PRICE_GEMS} جم\n\n"
        "🔻 موشک مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [[f"هسته‌ای 💰 {NUCLEAR_PRICE_COINS} + 💎 {NUCLEAR_PRICE_GEMS}"], ["بازگشت به منوی فروشگاه ↩️"]],
            resize_keyboard=True,
        ),
    )


async def revenge_attack_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    query = update.callback_query
    await query.answer()
    record = get_user_record(update.effective_user.id)
    data = query.data or ""
    try:
        attacker_id = int(data.split("_", 1)[1])
    except (IndexError, ValueError):
        await query.edit_message_text("❌ مهاجم مشخص نیست.")
        return
    targets = record.get("revenge_targets", [])
    if attacker_id not in targets:
        await query.edit_message_text("❌ انتقام قبلاً استفاده شده است.")
        return
    remove_single_revenge_target(record, attacker_id)
    save_user_data_store()
    context.user_data["awaiting_revenge_attack"] = True
    context.user_data["revenge_target_id"] = int(attacker_id)
    await query.edit_message_text(
        "⚔️ انتقام\n"
        "اسم موشک را بنویسید تا حمله شود."
    )


async def handle_revenge_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        context.user_data["awaiting_revenge_attack"] = False
        context.user_data["revenge_target_id"] = None
        return
    if not context.user_data.get("awaiting_revenge_attack"):
        return
    missile_name = (update.message.text or "").strip()
    if not missile_name:
        await update.message.reply_text("❌ اسم موشک را وارد کنید.")
        return
    target_id = context.user_data.get("revenge_target_id")
    context.user_data["awaiting_revenge_attack"] = False
    context.user_data["revenge_target_id"] = None
    if target_id is None:
        await update.message.reply_text("❌ هدف انتقام مشخص نیست.")
        return
    target_record = get_user_record(int(target_id))
    if is_admin_protection_enabled(target_record):
        await update.message.reply_text("❌ نمی‌توانید به این ادمین محافظت‌شده حمله کنید.")
        return
    record = get_user_record(update.effective_user.id)
    if user_in_active_duel(record.get("id")) or user_in_active_duel(int(target_id)):
        await update.message.reply_text("⛔️ یکی از شما در دوئل فعال است.")
        return
    update_league(record)
    update_league(target_record)
    today = datetime.now().strftime("%Y-%m-%d")
    allowed, limit_message = can_crystal_attack_today(record, target_record, today)
    if not allowed:
        await update.message.reply_text(limit_message)
        return
    remove_single_revenge_target(record, target_id)
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await update.message.reply_text("❌ موشک مورد نظر یافت نشد.")
        return
    if record.get(missile_key, 0) <= 0:
        await update.message.reply_text("❌ از این موشک موجودی ندارید.")
        return
    record[missile_key] -= 1
    if record.get("missiles", 0) > 0:
        record["missiles"] -= 1
    target_record = get_user_record(int(target_id))
    if is_shield_active(target_record):
        remaining = shield_remaining_text(target_record)
        note = f" ({remaining})" if remaining else ""
        await update.message.reply_text(f"❌ این بازیکن سپر فعال دارد{note}.")
        return
    blocked, defense_note = resolve_defense(target_record, missile_name)
    reward = 0 if blocked else calculate_attack_reward(target_record, missile_reward_range(missile_name, missile_key))
    if reward:
        record["coins"] += reward
        target_record["coins"] = max(0, target_record.get("coins", 0) - reward)
    damage = calculate_attack_damage(record, target_record, missile_name, blocked, missile_key)
    if blocked:
        rank_gain, rank_loss = 0, 0
    else:
        rank_gain, rank_loss = calculate_rank_transfer_for_missile(
            record, target_record, missile_name, damage
        )
        record["rank"] = record.get("rank", 0) + rank_gain
        target_record["rank"] = max(0, target_record.get("rank", 0) - rank_loss)
    apply_crystal_attack_limits(record, target_record)
    leveled_to_three = apply_experience(record, missile_experience(missile_name))
    update_league(record)
    update_league(target_record)
    if leveled_to_three:
        maybe_reward_inviter(record)
    save_user_data_store()
    report = format_attack_report(
        attacker=record,
        defender=target_record,
        missile_name=missile_name,
        damage=damage,
        attacker_coin_delta=reward,
        defender_coin_delta=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
        defense_note=defense_note,
    )
    defense_report = format_defense_report(
        attacker=record,
        defender=target_record,
        missile_name=missile_name,
        damage=damage,
        defender_coin_loss=reward,
        attacker_rank_delta=rank_gain,
        defender_rank_delta=rank_loss,
        timestamp=datetime.now(),
    )
    await notify_user(
        context,
        int(target_id),
        defense_report,
        reply_markup=revenge_inline_markup(record.get("id", update.effective_user.id)),
    )
    await update.message.reply_text(
        "✅ انتقام ثبت شد!\n"
        f"🧨 موشک: {missile_name}\n"
        f"💰 جایزه: {reward} سکه\n"
        f"🏆 رنک اضافه شده: {rank_gain}",
        reply_markup=main_menu_markup(update.effective_user.id if update.effective_user else None),
    )


async def missiles_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        NOT_AVAILABLE_TEXT,
        reply_markup=missiles_menu_markup(),
    )


async def shop_category_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        NOT_AVAILABLE_TEXT,
        reply_markup=store_menu_markup(),
    )


async def clan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    reset_clan_prompt_flags(context)
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if clan:
        is_leader = user_is_clan_leader(record, clan)
        is_sub_leader = user_is_sub_leader(record, clan)
        member_count = len(clan.get("members", []))
        capacity = get_clan_capacity(clan.get("level", 1))
        tank_level = clan.get("tank_level", 0)
        castle_level = clan.get("castle_level", 0)
        sub_leaders = clan.get("sub_leaders", [])
        await update.message.reply_text(
            "🏰 منوی کلن\n"
            f"نام: {clan.get('name', '---')}\n"
            f"کد: {clan.get('code')}\n"
            f"لول: {clan.get('level', 1)}\n"
            f"اعضا: {member_count}/{capacity}\n"
            f"تگ: {clan.get('tag') or 'ندارد'}\n"
            f"تانک کلن: لول {tank_level}\n"
            f"قلعه کلن: لول {castle_level}\n"
            f"ساب‌لیدرها: {', '.join(map(str, sub_leaders)) if sub_leaders else 'ندارد'}\n",
            reply_markup=clan_panel_markup(is_leader or is_sub_leader, is_leader),
        )
        return
    await update.message.reply_text(
        "👥 بخش کلن‌ها:\n"
        "یکی از موارد زیر را انتخاب کنید:",
        reply_markup=clan_menu_markup(),
    )


async def clan_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if record.get("clan_id"):
        await update.message.reply_text(
            "❌ شما عضو کلن هستید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    context.user_data["awaiting_clan_search_code"] = True
    await update.message.reply_text(
        "🔍 جستجوی کلن\n"
        "کد کلن را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی اصلی ↩️"]], resize_keyboard=True
        ),
    )


async def clan_create_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if record.get("clan_id"):
        await update.message.reply_text(
            "❌ شما عضو کلن هستید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    if record.get("coins", 0) < CLAN_CREATE_COST:
        await update.message.reply_text(
            f"❌ برای ساخت کلن {CLAN_CREATE_COST} سکه نیاز دارید.",
            reply_markup=clan_menu_markup(),
        )
        return
    context.user_data["awaiting_clan_create_name"] = True
    await update.message.reply_text(
        "🏗️ ساخت کلن\n"
        "نام کلن را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی اصلی ↩️"]], resize_keyboard=True
        ),
    )


async def clan_members_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text(
            "❌ شما عضو کلن نیستید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    is_leader = user_is_clan_leader(record, clan)
    members = []
    for member_id in clan.get("members", []):
        member_record = get_user_record(int(member_id))
        members.append(display_name_with_sticker(member_record, "کاربر"))
    members_text = "\n".join(f"• {member}" for member in members) if members else "خالی"
    await update.message.reply_text(
        "👥 اعضای کلن:\n"
        f"{members_text}",
        reply_markup=clan_members_markup(is_leader),
    )


async def clan_remove_member_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند عضو حذف کند.")
        return
    context.user_data["awaiting_clan_remove_member"] = True
    await update.message.reply_text(
        "➖ حذف عضو\n"
        "آیدی عددی عضو را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی کلن ↩️"]], resize_keyboard=True
        ),
    )


async def clan_requests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text(
            "❌ شما عضو کلن نیستید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند درخواست‌ها را ببیند.")
        return
    requests = clan.get("requests", [])
    if not requests:
        await update.message.reply_text("درخواستی وجود ندارد.")
        return
    await update.message.reply_text(
        "📩 درخواست‌های عضویت:",
        reply_markup=clan_requests_markup(requests),
    )


async def clan_upgrade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text(
            "❌ شما عضو کلن نیستید.",
            reply_markup=main_menu_markup(update.effective_user.id),
        )
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند کلن را ارتقا دهد.")
        return
    level = clan.get("level", 1)
    if level >= 5:
        await update.message.reply_text("✅ کلن در بالاترین لول است.")
        return
    next_level = level + 1
    cost = CLAN_LEVEL_COSTS.get(next_level, 0)
    if record.get("coins", 0) < cost:
        await update.message.reply_text("❌ سکه کافی برای ارتقا ندارید.")
        return
    record["coins"] -= cost
    clan["level"] = next_level
    save_user_data_store()
    save_clan_data_store()
    await update.message.reply_text(
        f"✅ کلن به لول {next_level} ارتقا یافت."
    )


async def clan_tank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند تانک کلن را مدیریت کند.")
        return
    level = clan.get("tank_level", 0)
    bonus = level * 20
    if level <= 0:
        action = "خرید تانک 🪖"
        cost_text = f"هزینه خرید: {CLAN_TANK_PURCHASE_COST} سکه"
    elif level >= 5:
        action = None
        cost_text = "تانک در بالاترین لول است."
    else:
        next_level = level + 1
        cost_text = f"هزینه ارتقا به لول {next_level}: {CLAN_TANK_LEVEL_COSTS[next_level]} سکه"
        action = "ارتقا تانک 🪖"
    keyboard = []
    if action:
        keyboard.append([action])
    keyboard.append(["بازگشت به منوی کلن ↩️"])
    await update.message.reply_text(
        "🪖 تانک کلن\n"
        f"لول فعلی: {level}\n"
        f"بونوس دمیج: {bonus}\n"
        f"{cost_text}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def clan_tank_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند تانک کلن را ارتقا دهد.")
        return
    level = clan.get("tank_level", 0)
    if level >= 5:
        await update.message.reply_text("✅ تانک کلن در بالاترین لول است.")
        return
    if level == 0:
        cost = CLAN_TANK_PURCHASE_COST
    else:
        next_level = level + 1
        cost = CLAN_TANK_LEVEL_COSTS.get(next_level, 0)
    if record.get("coins", 0) < cost:
        await update.message.reply_text("❌ سکه کافی برای ارتقا ندارید.")
        return
    record["coins"] -= cost
    clan["tank_level"] = level + 1
    save_user_data_store()
    save_clan_data_store()
    await update.message.reply_text(
        f"✅ تانک کلن به لول {clan['tank_level']} رسید."
    )


async def clan_castle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند قلعه کلن را مدیریت کند.")
        return
    level = clan.get("castle_level", 0)
    if level <= 0:
        action = "خرید قلعه 🏰"
        cost_text = f"هزینه خرید: {CLAN_CASTLE_LEVEL_COST} سکه"
        reduction_text = "کاهش دمیج: ۰"
    else:
        reduction_min = level * CLAN_CASTLE_DAMAGE_MIN_PER_LEVEL
        reduction_max = level * CLAN_CASTLE_DAMAGE_MAX_PER_LEVEL
        reduction_text = f"کاهش دمیج: {reduction_min} تا {reduction_max}"
        if level >= CLAN_CASTLE_MAX_LEVEL:
            action = None
            cost_text = "قلعه در بالاترین لول است."
        else:
            cost_text = f"هزینه ارتقا به لول {level + 1}: {CLAN_CASTLE_LEVEL_COST} سکه"
            action = "ارتقا قلعه 🏰"
    keyboard = []
    if action:
        keyboard.append([action])
    keyboard.append(["بازگشت به منوی کلن ↩️"])
    await update.message.reply_text(
        "🏰 قلعه کلن\n"
        f"لول فعلی: {level}\n"
        f"{reduction_text}\n"
        f"{cost_text}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )


async def clan_castle_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند قلعه کلن را ارتقا دهد.")
        return
    level = clan.get("castle_level", 0)
    if level >= CLAN_CASTLE_MAX_LEVEL:
        await update.message.reply_text("✅ قلعه کلن در بالاترین لول است.")
        return
    cost = CLAN_CASTLE_LEVEL_COST
    if record.get("coins", 0) < cost:
        await update.message.reply_text("❌ سکه کافی برای ارتقا ندارید.")
        return
    record["coins"] -= cost
    clan["castle_level"] = level + 1
    save_user_data_store()
    save_clan_data_store()
    await update.message.reply_text(
        f"✅ قلعه کلن به لول {clan['castle_level']} رسید."
    )


async def clan_set_tag_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند تگ تنظیم کند.")
        return
    context.user_data["awaiting_clan_tag"] = True
    await update.message.reply_text(
        "🏷️ تنظیم تگ\n"
        "یک تگ کوتاه ارسال کنید (مثلاً [ABC]):",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی کلن ↩️"]], resize_keyboard=True
        ),
    )


async def clan_clear_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not user_is_clan_leader(record, clan):
        await update.message.reply_text("❌ فقط لیدر می‌تواند تگ را پاک کند.")
        return
    clan["tag"] = None
    save_clan_data_store()
    await update.message.reply_text("✅ تگ کلن پاک شد.")


async def clan_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if get_active_clan_war_for_user(record.get("id")):
        await update.message.reply_text("❌ در کلن وار فعال هستید و نمی‌توانید خارج شوید.")
        return
    is_leader = user_is_clan_leader(record, clan)
    if is_leader:
        if any(get_user_record(int(member_id)).get("clan_war_id") for member_id in clan.get("members", [])):
            await update.message.reply_text("❌ اعضای کلن در کلن وار فعال هستند و نمی‌توانید کلن را حذف کنید.")
            return
        for member_id in clan.get("members", []):
            member_record = get_user_record(int(member_id))
            member_record["clan_id"] = None
        clan_data_store.pop(str(clan.get("id")), None)
        save_user_data_store()
        save_clan_data_store()
        await update.message.reply_text("✅ کلن حذف شد و شما خارج شدید.")
        return
    members = clan.get("members", [])
    if record.get("id") in members:
        members.remove(record.get("id"))
    record["clan_id"] = None
    save_user_data_store()
    save_clan_data_store()
    await update.message.reply_text("✅ از کلن خارج شدید.")


async def start_clan_war_session(
    context: ContextTypes.DEFAULT_TYPE,
    clan: dict,
    opponent: dict,
    team_a: list[int],
    team_b: list[int] | None = None,
    starts_at: datetime | None = None,
) -> tuple[bool, str]:
    opponent_members = opponent.get("members", [])
    if team_b is None:
        if len(opponent_members) < CLAN_WAR_TEAM_SIZE:
            return False, "❌ کلن حریف به حد نصاب نرسیده است."
        team_b = random.sample(opponent_members, CLAN_WAR_TEAM_SIZE)
    announce_chats = set()
    for candidate_id in (clan.get("leader_id"), opponent.get("leader_id")):
        if candidate_id:
            candidate_record = get_user_record(int(candidate_id))
            chat_id = candidate_record.get("last_group_chat_id")
            if chat_id:
                announce_chats.add(int(chat_id))
    war_id = uuid4().hex[:8]
    now = datetime.now()
    starts_at = starts_at or now
    user_clan_map = {user_id: str(clan.get("id")) for user_id in team_a}
    user_clan_map.update({user_id: str(opponent.get("id")) for user_id in team_b})
    clan_war_sessions[war_id] = {
        "id": war_id,
        "clan_ids": [str(clan.get("id")), str(opponent.get("id"))],
        "teams": {
            str(clan.get("id")): team_a,
            str(opponent.get("id")): team_b,
        },
        "user_clan_map": user_clan_map,
        "damage_totals": {str(clan.get("id")): 0, str(opponent.get("id")): 0},
        "damage_by_user": {},
        "completed": False,
        "announce_chats": list(announce_chats),
        "starts_at": starts_at.isoformat(),
        "started_at": None,
        "prep_started_at": now.isoformat(),
    }
    for user_id in team_a + team_b:
        user_record = get_user_record(int(user_id))
        user_record["clan_war_id"] = war_id
        user_record["clan_war_attacks_left"] = CLAN_WAR_ATTACKS_PER_USER
    save_user_data_store()
    opponent_name = opponent.get("name", "نامشخص")
    starts_at_text = starts_at.strftime("%Y-%m-%d %H:%M")
    wait_minutes = max(0, int((starts_at - now).total_seconds() // 60))
    war_message = (
        "⚔️ کلن وار در حال آماده‌سازی است!\n\n"
        f"کلن شما در برابر {opponent_name}\n"
        f"⏳ شروع تقریباً تا {wait_minutes} دقیقه دیگر ({starts_at_text})\n"
        f"هر نفر {CLAN_WAR_ATTACKS_PER_USER} حمله دارد.\n"
        "با شروع وار از منوی کلن وار حمله کنید."
    )
    for user_id in team_a:
        await notify_user(context, int(user_id), war_message)
    war_message_opponent = (
        "⚔️ کلن وار در حال آماده‌سازی است!\n\n"
        f"کلن شما در برابر {clan.get('name', 'نامشخص')}\n"
        f"⏳ شروع تقریباً تا {wait_minutes} دقیقه دیگر ({starts_at_text})\n"
        f"هر نفر {CLAN_WAR_ATTACKS_PER_USER} حمله دارد.\n"
        "با شروع وار از منوی کلن وار حمله کنید."
    )
    for user_id in team_b:
        await notify_user(context, int(user_id), war_message_opponent)
    return True, war_id


async def finalize_clan_war(context: ContextTypes.DEFAULT_TYPE, war: dict) -> None:
    if war.get("completed"):
        return
    ensure_war_started(war)
    clan_ids = war.get("clan_ids", [])
    if len(clan_ids) != 2:
        war["completed"] = True
        clan_war_sessions.pop(war.get("id"), None)
        return
    clan_a_id, clan_b_id = clan_ids
    damage_a = war.get("damage_totals", {}).get(clan_a_id, 0)
    damage_b = war.get("damage_totals", {}).get(clan_b_id, 0)
    winner_clan_id = None
    winner_text = "🏆 نتیجه: مساوی"
    if damage_a > damage_b:
        winner_clan_id = clan_a_id
    elif damage_b > damage_a:
        winner_clan_id = clan_b_id
    if winner_clan_id:
        winner_clan = clan_data_store.get(winner_clan_id, {})
        winner_clan["cups"] = winner_clan.get("cups", 0) + 3
        winner_text = f"🏆 برنده: کلن {winner_clan.get('name', 'نامشخص')}"
        winning_members = war.get("teams", {}).get(winner_clan_id, [])
        for member_id in winning_members:
            member_record = get_user_record(int(member_id))
            member_record["coins"] = member_record.get("coins", 0) + 3000
    top_damage = sorted(
        war.get("damage_by_user", {}).items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]
    top_lines = []
    for user_id, dmg in top_damage:
        user_record = get_user_record(int(user_id))
        top_lines.append(f"- {user_record.get('display_name', 'کاربر')} → {dmg} دمیج")
    top_section = "\n".join(top_lines) if top_lines else "اطلاعاتی ثبت نشد."
    reward_line = (
        "🎁 به اعضای تیم برنده 3000 سکه داده شد.\n" if winner_clan_id else ""
    )
    summary = (
        "⚔️ نتیجه کلن وار\n\n"
        f"{winner_text}\n"
        f"دمیج کلن اول: {damage_a}\n"
        f"دمیج کلن دوم: {damage_b}\n\n"
        f"⏱ مدت وار: {CLAN_WAR_DURATION_MINUTES} دقیقه\n"
        f"{reward_line}"
        "برترین دمیج‌ها:\n"
        f"{top_section}"
    )
    war["completed"] = True
    for user_id in war.get("user_clan_map", {}).keys():
        user_record = get_user_record(int(user_id))
        user_record["clan_war_id"] = None
        user_record["clan_war_attacks_left"] = 0
        await notify_user(context, int(user_id), summary)
    save_user_data_store()
    save_clan_data_store()
    clan_war_sessions.pop(war.get("id"), None)


async def clan_war_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    is_leader = user_is_clan_leader(record, clan)
    is_sub_leader = user_is_sub_leader(record, clan)
    war = get_active_clan_war_for_user(update.effective_user.id)
    if war:
        ensure_war_started(war)
        starts_at = war.get("starts_at")
        if starts_at:
            try:
                starts_dt = datetime.fromisoformat(starts_at)
            except ValueError:
                starts_dt = None
            if starts_dt and war.get("started_at") is None and datetime.now() < starts_dt:
                minutes_left = int((starts_dt - datetime.now()).total_seconds() // 60) + 1
                await update.message.reply_text(
                    "⚔️ کلن وار در صف است.\n"
                    f"⏳ شروع تا حدود {minutes_left} دقیقه دیگر.\n"
                    f"اعضای انتخاب‌شده شما: {CLAN_WAR_TEAM_SIZE} نفر\n"
                    f"حمله باقی‌مانده شما: {record.get('clan_war_attacks_left', 0)}",
                    reply_markup=clan_war_menu_markup(is_leader or is_sub_leader, True),
                )
                return
        if war_has_expired(war):
            if war_has_expired(war):
                await finalize_clan_war(context, war)
                await update.message.reply_text(
                    "⏰ زمان کلن وار تمام شد و نتیجه محاسبه شد.",
                    reply_markup=clan_war_menu_markup(is_leader, False),
                )
                return
        await update.message.reply_text(
            "⚔️ کلن وار فعال است.\n"
            f"🔁 حمله باقی‌مانده شما: {record.get('clan_war_attacks_left', 0)}\n"
            "برای حمله از دکمه زیر استفاده کنید.",
            reply_markup=clan_war_menu_markup(is_leader or is_sub_leader, True),
        )
        return
    if not (is_leader or is_sub_leader):
        await update.message.reply_text(
            "❌ کلن وار فعلاً فعال نیست.",
            reply_markup=clan_war_menu_markup(False, False),
        )
        return
    await update.message.reply_text(
        "⚔️ شروع کلن وار\n"
        "برای جستجوی حریف و شروع وار از دکمه زیر استفاده کنید.",
        reply_markup=clan_war_menu_markup(True, False),
    )


async def clan_war_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    clan = get_clan_for_user(record)
    if not clan:
        await update.message.reply_text("❌ شما عضو کلن نیستید.")
        return
    if not (user_is_clan_leader(record, clan) or user_is_sub_leader(record, clan)):
        await update.message.reply_text("❌ فقط لیدر یا ساب‌لیدر می‌تواند کلن وار را شروع کند.")
        return
    members = clan.get("members", [])
    if len(members) < CLAN_WAR_TEAM_SIZE:
        await update.message.reply_text(
            f"❌ برای شروع کلن وار حداقل {CLAN_WAR_TEAM_SIZE} عضو نیاز دارید."
        )
        return
    if any(get_user_record(int(member_id)).get("clan_war_id") for member_id in members):
        await update.message.reply_text("❌ یکی از اعضای کلن شما در کلن وار فعال است.")
        return
    if len(members) > CLAN_WAR_TEAM_SIZE:
        context.user_data["clan_war_selection"] = {
            "clan_id": clan.get("id"),
            "members": members,
            "selected": set(),
        }
        await update.message.reply_text(
            "✋ انتخاب اعضای کلن وار\n"
            f"از بین اعضا {CLAN_WAR_TEAM_SIZE} نفر را انتخاب کنید.\n"
            "روی نام اعضا بزنید و در نهایت شروع وار را بزنید.",
            reply_markup=clan_war_selection_markup(members, set()),
        )
        return
    team_a = random.sample(members, CLAN_WAR_TEAM_SIZE)
    result_message = await queue_clan_war_request(context, clan, team_a, update.message)
    if result_message:
        await update.message.reply_text(result_message)


async def clan_war_attack_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    if await reject_if_banned(update, context):
        return
    war = get_active_clan_war_for_user(update.effective_user.id)
    if not war:
        await update.message.reply_text("❌ شما در کلن وار فعال نیستید.")
        return
    ensure_war_started(war)
    starts_at = war.get("starts_at")
    if starts_at and war.get("started_at") is None:
        try:
            starts_dt = datetime.fromisoformat(starts_at)
        except ValueError:
            starts_dt = None
        if starts_dt and datetime.now() < starts_dt:
            minutes_left = int((starts_dt - datetime.now()).total_seconds() // 60) + 1
            await update.message.reply_text(f"⏳ وار هنوز شروع نشده است. حدود {minutes_left} دقیقه باقی مانده.")
            return
    if war_has_expired(war):
        await finalize_clan_war(context, war)
        await update.message.reply_text("⏰ زمان کلن وار تمام شد و نتیجه محاسبه شد.")
        return
    record = get_user_record(update.effective_user.id)
    attacks_left = record.get("clan_war_attacks_left", 0)
    if attacks_left <= 0:
        await update.message.reply_text("❌ حمله‌های شما در کلن وار تمام شده است.")
        return
    context.user_data["awaiting_clan_war_attack"] = True
    await update.message.reply_text(
        "⚔️ حمله در کلن وار\n"
        "اسم موشک را بنویسید تا حمله انجام شود.\n\n"
        f"موشک‌های شما:\n{format_owned_missiles(record)}"
    )


async def handle_clan_war_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        context.user_data["awaiting_clan_war_attack"] = False
        return
    if await reject_if_banned(update, context):
        context.user_data["awaiting_clan_war_attack"] = False
        return
    missile_name = (update.message.text or "").strip()
    if not missile_name:
        await update.message.reply_text("❌ اسم موشک را وارد کنید.")
        return
    war = get_active_clan_war_for_user(update.effective_user.id)
    if not war:
        context.user_data["awaiting_clan_war_attack"] = False
        await update.message.reply_text("❌ شما در کلن وار فعال نیستید.")
        return
    ensure_war_started(war)
    starts_at = war.get("starts_at")
    if starts_at and war.get("started_at") is None:
        try:
            starts_dt = datetime.fromisoformat(starts_at)
        except ValueError:
            starts_dt = None
        if starts_dt and datetime.now() < starts_dt:
            context.user_data["awaiting_clan_war_attack"] = False
            await update.message.reply_text("⏳ وار هنوز شروع نشده است.")
            return
    if war_has_expired(war):
        context.user_data["awaiting_clan_war_attack"] = False
        await finalize_clan_war(context, war)
        await update.message.reply_text("⏰ زمان کلن وار تمام شد و نتیجه محاسبه شد.")
        return
    record = get_user_record(update.effective_user.id)
    attacks_left = record.get("clan_war_attacks_left", 0)
    if attacks_left <= 0:
        context.user_data["awaiting_clan_war_attack"] = False
        await update.message.reply_text("❌ حمله‌های شما در کلن وار تمام شده است.")
        return
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await update.message.reply_text("❌ موشک مورد نظر یافت نشد.")
        return
    if record.get(missile_key, 0) <= 0:
        await update.message.reply_text("❌ از این موشک موجودی ندارید.")
        return
    record[missile_key] -= 1
    if record.get("missiles", 0) > 0:
        record["missiles"] -= 1
    damage = missile_damage(missile_name, missile_key) + clan_tank_bonus(record)
    clan_id = war.get("user_clan_map", {}).get(record.get("id"))
    if clan_id is None:
        await update.message.reply_text("❌ اطلاعات کلن وار یافت نشد.")
        return
    opponent_clan_id = None
    for candidate_id in war.get("clan_ids", []):
        if candidate_id != str(clan_id):
            opponent_clan_id = candidate_id
            break
    if opponent_clan_id:
        reduction = clan_castle_reduction({"clan_id": opponent_clan_id})
        damage = max(0, damage - reduction)
    clan_name = clan_data_store.get(str(clan_id), {}).get("name", "نامشخص")
    war["damage_totals"][clan_id] = war["damage_totals"].get(clan_id, 0) + damage
    war["damage_by_user"][record.get("id")] = (
        war["damage_by_user"].get(record.get("id"), 0) + damage
    )
    record["clan_war_attacks_left"] = attacks_left - 1
    context.user_data["awaiting_clan_war_attack"] = False
    save_user_data_store()
    report = format_clan_war_attack_report(
        attacker=record,
        clan_name=clan_name,
        missile_name=missile_name,
        damage=damage,
        attacks_left=record["clan_war_attacks_left"],
        timestamp=datetime.now(),
    )
    await update.message.reply_text(report)
    for chat_id in war.get("announce_chats", []):
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=report)
        except Exception:
            continue
    total_attacks_left = sum(
        get_user_record(int(user_id)).get("clan_war_attacks_left", 0)
        for user_id in war.get("user_clan_map", {}).keys()
    )
    if total_attacks_left <= 0 or war_has_expired(war):
        await finalize_clan_war(context, war)


async def customization_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        "🎨 بخش شخصی‌سازی:\n"
        "یکی از موارد زیر را انتخاب کنید:",
        reply_markup=customization_menu_markup(),
    )


async def level_pass_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    await update.message.reply_text(
        level_pass_status_text(record),
        reply_markup=ReplyKeyboardMarkup([["بازگشت به منوی اصلی ↩️"]], resize_keyboard=True),
    )


async def customization_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        NOT_AVAILABLE_TEXT,
        reply_markup=customization_menu_markup(),
    )


async def customization_titles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    titles = record.get("available_titles", [])
    context.user_data["awaiting_title_choice"] = True
    if not titles:
        await update.message.reply_text(
            "فعلاً تایتلی برای شما فعال نیست.",
            reply_markup=customization_menu_markup(),
        )
        return
    current = record.get("selected_title") or "ندارد"
    await update.message.reply_text(
        "🎗️ تایتل‌ها\n"
        f"تایتل فعال: {current}\n"
        "یکی را انتخاب کنید:",
        reply_markup=title_menu_markup(titles),
    )


async def handle_title_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_title_choice"):
        return
    text = (update.message.text or "").strip()
    record = get_user_record(update.effective_user.id)
    titles = record.get("available_titles", [])
    if text == "بازگشت به شخصی سازی ↩️":
        context.user_data["awaiting_title_choice"] = False
        await back_to_customization(update, context)
        return
    if text == "حذف تایتل ❌":
        record["selected_title"] = None
        save_user_data_store()
        context.user_data["awaiting_title_choice"] = False
        await update.message.reply_text(
            "✅ تایتل حذف شد.",
            reply_markup=customization_menu_markup(),
        )
        return
    if text not in titles:
        await update.message.reply_text(
            "❌ تایتل معتبر نیست.",
            reply_markup=title_menu_markup(titles),
        )
        return
    record["selected_title"] = text
    save_user_data_store()
    context.user_data["awaiting_title_choice"] = False
    await update.message.reply_text(
        f"✅ تایتل فعال شد: {text}",
        reply_markup=customization_menu_markup(),
    )


async def chat_sticker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if not record.get("starpass_active"):
        await update.message.reply_text(
            "❌ برای استفاده از چت استیکر باید سولارپس فعال باشد.",
            reply_markup=customization_menu_markup(),
        )
        return
    await update.message.reply_text(
        "⭐ انتخاب چت استیکر:\n"
        "یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=chat_sticker_menu_markup(),
    )


async def chat_sticker_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if not record.get("starpass_active"):
        await update.message.reply_text(
            "❌ برای استفاده از چت استیکر باید سولارپس فعال باشد.",
            reply_markup=customization_menu_markup(),
        )
        return
    text = (update.message.text or "").strip()
    sticker_map = dict(STARPASS_CHAT_STICKERS)
    if text == "حذف استیکر ❌":
        record["chat_sticker"] = None
        save_user_data_store()
        await update.message.reply_text(
            "✅ چت استیکر حذف شد.",
            reply_markup=customization_menu_markup(),
        )
        return
    if text not in sticker_map:
        await update.message.reply_text(
            "❌ گزینه نامعتبر است.",
            reply_markup=chat_sticker_menu_markup(),
        )
        return
    record["chat_sticker"] = sticker_map[text]
    save_user_data_store()
    await update.message.reply_text(
        f"✅ چت استیکر شما ثبت شد: {sticker_map[text]}",
        reply_markup=customization_menu_markup(),
    )


async def back_to_customization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        "بازگشت به شخصی‌سازی 👇",
        reply_markup=customization_menu_markup(),
    )


async def cruise_missiles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id) if update.effective_user else None
    atlas_level = max(1, record.get("atlas_level", 1)) if record else 1
    atlas_price = atlas_unit_price(atlas_level)
    items = [f"قدر 💰 {QADR_PRICE}", f"اطلس 💰 {atlas_price}"]
    if record and record.get("level", 1) >= 6:
        items.append(f"خیبرشکن 💰 {KHEIBAR_PRICE}")
    rows = [[item] for item in items]
    rows.append(["بازگشت به منوی فروشگاه ↩️"])
    await update.message.reply_text(
        "🛒 فروشگاه موشک‌های کروز 🧨\n"
        f"💰 سکه‌های شما: {record['coins'] if record else 0}\n\n"
        "🔻 موشک مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )


async def atlas_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    current_level = max(1, record.get("atlas_level", 1))
    max_buy = atlas_max_buy(record["coins"], current_level)
    current_price = atlas_unit_price(current_level)
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = True
    await update.message.reply_text(
        "🛒 خرید اطلس\n"
        f"💰 قیمت هر واحد (فعلی): {current_price} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {max_buy}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def generic_missile_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    text = (update.message.text or "").strip()
    label = text.split("💰")[0].strip()
    item = GENERIC_MISSILE_SHOP.get(label)
    if not item:
        return
    record = get_user_record(update.effective_user.id)
    if record.get("level", 1) < item.get("level", 1):
        await update.message.reply_text("❌ لول شما برای این موشک کافی نیست.")
        return
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_generic_missile_quantity"] = True
    context.user_data["generic_missile_key"] = item["key"]
    context.user_data["generic_missile_label"] = label
    context.user_data["generic_missile_price"] = item["price"]
    await update.message.reply_text(
        f"🛒 خرید {label}\n"
        f"💰 قیمت هر واحد: {item['price']} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {record['coins'] // item['price']}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_atlas_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_atlas_quantity"):
        return
    message_text = (update.message.text or "").strip()
    quantity = parse_positive_int(message_text)
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    if quantity > 1000:
        await update.message.reply_text("❌ تعداد وارد شده خیلی زیاد است.")
        return
    record = get_user_record(update.effective_user.id)
    current_level = max(1, record.get("atlas_level", 1))
    total_cost = atlas_total_cost(current_level, quantity)
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record["atlas_missiles"] += quantity
    record["missiles"] += quantity
    record["atlas_level"] = current_level + quantity
    save_user_data_store()
    context.user_data["awaiting_atlas_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} اطلس با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def handle_generic_missile_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_generic_missile_quantity"):
        return
    quantity = parse_positive_int((update.message.text or "").strip())
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    key = context.user_data.get("generic_missile_key")
    label = context.user_data.get("generic_missile_label", "موشک")
    price = context.user_data.get("generic_missile_price", 0)
    total_cost = price * quantity
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record[key] = record.get(key, 0) + quantity
    record["missiles"] = record.get("missiles", 0) + quantity
    save_user_data_store()
    context.user_data["awaiting_generic_missile_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} {label} با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def khorramshahr_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_khorramshahr_quantity"] = True
    await update.message.reply_text(
        "🛒 خرید خرمشهر\n"
        f"💰 قیمت هر واحد: {KHORRAMSHAHR_PRICE} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {record['coins'] // KHORRAMSHAHR_PRICE}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_khorramshahr_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_khorramshahr_quantity"):
        return
    quantity = parse_positive_int((update.message.text or "").strip())
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    total_cost = KHORRAMSHAHR_PRICE * quantity
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record["khorramshahr_missiles"] += quantity
    record["missiles"] += quantity
    save_user_data_store()
    context.user_data["awaiting_khorramshahr_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} خرمشهر با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def emad_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_emad_quantity"] = True
    await update.message.reply_text(
        "🛒 خرید عماد\n"
        f"💰 قیمت هر واحد: {EMAD_PRICE} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {record['coins'] // EMAD_PRICE}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_emad_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_emad_quantity"):
        return
    quantity = parse_positive_int((update.message.text or "").strip())
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    total_cost = EMAD_PRICE * quantity
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record["emad_missiles"] += quantity
    record["missiles"] += quantity
    save_user_data_store()
    context.user_data["awaiting_emad_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} عماد با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def chemical_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_khorramshahr_quantity"] = False
    context.user_data["awaiting_emad_quantity"] = False
    context.user_data["awaiting_chemical_quantity"] = True
    await update.message.reply_text(
        "🛒 خرید شیمیایی\n"
        f"💰 قیمت هر واحد: {CHEMICAL_PRICE} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {record['coins'] // CHEMICAL_PRICE}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_chemical_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_chemical_quantity"):
        return
    quantity = parse_positive_int((update.message.text or "").strip())
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    total_cost = CHEMICAL_PRICE * quantity
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record["chemical_missiles"] += quantity
    record["missiles"] += quantity
    save_user_data_store()
    context.user_data["awaiting_chemical_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} شیمیایی با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def nuclear_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    context.user_data["awaiting_support_message"] = False
    context.user_data["awaiting_coin_transfer_target"] = False
    context.user_data["awaiting_coin_transfer_amount"] = False
    context.user_data["awaiting_atlas_quantity"] = False
    context.user_data["awaiting_khorramshahr_quantity"] = False
    context.user_data["awaiting_emad_quantity"] = False
    context.user_data["awaiting_chemical_quantity"] = False
    context.user_data["awaiting_nuclear_quantity"] = True
    max_buy = min(
        record["coins"] // NUCLEAR_PRICE_COINS,
        record["gems"] // NUCLEAR_PRICE_GEMS,
    )
    await update.message.reply_text(
        "🛒 خرید هسته‌ای\n"
        f"💰 قیمت هر واحد: {NUCLEAR_PRICE_COINS} سکه + {NUCLEAR_PRICE_GEMS} جم\n"
        f"📦 حداکثر خرید با موجودی شما: {max_buy}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_nuclear_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_nuclear_quantity"):
        return
    quantity = parse_positive_int((update.message.text or "").strip())
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    total_coins = NUCLEAR_PRICE_COINS * quantity
    total_gems = NUCLEAR_PRICE_GEMS * quantity
    if record["coins"] < total_coins or record["gems"] < total_gems:
        await update.message.reply_text("❌ سکه یا جم کافی ندارید.")
        return
    record["coins"] -= total_coins
    record["gems"] -= total_gems
    record["nuclear_missiles"] += quantity
    record["missiles"] += quantity
    save_user_data_store()
    context.user_data["awaiting_nuclear_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity} هسته‌ای با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_coins} سکه + {total_gems} جم",
        reply_markup=store_menu_markup(),
    )


async def tirbar_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await defense_purchase_prompt(update, context)


async def handle_tirbar_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_defense_quantity(update, context)


async def defense_purchase_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    text = (update.message.text or "").strip()
    item = next(
        (entry for entry in DEFENSE_ITEMS if text == f"{entry['label']} 🛡️ - {entry['price']}"),
        None,
    )
    if not item:
        return
    record = get_user_record(update.effective_user.id)
    if record.get("level", 1) < item["level"]:
        await update.message.reply_text("❌ لول شما برای این پدافند کافی نیست.")
        return
    context.user_data["awaiting_defense_quantity"] = True
    context.user_data["defense_key"] = item["key"]
    context.user_data["defense_price"] = item["price"]
    context.user_data["defense_label"] = item["label"]
    await update.message.reply_text(
        f"🛡️ خرید پدافند {item['label']}\n"
        f"💰 قیمت هر واحد: {item['price']} سکه\n"
        f"📦 حداکثر خرید با موجودی شما: {record['coins'] // item['price']}\n\n"
        "تعداد مورد نظر خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["بازگشت به منوی فروشگاه ↩️"]], resize_keyboard=True
        ),
    )


async def handle_defense_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not context.user_data.get("awaiting_defense_quantity"):
        return
    message_text = (update.message.text or "").strip()
    if message_text == "بازگشت به منوی فروشگاه ↩️":
        context.user_data["awaiting_defense_quantity"] = False
        await back_to_shop(update, context)
        return
    quantity = parse_positive_int(message_text)
    if quantity is None:
        await update.message.reply_text("❌ فقط عدد وارد کنید.")
        return
    record = get_user_record(update.effective_user.id)
    price = context.user_data.get("defense_price", 0)
    key = context.user_data.get("defense_key")
    label = context.user_data.get("defense_label", "پدافند")
    total_cost = price * quantity
    if record["coins"] < total_cost:
        await update.message.reply_text("❌ سکه کافی ندارید.")
        return
    record["coins"] -= total_cost
    record[key] = record.get(key, 0) + (quantity * 10)
    save_user_data_store()
    context.user_data["awaiting_defense_quantity"] = False
    await update.message.reply_text(
        f"✅ تعداد {quantity * 10} {label} با موفقیت خریداری شد!\n"
        f"💰 هزینه کل: {total_cost} سکه",
        reply_markup=store_menu_markup(),
    )


async def back_to_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    await update.message.reply_text(
        "بازگشت به منوی فروشگاه 👇",
        reply_markup=store_menu_markup(),
    )


async def shop_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    await update.message.reply_text(
        NOT_AVAILABLE_TEXT,
        reply_markup=shop_menu_markup(),
    )


async def coin_packs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    packs_text = "\n".join(
        f"• {pack['coins']:,} سکه — {format_toman(pack['price'])} تومان"
        for pack in COIN_PACKS
    )
    await update.message.reply_text(
        "💰 پک‌های سکه\n\n"
        f"{packs_text}\n\n"
        "برای انتخاب، یکی از گزینه‌های زیر را بزنید:",
        reply_markup=coin_pack_choice_markup(),
    )


async def coin_pack_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    label = (update.message.text or "").strip()
    pack = find_pack_by_label(label, COIN_PACKS, "coins", "سکه")
    if not pack:
        await update.message.reply_text(
            "❌ پک انتخاب‌شده معتبر نیست.",
            reply_markup=coin_pack_choice_markup(),
        )
        return
    record = get_user_record(update.effective_user.id)
    price = pack["price"]
    if record["toman"] < price:
        await update.message.reply_text(
            "❌ اعتبار کافی ندارید.",
            reply_markup=ReplyKeyboardMarkup(
                [["افزایش موجودی 🔁"], ["بازگشت به دسته ها ◀️"]],
                resize_keyboard=True,
            ),
        )
        return
    record["toman"] -= price
    record["coins"] += pack["coins"]
    save_user_data_store()
    await update.message.reply_text(
        "✅ پک سکه با موفقیت فعال شد!\n"
        f"مقدار: {pack['coins']:,} سکه\n"
        f"اعتبار باقی‌مانده: {format_toman(record['toman'])} تومان",
        reply_markup=shop_menu_markup(),
    )


def starpass_day_key(now: datetime) -> str:
    if now.time() >= STARPASS_RESET_TIME:
        return now.date().isoformat()
    return (now.date() - timedelta(days=1)).isoformat()


def starpass_allowed_day(record: dict, now: datetime) -> int:
    started_at = record.get("starpass_started_at")
    if started_at:
        try:
            started_dt = datetime.fromisoformat(started_at)
        except ValueError:
            started_dt = now
    else:
        started_dt = now
    start_key = starpass_day_key(started_dt)
    current_key = starpass_day_key(now)
    try:
        start_date = datetime.fromisoformat(start_key).date()
        current_date = datetime.fromisoformat(current_key).date()
    except ValueError:
        return 1
    days_passed = max(0, (current_date - start_date).days)
    return min(len(STARPASS_REWARDS), days_passed + 1)


def apply_starpass_reward(record: dict, reward: dict) -> None:
    if reward.get("coins"):
        record["coins"] += reward["coins"]
    if reward.get("gems"):
        record["gems"] += reward["gems"]
    if reward.get("experience"):
        record["experience"] += reward["experience"]
    if reward.get("missiles"):
        missiles = reward["missiles"]
        if isinstance(missiles, dict):
            for key, count in missiles.items():
                record[key] = record.get(key, 0) + count
                record["missiles"] += count
        else:
            record["missiles"] += missiles
    if reward.get("defenses"):
        for key, count in reward["defenses"].items():
            record[key] = record.get(key, 0) + (count * 10)
    if reward.get("title"):
        titles = record.setdefault("available_titles", [])
        if reward["title"] not in titles:
            titles.append(reward["title"])


async def starpass_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    status = "✅ خریداری شده" if record["starpass_active"] else "❌ شما هنوز سولارپس را نخریده‌اید."
    await update.message.reply_text(
        "⭐ منوی سولارپس\n"
        f"{status}",
        reply_markup=starpass_menu_markup(),
    )


async def starpass_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if await reject_if_not_private(update):
        return
    rewards_list = "\n".join(
        f"روز {reward['day']} → {reward['label']}" for reward in STARPASS_REWARDS
    )
    await update.message.reply_text(
        "🛒 خرید سولارپس\n"
        "با خرید سولارپس امکانات ویژه‌ای دریافت می‌کنید:\n"
        "• دسترسی به جوایز روزانه اختصاصی\n"
        "• نمایش کنار نام شما در لیدربورد\n\n"
        f"هزینه خرید: {STARPASS_COST} جم 💎\n\n"
        "جوایز این فصل:\n"
        f"{rewards_list}",
        reply_markup=starpass_purchase_markup(),
    )


async def starpass_purchase_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query is None or update.effective_user is None:
        return
    query = update.callback_query
    await query.answer()
    record = get_user_record(update.effective_user.id)
    if record["starpass_active"]:
        await query.message.reply_text(
            "✅ سولارپس برای شما فعال است.",
            reply_markup=starpass_menu_markup(),
        )
        return
    if record["gems"] < STARPASS_COST:
        await query.message.reply_text(
            "❌ جم کافی برای خرید سولارپس ندارید.",
            reply_markup=starpass_purchase_markup(),
        )
        return
    record["gems"] -= STARPASS_COST
    record["starpass_active"] = True
    record["starpass_day"] = 1
    record["starpass_last_claim"] = None
    record["starpass_started_at"] = datetime.now().isoformat()
    save_user_data_store()
    await query.message.reply_text(
        "✅ سولارپس با موفقیت فعال شد!",
        reply_markup=starpass_menu_markup(),
    )


async def starpass_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    if not record["starpass_active"]:
        await update.message.reply_text(
            "❌ شما هنوز سولارپس خریداری نکردید.",
            reply_markup=starpass_menu_markup(),
        )
        return
    now = datetime.now()
    if not record.get("starpass_started_at"):
        record["starpass_started_at"] = now.isoformat()
    today_key = starpass_day_key(now)
    day_index = record.get("starpass_day", 1)
    allowed_day = starpass_allowed_day(record, now)
    if day_index > allowed_day:
        await update.message.reply_text(
            "⏳ هنوز روز بعدی سولارپس باز نشده است.",
            reply_markup=starpass_menu_markup(),
        )
        return
    if day_index > len(STARPASS_REWARDS):
        await update.message.reply_text(
            "✅ تمام جوایز این فصل را دریافت کردید.",
            reply_markup=starpass_menu_markup(),
        )
        return
    reward = STARPASS_REWARDS[day_index - 1]
    apply_starpass_reward(record, reward)
    record["starpass_last_claim"] = today_key
    record["starpass_day"] = min(day_index + 1, len(STARPASS_REWARDS))
    save_user_data_store()
    await update.message.reply_text(
        f"✅ جایزه روز {reward['day']} دریافت شد: {reward['label']}",
        reply_markup=starpass_menu_markup(),
    )


async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if await reject_if_not_private(update):
        return
    record = get_user_record(update.effective_user.id)
    today = datetime.now().date().isoformat()
    if record["last_daily_reward"] == today:
        await update.message.reply_text("🎁 جایزه روزانه امروزت رو قبلاً گرفتی.")
        return
    record["coins"] += 500
    record["last_daily_reward"] = today
    save_user_data_store()
    await update.message.reply_text("✅ 500 سکه جایزه روزانه بهت اضافه شد.")


async def admin_only_reply(update: Update, text: str):
    if update.message is None:
        return
    await update.message.reply_text(text)


async def notify_user(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    if user_id is None:
        return
    try:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    except Exception:
        return


async def set_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_coins <user_id> <amount> (یا ریپلای با /set_coins <amount>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        amount = int(context.args[0])
    else:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    record = get_user_record(user_id)
    record["coins"] += amount
    log_admin_action(user_id, update.effective_user.id, f"سکه: {amount:+d}")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} {amount:+d} سکه برای کاربر {user_id} تنظیم کرد.",
    )
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"💰 تغییر سکه: {amount:+d}\n"
            f"💰 موجودی جدید: {record['coins']}"
        ),
    )
    await admin_only_reply(update, f"✅ سکه کاربر {user_id} {amount:+d} شد.")


async def set_toman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_toman <user_id> <amount> (یا ریپلای با /set_toman <amount>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        amount = int(context.args[0])
    else:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    record = get_user_record(user_id)
    record["toman"] += amount
    log_admin_action(user_id, update.effective_user.id, f"تومان: {amount:+d}")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} {amount:+d} تومان برای کاربر {user_id} تنظیم کرد.",
    )
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"💵 تغییر تومان: {amount:+d}\n"
            f"💵 موجودی جدید: {record['toman']}"
        ),
    )
    await admin_only_reply(update, f"✅ تومان کاربر {user_id} {amount:+d} شد.")


async def set_gems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_gems <user_id> <amount> (یا ریپلای با /set_gems <amount>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        amount = int(context.args[0])
    else:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    record = get_user_record(user_id)
    record["gems"] += amount
    log_admin_action(user_id, update.effective_user.id, f"جم: {amount:+d}")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} {amount:+d} جم برای کاربر {user_id} تنظیم کرد.",
    )
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"💎 تغییر جم: {amount:+d}\n"
            f"💎 موجودی جدید: {record['gems']}"
        ),
    )
    await admin_only_reply(update, f"✅ جم کاربر {user_id} {amount:+d} شد.")


async def set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_level <user_id> <level> (یا ریپلای با /set_level <level>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        level = int(context.args[0])
    else:
        user_id = int(context.args[0])
        level = int(context.args[1])
    record = get_user_record(user_id)
    record["level"] = level
    record["experience"] = 0
    record["experience_needed"] = 100 + max(level - 1, 0) * 100
    update_league(record)
    save_user_data_store()
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"🔼 لول شما تنظیم شد: {level}"
        ),
    )
    await admin_only_reply(update, f"✅ لول کاربر {user_id} شد {level}.")


async def set_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_rank <user_id> <rank> (یا ریپلای با /set_rank <rank>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        rank = int(context.args[0])
    else:
        user_id = int(context.args[0])
        rank = int(context.args[1])
    record = get_user_record(user_id)
    record["rank"] = rank
    update_league(record)
    save_user_data_store()
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"🏆 رنک شما تنظیم شد: {rank}"
        ),
    )
    await admin_only_reply(update, f"✅ رنک کاربر {user_id} شد {rank}.")


async def reset_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    target_id = reply_user_id(update)
    if target_id is None:
        if not context.args:
            await admin_only_reply(update, "فرمت: /reset_rank <user_id> (یا ریپلای بدون آرگومان)")
            return
        try:
            target_id = int(context.args[0])
        except ValueError:
            await admin_only_reply(update, "شناسه عددی معتبر وارد کنید.")
            return
    record = get_user_record(int(target_id))
    record["rank"] = 0
    record["highest_rank"] = 0
    update_league(record)
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} رنک کاربر {target_id} را ریست کرد.",
    )
    await admin_only_reply(update, f"✅ رنک کاربر {target_id} ریست شد.")


async def adjust_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /adjust_balance <user_id> <coins_delta> [gems_delta] (یا ریپلای با /adjust_balance <coins_delta> [gems_delta])")
        return
    if reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        if len(context.args) < 1:
            await admin_only_reply(update, "❌ مقدار سکه را مشخص کنید.")
            return
        coins_delta = int(context.args[0])
        gems_delta = int(context.args[1]) if len(context.args) > 1 else 0
    else:
        user_id = int(context.args[0])
        coins_delta = int(context.args[1])
        gems_delta = int(context.args[2]) if len(context.args) > 2 else 0
    record = get_user_record(user_id)
    record["coins"] += coins_delta
    record["gems"] += gems_delta
    log_admin_action(
        user_id,
        update.effective_user.id,
        f"موجودی: سکه {coins_delta:+d} | جم {gems_delta:+d}",
    )
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        (
            f"ℹ️ ادمین {update.effective_user.id} موجودی کاربر {user_id} را تغییر داد:\n"
            f"سکه: {coins_delta:+d} | جم: {gems_delta:+d}"
        ),
    )
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"💰 تغییر سکه: {coins_delta:+d}\n"
            f"💎 تغییر جم: {gems_delta:+d}\n"
            f"💰 موجودی جدید: {record['coins']}\n"
            f"💎 موجودی جدید: {record['gems']}"
        ),
    )
    await admin_only_reply(
        update,
        f"✅ موجودی کاربر {user_id} بروزرسانی شد.\n"
        f"سکه: {record['coins']}\n"
        f"جم: {record['gems']}",
    )


async def list_all_assets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if not user_data_store:
        await admin_only_reply(update, "هیچ کاربری ثبت نشده است.")
        return
    lines = []
    for key, record in user_data_store.items():
        lines.append(
            f"🆔 {key} | 👤 {record.get('display_name', 'کاربر')} | "
            f"💰 {record.get('coins', 0)} | 💵 {record.get('toman', 0)} | "
            f"💎 {record.get('gems', 0)} | "
            f"⭐ {record.get('level', 1)} | 🏆 {record.get('rank', 0)}"
        )
    chunk_size = 30
    for i in range(0, len(lines), chunk_size):
        await update.message.reply_text("\n".join(lines[i : i + chunk_size]))


def format_user_assets(record: dict) -> str:
    missiles = []
    for _, items in MISSILE_CATEGORIES + CUSTOM_MISSILE_CATEGORIES:
        for label, key in items:
            count = record.get(key, 0)
            if count:
                missiles.append(f"{label}: {count}")
    defenses = []
    for item in DEFENSE_ITEMS:
        count = record.get(item["key"], 0)
        if count:
            defenses.append(f"{item['label']}: {count}")
    return (
        f"🆔 آیدی: {record.get('id')}\n"
        f"👤 نام: {record.get('display_name', 'کاربر')}\n"
        f"💰 سکه: {record.get('coins', 0)}\n"
        f"💵 تومان: {record.get('toman', 0)}\n"
        f"💎 جم: {record.get('gems', 0)}\n"
        f"🏆 رنک: {record.get('rank', 0)} (بالاترین: {record.get('highest_rank', 0)})\n"
        f"⭐ لول: {record.get('level', 1)} | لیگ: {record.get('league', 'نامشخص')}\n"
        f"🛡️ سپر فعال: {record.get('shield_active', False)}\n"
        f"🧨 موشک‌ها: {', '.join(missiles) if missiles else 'ندارد'}\n"
        f"🛡️ پدافندها: {', '.join(defenses) if defenses else 'ندارد'}\n"
        f"کلن: {record.get('clan_id') or 'ندارد'}"
    )


async def user_assets_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1:
        await admin_only_reply(update, "فرمت: /user_assets <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await admin_only_reply(update, "آیدی باید عددی باشد.")
        return
    record = get_user_record(user_id)
    await admin_only_reply(update, format_user_assets(record))


async def reset_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    for record in user_data_store.values():
        current = record.get("rank", 0)
        record["rank"] = int(current * 0.05)
        update_league(record)
    save_user_data_store()
    await admin_only_reply(update, "✅ کاپ همه کاربران ریست شد (۵٪ باقی ماند).")


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /ban <user_id> <minutes> (یا ریپلای با /ban <minutes>)")
        return
    if reply_user_id(update) is not None and len(context.args) == 1:
        user_id = reply_user_id(update)
        minutes = int(context.args[0])
    else:
        user_id = int(context.args[0])
        minutes = int(context.args[1])
    if minutes <= 0:
        await admin_only_reply(update, "مدت بن باید بیشتر از صفر باشد.")
        return
    record = get_user_record(user_id)
    record["banned"] = False
    record["banned_until"] = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    save_user_data_store()
    await admin_only_reply(update, f"🚫 کاربر {user_id} به مدت {minutes} دقیقه بن شد.")


async def permanent_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /bang <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    record = get_user_record(user_id)
    record["banned"] = True
    record["banned_until"] = None
    save_user_data_store()
    await admin_only_reply(update, f"🚫 کاربر {user_id} دائمی بن شد.")


async def delete_clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1:
        await admin_only_reply(update, "فرمت: /delete_clan <clan_id>")
        return
    clan_id = context.args[0].upper()
    success, message = _delete_clan_by_id(clan_id)
    await admin_only_reply(update, message)


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /unban <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    record = get_user_record(user_id)
    record["banned"] = False
    record["banned_until"] = None
    save_user_data_store()
    await admin_only_reply(update, f"✅ کاربر {user_id} از بن خارج شد.")


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /add_admin <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    ADMIN_IDS.add(user_id)
    await admin_only_reply(update, f"✅ کاربر {user_id} ادمین شد.")


async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /remove_admin <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    if user_id == PRIMARY_ADMIN_ID and update.effective_user.id != PRIMARY_ADMIN_ID:
        return
    if user_id in ADMIN_IDS:
        ADMIN_IDS.remove(user_id)
        await admin_only_reply(update, f"✅ کاربر {user_id} از ادمین خارج شد.")
    else:
        await admin_only_reply(update, "این کاربر ادمین نیست.")


async def give_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /give_title <user_id> <title> (یا ریپلای با /give_title <title>)")
        return
    if reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        title = " ".join(context.args).strip()
    else:
        user_id = int(context.args[0])
        title = " ".join(context.args[1:]).strip()
    if not title:
        await admin_only_reply(update, "تایتل نمی‌تواند خالی باشد.")
        return
    record = get_user_record(user_id)
    titles = record.setdefault("available_titles", [])
    if title not in titles:
        titles.append(title)
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} تایتل «{title}» را به کاربر {user_id} داد.",
    )
    await notify_user(
        context,
        user_id,
        f"🎗️ یک تایتل جدید دریافت کردید: {title}\n"
        "از منوی شخصی‌سازی انتخابش کنید.",
    )
    await admin_only_reply(update, f"✅ تایتل «{title}» به کاربر {user_id} داده شد.")


def _remove_user_everywhere(user_id: int) -> bool:
    key = str(user_id)
    removed = False
    if key in user_data_store:
        del user_data_store[key]
        removed = True
    for record in user_data_store.values():
        targets = record.get("revenge_targets", [])
        if user_id in targets:
            record["revenge_targets"] = [tid for tid in targets if tid != user_id]
            record["revenge_available"] = bool(record["revenge_targets"])
            removed = True
    clans_changed = False
    for clan in clan_data_store.values():
        members = clan.get("members", [])
        if user_id in members:
            clan["members"] = [mid for mid in members if mid != user_id]
            clans_changed = True
        subs = clan.get("sub_leaders", [])
        if user_id in subs:
            clan["sub_leaders"] = [sid for sid in subs if sid != user_id]
            clans_changed = True
        requests = clan.get("requests", [])
        filtered_requests = [req for req in requests if req.get("user_id") != user_id]
        if len(filtered_requests) != len(requests):
            clan["requests"] = filtered_requests
            clans_changed = True
        if clan.get("leader_id") == user_id:
            clan["leader_id"] = None
            clans_changed = True
    if removed:
        save_user_data_store()
    if clans_changed:
        save_clan_data_store()
    return removed


def _delete_clan_by_id(clan_id: str) -> tuple[bool, str]:
    clan = clan_data_store.get(clan_id)
    if not clan:
        return False, "❌ کلن پیدا نشد."
    members = clan.get("members", [])
    for member_id in members:
        user_record = get_user_record(int(member_id))
        user_record["clan_id"] = None
        user_record["clan_war_id"] = None
        user_record["clan_war_attacks_left"] = 0
    clan_data_store.pop(clan_id, None)
    save_user_data_store()
    save_clan_data_store()
    return True, "✅ کلن حذف شد."


async def reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /reset_user <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    removed = _remove_user_everywhere(int(user_id))
    if removed:
        await admin_only_reply(update, f"✅ کاربر {user_id} به طور کامل ریست/حذف شد.")
    else:
        await admin_only_reply(update, f"ℹ️ کاربر {user_id} داده‌ای نداشت یا قبلاً پاک شده بود.")


async def reset_all_assets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    missile_keys = set(MISSILE_NAME_TO_KEY.values())
    defense_keys = {item["key"] for item in DEFENSE_ITEMS}
    for record in user_data_store.values():
        record["coins"] = 0
        record["gems"] = 0
        record["toman"] = 0
        record["missiles"] = 0
        record["level"] = 1
        record["experience"] = 0
        record["experience_needed"] = 100
        record["rank"] = 0
        record["highest_rank"] = 0
        record["league"] = "🎗 تازه‌کار"
        record["gold_mine_stored"] = 0
        record["gold_mine_level"] = 1
        record["gold_mine_last_collect"] = None
        record["gem_mine_last_collect"] = None
        record["daily_boxes_opened"] = 0
        record["last_box_open_date"] = None
        record["shield_active"] = False
        record["shield_until"] = None
        record["starpass_active"] = False
        record["starpass_day"] = 1
        record["starpass_last_claim"] = None
        record["atlas_level"] = 1
        record["daily_coin_transfer"] = 0
        record["last_coin_transfer_date"] = None
        record["last_global_attack_open"] = None
        record["last_attack_from"] = None
        record["revenge_available"] = False
        record["revenge_targets"] = []
        record["last_group_attack"] = None
        record["daily_attacks_done"] = 0
        record["daily_attacks_received"] = 0
        record["last_attack_day"] = None
        record["daily_duels_started"] = 0
        record["last_duel_day"] = None
        record["active_defense"] = None
        record["selected_title"] = None
        for key in missile_keys:
            record[key] = 0
        for key in defense_keys:
            record[key] = 0
    save_user_data_store()
    await admin_only_reply(update, "✅ تمام دارایی کاربران صفر شد.")


async def reset_solarpass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /reset_solarpass <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    record = get_user_record(user_id)
    record["starpass_active"] = True
    record["starpass_day"] = 1
    record["starpass_last_claim"] = None
    record["starpass_started_at"] = datetime.now().isoformat()
    log_admin_action(user_id, update.effective_user.id, "ریست سولارپس")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} سولارپس کاربر {user_id} را ریست کرد.",
    )
    await notify_user(
        context,
        user_id,
        "⭐ سولارپس شما به روز اول بازنشانی شد.",
    )
    await admin_only_reply(update, f"✅ سولارپس کاربر {user_id} به روز اول ریست شد.")


async def reset_solarpass_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    reset_count = 0
    for record in user_data_store.values():
        if record.get("starpass_active"):
            record["starpass_active"] = False
            record["starpass_day"] = 1
            record["starpass_last_claim"] = None
            record["starpass_started_at"] = None
            user_id = record.get("id")
            if user_id is not None:
                log_admin_action(user_id, update.effective_user.id, "حذف سولارپس (همه)")
            reset_count += 1
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} سولارپس {reset_count} کاربر را حذف کرد.",
    )
    await admin_only_reply(update, f"✅ سولارپس {reset_count} کاربر حذف شد.")


async def admin_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /admin_history <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    record = get_user_record(user_id)
    history = record.get("admin_history", [])
    if not history:
        await admin_only_reply(update, f"هیچ سابقه‌ای برای کاربر {user_id} ثبت نشده است.")
        return
    lines = []
    for entry in history[-20:]:
        lines.append(
            f"{entry.get('at', '')} | ادمین {entry.get('admin_id', 'نامشخص')} | {entry.get('action', '')}"
        )
    await admin_only_reply(
        update,
        "📜 تاریخچه اقدامات ادمین\n" + "\n".join(lines),
    )


async def admin_protection_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    record = get_user_record(update.effective_user.id)
    record["admin_protection"] = True
    save_user_data_store()
    await admin_only_reply(update, "🛡️ حالت محافظت ادمین فعال شد؛ دیگران نمی‌توانند به شما حمله کنند.")


async def admin_protection_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    record = get_user_record(update.effective_user.id)
    record["admin_protection"] = False
    save_user_data_store()
    await admin_only_reply(update, "⚔️ حالت محافظت ادمین غیرفعال شد؛ دیگران می‌توانند به شما حمله کنند.")


async def set_mine_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /set_mine_level <user_id> <level> (یا ریپلای با /set_mine_level <level>)")
        return
    if len(context.args) == 1 and reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        level = int(context.args[0])
    else:
        user_id = int(context.args[0])
        level = int(context.args[1])
    if level < 1:
        await admin_only_reply(update, "لول باید بیشتر از صفر باشد.")
        return
    record = get_user_record(user_id)
    record["gold_mine_level"] = level
    save_user_data_store()
    await admin_only_reply(update, f"✅ لول معدن کاربر {user_id} روی {level} تنظیم شد.")


async def remove_missile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 3 and reply_user_id(update) is None:
        await admin_only_reply(
            update,
            "فرمت: /remove_missile <user_id> <missile_name> <count> (یا ریپلای با /remove_missile <missile_name> <count>)",
        )
        return
    if reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        count = parse_positive_int(context.args[-1] or "")
        missile_name = " ".join(context.args[:-1])
    else:
        user_id = int(context.args[0])
        count = parse_positive_int(context.args[-1] or "")
        missile_name = " ".join(context.args[1:-1])
    if count is None:
        await admin_only_reply(update, "تعداد نامعتبر است.")
        return
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await admin_only_reply(update, "نام موشک معتبر نیست.")
        return
    record = get_user_record(user_id)
    current = record.get(missile_key, 0)
    new_value = max(0, current - count)
    record[missile_key] = new_value
    record["missiles"] = max(0, record.get("missiles", 0) - (current - new_value))
    save_user_data_store()
    await admin_only_reply(
        update,
        f"✅ {count} موشک {missile_name} از کاربر {user_id} کم شد.",
    )


async def remove_all_patriot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار را دارد.")
        return
    removed_total = 0
    for record in user_data_store.values():
        existing = record.get("patriot_missiles", 0)
        if existing:
            removed_total += existing
            record["missiles"] = max(0, record.get("missiles", 0) - existing)
            record["patriot_missiles"] = 0
    save_user_data_store()
    await admin_only_reply(
        update,
        f"✅ همه موشک‌های پاتریوت حذف شد. مجموع حذف‌شده: {removed_total}",
    )


async def grant_solarpass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 1 and reply_user_id(update) is None:
        await admin_only_reply(update, "فرمت: /grant_solarpass <user_id> (یا ریپلای بدون آرگومان)")
        return
    user_id = reply_user_id(update) if reply_user_id(update) is not None else int(context.args[0])
    record = get_user_record(user_id)
    record["starpass_active"] = True
    record["starpass_day"] = 1
    record["starpass_last_claim"] = None
    record["starpass_started_at"] = datetime.now().isoformat()
    log_admin_action(user_id, update.effective_user.id, "فعال‌سازی سولارپس")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} سولارپس را برای کاربر {user_id} فعال کرد.",
    )
    await admin_only_reply(update, f"✅ سولارپس برای کاربر {user_id} فعال شد.")


async def give_missile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 3 and reply_user_id(update) is None:
        await admin_only_reply(
            update,
            "فرمت: /give_missile <user_id> <missile_name> <count> (یا ریپلای با /give_missile <missile_name> <count>)",
        )
        return
    if reply_user_id(update) is not None:
        user_id = reply_user_id(update)
        count = parse_positive_int(context.args[-1] or "")
        missile_name = " ".join(context.args[:-1])
    else:
        user_id = int(context.args[0])
        count = parse_positive_int(context.args[-1] or "")
        missile_name = " ".join(context.args[1:-1])
    if count is None:
        await admin_only_reply(update, "تعداد نامعتبر است.")
        return
    missile_key = find_missile_key(missile_name)
    if missile_key is None:
        await admin_only_reply(update, "نام موشک معتبر نیست.")
        return
    record = get_user_record(user_id)
    record[missile_key] = record.get(missile_key, 0) + count
    record["missiles"] = record.get("missiles", 0) + count
    log_admin_action(user_id, update.effective_user.id, f"موشک {missile_name}: {count:+d}")
    save_user_data_store()
    await notify_primary_admin_of_action(
        context,
        update.effective_user.id,
        f"ℹ️ ادمین {update.effective_user.id} تعداد {count} از موشک {missile_name} به کاربر {user_id} داد.",
    )
    await notify_user(
        context,
        user_id,
        (
            "🛠 بروزرسانی ادمین\n"
            f"🧨 موشک: {missile_name}\n"
            f"📦 تعداد: {count}"
        ),
    )
    await admin_only_reply(
        update,
        f"✅ {count} موشک {missile_name} به کاربر {user_id} اضافه شد.",
    )


async def create_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if not is_admin(update.effective_user.id):
        await admin_only_reply(update, "⛔️ فقط ادمین اجازه این کار رو داره.")
        return
    if len(context.args) < 2:
        await admin_only_reply(update, "فرمت: /create_gift <uses> <amount>")
        return
    uses = int(context.args[0])
    amount = int(context.args[1])
    if uses <= 0 or amount <= 0:
        await admin_only_reply(update, "تعداد استفاده و مبلغ باید بیشتر از صفر باشه.")
        return
    code = generate_gift_code()
    gift_codes[code] = {"uses_left": uses, "amount": amount, "redeemed_by": []}
    await admin_only_reply(
        update,
        f"🎁 کد هدیه ساخته شد: {code}\n"
        f"تعداد استفاده: {uses}\n"
        f"مبلغ: {amount}",
    )

async def redeem_gift_code_for_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, code: str
):
    if update.message is None or update.effective_user is None:
        return
    gift = gift_codes.get(code)
    if gift is None or gift.get("uses_left", 0) <= 0:
        await update.message.reply_text("این کد هدیه معتبر نیست یا تمام شده.")
        return
    redeemed_by = gift.setdefault("redeemed_by", [])
    if update.effective_user.id in redeemed_by:
        await update.message.reply_text("❌ این کد را قبلاً استفاده کرده‌اید.")
        return
    gift["uses_left"] -= 1
    redeemed_by.append(update.effective_user.id)
    record = get_user_record(update.effective_user.id)
    record["coins"] += gift["amount"]
    save_user_data_store()
    await update.message.reply_text(
        f"✅ کد هدیه اعمال شد! {gift['amount']} سکه گرفتی.\n"
        f"استفاده باقی‌مانده: {gift['uses_left']}"
    )


async def redeem_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if len(context.args) < 1:
        await update.message.reply_text("فرمت: /redeem <code>")
        return
    code = normalize_gift_code(context.args[0])
    await redeem_gift_code_for_user(update, context, code)


def create_flask_app() -> Flask:
    load_user_data_store()
    load_pending_payments()
    load_clan_data_store()
    app = Flask(__name__)

    @app.route("/verify", methods=["GET"])
    def verify_payment():
        status = request.args.get("Status")
        authority = request.args.get("Authority")
        user_id = request.args.get("user_id")
        if not authority or not user_id:
            return jsonify({"ok": False, "message": "Missing parameters"}), 400
        payment = pending_payments.get(authority)
        if payment is None:
            return jsonify({"ok": False, "message": "Payment not found"}), 404
        if str(payment.get("user_id")) != str(user_id):
            return jsonify({"ok": False, "message": "User mismatch"}), 400
        if status != "OK":
            return jsonify({"ok": False, "message": "Payment canceled"}), 400
        amount_toman = payment.get("amount_toman", 0)
        amount_rial = amount_toman * 10
        payload = {
            "merchant_id": ZARINPAL_MERCHANT_ID,
            "amount": amount_rial,
            "authority": authority,
        }
        try:
            response = requests.post(ZARINPAL_VERIFY_URL, json=payload, timeout=15)
            data = response.json()
        except Exception:
            return jsonify({"ok": False, "message": "Verify failed"}), 500
        code = data.get("data", {}).get("code")
        if code not in {100, 101}:
            return jsonify({"ok": False, "message": "Verify rejected"}), 400
        record = get_user_record(int(user_id))
        record["toman"] += amount_toman
        save_user_data_store()
        pending_payments.pop(authority, None)
        save_pending_payments()
        if telegram_app is not None:
            try:
                telegram_app.bot.send_message(
                    chat_id=int(user_id),
                    text=(
                        "✅ پرداخت با موفقیت انجام شد.\n"
                        f"💼 مبلغ: {amount_toman} تومان\n"
                        f"💰 موجودی جدید: {record['toman']} تومان"
                    ),
                )
            except Exception:
                pass
        return jsonify({"ok": True, "message": "Payment verified"}), 200

    return app


async def log_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger = logging.getLogger(__name__)
    logger.exception("Unhandled exception while handling update: %s", update, exc_info=context.error)


def main():
    global telegram_app
    setup_logging()
    load_user_data_store()
    load_pending_payments()
    load_clan_data_store()
    app = ApplicationBuilder().token(TOKEN).build()
    telegram_app = app

    app.add_handler(MessageHandler(filters.ALL, membership_message_gate), group=-1)
    app.add_handler(CallbackQueryHandler(check_subscriptions_callback, pattern="^check_subs$"), group=-1)
    app.add_handler(CallbackQueryHandler(membership_callback_gate, pattern=".*"), group=-1)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", invite_link))
    app.add_handler(CommandHandler("set_coins", set_coins))
    app.add_handler(CommandHandler("set_toman", set_toman))
    app.add_handler(CommandHandler("set_gems", set_gems))
    app.add_handler(CommandHandler("set_level", set_level))
    app.add_handler(CommandHandler("set_rank", set_rank))
    app.add_handler(CommandHandler("reset_rank", reset_rank))
    app.add_handler(CommandHandler("adjust_balance", adjust_balance))
    app.add_handler(CommandHandler("list_assets", list_all_assets))
    app.add_handler(CommandHandler("user_assets", user_assets_by_id))
    app.add_handler(CommandHandler("reset_caps", reset_caps))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("bang", permanent_ban))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("give_title", give_title))
    app.add_handler(CommandHandler("reset_user", reset_user))
    app.add_handler(CommandHandler("reset_all_assets", reset_all_assets))
    app.add_handler(CommandHandler("reset_solarpass", reset_solarpass))
    app.add_handler(CommandHandler("reset_solarpass_all", reset_solarpass_all))
    app.add_handler(CommandHandler("admin_history", admin_history))
    app.add_handler(CommandHandler("set_mine_level", set_mine_level))
    app.add_handler(CommandHandler("remove_missile", remove_missile))
    app.add_handler(CommandHandler("remove_all_patriot", remove_all_patriot))
    app.add_handler(CommandHandler("grant_solarpass", grant_solarpass))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("give_missile", give_missile))
    app.add_handler(CommandHandler("admin_protection_on", admin_protection_on))
    app.add_handler(CommandHandler("admin_protection_off", admin_protection_off))
    app.add_handler(CommandHandler("create_gift", create_gift_code))
    app.add_handler(CommandHandler("redeem", redeem_gift_code))
    app.add_handler(CommandHandler("clan_info", clan_info_by_id))
    app.add_handler(CommandHandler("delete_clan", delete_clan))
    app.add_handler(CallbackQueryHandler(loot_box_open_action, pattern="^box_open_"))
    app.add_handler(CallbackQueryHandler(redline_wheel_action, pattern="^wheel_redline_"))
    app.add_handler(CallbackQueryHandler(global_attack_action, pattern="^global_attack_"))
    app.add_handler(CallbackQueryHandler(revenge_attack_action, pattern="^revenge_"))
    app.add_handler(CallbackQueryHandler(duel_request_action, pattern="^duel_"))
    app.add_handler(CallbackQueryHandler(ranking_action, pattern="^ranking_"))
    app.add_handler(CallbackQueryHandler(clan_action, pattern="^clan_"))
    app.add_handler(CallbackQueryHandler(help_action, pattern="^help_"))
    app.add_handler(
        CallbackQueryHandler(starpass_purchase_confirm, pattern="^starpass_purchase_")
    )
    app.add_handler(MessageHandler(filters.Regex("^گردونه 🎡$"), wheel_menu))
    app.add_handler(MessageHandler(filters.Regex("^رد لاین 🔴$"), wheel_choice))
    app.add_handler(MessageHandler(filters.Regex("^حمله جهانی 🌐$"), global_attack_menu))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت به منوی اصلی ↩️$"), back_to_main_menu))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت ↩️$"), back_to_main_menu))
    app.add_handler(MessageHandler(filters.Regex("^دارایی 📦$"), assets_menu))
    app.add_handler(MessageHandler(filters.Regex("^فروشگاه 🛒$"), store_menu))
    app.add_handler(MessageHandler(filters.Regex("^خرید آیتم 💳$"), shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^تبادل سکه 💸$"), coin_transfer_menu))
    app.add_handler(MessageHandler(filters.Regex("^کلن 👥$"), clan_menu))
    app.add_handler(MessageHandler(filters.Regex("^معدن طلا ⛏️$"), gold_mine_menu))
    app.add_handler(MessageHandler(filters.Regex("^معدن جم 💎$"), gem_mine_menu))
    app.add_handler(MessageHandler(filters.Regex("^افزایش موجودی 🔁$"), topup_menu))
    app.add_handler(MessageHandler(filters.Regex("^ارسال رسید 🧾$"), topup_receipt_menu))
    app.add_handler(MessageHandler(filters.Regex("^پدافند ها 🛡️$"), defense_status_menu))
    app.add_handler(MessageHandler(filters.Regex("^پنل ادمین 🛠️$"), admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^راهنما ❓$"), help_menu))
    app.add_handler(MessageHandler(filters.Regex("^پک های ویژه 💥$"), special_packs_menu))
    app.add_handler(MessageHandler(filters.Regex("^پک های جم 💎$"), gem_packs_menu))
    app.add_handler(MessageHandler(filters.Regex("^پک های سکه 💰$"), coin_packs_menu))
    app.add_handler(MessageHandler(filters.Regex("^خرید لول ⏫$"), shop_placeholder))
    app.add_handler(MessageHandler(filters.Regex("^باندل ها 🥷$"), bundle_packs_menu))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت به دسته ها ◀️$"), shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^سکه\\s*\\d+\\s*🛒$"), coin_pack_purchase))
    app.add_handler(MessageHandler(filters.Regex("^موشک 🚀$"), missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^پدافند 🛡️$"), defense_shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^سپر 🛡️$"), shield_shop_menu))
    app.add_handler(MessageHandler(filters.Regex("^💎\\s*\\d+\\s*-"), shield_purchase))
    app.add_handler(MessageHandler(filters.Regex("^کروز 🚀$"), cruise_missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^بالستیک 🚀$"), ballistic_missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^هایپرسونیک 🚀$"), hypersonic_missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^شیمیایی 🚀$"), chemical_missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^هسته‌ای 🚀$"), nuclear_missiles_menu))
    app.add_handler(MessageHandler(filters.Regex("^اطلس 💰"), atlas_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^قدر 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^خیبرشکن 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^خرمشهر 💰"), khorramshahr_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^عماد 💰"), emad_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^سجیل 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^شهاب 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^طوفان 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^الماس 💰"), generic_missile_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("🛡️\\s*-\\s*\\d+$"), defense_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^شیمیایی 💰"), chemical_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^هسته‌ای 💰"), nuclear_purchase_prompt))
    app.add_handler(MessageHandler(filters.Regex("^خروج از خرید ◀️$"), back_to_main_menu))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت به منوی فروشگاه ↩️$"), back_to_shop))
    app.add_handler(MessageHandler(filters.Regex("^جایزه روزانه 🎁$"), daily_reward))
    app.add_handler(MessageHandler(filters.Regex("^رنکینگ 🏆$"), ranking_menu))
    app.add_handler(CommandHandler("rank_info", rank_info))
    app.add_handler(MessageHandler(filters.Regex("^جمع‌آوری سکه 💰$"), gold_mine_collect))
    app.add_handler(MessageHandler(filters.Regex("^جمع‌آوری جم 💎$"), gem_mine_collect))
    app.add_handler(MessageHandler(filters.Regex("^ارتقای معدن ⛏️$"), gold_mine_upgrade))
    app.add_handler(MessageHandler(filters.Regex("^پشتیبانی 📞$"), support_menu))
    app.add_handler(MessageHandler(filters.Regex("^سولارپس ⭐$"), starpass_menu))
    app.add_handler(MessageHandler(filters.Regex("^خرید سولارپس 🛒$"), starpass_purchase))
    app.add_handler(MessageHandler(filters.Regex("^دریافت جوایز 🎁$"), starpass_rewards))
    app.add_handler(MessageHandler(filters.Regex("^شخصی سازی 🎨$"), customization_menu))
    app.add_handler(MessageHandler(filters.Regex("^جستجو کلن 🔍$"), clan_search_menu))
    app.add_handler(MessageHandler(filters.Regex("^ساخت کلن 🏗️$"), clan_create_menu))
    app.add_handler(MessageHandler(filters.Regex("^اعضا 👥$"), clan_members_menu))
    app.add_handler(MessageHandler(filters.Regex("^درخواست‌ها 📩$"), clan_requests_menu))
    app.add_handler(MessageHandler(filters.Regex("^ارتقا کلن ⬆️$"), clan_upgrade_menu))
    app.add_handler(MessageHandler(filters.Regex("^ترک کلن 🚪$"), clan_leave))
    app.add_handler(MessageHandler(filters.Regex("^تنظیم تگ 🏷️$"), clan_set_tag_menu))
    app.add_handler(MessageHandler(filters.Regex("^پاک کردن تگ ❌$"), clan_clear_tag))
    app.add_handler(MessageHandler(filters.Regex("^تغییر لیدر 👑$"), clan_leader_change_prompt))
    app.add_handler(MessageHandler(filters.Regex("^ساب لیدر 👥$"), clan_sub_leader_prompt))
    app.add_handler(MessageHandler(filters.Regex("^تانک کلن 🪖$"), clan_tank_menu))
    app.add_handler(MessageHandler(filters.Regex("^خرید تانک 🪖$"), clan_tank_upgrade))
    app.add_handler(MessageHandler(filters.Regex("^ارتقا تانک 🪖$"), clan_tank_upgrade))
    app.add_handler(MessageHandler(filters.Regex("^قلعه کلن 🏰$"), clan_castle_menu))
    app.add_handler(MessageHandler(filters.Regex("^خرید قلعه 🏰$"), clan_castle_upgrade))
    app.add_handler(MessageHandler(filters.Regex("^ارتقا قلعه 🏰$"), clan_castle_upgrade))
    app.add_handler(MessageHandler(filters.Regex("^کلن وار ⚔️$"), clan_war_menu))
    app.add_handler(MessageHandler(filters.Regex("^شروع کلن وار ⚔️$"), clan_war_start))
    app.add_handler(MessageHandler(filters.Regex("^حمله در وار ⚔️$"), clan_war_attack_prompt))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت به منوی کلن ↩️$"), clan_menu))
    app.add_handler(MessageHandler(filters.Regex("^حذف عضو ➖$"), clan_remove_member_prompt))
    app.add_handler(MessageHandler(filters.Regex("^افکت های حمله ✨$"), customization_placeholder))
    app.add_handler(MessageHandler(filters.Regex("^تایتل ها 🎗️$"), customization_titles_menu))
    app.add_handler(MessageHandler(filters.Regex("^چت استیکر ⭐$"), chat_sticker_menu))
    for label, _ in STARPASS_CHAT_STICKERS:
        app.add_handler(MessageHandler(filters.Regex(f"^{re.escape(label)}$"), chat_sticker_choice))
    app.add_handler(MessageHandler(filters.Regex("^حذف استیکر ❌$"), chat_sticker_choice))
    app.add_handler(MessageHandler(filters.Regex("^بازگشت به شخصی سازی ↩️$"), back_to_customization))
    app.add_handler(MessageHandler(filters.Regex("^فعال کردن تیر بار 🛡️$"), defense_activate_tirbar))
    app.add_handler(MessageHandler(filters.Regex("^فعال کردن .+ 🛡️$"), defense_activate_generic))
    app.add_handler(MessageHandler(filters.Regex("^غیرفعال کردن پدافند ❌$"), defense_deactivate))
    app.add_handler(MessageHandler(filters.Regex("^(دوئل|فایت)$"), start_duel))
    app.add_handler(
        MessageHandler(filters.Regex("^حمله\\s+.+$") & ~filters.COMMAND, group_attack_by_reply)
    )
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            group_loot_box_tracker,
        ),
        group=1,
    )
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_topup_receipt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    app.add_error_handler(log_error)

    def handle_shutdown(signum, frame):
        logging.getLogger(__name__).info("Shutdown signal received: %s", signum)
        save_user_data_store(force=True)
        save_clan_data_store()
        save_pending_payments()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logging.getLogger(__name__).info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


flask_app = create_flask_app()


if __name__ == "__main__":
    main()
