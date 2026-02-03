
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
    ("📊 میزان تطبیق سوالات با جزوه (از 5)", "تطبیق سوالات"), ("📞 راه ارتباطی", "راه ارتباطی"),
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

# تابع کمکی برای ایجاد دکمه انصراف در هر مرحله
# تابع کمکی برای دکمه انصراف
def cancel_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف و لغو فرم", callback_data="delete_form")]])

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "✨ *شروع ثبت تجربه جدید*\n" + "─" * 15 + "\n👨‍🏫 *نام استاد:* \nلطفاً نام استاد را وارد کنید:"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=cancel_markup())
    else:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=cancel_markup())
    context.user_data.clear()
    return ASK_PROF

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("📚 *عنوان درس:*\nنام درس را وارد کنید:", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("🎓 *شیوه تدریس:*\nنحوه تدریس استاد چطور بود؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("💬 *اخلاق و برخورد:*\nبرخورد استاد با دانشجوها چطور بود؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("📄 *وضعیت جزوه:*\nآیا استاد جزوه کامل می‌دهد؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("🧪 *پروژه و کار عملی:*\nآیا این درس پروژه داشت؟ نمره‌دهی چطور بود؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("🕒 *حضور و غیاب:*\nوضعیت حضور غیاب و حساسیت استاد؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("📝 *امتحان میان‌ترم:*\nامتحان میان‌ترم چطور بود؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("📘 *امتحان پایان‌ترم:*\nسطح سوالات پایان‌ترم؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("📊 * (از 1 تا 5) تطبیق با جزوه:*\nتطبیق سوالات با جزوه (از 1 تا 5)؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("📞 *راه ارتباطی:*\nنحوه پاسخگویی و ارتباط با استاد؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("📌 *نتیجه‌گیری:*\nدر کل این استاد را پیشنهاد می‌کنید؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("📅 *ترم تحصیلی:*\nچه ترمی با این استاد داشتید؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("⭐️ *نمره نهایی:*\nنمره‌ای که از این درس گرفتید (از 20)؟", parse_mode="Markdown", reply_markup=cancel_markup())
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ ارسال نهایی", callback_data="submit_form")],
                [InlineKeyboardButton("🗑 لغو و حذف", callback_data="delete_form")]]
    # استفاده از Markdown معمولی برای جلوگیری از ارور کاراکترهای خاص
    await update.message.reply_text(f"🌈 *پیش‌نمایش فرم شما:*\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

async def delete_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🗑 فرم حذف شد.")
    await query.message.edit_text("❌ عملیات ثبت نظر لغو شد. برای شروع مجدد /start را بزنید.")
    context.user_data.clear()
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
        
        # کیبورد برای کاربر (شامل دکمه پاسخ و پایان)
        user_keyboard = [
            [InlineKeyboardButton("✉️ پاسخ به ادمین", callback_data="anon_start")], # بازنشانی حالت چت اگر قطع شده باشد
            [InlineKeyboardButton("❌ پایان چت", callback_data="end_chat")]
        ]
        
        try:
            await context.bot.send_message(
                chat_id=target_id, 
                text=f"📩 **پیام جدید از طرف ادمین:**\n\n{update.message.text}",
                reply_markup=InlineKeyboardMarkup(user_keyboard),
                parse_mode="Markdown"
            )
            await update.message.reply_text(f"✅ پیام شما به کاربر `{target_id}` تحویل داده شد.")
        except:
            await update.message.reply_text("❌ خطا: امکان ارسال پیام به کاربر وجود ندارد (شاید ربات را بلاک کرده باشد).")
        return

    # ۲. اگر کاربر عادی در حالت چت فعال باشد
    if active_chats.get(user_id):
        username = f"@{user.username}" if user.username else "بدون یوزرنیم"
        
        # کیبورد برای ادمین
        admin_keyboard = [
            [InlineKeyboardButton("✉️ پاسخ به این کاربر", callback_data=f"reply_to:{user_id}")],
            [InlineKeyboardButton("❌ قطع دسترسی کاربر", callback_data="end_chat")]
        ]
        
        admin_info = (
            f"🕵️ **پیام ناشناس جدید**\n"
            f"👤 **فرستنده:** {user.full_name}\n"
            f"🆔 `{user_id}` | {username}\n"
            f"────────────────\n"
            f"📝 **متن:** {update.message.text}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=admin_info, 
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )
        
        # تاییدیه برای کاربر (با دکمه پایان برای اطمینان)
        user_status_keyboard = [[InlineKeyboardButton("❌ پایان گفتگو", callback_data="end_chat")]]
        await update.message.reply_text(
            "🚀 پیام شما با موفقیت به ادمین رسید.\nشما می‌توانید پیام‌های بعدی خود را همینجا بفرستید یا چت را تمام کنید:",
            reply_markup=InlineKeyboardMarkup(user_status_keyboard)
        )

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    target_id = int(update.callback_query.data.split(":")[1])
    reply_sessions[ADMIN_ID] = target_id
    await update.callback_query.message.reply_text(f"✍️ در حال پاسخ به `{target_id}` هستید. پیام خود را بفرستید:")

# ================= MAIN =================
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
