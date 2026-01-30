import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)

# ====== CONFIG ======
TOKEN = "8558196271:AAGd0nkuogmvrF9lWSyjzjsIEV2sZkt3F3w"
ADMIN_ID = 7997819976
CHANNEL_USERNAME = "@UniVoiceHub"

logging.basicConfig(level=logging.INFO)

# ====== STATES ======
(
    TEACHER, COURSE, TEACHING_STYLE, ETHICS, NOTES, PROJECT,
    ATTENDANCE, MIDTERM, FINAL, MATCHING, CONTACT, SUMMARY,
    TERM, SCORE
) = range(14)

pending_posts = {}
post_votes = {}
user_votes = {}
post_counter = 1

WELCOME_TEXT = (
    "🎓 سلام به UniVoice!\n\n"
    "اینجا جاییه که می‌تونی بدون استرس و با خیال راحت تجربه‌ت درباره استاد یا درس‌هات رو ثبت کنی 💬✨\n\n"
    "فرم کوتاهی جلوت میاد — پرش کن و بفرست.\n"
    "بعد از بررسی، نظرت تو کانال منتشر می‌شه 💙\n\n"
    "آماده‌ای؟ بزن بریم 🚀"
)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT)
    await update.message.reply_text("👨‍🏫 نام استاد رو بنویس:")
    return TEACHER


# ====== FORM STEPS ======
async def teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["teacher"] = update.message.text
    await update.message.reply_text("📘 نام درس رو بنویس:")
    return COURSE

async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["course"] = update.message.text
    await update.message.reply_text("🎤 نوع تدریس استاد چطور بود؟")
    return TEACHING_STYLE

async def teaching_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["teaching_style"] = update.message.text
    await update.message.reply_text("😊 خصوصیات اخلاقی استاد؟")
    return ETHICS

async def ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ethics"] = update.message.text
    await update.message.reply_text("📄 جزوه‌ها چطور بودن؟")
    return NOTES

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["notes"] = update.message.text
    await update.message.reply_text("🛠 پروژه داشت؟ اگر بله توضیح بده:")
    return PROJECT

async def project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["project"] = update.message.text
    await update.message.reply_text("📋 حضور و غیاب چطور بود؟")
    return ATTENDANCE

async def attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["attendance"] = update.message.text
    await update.message.reply_text("📝 میان‌ترم چطور بود؟")
    return MIDTERM

async def midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["midterm"] = update.message.text
    await update.message.reply_text("📚 پایان‌ترم چطور بود؟")
    return FINAL

async def final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["final"] = update.message.text
    await update.message.reply_text("📊 میزان تطبیق سوالات با جزوه از ۵؟ (عدد بنویس)")
    return MATCHING

async def matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["matching"] = update.message.text
    await update.message.reply_text("📞 راه ارتباطی با استاد؟")
    return CONTACT

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    await update.message.reply_text("🧠 نتیجه‌گیری کلی؟")
    return SUMMARY

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["summary"] = update.message.text
    await update.message.reply_text("📅 ترمی که این استاد داشتی؟")
    return TERM

