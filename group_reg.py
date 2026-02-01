import random
import string
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= CONFIG =================
GROUP_CHANNEL_ID = "@classLink_online" # آیدی کانال را اینجا وارد کنید
ADMIN_ID = 7997819976
CHANNEL_TAG = "@UniVoiceHub"
DB_FILE = "groups_data.json"

# توابع مدیریت دیتابیس
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ================= STATES =================
G_RULES, G_NAME, G_PROF, G_ID, G_DAYS, G_TIME, G_BOT_ADD = range(100, 107)

# ================= HANDLERS =================

async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(
        "✨ **به بخش ثبت گروه کلاسی خوش آمدید**\n\nبرای ثبت مشخصات گروه خود روی دکمه زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rules_text = (
        "📜 **قوانین و شرایط ثبت گروه:**\n\n"
        "1 - ربات باید حتماً در گروه ادمین باشد.\n"
        "2 - نام درس، استاد و مشخصه باید دقیق وارد شود.\n"
        "3 - مسئولیت محتوای تبادل شده در گروه با سازنده آن است.\n"
        "4 - پذیرش عضویت اعضا به عهده ثبت کننده گروه میباشد(دقت کنید الزامی ندارد ثبت کننده حتما ادمین باشد اما باید از ادمین بخواهد تا ربات را در گروه ادمین کنند )"
        "5 - مسئولیت پذیرش افرادی که شایستگی عضویت در گروه شمارا ندارند به عهده خود شما خواهد بود "
        "6 - گروه‌های غیر درسی یا با محتوای نامناسب تایید نخواهند شد.\n\n"
        "آیا قوانین را می‌پذیرید؟"
        "@UniVoiceHub"
        "@classLink_online"
    )
    keyboard = [[InlineKeyboardButton("✅ بله، قبول دارم", callback_data="g_accept")],
                [InlineKeyboardButton("❌ انصراف", callback_data="start")]]
    await update.callback_query.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📍 **گام اول:**\n\nنام درس را وارد کنید:")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 **گام دوم:**\n\nنام استاد درس *{update.message.text}* را وارد کنید:", parse_mode="Markdown")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 **گام سوم:**\n\nشماره مشخصه درس (عدد) را وارد کنید:")
    return G_DAYS

async def ask_g_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    await update.message.reply_text("📍 **گام چهارم:**\n\nروزهای برگزاری کلاس را وارد کنید (مثلاً: شنبه و چهارشنبه):")
    return G_TIME

async def ask_g_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_days"] = update.message.text
    await update.message.reply_text("📍 **گام آخر:**\n\nساعت برگزاری کلاس را وارد کنید (مثلاً: ساعت ۱۰:۳۰ تا ۱۲:۰۰):")
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
    
    admin_text = (f"🔔 **درخواست گروه جدید**\n\n"
                  f"📚 درس: {context.user_data['g_name']}\n"
                  f"👨‍🏫 استاد: {context.user_data['g_prof']}\n"
                  f"📅 روزها: {context.user_data['g_days']}\n"
                  f"🕒 ساعت: {context.user_data['g_time']}\n"
                  f"🔢 مشخصه: {context.user_data['g_id']}\n"
                  
    
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_pub:{ref_id}")],
                [InlineKeyboardButton("❌ رد درخواست", callback_data=f"g_rej:{ref_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    await update.message.reply_text(
        f"📨 **درخواست شما برای ادمین ارسال شد.**\n\n"
        f"🔑 توکن اختصاصی شما:\n`{user_token}`\n\n"
        "لطفاً توکن را در گروه خود ارسال کنید. پس از تایید ادمین، گروه در کانال منتشر می‌شود.", parse_mode="Markdown")
    return ConversationHandler.END

async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    action, ref_id = parts[0], parts[1]
    
    db = load_db()
    data = db.get(ref_id)
    if not data:
        await q.answer("❌ خطا: اطلاعات یافت نشد.", show_alert=True)
        return

    if action == "g_pub":
        channel_kb = [[InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{ref_id}")],
                      [InlineKeyboardButton("🚩 گزارش تخلف", callback_data=f"report_g:{ref_id}")]]
        
        channel_text = (f"📚 **گروه کلاسی جدید**\n\n"
                        f"📖 درس: {data['name']}\n"
                        f"👨‍🏫 استاد: {data['prof']}\n"
                        f"📅 روزها: {data['days']}\n"
                        f"🕒 ساعت: {data['time']}\n\n"
                        f"🔢 مشخصه: {data['id']}\n"
                        f"🆔 {CHANNEL_TAG}")
        
        await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=channel_text, reply_markup=InlineKeyboardMarkup(channel_kb), parse_mode="Markdown")
        await context.bot.send_message(chat_id=data['owner_id'], text=f"✅ گروه شما ({data['name']}) در کانال منتشر شد.")
        await q.message.edit_text("✅ با موفقیت منتشر شد.")

    elif action == "join_req":
        user = q.from_user
        owner_id = data['owner_id']
        
        owner_msg = (
            f"✳️ یک درخواست عضویت برای **{data['name']}** دریافت شد:\n\n"
            f"کاربر **{user.first_name}** درخواست عضویت برای گروه شما ارسال کرده است.\n\n"
            f"⚠️ شما می‌توانید از طریق گروه عضویت دوستانتان را تایید کنید اما پیشنهاد می‌کنیم "
            f"با استفاده از دکمه زیر این‌کار را انجام دهید تا این گروه در بخش "
            f"حساب کاربری (**{user.first_name}**) -> درس‌های من در دسترس باشد تا ما نیز بتوانیم "
            f"عضویت کاربران در گروه‌ها را محدود کنیم و با این اقدام از حضور افراد سودجو در گروه‌ها پیشگیری کنیم🌹"
        )
        
        owner_kb = [[InlineKeyboardButton("✅ پذیرش", callback_data=f"acc_join:{user.id}:{ref_id}"),
                     InlineKeyboardButton("❌ رد", callback_data=f"rej_join:{user.id}:{ref_id}")]]
        
        await context.bot.send_message(chat_id=owner_id, text=owner_msg, reply_markup=InlineKeyboardMarkup(owner_kb), parse_mode="Markdown")
        await q.answer("✅ درخواست به صاحب گروه ارسال شد.", show_alert=True)

    elif action == "acc_join":
        target_id = int(parts[1])
        await context.bot.send_message(chat_id=target_id, text=f"✅ درخواست عضویت شما در گروه **{data['name']}** تایید شد!")
        await q.edit_message_text("✅ درخواست کاربر تایید شد.")

    elif action == "rej_join":
        target_id = int(parts[1])
        await context.bot.send_message(chat_id=target_id, text="❌ متأسفانه درخواست عضویت شما رد شد.")
        await q.edit_message_text("❌ درخواست رد شد.")

    elif action == "report_g":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚩 گزارش تخلف گروه: {data['name']}\nشناسه: {ref_id}")
        await q.answer("✅ گزارش ارسال شد.", show_alert=True)

# Conversation Handler
group_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_group_reg, pattern="^start_group_reg$")],
    states={
        G_RULES: [CallbackQueryHandler(show_rules, pattern="^g_add$")],
        G_NAME: [CallbackQueryHandler(ask_g_name, pattern="^g_accept$")],
        G_PROF: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_prof)],
        G_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_id)],
        G_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_days)],
        G_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_time)],
        G_BOT_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_bot_add)],
    },
    fallbacks=[CallbackQueryHandler(start_group_reg, pattern="^start$")]
)
