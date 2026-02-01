import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= تنظیمات (حتماً آیدی‌ها را چک کن) =================
GROUP_CHANNEL_ID = "@classLink_online"  # آیدی کانال گروه‌ها (با @)
ADMIN_ID = 7997819976
CHANNEL_TAG = "@UniVoiceHub"

# دیتابیس موقت برای ذخیره اطلاعات گروه‌ها در حافظه (تا زمان ری‌استارت ربات)
groups_db = {}

# ================= وضعیت‌ها =================
G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD = range(100, 105)

# ================= توابع کمکی =================
def generate_token():
    return 'UNITOK-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ================= مراحل ثبت گروه =================
async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(
        "✨ **به بخش ثبت گروه کلاسی خوش اومدی**\n\nلطفاً برای شروع روی دکمه زیر کلیک کن:",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rules_text = (
        "📜 **قوانین و شرایط ثبت گروه:**\n\n"
        "۱- ربات باید حتماً در گروه ادمین باشد.\n"
        "۲- نام درس و استاد باید به درستی وارد شود.\n"
        "۳- مسئولیت محتوای گروه با شخص سازنده است.\n\n"
        "آیا قوانین را می‌پذیرید؟"
    )
    keyboard = [[InlineKeyboardButton("✅ بله، قبول دارم", callback_data="g_accept")],
                [InlineKeyboardButton("❌ خیر، انصراف", callback_data="start")]]
    await update.callback_query.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("📍 **گام اول:**\n\nنام درس را وارد کنید:\n\n(پاسخ خود را وارد کنید)")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 **گام دوم:**\n\nنام استاد درس *{update.message.text}* را وارد کنید:\n\n(پاسخ خود را وارد کنید)", parse_mode="Markdown")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 **گام سوم:**\n\nشماره مشخصه درس (عدد) را وارد کنید:")
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    token = generate_token()
    owner_id = update.effective_user.id
    
    # ذخیره اطلاعات در دیتابیس موقت
    groups_db[token] = {
        "owner_id": owner_id,
        "name": context.user_data["g_name"],
        "prof": context.user_data["g_prof"],
        "id": context.user_data["g_id"]
    }
    
    # ارسال برای ادمین (شما) جهت تایید
    admin_summary = (
        "🔔 **درخواست ثبت گروه جدید**\n\n"
        f"📚 درس: {context.user_data['g_name']}\n"
        f"👨‍🏫 استاد: {context.user_data['g_prof']}\n"
        f"🔢 مشخصه: {context.user_data['g_id']}\n"
        f"🔑 توکن: `{token}`"
    )
    admin_kb = [[InlineKeyboardButton("✅ تایید و انتشار در کانال", callback_data=f"g_pub:{token}"),
                 InlineKeyboardButton("❌ رد درخواست", callback_data=f"g_rej:{owner_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_summary, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")
    
    await update.message.reply_text(
        "📨 **درخواست شما برای ادمین ارسال شد.**\n\n"
        f"توکن اختصاصی گروه شما: `{token}`\n\n"
        "لطفاً ربات را در گروه خود ادمین کنید و منتظر تایید بمانید.", parse_mode="Markdown")
    return ConversationHandler.END

# ================= منطق دکمه‌های انتشار، درخواست عضویت و گزارش =================
async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data.split(":")
    action = data[0]

    # ۱. انتشار در کانال توسط ادمین اصلی
    if action == "g_pub":
        token = data[1]
        group = groups_db.get(token)
        if group:
            channel_kb = [[InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{token}")],
                          [InlineKeyboardButton("🚩 گزارش تخلف", callback_data=f"report_g:{token}")]]
            
            text = (f"📚 **گروه کلاسی جدید**\n\n"
                    f"📖 درس: {group['name']}\n"
                    f"👨‍🏫 استاد: {group['prof']}\n"
                    f"🔢 مشخصه: {group['id']}\n\n"
                    f"🆔 {CHANNEL_TAG}")
            
            await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=text, reply_markup=InlineKeyboardMarkup(channel_kb), parse_mode="Markdown")
            await context.bot.send_message(chat_id=group['owner_id'], text=f"✅ گروه شما (درس {group['name']}) تایید و در کانال منتشر شد!")
            await q.message.edit_text(f"✅ منتشر شد.\nتوکن: {token}")

    # ۲. درخواست عضویت کاربر از داخل کانال
    elif action == "join_req":
        token = data[1]
        group = groups_db.get(token)
        req_user = q.from_user
        
        if group:
            owner_id = group['owner_id']
            # ارسال پیام به صاحب گروه با مشخصات فرد درخواست دهنده
            owner_msg = (
                f"✳️ **یک درخواست عضویت برای درس {group['name']} دریافت شد:**\n\n"
                f"👤 کاربر: [{req_user.first_name}](tg://user?id={req_user.id})\n"
                f"🆔 یوزرنیم: @{req_user.username if req_user.username else 'ندارد'}\n\n"
                f"درخواست عضویت برای گروه شما ارسال کرده است.\n\n"
                "⚠️ پیشنهاد می‌کنیم با استفاده از دکمه زیر این کار را انجام دهید تا از حضور افراد سودجو پیشگیری کنیم🌹"
            )
            owner_kb = [[InlineKeyboardButton("✅ پذیرش", callback_data=f"acc_join:{req_user.id}:{token}"),
                         InlineKeyboardButton("❌ رد", callback_data=f"rej_join:{req_user.id}:{token}")]]
            
            await context.bot.send_message(chat_id=owner_id, text=owner_msg, reply_markup=InlineKeyboardMarkup(owner_kb), parse_mode="Markdown")
            await q.answer("✅ درخواست شما برای صاحب گروه ارسال شد. منتظر تایید بمانید.", show_alert=True)

    # ۳. پذیرش عضویت توسط صاحب گروه
    elif action == "acc_join":
        target_id = int(data[1])
        token = data[2]
        group_name = groups_db[token]['name'] if token in groups_db else "درس انتخابی"
        
        await context.bot.send_message(chat_id=target_id, text=f"🎉 **تبریک!**\n\nدرخواست عضویت شما در گروه درس **{group_name}** توسط صاحب گروه تایید شد.")
        await q.edit_message_text("✅ شما درخواست این کاربر را پذیرفتید.")

    # ۴. رد عضویت توسط صاحب گروه
    elif action == "rej_join":
        target_id = int(data[1])
        await context.bot.send_message(chat_id=target_id, text="❌ متأسفانه درخواست عضویت شما در گروه مورد نظر رد شد.")
        await q.edit_message_text("❌ شما درخواست عضویت را رد کردید.")

    # ۵. گزارش تخلف
    elif action == "report_g":
        token = data[1]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚩 **گزارش تخلف گروه!**\n\nتوکن گروه: `{token}`\nگزارش دهنده: `{q.from_user.id}`", parse_mode="Markdown")
        await q.answer("✅ گزارش شما برای بررسی به ادمین کل ارسال شد.", show_alert=True)

# ================= هندلر Conversation =================
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
