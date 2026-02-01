import json
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= CONFIG =================
GROUP_CHANNEL_ID = "@classLink_online"  # آیدی کانال گروه‌ها را اینجا دقیق وارد کنید
ADMIN_ID = 7997819976
CHANNEL_TAG = "@UniVoiceHub"
DB_FILE = "groups_data.json"

# ذخیره و بازیابی اطلاعات در فایل (برای جلوگیری از پاک شدن با ری‌استارت)
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ================= STATES =================
G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD = range(100, 105)

# ================= HANDLERS =================
async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text("✨ به بخش ثبت گروه خوش آمدید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("✅ پذیرش قوانین", callback_data="g_accept")]]
    await update.callback_query.message.edit_text("📜 قوانین:\n۱. ادمین کردن ربات الزامیست.\n۲. مسئولیت با سازنده است.", reply_markup=InlineKeyboardMarkup(keyboard))
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📍 نام درس استادی که باهاش درس داری:")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 نام استاد درس {update.message.text}:")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 شماره مشخصه درس:")
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    owner_id = update.effective_user.id
    ref_id = str(random.randint(100000, 999999)) # شناسه ۶ رقمی
    
    # ذخیره در فایل
    db = load_db()
    db[ref_id] = {
        "owner_id": owner_id,
        "name": context.user_data["g_name"],
        "prof": context.user_data["g_prof"],
        "id": context.user_data["g_id"]
    }
    save_db(db)
    
    admin_text = (f"🔔 **درخواست گروه جدید**\n\n"
                  f"📚 درس: {context.user_data['g_name']}\n"
                  f"👨‍🏫 استاد: {context.user_data['g_prof']}\n"
                  f"🔢 مشخصه: {context.user_data['g_id']}\n"
                  f"👤 آیدی عددی صاحب: `{owner_id}`")
    
    # دکمه فقط شامل ref_id است (بسیار کوتاه)
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_pub:{ref_id}")],
                [InlineKeyboardButton("❌ رد", callback_data=f"g_rej:{ref_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await update.message.reply_text("✅ درخواست شما ارسال شد. منتظر تایید ادمین باشید.")
    return ConversationHandler.END

async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    action = parts[0]
    ref_id = parts[1]
    
    db = load_db()
    data = db.get(ref_id)
    
    if not data:
        await q.answer("❌ خطا: اطلاعات یافت نشد.", show_alert=True)
        return

    if action == "g_pub":
        # انتشار در کانال بدون نمایش توکن یا آیدی صاحب
        channel_kb = [[InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{ref_id}")],
                      [InlineKeyboardButton("🚩 گزارش تخلف", callback_data=f"report_g:{ref_id}")]]
        
        channel_text = (f"📚 **گروه کلاسی جدید**\n\n"
                       f"📖 درس: {data['name']}\n"
                       f"👨‍🏫 استاد: {data['prof']}\n"
                       f"🔢 مشخصه: {data['id']}\n\n"
                       f"🆔 {CHANNEL_TAG}")
        
        await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=channel_text, reply_markup=InlineKeyboardMarkup(channel_kb), parse_mode="Markdown")
        await context.bot.send_message(chat_id=data['owner_id'], text=f"✅ گروه شما برای درس {data['name']} تایید و در کانال منتشر شد.")
        await q.message.edit_text(f"✅ با موفقیت در کانال منتشر شد.\nشناسه: {ref_id}")

    elif action == "join_req":
        user = q.from_user
        owner_id = data['owner_id']
        
        owner_kb = [[InlineKeyboardButton("✅ پذیرش", callback_data=f"acc_join:{user.id}:{ref_id}"),
                     InlineKeyboardButton("❌ رد", callback_data=f"rej_join:{user.id}")] ]
        
        msg = (f"✳️ درخواست عضویت برای درس **{data['name']}**:\n"
               f"👤 کاربر: [{user.first_name}](tg://user?id={user.id})\n"
               f"🆔 یوزرنیم: @{user.username if user.username else 'ندارد'}\n\n"
               "آیا تایید می‌کنید؟")
        
        await context.bot.send_message(chat_id=owner_id, text=msg, reply_markup=InlineKeyboardMarkup(owner_kb), parse_mode="Markdown")
        await q.answer("✅ درخواست به صاحب گروه ارسال شد.", show_alert=True)

    elif action == "acc_join":
        target_id = parts[1]
        await context.bot.send_message(chat_id=target_id, text=f"✅ درخواست شما برای گروه {data['name']} تایید شد!")
        await q.edit_message_text("✅ تایید کردید.")

    elif action == "report_g":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚩 گزارش برای گروه {ref_id} از کاربر {q.from_user.id}")
        await q.answer("گزارش شد.", show_alert=True)

# هندلر نهایی
group_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_group_reg, pattern="^start_group_reg$")],
    states={
        G_RULES: [CallbackQueryHandler(show_rules, pattern="^g_add$")],
        G_NAME: [CallbackQueryHandler(ask_g_name, pattern="^g_accept$")],
        G_PROF: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_prof)],
        G_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_id)],
        G_BOT_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_g_bot_add)],
    },
    fallbacks=[CallbackQueryHandler(start_group_reg, pattern="^start$")]
)
