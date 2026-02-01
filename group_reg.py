import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= CONFIG (تنظیمات اختصاصی کانال گروه‌ها) =================
# آیدی کانالی که گروه‌ها باید در آن منتشر شوند را اینجا وارد کن
GROUP_CHANNEL_ID = "@classLink_online" 
ADMIN_ID = 7997819976

# ================= STATES =================
G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD, G_CONFIRM = range(100, 106)

# ================= HELPERS =================
def generate_token():
    """تولید توکن اختصاصی ۸ رقمی"""
    return 'UNITOK-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ================= HANDLERS =================
async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند ثبت گروه و نمایش دکمه افزودن"""
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="start")]
    ]
    await update.callback_query.message.edit_text(
        "✨ **به بخش ثبت گروه کلاسی خوش اومدی**\n\nلطفاً برای شروع روی دکمه زیر کلیک کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش قوانین"""
    await update.callback_query.answer()
    rules_text = (
        "📜 **قوانین و شرایط ثبت گروه:**\n\n"
        "۱- ربات باید حتماً در گروه ادمین باشد.\n"
        "۲- نام درس و استاد باید به درستی وارد شود.\n"
        "۳- از ثبت گروه‌های تکراری خودداری کنید.\n"
        "۴- مسئولیت محتوای گروه با شخص سازنده است.\n\n"
        "آیا قوانین را می‌پذیرید؟"
    )
    keyboard = [
        [InlineKeyboardButton("✅ بله، قبول دارم", callback_data="g_accept")],
        [InlineKeyboardButton("❌ خیر، انصراف", callback_data="start")]
    ]
    await update.callback_query.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گام اول: نام درس"""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📍 **گام اول:**\n\nاسم درسی که می‌خوای براش گروه بزنی رو کامل و به فارسی وارد کن:\n\n"
        "پاسخ خود را وارد کنید:"
    )
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گام دوم: نام استاد"""
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(
        f"📍 **گام دوم:**\n\nلطفاً نام استادی که درس *{update.message.text}* رو باهاشون داری ارسال کن:\n\n"
        "پاسخ خود را وارد کنید:",
        parse_mode="Markdown"
    )
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گام سوم: شماره مشخصه"""
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text(
        "📍 **گام سوم:**\n\nشماره مشخصه درس (عدد) رو وارد کن:\n\n"
        "نکته: این کد برای جلوگیری از گروه‌های تکراریه."
    )
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گام چهارم: توکن و ادمین کردن ربات"""
    context.user_data["g_id"] = update.message.text
    token = generate_token()
    context.user_data["g_token"] = token
    
    msg = (
        "📍 **گام چهارم (نهایی):**\n\n"
        "۱- ربات را در گروه خود عضو کنید.\n"
        "۲- ربات را **ادمین** گروه کنید.\n"
        "۳- سپس کد اختصاصی زیر را در گروه ارسال کنید:\n\n"
        f"`{token}`\n\n"
        "⚠️ پس از انجام این مراحل، برای تایید نهایی ادمین صبر کنید."
    )
    
    # ارسال اطلاعات برای ادمین اصلی جهت بررسی
    admin_summary = (
        "🔔 **درخواست ثبت گروه جدید**\n\n"
        f"📚 درس: {context.user_data['g_name']}\n"
        f"👨‍🏫 استاد: {context.user_data['g_prof']}\n"
        f"🔢 مشخصه: {context.user_data['g_id']}\n"
        f"🔑 توکن: `{token}`\n"
        f"👤 فرستنده: {update.effective_user.first_name}"
    )
    
    admin_kb = [[
        InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_approve:{update.effective_user.id}"),
        InlineKeyboardButton("❌ رد درخواست", callback_data=f"g_reject:{update.effective_user.id}")
    ]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_summary, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")
    await update.message.reply_text(msg, parse_mode="Markdown")
    
    return ConversationHandler.END

# ================= ADMIN ACTIONS FOR GROUPS =================
async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه تایید یا رد گروه توسط ادمین"""
    q = update.callback_query
    action, user_id = q.data.split(":")
    
    if action == "g_approve":
        # ارسال اطلاعات به کانال مخصوص گروه‌ها
        await context.bot.send_message(
            chat_id=GROUP_CHANNEL_ID,
            text=f"✅ **گروه کلاسی جدید تایید شد**\n\n{q.message.text.split('🔑')[0]}\n🆔 @UniVoiceHub",
            parse_mode="Markdown"
        )
        await context.bot.send_message(chat_id=user_id, text="✅ گروه کلاسی شما تایید و در کانال گروه‌ها منتشر شد.")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ متأسفانه درخواست ثبت گروه شما رد شد.")
    
    await q.message.delete()
    await q.answer()

# ================= EXPORTING HANDLER =================
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
