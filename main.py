
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
# ================= SERVER FOR RENDER (KEEP ALIVE) =================
# ================= KEEP ALIVE SERVER =================
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)
# ================= CONFIG =================
TOKEN = "8558196271:AAGsm4xqHnFeT7avPKcOVJvcy5pWrq5ZlN0"
ADMIN_ID = 7997819976
CHANNEL_ID = "@UniVoiceHub"
BOT_USERNAME = "UniEchoFeedbackBot"
CHANNEL_DIRECT_LINK = "https://t.me/UniVoiceHub?direct"
CHANNEL_TAG = "@UniVoiceHub"

# ================= STATES =================
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(14)

# ================= FORM QUESTIONS =================
FORM_QUESTIONS = [
    ("👨‍🏫 استاد", "استاد"), ("📚 درس", "درس"), ("🎓 نوع تدریس", "نوع تدریس"),
    ("💬 خصوصیات اخلاقی", "خصوصیات اخلاقی"), ("📄 جزوه", "جزوه"), ("🧪 پروژه", "پروژه"),
    ("🕒 حضور و غیاب", "حضور و غیاب"), ("📝 میان‌ترم", "میان‌ترم"), ("📘 پایان‌ترم", "پایان‌ترم"),
    ("📊 میزان تطبیق سوالات با جزوه", "تطبیق سوالات"), ("📞 راه ارتباطی", "راه ارتباطی"),
    ("📌 نتیجه‌گیری", "نتیجه‌گیری"), ("📅 ترمی که با استاد داشتی", "ترم"), ("⭐️ نمره از ۲۰", "نمره"),
]

post_reactions = {} # message_id -> {"likes": set(), "dislikes": set()}
anon_sessions = {}
reply_sessions = {}

# ================= HELPERS =================
def reaction_keyboard(msg_id):
    data = post_reactions.get(msg_id, {"likes": set(), "dislikes": set()})
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {len(data['likes'])}", callback_data=f"like:{msg_id}"),
            InlineKeyboardButton(f"👎 {len(data['dislikes'])}", callback_data=f"dislike:{msg_id}")
        ],
        [InlineKeyboardButton("📝 ثبت نظر", url=f"https://t.me/{BOT_USERNAME}?start=form")]
    ])

def build_form_text(data):
    lines = []
    for title, key in FORM_QUESTIONS:
        value = data.get(key, "-")
        lines.append(f"*{title}:*\n{value}\n")
    lines.extend(["──────────────", f"🆔 {CHANNEL_TAG}"])
    return "\n".join(lines)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📝 ثبت نظر درباره استاد", callback_data="start_form")],
        [InlineKeyboardButton("💬 چت خصوصی", url=CHANNEL_DIRECT_LINK)],
        [InlineKeyboardButton("🕵️ چت ناشناس با ادمین", callback_data="anon_start")]
    ]
    text = """🎉 سلام به شما رفیق تازه‌وارد! 🎉

خوش اومدی به جایی که می‌تونی با خیال راحت تجربه و نظر خودت درباره اساتید رو با بقیه دانشجوها به اشتراک بذاری! هدف؟ کمک به همه برای انتخاب بهتر ترم‌های بعد 😎

💌 نگران نباش، همه پیام‌ها کاملاً ناشناس ارسال می‌شن، پس راحت باش و هر چی دوست داری بگو.

✨ و یه چیز دیگه: اگه پیشنهادی داری یا دوست داری چیزی به ربات اضافه بشه، حتماً تو دایرکت کانال با من درمیون بذار تا با هم یه تجربه تحصیلی عالی و بی‌دردسر بسازیم!

خب، آماده‌ای شروع کنی؟ 🚀
"""
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("*👨‍🏫 استاد:*\n\nنام استاد را وارد کنید:", parse_mode="Markdown")
    else:
        await update.message.reply_text("*👨‍🏫 استاد:*\n\nنام استاد را وارد کنید:", parse_mode="Markdown")
    context.user_data.clear()
    return ASK_PROF

async def delete_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer("فرم حذف شد")
        await query.message.edit_text("❌ عملیات لغو شد. فرم شما پاک گردید.")
    else:
        await update.message.reply_text("❌ عملیات لغو شد.")
    context.user_data.clear()
    return ConversationHandler.END

