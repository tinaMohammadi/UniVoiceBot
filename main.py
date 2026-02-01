import os
import logging
import threading
import time
import requests
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)

# فراخوانی فایل ثبت گروه (بعداً این فایل را ایجاد می‌کنیم)
try:
    from group_reg import group_conv
except ImportError:
    group_conv = None

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
SELF_URL = os.getenv("SELF_URL")
ADMIN_ID = 7997819976
CHANNEL_ID = "@UniVoiceHub"
BOT_USERNAME = "UniEchoFeedbackBot"
CHANNEL_DIRECT_LINK = "https://t.me/UniVoiceHub?direct"
CHANNEL_TAG = "@UniVoiceHub"

logging.basicConfig(level=logging.INFO)

# ================= KEEP ALIVE SERVER =================
web_app = Flask(__name__)
@web_app.route("/")
def home(): return "Bot is alive!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def self_ping():
    while True:
        try:
            if SELF_URL: requests.get(SELF_URL)
        except: pass
        time.sleep(300)

# ================= STATES =================
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(14)

# وضعیت‌های چت ناشناس
(ANON_GET_MSG, ANON_CONFIRM_SEND) = range(20, 22)

# ================= HELPERS =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 ثبت نظر درباره استاد", callback_data="start_form")],
        [InlineKeyboardButton("💬 چت خصوصی ادمین", url=CHANNEL_DIRECT_LINK)],
        [InlineKeyboardButton("👥 ثبت گروه کلاسی ❤️", callback_data="start_group_reg")],
        [InlineKeyboardButton("🕵️ چت ناشناس با ادمین", callback_data="anon_start")]
    ])

def build_form_text(data):
    questions = [
        ("👨‍🏫 استاد", "استاد"), ("📚 درس", "درس"), ("🎓 نوع تدریس", "نوع تدریس"),
        ("💬 خصوصیات اخلاقی", "خصوصیات اخلاقی"), ("📄 جزوه", "جزوه"), ("🧪 پروژه", "پروژه"),
        ("🕒 حضور و غیاب", "حضور و غیاب"), ("📝 میان‌ترم", "میان‌ترم"), ("📘 پایان‌ترم", "پایان‌ترم"),
        ("📊 میزان تطبیق", "تطبیق سوالات"), ("📞 راه ارتباطی", "راه ارتباطی"),
        ("📌 نتیجه‌گیری", "نتیجه‌گیری"), ("📅 ترم", "ترم"), ("⭐ نمره", "نمره"),
    ]
    lines = [f"*{q[0]}:*\n{data.get(q[1], '-')}\n" for q in questions]
    lines.append(f"──────────────\n🆔 {CHANNEL_TAG}")
    return "\n".join(lines)

# ================= GENERAL HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = """🎉 سلام به شما رفیق تازه‌وارد! 🎉

خوش اومدی به جایی که می‌تونی با خیال راحت تجربه و نظر خودت درباره اساتید رو با بقیه دانشجوها به اشتراک بذاری! هدف؟ کمک به همه برای انتخاب بهتر ترم‌های بعد 😎

💌 نگران نباش، همه پیام‌ها کاملاً ناشناس ارسال می‌شن، پس راحت باش و هر چی دوست داری بگو.

✨ و یه چیز دیگه: اگه پیشنهادی داری یا دوست داری چیزی به ربات اضافه بشه، حتماً تو دایرکت کانال با من درمیون بذار تا با هم یه تجربه تحصیلی عالی و بی‌دردسر بسازیم!

