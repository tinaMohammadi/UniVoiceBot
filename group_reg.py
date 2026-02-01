import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= CONFIG =================
GROUP_CHANNEL_ID = "@classLink_online"  # آیدی کانال گروه‌ها
ADMIN_ID = 7997819976
# ذخیره موقت گروه‌ها (در پروژه‌های واقعی باید از دیتابیس استفاده شود)
groups_db = {} 

# ================= STATES =================
G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD = range(100, 105)

# ================= HELPERS =================
def generate_token():
    return 'UNITOK-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ================= HANDLERS =================
async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text("لطفاً برای ثبت گروه اقدام کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rules = "📜 قوانین ثبت گروه کلاسی..."
    keyboard = [[InlineKeyboardButton("✅ پذیرش قوانین", callback_data="g_accept")]]
    await update.callback_query.message.edit_text(rules, reply_markup=InlineKeyboardMarkup(keyboard))
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📍 نام درس را وارد کنید:")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 نام استاد درس {update.message.text}:")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 شماره مشخصه درس را وارد کنید:")
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    token = generate_token()
    owner_id = update.effective_user.id
    
    # ذخیره در دیتابیس موقت
    groups_db[token] = {
        "owner_id": owner_id,
        "name": context.user_data["g_name"],
        "prof": context.user_data["g_prof"],
        "id": context.user_data["g_id"]
    }
    
    admin_text = (f"🔔 درخواست گروه:\nدرس: {context.user_data['g_name']}\n"
                  f"استاد: {context.user_data['g_prof']}\nتوکن: {token}")
    
    # دکمه تایید برای ادمین (تو) که توکن را هم در callback_data حمل می‌کند
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_pub:{token}"),
                 InlineKeyboardButton("❌ رد", callback_data=f"g_rej:{owner_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text(f"📨 درخواست شما ارسال شد.\nتوکن اختصاصی: `{token}`", parse_mode="Markdown")
    return ConversationHandler.END

# ================= PUBLISH & REQUEST LOGIC =================
async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data.split(":")
    action = data[0]
    
    if action == "g_pub":
        token = data[1]
        group = groups_db.get(token)
        if group:
            # ارسال به کانال با دکمه درخواست و گزارش
            channel_kb = [
                [InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{token}")],
                [InlineKeyboardButton("🚩 گزارش تخلف", callback_data=f"report_g:{token}")]
            ]
            text = (f"📚 درس: {group['name']}\n👨‍🏫 استاد: {group['prof']}\n🔢 مشخصه: {group['id']}\n"
                    f"──────────────\n🆔 @UniVoiceHub")
            await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=text, reply_markup=InlineKeyboardMarkup(channel_kb))
            await context.bot.send_message(chat_id=group['owner_id'], text="✅ گروه شما در کانال منتشر شد.")
            await q.message.delete()

    elif action == "join_req":
        token = data[1]
        group = groups_db.get(token)
        user = q.from_user
        if group:
            owner_id = group['owner_id']
            # پیام به سازنده گروه
            req_text = (f"✳️ یک درخواست عضویت برای درس {group['name']} دریافت شد:\n"
                        f"کاربر: [{user.first_name}](tg://user?id={user.id})\n\n"
                        "⚠️ شما می‌توانید عضویت دوستانتان را تایید کنید...")
            
            owner_kb = [[InlineKeyboardButton("✅ پذیرش", callback_data=f"acc_join:{user.id}:{token}"),
                         InlineKeyboardButton("❌ رد", callback_data=f"rej_join:{user.id}:{token}")]]
            
            await context.bot.send_message(chat_id=owner_id, text=req_text, reply_markup=InlineKeyboardMarkup(owner_kb), parse_mode="Markdown")
            await q.answer("✅ درخواست شما برای سازنده گروه ارسال شد.", show_alert=True)

    elif action == "acc_join":
        target_user_id = int(data[1])
        token = data[2]
        await context.bot.send_message(chat_id=target_user_id, text=f"✅ درخواست عضویت شما در گروه {groups_db[token]['name']} تایید شد!")
        await q.edit_message_text("✅ کاربر با موفقیت پذیرفته شد.")

    elif action == "report_g":
        # ارسال گزارش به ادمین (تو)
        token = data[1]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚩 گزارش تخلف برای گروه با توکن {token} توسط کاربر {q.from_user.id}")
        await q.answer("گزارش شما برای ادمین ارسال شد.", show_alert=True)

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
