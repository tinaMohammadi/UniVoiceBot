import os
import logging
import threading
import time
import requests
import random
import string
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
SELF_URL = os.getenv("SELF_URL")
ADMIN_ID = 7997819976
CHANNEL_ID = "@UniVoiceHub"
BOT_USERNAME = "UniEchoFeedbackBot"
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
# نظرسنجی استاد
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(14)

# ثبت گروه
(G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD) = range(100, 105)

# ================= HELPERS =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 ثبت نظر درباره استاد", callback_data="start_form")],
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

خب، آماده‌ای شروع کنی؟ 🚀
"""
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu())

async def anon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["mode"] = "ANON_WAITING"
    await update.callback_query.message.reply_text("🕵️ پیام خودت رو بنویس تا ناشناس برای ادمین ارسال بشه:")

# ================= FORM LOGIC =================
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["mode"] = "IN_FORM"
    await update.callback_query.message.reply_text("*👨‍🏫 گام اول: نام استاد:*", parse_mode="Markdown")
    return ASK_PROF

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("*📚 درس:*", parse_mode="Markdown")
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("*🎓 نوع تدریس:*", parse_mode="Markdown")
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("*💬 خصوصیات اخلاقی:*", parse_mode="Markdown")
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("*📄 جزوه:*", parse_mode="Markdown")
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("*🧪 پروژه:*", parse_mode="Markdown")
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("*🕒 حضور و غیاب:*", parse_mode="Markdown")
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("*📝 میان‌ترم:*", parse_mode="Markdown")
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("*📘 پایان‌ترم:*", parse_mode="Markdown")
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("*📊 میزان تطبیق سوالات با جزوه:*", parse_mode="Markdown")
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("*📞 راه ارتباطی:*", parse_mode="Markdown")
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("*📌 نتیجه‌گیری:*", parse_mode="Markdown")
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("*📅 ترمی که با استاد داشتی:*", parse_mode="Markdown")
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("*⭐ نمره از ۲۰:*", parse_mode="Markdown")
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ ارسال نهایی", callback_data="submit_form"), InlineKeyboardButton("❌ انصراف", callback_data="start")]]
    await update.message.reply_text(f"📋 *پیش‌نمایش فرم شما:*\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# ================= MESSAGE ROUTER (CRITICAL FIX) =================
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mode = context.user_data.get("mode")

    if mode == "ANON_WAITING":
        keyboard = [[InlineKeyboardButton("✉️ پاسخ به کاربر", callback_data=f"admin_reply:{user_id}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام ناشناس از طرف دانشجو:\n\n{update.message.text}", reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("✅ پیام شما با موفقیت و به‌صورت ناشناس برای ادمین ارسال شد.")
        context.user_data["mode"] = None
        return

    if user_id == ADMIN_ID and context.user_data.get("replying_to"):
        target_id = context.user_data["replying_to"]
        await context.bot.send_message(chat_id=target_id, text=f"📩 *پاسخ ادمین به شما:*\n\n{update.message.text}", parse_mode="Markdown")
        await update.message.reply_text("✅ پاسخ شما برای دانشجو ارسال شد.")
        context.user_data["replying_to"] = None
        return

    await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کنید یا دستور /start را بزنید.", reply_markup=main_menu())

# ================= ADMIN & CALLBACKS =================
async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"admin_accept:{q.from_user.id}"), InlineKeyboardButton("❌ رد فرم", callback_data=f"admin_reject:{q.from_user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📝 فرم جدید برای بررسی:\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await q.edit_message_text("📨 فرم شما برای ادمین ارسال شد. پس از تایید در کانال منتشر می‌شود.")

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = int(q.data.split(":")[1])
    context.user_data["replying_to"] = user_id
    await q.message.reply_text("✍️ پاسخ خود را بنویسید:")
    await q.answer()

async def admin_accept_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    action, user_id = q.data.split(":")
    if action == "admin_accept":
        await context.bot.send_message(chat_id=CHANNEL_ID, text=q.message.text, parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="✅ نظر شما تایید و در کانال منتشر شد.")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ متاسفانه فرم شما توسط ادمین تایید نشد.")
    await q.message.delete()

# ================= MAIN =================
def main():
    if not TOKEN: return
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=self_ping, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    # هندلر فرم نظرسنجی
    form_conv = ConversationHandler(
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
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^start$")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(form_conv)
    app.add_handler(CallbackQueryHandler(anon_start, pattern="^anon_start$"))
    app.add_handler(CallbackQueryHandler(submit_form, pattern="^submit_form$"))
    app.add_handler(CallbackQueryHandler(admin_reply_start, pattern="^admin_reply:"))
    app.add_handler(CallbackQueryHandler(admin_accept_reject, pattern="^admin_accept:|^admin_reject:"))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    
    # هندلر نهایی برای چت ناشناس و پیام‌های معمولی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    print("🚀 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
