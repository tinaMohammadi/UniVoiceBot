from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)

# ================= CONFIG =================
TOKEN = "8558196271:AAEuw7Rh7IZrU4_I11sJRX9TSPSPGIbGJKk"
ADMIN_ID = 7997819976
CHANNEL_ID = "@UniVoiceHub"
CHANNEL_DIRECT_LINK = "https://t.me/UniVoiceHub?direct"

# ================= STATES =================
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(14)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 ثبت نظر درباره استاد", callback_data="start_form")],
        [InlineKeyboardButton("💬 چت خصوصی", url=CHANNEL_DIRECT_LINK)],
        [InlineKeyboardButton("🕵️ چت ناشناس با ادمین", callback_data="anon_start")]
    ]
    text = """
🎉 سلام به شما رفیق تازه‌وارد! 🎉

خوش اومدی به جایی که می‌تونی با خیال راحت تجربه و نظر خودت درباره اساتید رو با بقیه دانشجوها به اشتراک بذاری! هدف؟ کمک به همه برای انتخاب بهتر ترم‌های بعد 😎

💌 نگران نباش، همه پیام‌ها کاملاً ناشناس ارسال می‌شن، پس راحت باش و هر چی دوست داری بگو.

✨ و یه چیز دیگه: اگه پیشنهادی داری یا دوست داری چیزی به ربات اضافه بشه، حتماً تو دایرکت کانال با من درمیون بذار تا با هم یه تجربه تحصیلی عالی و بی‌دردسر بسازیم!

خب، آماده‌ای شروع کنی؟ 🚀"""
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        q = update.callback_query
        await q.answer()
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= FORM =================
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await q.message.reply_text("👨‍🏫 استاد:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_PROF

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("📚 درس:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("🎓 نوع تدریس:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("💬 خصوصیات اخلاقی:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("📄 جزوه:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("🧪 پروژه:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("🕒 حضور و غیاب:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("📝 میان‌ترم:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("📘 پایان‌ترم:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("📊 میزان تطبیق سوالات با جزوه (از ۵):\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("📞 راه ارتباطی:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("📌 نتیجه‌گیری:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("📅 ترمی که با استاد داشتی:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("⭐ نمره از ۲۰:\n\nلطفا پاسخ خود را وارد کنید:")
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = "\n".join([f"{k}: {v}" for k, v in context.user_data.items()])
    keyboard = [
        [InlineKeyboardButton("✅ ارسال", callback_data="submit_form"),
         InlineKeyboardButton("❌ حذف", callback_data="delete_form")]
    ]
    await update.message.reply_text("فرم شما تکمیل شد:\n\n" + summary,
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# ================= SUBMIT =================
async def submit_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    summary = "\n".join([f"{k}: {v}" for k, v in context.user_data.items()])
    keyboard = [
        [InlineKeyboardButton("✅ قبول", callback_data=f"admin_accept:{q.from_user.id}"),
         InlineKeyboardButton("❌ رد", callback_data=f"admin_reject:{q.from_user.id}")]
    ]
    # ارسال فرم به ادمین برای بررسی
    await context.bot.send_message(chat_id=ADMIN_ID, text=summary,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
    await q.message.edit_text("📨 فرم ارسال شد و بعد از بررسی توسط ادمین منتشر می‌شود 🙏")

# ================= ADMIN ACTIONS =================
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("admin_accept:"):
        user_id = int(data.split(":")[1])
        # ارسال فرم به کانال
        summary = q.message.text
        await context.bot.send_message(chat_id=CHANNEL_ID, text=summary)
        # اطلاع کاربر
        await context.bot.send_message(chat_id=user_id, text="✅ فرم شما توسط ادمین تایید شد و در کانال منتشر شد 🙌")
        await q.message.edit_text("✅ فرم تایید و ارسال شد به کانال.")
    elif data.startswith("admin_reject:"):
        user_id = int(data.split(":")[1])
        await context.bot.send_message(chat_id=user_id, text="❌ فرم شما توسط ادمین رد شد.")
        await q.message.edit_text("❌ فرم رد شد.")

# ================= DELETE =================
async def delete_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("❌ فرم حذف شد.", reply_markup=None)

# ================= ANON CHAT =================
anon_sessions = {}   # user_id -> last message
reply_sessions = {}  # admin_id -> user_id

async def anon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["anon_mode"] = True
    await q.message.reply_text("🕵️ پیام خودت رو وارد کن تا ناشناس برای ادمین ارسال شود:")

async def receive_anon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("anon_mode"):
        user_id = update.message.from_user.id
        msg_text = update.message.text
        anon_sessions[user_id] = msg_text
        keyboard = [[InlineKeyboardButton("✉️ پاسخ به کاربر", callback_data=f"admin_reply:{user_id}")]]
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"📩 پیام ناشناس از کاربر {user_id}:\n\n{msg_text}",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("✅ پیام شما به ادمین ارسال شد.")
        context.user_data["anon_mode"] = False

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = int(q.data.split(":")[1])
    reply_sessions[q.from_user.id] = user_id
    await q.message.reply_text("✍️ پیام خود را برای کاربر وارد کنید:")

async def admin_receive_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.message.from_user.id
    if admin_id in reply_sessions:
        user_id = reply_sessions[admin_id]
        msg = update.message.text
        keyboard = [
            [InlineKeyboardButton("✉️ پاسخ به ادمین", callback_data="anon_start")],
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ]
        await context.bot.send_message(chat_id=user_id,
                                       text=f"📩 پیام ادمین:\n\n{msg}",
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("✅ پیام شما برای کاربر ارسال شد.")
        del reply_sessions[admin_id]

async def user_show_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    msg = q.data.split("user_show_msg:", 1)[1]
    keyboard = [
        [InlineKeyboardButton("✉️ پاسخ به ادمین", callback_data="anon_start")],
        [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
    ]
    await q.message.edit_text(f"📩 پیام ادمین:\n\n{msg}", reply_markup=InlineKeyboardMarkup(keyboard))

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await start(update, context)


# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()

    # ConversationHandler فرم
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
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(admin_accept|admin_reject):"))

    # هندلرهای چت ناشناس
    app.add_handler(CallbackQueryHandler(anon_start, pattern="^anon_start$"))
    app.add_handler(CallbackQueryHandler(admin_reply_start, pattern="^admin_reply:"))
    app.add_handler(CallbackQueryHandler(user_show_msg, pattern="^user_show_msg:"))
    app.add_handler(CallbackQueryHandler(end_chat, pattern="^end_chat$"))

    # جدا کردن پیام‌های کاربر و ادمین
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_ID), receive_anon))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), admin_receive_reply))

    print("✅ ربات اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
