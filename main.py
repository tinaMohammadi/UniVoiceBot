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
def home():
    return "Bot is alive!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ================= SELF-PING =================
def self_ping():
    while True:
        try:
            if SELF_URL:
                requests.get(SELF_URL)
                print("🔁 Pinged self to stay awake.")
        except Exception as e:
            print("❌ Ping failed:", e)
        time.sleep(300)

# ================= STATES =================
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(14)

FORM_QUESTIONS = [
    ("👨‍🏫 استاد", "استاد"), ("📚 درس", "درس"), ("🎓 نوع تدریس", "نوع تدریس"),
    ("💬 خصوصیات اخلاقی", "خصوصیات اخلاقی"), ("📄 جزوه", "جزوه"), ("🧪 پروژه", "پروژه"),
    ("🕒 حضور و غیاب", "حضور و غیاب"), ("📝 میان‌ترم", "میان‌ترم"), ("📘 پایان‌ترم", "پایان‌ترم"),
    ("📊 میزان تطبیق سوالات با جزوه", "تطبیق سوالات"), ("📞 راه ارتباطی", "راه ارتباطی"),
    ("📌 نتیجه‌گیری", "نتیجه‌گیری"), ("📅 ترمی که با استاد داشتی", "ترم"), ("⭐ نمره از ۲۰", "نمره"),
]

post_reactions = {}
anon_sessions = {}
reply_sessions = {}

# ================= HELPERS =================
def reaction_keyboard(msg_id):
    data = post_reactions.get(msg_id, {"likes": set(), "dislikes": set()})
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"👍 {len(data['likes'])}", callback_data=f"like:{msg_id}"),
        InlineKeyboardButton(f"👎 {len(data['dislikes'])}", callback_data=f"dislike:{msg_id}")
    ], [InlineKeyboardButton("📝 ثبت نظر", url=f"https://t.me/{BOT_USERNAME}?start=form")]])

def build_form_text(data):
    lines = []
    for title, key in FORM_QUESTIONS:
        value = data.get(key, "-")
        lines.append(f"*{title}:*\n{value}\n")
    lines.append("──────────────")
    lines.append(f"🆔 {CHANNEL_TAG}")
    return "\n".join(lines)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 ثبت نظر درباره استاد", callback_data="start_form")],
        [InlineKeyboardButton("💬 چت خصوصی", url=CHANNEL_DIRECT_LINK)],
        [InlineKeyboardButton("🕵️ چت ناشناس با ادمین", callback_data="anon_start")]
    ]
    text = "🎉 سلام خوش اومدی! برای شروع یکی از گزینه‌های زیر رو انتخاب کن:"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- FORM LOGIC ---
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["anon_mode"] = False # غیرفعال کردن حالت ناشناس هنگام شروع فرم
    msg = "*👨‍🏫 استاد:*\n\nلطفاً پاسخ خود را وارد کنید:"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")
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
    await update.message.reply_text("*📊 میزان تطبیق سوالات با جزوه (از ۵):*", parse_mode="Markdown")
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
    keyboard = [[InlineKeyboardButton("✅ ارسال", callback_data="submit_form"), InlineKeyboardButton("❌ حذف", callback_data="delete_form")]]
    await update.message.reply_text(f"📋 *فرم تکمیل شد:*\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# --- ANON CHAT LOGIC ---
async def anon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["anon_mode"] = True
    await q.message.reply_text("🕵️ پیام خودت رو بفرست تا ناشناس برای ادمین ارسال بشه:")

async def receive_anon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # این تابع فقط وقتی اجرا می‌شود که کاربر در حالت anon_mode باشد
    if context.user_data.get("anon_mode"):
        user_id = update.message.from_user.id
        msg_text = update.message.text
        keyboard = [[InlineKeyboardButton("✉️ پاسخ به کاربر", callback_data=f"admin_reply:{user_id}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام ناشناس:\n\n{msg_text}", reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("✅ پیام شما به ادمین ارسال شد.")
        context.user_data["anon_mode"] = False
    else:
        # اگر در حالت ناشناس نیست، به منوی اصلی هدایتش کن
        await start(update, context)

# --- ADMIN & REACTIONS ---
async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ قبول", callback_data=f"admin_accept:{q.from_user.id}"), InlineKeyboardButton("❌ رد", callback_data=f"admin_reject:{q.from_user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await q.message.edit_text("📨 فرم برای تایید ادمین ارسال شد.")

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("admin_accept:"):
        user_id = int(data.split(":")[1])
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=q.message.text, parse_mode="Markdown")
        post_reactions[msg.message_id] = {"likes": set(), "dislikes": set()}
        await msg.edit_reply_markup(reply_markup=reaction_keyboard(msg.message_id))
        await context.bot.send_message(chat_id=user_id, text="✅ نظر شما در کانال منتشر شد.")
    await q.message.delete()

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    action, msg_id = q.data.split(":")
    msg_id = int(msg_id)
    user_id = q.from_user.id
    res = post_reactions.setdefault(msg_id, {"likes": set(), "dislikes": set()})
    if action == "like":
        res["dislikes"].discard(user_id)
        res["likes"].add(user_id)
    else:
        res["likes"].discard(user_id)
        res["dislikes"].add(user_id)
    await q.answer("نظر شما ثبت شد")
    await q.message.edit_reply_markup(reply_markup=reaction_keyboard(msg_id))

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = int(q.data.split(":")[1])
    reply_sessions[q.from_user.id] = user_id
    await q.message.reply_text("✍️ پاسخ خود را بنویسید:")

async def admin_receive_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.message.from_user.id
    if admin_id in reply_sessions:
        user_id = reply_sessions[admin_id]
        await context.bot.send_message(chat_id=user_id, text=f"📩 پیام ادمین:\n\n{update.message.text}")
        await update.message.reply_text("✅ ارسال شد.")
        del reply_sessions[admin_id]

async def delete_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.delete()

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ================= MAIN =================
def main():
    if not TOKEN: return
    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=self_ping, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    # ۱. هندلرهای اولویت‌دار (Admin & Reactions)
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin_accept:|^admin_reject:"))
    app.add_handler(CallbackQueryHandler(handle_reaction, pattern="^(like|dislike):"))
    app.add_handler(CallbackQueryHandler(admin_reply_start, pattern="^admin_reply:"))

    # ۲. هندلر فرم (Conversation)
    conv = ConversationHandler(
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
        fallbacks=[CallbackQueryHandler(delete_form, pattern="^delete_form$")]
    )
    app.add_handler(conv)

    # ۳. هندلرهای عمومی و پیام ناشناس
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(anon_start, pattern="^anon_start$"))
    app.add_handler(CallbackQueryHandler(submit_form, pattern="^submit_form$"))
    app.add_handler(CallbackQueryHandler(end_chat, pattern="^end_chat$"))
    
    # هندلر پیام ادمین (پاسخ به ناشناس)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), admin_receive_reply))
    # هندلر پیام کاربر (ارسال ناشناس)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_anon))

    print("🚀 Bot is live...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