async def term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["term"] = update.message.text
    await update.message.reply_text("⭐ نمره کلی از ۲۰؟ (عدد بنویس)")
    return SCORE

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global post_counter
    context.user_data["score"] = update.message.text

    text = (
        f"👨‍🏫 استاد: {context.user_data['teacher']}\n"
        f"📘 درس: {context.user_data['course']}\n"
        f"🎤 نوع تدریس: {context.user_data['teaching_style']}\n"
        f"😊 خصوصیات اخلاقی: {context.user_data['ethics']}\n"
        f"📄 جزوه: {context.user_data['notes']}\n"
        f"🛠 پروژه: {context.user_data['project']}\n"
        f"📋 حضور غیاب: {context.user_data['attendance']}\n"
        f"📝 میان‌ترم: {context.user_data['midterm']}\n"
        f"📚 پایان‌ترم: {context.user_data['final']}\n"
        f"📊 تطبیق با جزوه (از ۵): {context.user_data['matching']}\n"
        f"📞 راه ارتباطی: {context.user_data['contact']}\n"
        f"🧠 نتیجه‌گیری: {context.user_data['summary']}\n"
        f"📅 ترم: {context.user_data['term']}\n"
        f"⭐ نمره نهایی (از ۲۰): {context.user_data['score']}\n"
    )

    post_id = post_counter
    post_counter += 1
    pending_posts[post_id] = {
        "text": text,
        "user_id": update.effective_user.id
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{post_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="📥 نظر جدید برای بررسی:\n\n" + text,
        reply_markup=keyboard
    )

    await update.message.reply_text("📨 نظرت ثبت شد! بعد از بررسی نتیجه برات ارسال می‌شه 💙")
    return ConversationHandler.END


# ====== CALLBACK BUTTONS ======
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("approve_"):
        post_id = int(data.split("_")[1])
        post = pending_posts.pop(post_id, None)
        if not post:
            return

        post_votes[post_id] = {"like": 0, "dislike": 0}
        user_votes[post_id] = set()

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 0", callback_data=f"like_{post_id}"),
                InlineKeyboardButton("👎 0", callback_data=f"dislike_{post_id}")
            ],
            [
                InlineKeyboardButton("💬 ثبت کامنت", callback_data=f"comment_{post_id}"),
                InlineKeyboardButton("🚩 گزارش", callback_data=f"report_{post_id}")
            ],
            [
                InlineKeyboardButton("💌 چت خصوصی", url=f"tg://user?id={post['user_id']}"),
                InlineKeyboardButton("🎲 ثبت استاد شانسی", callback_data="random")
            ]
        ])

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=post["text"],
            reply_markup=keyboard
        )

        await context.bot.send_message(
            chat_id=post["user_id"],
            text="✅ نظرت تأیید شد و در کانال منتشر شد 💙 ممنون از مشارکتت!"
        )

    elif data.startswith("reject_"):
        post_id = int(data.split("_")[1])
        post = pending_posts.pop(post_id, None)
        if not post:
            return

        await context.bot.send_message(
            chat_id=post["user_id"],
            text="❌ متأسفانه نظرت تأیید نشد. می‌تونی دوباره ارسال کنی 🌱"
        )

    elif data.startswith("like_") or data.startswith("dislike_"):
        action, post_id = data.split("_")
        post_id = int(post_id)

        if update.effective_user.id in user_votes.get(post_id, set()):
            await query.answer("❗ فقط یک‌بار می‌تونی رأی بدی", show_alert=True)
            return

        user_votes[post_id].add(update.effective_user.id)
        post_votes[post_id][action] += 1

        counts = post_votes[post_id]
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"👍 {counts['like']}", callback_data=f"like_{post_id}"),
                InlineKeyboardButton(f"👎 {counts['dislike']}", callback_data=f"dislike_{post_id}")
            ],
            [
                InlineKeyboardButton("💬 ثبت کامنت", callback_data=f"comment_{post_id}"),
                InlineKeyboardButton("🚩 گزارش", callback_data=f"report_{post_id}")
            ],
            [
                InlineKeyboardButton("💌 چت خصوصی", callback_data="noop"),
                InlineKeyboardButton("🎲 ثبت استاد شانسی", callback_data="random")
            ]
        ])

        await query.edit_message_reply_markup(reply_markup=keyboard)

    elif data.startswith("comment_"):
        await query.answer("💬 این بخش به‌زودی فعال می‌شه!", show_alert=True)

    elif data.startswith("report_"):
        await query.answer("🚩 گزارش ثبت شد — بررسی می‌کنیم.", show_alert=True)

    elif data == "random":
        await query.answer("🎲 استاد شانسی بعداً فعال می‌شه 😄", show_alert=True)


# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TEACHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, teacher)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, course)],
            TEACHING_STYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, teaching_style)],
            ETHICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ethics)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, notes)],
            PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, project)],
            ATTENDANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, attendance)],
            MIDTERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, midterm)],
            FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, final)],
            MATCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, matching)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, summary)],
            TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, term)],
            SCORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, score)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_actions))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