خب، آماده‌ای شروع کنی؟ 🚀"""
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# ================= ANON CHAT SYSTEM (FIXED) =================
async def anon_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🕵️ **حالت ناشناس فعال شد.**\n\nپیام خودت رو بنویس تا آماده ارسال بشه:", parse_mode="Markdown")
    return ANON_GET_MSG

async def anon_receive_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["temp_anon_msg"] = update.message.text
    keyboard = [[InlineKeyboardButton("👁️ نمایش و ارسال پیام", callback_data="anon_confirm_send")]]
    await update.message.reply_text("✅ پیام شما دریافت شد. برای ارسال نهایی روی دکمه زیر بزنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ANON_CONFIRM_SEND

async def anon_final_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    msg_text = context.user_data.get("temp_anon_msg")
    
    # ارسال به ادمین (همراه با اطلاعات مخفی)
    admin_kb = [[InlineKeyboardButton("✉️ پاسخ به کاربر", callback_data=f"admin_reply:{user.id}")]]
    user_info = f"\n\n--- 🕵️ گزارش هویت (فقط برای ادمین) ---\n👤 نام: {user.first_name}\n🆔 یوزرنیم: @{user.username}\n🔢 آیدی: {user.id}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام ناشناس جدید:\n\n{msg_text}{user_info}", reply_markup=InlineKeyboardMarkup(admin_kb))
    
    # نمایش به کاربر
    user_kb = [
        [InlineKeyboardButton("✉️ پاسخ به ادمین", callback_data="anon_start")],
        [InlineKeyboardButton("❌ پایان چت", callback_data="start")]
    ]
    await q.edit_message_text(f"🚀 **پیام شما با موفقیت ارسال شد:**\n\n{msg_text}", reply_markup=InlineKeyboardMarkup(user_kb), parse_mode="Markdown")
    return ConversationHandler.END

# ================= FORM LOGIC =================
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("*👨‍🏫  نام استاد:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_PROF

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("*📚 درس:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("*🎓 نوع تدریس:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("*💬 خصوصیات اخلاقی:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("*📄 جزوه:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("*🧪 پروژه:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("*🕒 حضور و غیاب:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("*📝 میان‌ترم:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("*📘 پایان‌ترم:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("*📊(از 5) میزان تطبیق سوالات با جزوه:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("*📞 راه ارتباطی:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("*📌 نتیجه‌گیری:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("*📅 ترمی که با استاد داشتی:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("*⭐ نمره از 20:*\n\nپاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ ارسال نهایی", callback_data="submit_form"), InlineKeyboardButton("❌ انصراف", callback_data="start")]]
    await update.message.reply_text(f"📋 **پیش‌نمایش فرم شما:**\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# ================= MESSAGE ROUTER =================
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # پاسخ ادمین به پیام ناشناس
    if user.id == ADMIN_ID and context.user_data.get("replying_to"):
        target_id = context.user_data["replying_to"]
        kb = [[InlineKeyboardButton("✉️ پاسخ به ادمین", callback_data="anon_start"), InlineKeyboardButton("❌ پایان چت", callback_data="start")]]
        await context.bot.send_message(chat_id=target_id, text=f"📩 **پاسخ ادمین به پیام ناشناس شما:**\n\n{update.message.text}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        await update.message.reply_text("✅ پاسخ برای دانشجو ارسال شد.")
        context.user_data["replying_to"] = None
        return

    await update.message.reply_text("لطفاً یک گزینه را انتخاب کنید:", reply_markup=main_menu())

# ================= ADMIN ACTIONS =================
async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ تایید", callback_data=f"admin_accept:{q.from_user.id}"), InlineKeyboardButton("❌ رد", callback_data=f"admin_reject:{q.from_user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📝 فرم جدید:\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await q.edit_message_text("📨 فرم برای ادمین ارسال شد.")

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = int(q.data.split(":")[1])
    context.user_data["replying_to"] = user_id
    await q.message.reply_text("✍️ پاسخ خود را برای کاربر بنویسید:")
    await q.answer()

async def admin_accept_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    action, user_id = q.data.split(":")
    if action == "admin_accept":
        await context.bot.send_message(chat_id=CHANNEL_ID, text=q.message.text, parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="✅ نظر شما در کانال منتشر شد.")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ فرم شما تایید نشد.")
    await q.message.delete()
# ================= MAIN =================
def main():
    # راه‌اندازی سرور برای زنده نگه داشتن ربات
    if 'run_web' in globals():
        threading.Thread(target=run_web, daemon=True).start()
    if 'self_ping' in globals():
        threading.Thread(target=self_ping, daemon=True).start()

    # ساخت اپلیکیشن ربات
    app = Application.builder().token(TOKEN).build()

    # ۱. تعریف متغیرهای Conversation (بسیار مهم: اول تعریف، بعد استفاده)
    
    # الف) سیستم چت ناشناس
    anon_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(anon_start_callback, pattern="^anon_start$")],
        states={
            ANON_GET_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, anon_receive_msg)],
            ANON_CONFIRM_SEND: [CallbackQueryHandler(anon_final_send, pattern="^anon_confirm_send$")]
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^start$"), CommandHandler("start", start)],
        per_message=False
    )

    # ب) سیستم فرم نظرسنجی اساتید
    form_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_form, pattern="^start_form$")],
        states={
            ASK_PROF: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_course)],
            ASK_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_teaching)],
            ASK_TEACHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ethics)],
            ASK_ETHICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_notes)],
            ASK_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_project)],
            ASK_PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_attend)],
            ASK_ATTEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_midterm)],
            ASK_MIDTERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_final)],
            ASK_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_match)],
            ASK_MATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_contact)],
            ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_conclusion)],
            ASK_CONCLUSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_semester)],
            ASK_SEMESTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_grade)],
            ASK_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_form)],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^start$"), CommandHandler("start", start)],
        per_message=False
    )

    # ۲. اضافه کردن هندلرها به ترتیب اولویت صحیح
    
    # اولویت ۱: دستور استارت
    app.add_handler(CommandHandler("start", start))

    # اولویت ۲: مدیریت گروه‌ها (Import از فایل دیگر)
    try:
        from group_reg import group_conv, admin_group_decision
        app.add_handler(group_conv)
        app.add_handler(CallbackQueryHandler(admin_group_decision, pattern="^(g_pub|g_rej|join_req|acc_join|rej_join|report_g):"))
    except ImportError:
        print("❌ خطا: فایل group_reg.py یافت نشد!")

    # اولویت ۳: اضافه کردن سایر گفتگوها (که در بالا تعریف کردیم)
    app.add_handler(anon_conv_handler)
    app.add_handler(form_conv_handler)

    # اولویت ۴: سایر دکمه‌های عملیاتی
    app.add_handler(CallbackQueryHandler(submit_form, pattern="^submit_form$"))
    app.add_handler(CallbackQueryHandler(admin_reply_start, pattern="^admin_reply:"))
    app.add_handler(CallbackQueryHandler(admin_accept_reject, pattern="^admin_accept:|^admin_reject:"))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))

    # اولویت ۵: پیام‌های متنی آزاد
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    # شروع به کار ربات
    print("🚀 Bot is live and fixed...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