# Logic for asking questions
async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("*📚 درس:\n\n نام درس را وارد کنید :*", parse_mode="Markdown")
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("*🎓 نوع تدریس:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("*💬 خصوصیات اخلاقی:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("*📄 جزوه:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("*🧪 پروژه:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("*🕒 حضور و غیاب:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("*📝 میان‌ترم:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("*📘 پایان‌ترم:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("*📊 میزان تطبیق سوالات با جزوه (از 5):\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("*📞 راه ارتباطی:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("*📌 نتیجه‌گیری:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("*📅 ترمی که با استاد داشتی:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("*⭐️ نمره از ۲۰:\n\n پاسخ خود را وارد کنید:*", parse_mode="Markdown")
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = build_form_text(context.user_data)
    keyboard = [
        [InlineKeyboardButton("✅ ارسال نهایی", callback_data="submit_form"),
         InlineKeyboardButton("❌ حذف و انصراف", callback_data="delete_form")]
    ]
    await update.message.reply_text(f"📋 *پیش‌نمایش فرم شما:*\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# ================= SUBMIT & ADMIN =================
async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    summary = build_form_text(context.user_data)
    keyboard = [
        [InlineKeyboardButton("✅ تایید انتشار", callback_data=f"admin_accept:{query.from_user.id}"),
         InlineKeyboardButton("❌ رد فرم", callback_data=f"admin_reject:{query.from_user.id}")]
    ]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 فرم جدید دریافت شد:\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await query.message.edit_text("📨 فرم شما برای ادمین ارسال شد. پس از بررسی در کانال منتشر می‌شود.")

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    action = data[0]
    user_id = int(data[1])

    if action == "admin_accept":
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=query.message.text.replace("📥 فرم جدید دریافت شد:\n\n", ""), parse_mode="Markdown")
        post_reactions[msg.message_id] = {"likes": set(), "dislikes": set()}
        await msg.edit_reply_markup(reply_markup=reaction_keyboard(msg.message_id))
        await context.bot.send_message(chat_id=user_id, text="✅ نظر شما تایید و در کانال منتشر شد. ممنون از مشارکت شما!")
        await query.message.edit_text("✅ با موفقیت در کانال منتشر شد.")
    else:
        await context.bot.send_message(chat_id=user_id, text="❌ متاسفانه فرم شما توسط ادمین تایید نشد.")
        await query.message.edit_text("❌ فرم رد شد.")

# ================= REACTION SYSTEM =================
async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, msg_id = query.data.split(":")
    msg_id = int(msg_id)
    user_id = query.from_user.id
    
    res = post_reactions.setdefault(msg_id, {"likes": set(), "dislikes": set()})
    if action == "like":
        res["dislikes"].discard(user_id)
        res["likes"].add(user_id)
    else:
        res["likes"].discard(user_id)
        res["dislikes"].add(user_id)
    await query.message.edit_reply_markup(reply_markup=reaction_keyboard(msg_id))

# ================= ANON CHAT =================
# ================= GLOBAL SESSIONS =================
active_chats = {}  # user_id -> True (نشست‌های فعال چت)
reply_sessions = {} # admin_id -> target_user_id
post_reactions = {}
# ================= ANON CHAT HANDLERS =================

async def anon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    active_chats[user_id] = True  # شروع نشست چت
    
    keyboard = [[InlineKeyboardButton("❌ پایان چت ناشناس", callback_data="end_chat")]]
    await update.callback_query.message.reply_text(
        "🕵️ وارد حالت ناشناس شدی.\nهر پیامی بفرستی برای ادمین ارسال می‌شه. برای خروج دکمه زیر رو بزن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in active_chats:
        del active_chats[user_id]
    
    # اگر ادمین چت را بست
    if user_id == ADMIN_ID and user_id in reply_sessions:
        target_id = reply_sessions[user_id]
        if target_id in active_chats: del active_chats[target_id]
        await context.bot.send_message(chat_id=target_id, text="🔚 ادمین به این گفتگو پایان داد.")
        del reply_sessions[user_id]

    await query.message.edit_text("✅ چت پایان یافت. برای شروع مجدد /start را بزنید.")

async def receive_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    # ۱. اگر ادمین پیامی بفرستد و در حال پاسخ به کسی باشد
    if user_id == ADMIN_ID and user_id in reply_sessions:
        target_id = reply_sessions[user_id]
        keyboard = [[InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]]
        try:
            await context.bot.send_message(
                chat_id=target_id, 
                text=f"📩 **پاسخ ادمین:**\n\n{update.message.text}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ ارسال شد. (منتظر پیام کاربر باشید یا با /start چت را ببندید)")
        except:
            await update.message.reply_text("❌ خطا: کاربر ربات را بلاک کرده است.")
        return

    # ۲. اگر کاربر عادی در حالت چت فعال باشد
    if active_chats.get(user_id):
        username = f"@{user.username}" if user.username else "بدون یوزرنیم"
        
        keyboard = [
            [InlineKeyboardButton("✉️ پاسخ به این کاربر", callback_data=f"reply_to:{user_id}")],
            [InlineKeyboardButton("❌ قطع دسترسی کاربر", callback_data="end_chat")]
        ]
        
        admin_info = (
            f"🕵️ **پیام از:** {user.full_name}\n"
            f"🆔 `{user_id}` | {username}\n"
            f"────────────────\n"
            f"{update.message.text}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=admin_info, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        user_keyboard = [[InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]]
        await update.message.reply_text("✅ پیامت ارسال شد.", reply_markup=InlineKeyboardMarkup(user_keyboard))

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    target_id = int(update.callback_query.data.split(":")[1])
    reply_sessions[ADMIN_ID] = target_id
    await update.callback_query.message.reply_text(f"✍️ در حال پاسخ به `{target_id}` هستید. پیام خود را بفرستید:")

# ================= MAIN =================
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(submit_form, pattern="^submit_form$"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^admin_(accept|reject):"))
    app.add_handler(CallbackQueryHandler(handle_reaction, pattern="^(like|dislike):"))
    app.add_handler(CallbackQueryHandler(anon_start, pattern="^anon_start$"))
    app.add_handler(CallbackQueryHandler(admin_reply_start, pattern="^reply_to:"))
    app.add_handler(CallbackQueryHandler(end_chat, pattern="^end_chat$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_msg))

    print("✅ ربات آنلاین شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
