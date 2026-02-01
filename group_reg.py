import random
import string
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    CommandHandler, 
    filters
)

# فرض بر این است که تابع start در فایل اصلی تعریف شده و اینجا ایمپورت می‌شود
# اگر خطا داد، می‌توانید تابع start را هم به ابتدای این فایل بیاورید
try:
    from main import start 
except ImportError:
    # تعریف موقت تابع استارت اگر ایمپورت نشد (برای جلوگیری از کرش)
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

# ================= CONFIG =================
GROUP_CHANNEL_ID = "@classLink_online" 
ADMIN_ID = 7997819976
CHANNEL_TAG = "@UniVoiceHub"
DB_FILE = "groups_data.json"

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

# ================= STATES =================
G_RULES, G_NAME, G_PROF, G_ID, G_DAYS, G_TIME, G_BOT_ADD = range(100, 107)

# ================= HANDLERS =================

async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await query.message.edit_text(
        "✨ **به بخش ثبت گروه کلاسی خوش آمدید**\n\nبرای ثبت مشخصات گروه خود روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_RULES 

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rules_text = (
        "📜 **قوانین و شرایط ثبت گروه:**\n\n"
        "1 - ربات باید حتماً در گروه ادمین باشد.\n"
        "2 - نام درس، استاد و مشخصه باید دقیق وارد شود.\n"
        "3 - مسئولیت محتوای تبادل شده در گروه با سازنده آن است.\n"
        "4 - مسئولیت پذیرش افراد به عهده شما خواهد بود.\n"
        "5 - گروه‌های غیردرسی تایید نخواهند شد.\n\n"
        f"🆔 {CHANNEL_TAG}\n🆔 {GROUP_CHANNEL_ID}"
    )
    keyboard = [[InlineKeyboardButton("✅ بله، قبول دارم", callback_data="g_accept")],
                [InlineKeyboardButton("❌ انصراف و بازگشت", callback_data="start")]]
    await query.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📍 **گام اول:**\n\nنام درس را وارد کنید:")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 **گام دوم:**\n\nنام استاد درس *{update.message.text}* را وارد کنید:", parse_mode="Markdown")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 **گام سوم:**\n\nشماره مشخصه درس را وارد کنید:")
    return G_DAYS

async def ask_g_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    await update.message.reply_text("📍 **گام چهارم:**\n\nروزهای برگزاری کلاس را وارد کنید:")
    return G_TIME

async def ask_g_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_days"] = update.message.text
    await update.message.reply_text("📍 **گام آخر:**\n\nساعت برگزاری کلاس را وارد کنید:")
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_time"] = update.message.text
    owner_id = update.effective_user.id
    ref_id = str(random.randint(100000, 999999))
    user_token = 'UNITOK-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    db = load_db()
    db[ref_id] = {
        "owner_id": owner_id,
        "name": context.user_data["g_name"],
        "prof": context.user_data["g_prof"],
        "id": context.user_data["g_id"],
        "days": context.user_data["g_days"],
        "time": context.user_data["g_time"],
        "token": user_token
    }
    save_db(db)
    
    admin_text = (f"🔔 **درخواست گروه جدید**\n\n📚 درس: {db[ref_id]['name']}\n👨‍🏫 استاد: {db[ref_id]['prof']}\n"
                  f"📅 روزها: {db[ref_id]['days']}\n🕒 ساعت: {db[ref_id]['time']}\n🔢 مشخصه: {db[ref_id]['id']}")
    
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_pub:{ref_id}")],
                [InlineKeyboardButton("❌ رد درخواست", callback_data=f"g_rej:{ref_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text(f"📨 درخواست ارسال شد.\n🔑 توکن شما:\n`{user_token}`", parse_mode="Markdown")
    return ConversationHandler.END

async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":")
    action, ref_id = parts[0], parts[1]
    
    db = load_db()
    data = db.get(ref_id)
    if not data: return

    if action == "g_pub":
        channel_kb = [[InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{ref_id}")]]
        text = (f"📚 **گروه کلاسی جدید**\n\n📖 درس: {data['name']}\n👨‍🏫 استاد: {data['prof']}\n"
                f"📅 روز: {data['days']}\n🕒 ساعت: {data['time']}\n🔢 مشخصه: {data['id']}\n\n🆔 {CHANNEL_TAG}")
        await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=text, reply_markup=InlineKeyboardMarkup(channel_kb), parse_mode="Markdown")
        await q.message.edit_text("✅ منتشر شد.")

# کانورزیشن با اصلاح دکمه افزودن و بازگشت
group_conv = ConversationHandler(
    entry_points=[
        # وقتی از منوی اصلی روی دکمه "ثبت گروه" کلیک میشه
        CallbackQueryHandler(start_group_reg, pattern="^start_group_reg$"),
        # وقتی مستقیماً روی "افزودن گروه جدید" (دکمه سبز) کلیک میشه
        CallbackQueryHandler(show_rules, pattern="^g_add$")
    ],
    states={
        G_RULES: [
            CallbackQueryHandler(show_rules, pattern="^g_add$"),
            CallbackQueryHandler(start, pattern="^start$")
        ],
        G_NAME: [
            CallbackQueryHandler(ask_g_name, pattern="^g_accept$"),
            CallbackQueryHandler(start, pattern="^start$")
        ],
        # بقیه استیت‌ها رو دست نزن، فقط مطمئن شو ترتیبشون در فایل درسته
        G_PROF: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_prof)],
        G_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_id)],
        G_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_days)],
        G_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_time)],
        G_BOT_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_bot_add)],
    },
    fallbacks=[CallbackQueryHandler(start, pattern="^start$")],
    per_chat=True,
    per_message=False
)
