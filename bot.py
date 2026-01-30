import logging
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ================= CONFIG =================
TOKEN = "8558196271:AAGd0nkuogmvrF9lWSyjzjsIEV2sZkt3F3w"
ADMIN_ID = 7997819976
CHANNEL_USERNAME = "@UniVoiceHub"

DATA_FILE = "data.json"

# ==========================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Storage ----------
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"posts": {}, "votes": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


db = load_data()


# ---------- Texts ----------
WELCOME_TEXT = """🌟 به UniVoice خوش اومدی!

اینجا جاییه که می‌تونی تجربه‌ات با استادها و درس‌ها رو بدون سانسور ولی محترمانه به اشتراک بذاری ✨  
نظرت بعد از بررسی منتشر می‌شه تا بقیه هم استفاده کنن.

👇 فقط کافیه فرم رو پر کنی و بفرستی.
"""

FORM_TEXT = """📝 لطفاً این فرم رو کپی کن، پرش کن و بفرست:

👨‍🏫 استاد:
📚 درس:
🎓 نوع تدریس:
💬 خصوصیات اخلاقی:
📄 جزوه:
🧪 پروژه:
🕒 حضور و غیاب:
📝 میان‌ترم:
📘 پایان‌ترم:
📊 میزان تطبیق سوالات با جزوه (از ۵):
📞 راه ارتباطی:
🧠 نتیجه‌گیری:
📅 ترمی که با استاد داشتی:
⭐ نمره از ۲۰:
"""

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT)
    await update.message.reply_text(FORM_TEXT)


async def receive_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ✅ چک کردن که پیام واقعی و متنی باشه
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data="approve"),
            InlineKeyboardButton("❌ رد", callback_data="reject"),
        ]
    ])

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 نظر جدید از @{user.username or user.first_name}:\n\n{text}",
        reply_markup=admin_keyboard,
    )

    db["posts"][str(msg.message_id)] = {
        "user_id": user.id,
        "text": text,
        "status": "pending",
    }
    save_data(db)

    await update.message.reply_text("🌈 نظرت ثبت شد و بعد از بررسی منتشر می‌شه. ممنون از مشارکتت 💙")


# ---------- Admin Actions ----------
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    message_id = str(query.message.message_id)
    post = db["posts"].get(message_id)
    if not post:
        return

    if query.data == "approve":
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 لایک", callback_data="like"),
                InlineKeyboardButton("👎 دیسلایک", callback_data="dislike"),
            ],
            [
                InlineKeyboardButton("💬 ثبت کامنت", callback_data="comment"),
                InlineKeyboardButton("🚩 گزارش", callback_data="report"),
            ],
            [
                InlineKeyboardButton("💌 چت خصوصی", callback_data="chat"),
                InlineKeyboardButton("🎲 ثبت استاد شانسی", callback_data="random"),
            ],
        ])

        sent = await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"📢 نظر دانشجو:\n\n{post['text']}",
            reply_markup=buttons,
        )

        post["status"] = "approved"
        post["channel_msg_id"] = sent.message_id
        save_data(db)

        await context.bot.send_message(
            chat_id=post["user_id"],
            text="✅ پیام شما تایید شد و در کانال منتشر گردید 🌟",
        )

        await query.edit_message_text("✅ تایید شد و ارسال گردید.")

    elif query.data == "reject":
        await context.bot.send_message(
            chat_id=post["user_id"],
            text="❌ متأسفانه پیام شما تایید نشد. اگر دوست داشتی می‌تونی دوباره ارسال کنی 💬",
        )
        post["status"] = "rejected"
        save_data(db)
        await query.edit_message_text("❌ رد شد.")


# ---------- Voting ----------
async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    key = f"{query.message.message_id}_{user_id}"

    if key in db["votes"]:
        await query.answer("❗ قبلاً رأی دادی", show_alert=True)
        return

    db["votes"][key] = query.data
    save_data(db)

    counts = {"like": 0, "dislike": 0}
    for v in db["votes"].values():
        if v == "like":
            counts["like"] += 1
        elif v == "dislike":
            counts["dislike"] += 1

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {counts['like']}", callback_data="like"),
            InlineKeyboardButton(f"👎 {counts['dislike']}", callback_data="dislike"),
        ],
        [
            InlineKeyboardButton("💬 ثبت کامنت", callback_data="comment"),
            InlineKeyboardButton("🚩 گزارش", callback_data="report"),
        ],
        [
            InlineKeyboardButton("💌 چت خصوصی", callback_data="chat"),
            InlineKeyboardButton("🎲 ثبت استاد شانسی", callback_data="random"),
        ],
    ])

    await query.edit_message_reply_markup(reply_markup=buttons)


# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_review))
    app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^(approve|reject)$"))
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="^(like|dislike)$"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
