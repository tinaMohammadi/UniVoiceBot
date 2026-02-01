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

# ایمپورت کردن از فایل ثبت گروه
try:
    from group_reg import group_conv, admin_group_decision
except ImportError:
    group_conv = None

# ================= CONFIG =================
TOKEN = "8558196271:AAGsm4xqHnFeT7avPKcOVJvcy5pWrq5ZlN0"
ADMIN_ID = 7997819976
CHANNEL_ID = "@UniVoiceHub"
CHANNEL_TAG = "@UniVoiceHub"
CHANNEL_DIRECT_LINK = "https://t.me/UniVoiceHub?direct"

logging.basicConfig(level=logging.INFO)

# ================= LIKE SYSTEM =================
post_reactions = {}  # message_id -> {"likes": set(), "dislikes": set()}

def reaction_keyboard(msg_id):
    data = post_reactions.get(msg_id, {"likes": set(), "dislikes": set()})
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"👍 {len(data['likes'])}", callback_data=f"like:{msg_id}"),
            InlineKeyboardButton(f"👎 {len(data['dislikes'])}", callback_data=f"dislike:{msg_id}")
        ],
        [
            InlineKeyboardButton("📝 ثبت نظر", url=f"https://t.me/{BOT_USERNAME}?start=form")
        ]
    ])

# ================= FORMAT FORM =================
def build_form_text(data):
    lines = []
    for title, key in FORM_QUESTIONS:
        value = data.get(key, "-")
        lines.append(f"*{title}:*\n{value}\n")

    lines.append("──────────────")
    lines.append("👍 *موافق این نظر هستم*")
    lines.append("👎 *مخالف این نظر هستم*")
    lines.append("\n⚠️ *مهم: قبل از تصمیم‌گیری بخوانید*")
    lines.append(f"\n🆔 {CHANNEL_TAG}")
    return "\n".join(lines)
# ================= STATES =================
# استفاده از اعداد بزرگ برای فرم نظرسنجی جهت جلوگیری از تداخل با group_reg
(ASK_PROF, ASK_COURSE, ASK_TEACHING, ASK_ETHICS, ASK_NOTES,
 ASK_PROJECT, ASK_ATTEND, ASK_MIDTERM, ASK_FINAL, ASK_MATCH,
 ASK_CONTACT, ASK_CONCLUSION, ASK_SEMESTER, ASK_GRADE) = range(100, 114)

(ANON_GET_MSG, ANON_CONFIRM_SEND) = range(200, 202)

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

خب، آماده‌ای شروع کنی؟ 🚀
"""
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# ================= FORM LOGIC =================
async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("*👨‍🏫 نام استاد:\n\n پاسخ خود را وارد کنید*", parse_mode="Markdown")
    return ASK_PROF

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["استاد"] = update.message.text
    await update.message.reply_text("*📚 درس:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_COURSE

async def ask_teaching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["درس"] = update.message.text
    await update.message.reply_text("*🎓 نوع تدریس:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_TEACHING

async def ask_ethics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نوع تدریس"] = update.message.text
    await update.message.reply_text("*💬 خصوصیات اخلاقی:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_ETHICS

async def ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["خصوصیات اخلاقی"] = update.message.text
    await update.message.reply_text("*📄 جزوه:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_NOTES

async def ask_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["جزوه"] = update.message.text
    await update.message.reply_text("*🧪 پروژه:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_PROJECT

async def ask_attend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پروژه"] = update.message.text
    await update.message.reply_text("*🕒 حضور و غیاب:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_ATTEND

async def ask_midterm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["حضور و غیاب"] = update.message.text
    await update.message.reply_text("*📝 میان‌ترم:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_MIDTERM

async def ask_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["میان‌ترم"] = update.message.text
    await update.message.reply_text("*📘 پایان‌ترم:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_FINAL

async def ask_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["پایان‌ترم"] = update.message.text
    await update.message.reply_text("*📊 میزان تطبیق سوالات با جزوه (از ۵):*\n\nعدد وارد کنید:", parse_mode="Markdown")
    return ASK_MATCH

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["تطبیق سوالات"] = update.message.text
    await update.message.reply_text("*📞 راه ارتباطی:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_CONTACT

async def ask_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["راه ارتباطی"] = update.message.text
    await update.message.reply_text("*📌 نتیجه‌گیری:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_CONCLUSION

async def ask_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نتیجه‌گیری"] = update.message.text
    await update.message.reply_text("*📅 ترمی که با استاد داشتی:*\n\nلطفاً پاسخ خود را وارد کنید:", parse_mode="Markdown")
    return ASK_SEMESTER

async def ask_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ترم"] = update.message.text
    await update.message.reply_text("*⭐️ نمره از ۲۰:*\n\nعدد وارد کنید:", parse_mode="Markdown")
    return ASK_GRADE

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["نمره"] = update.message.text
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ ارسال نهایی", callback_data="submit_form"), InlineKeyboardButton("❌ انصراف", callback_data="start")]]
    await update.message.reply_text(f"📋 **پیش‌نمایش فرم شما:**\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

# ================= ROUTER =================
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً یک گزینه را از منو انتخاب کنید یا دستور /start را بزنید:", reply_markup=main_menu())

# --- دکمه‌های تایید فرم توسط ادمین ---
async def submit_form_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    summary = build_form_text(context.user_data)
    keyboard = [[InlineKeyboardButton("✅ تایید", callback_data=f"admin_accept:{q.from_user.id}"), InlineKeyboardButton("❌ رد", callback_data=f"admin_reject:{q.from_user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📝 فرم جدید:\n\n{summary}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await q.edit_message_text("📨 فرم برای ادمین ارسال شد.")

# ================= ADMIN ACTIONS =================
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("admin_accept:"):
        user_id = int(data.split(":")[1])
        summary = q.message.text

        msg = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=summary,
            parse_mode="Markdown"
        )

        post_reactions[msg.message_id] = {"likes": set(), "dislikes": set()}
        await msg.edit_reply_markup(reply_markup=reaction_keyboard(msg.message_id))

        await context.bot.send_message(chat_id=user_id, text="✅ فرم شما توسط ادمین تایید شد و در کانال منتشر شد 🙌")
        await q.message.edit_text("✅ فرم تایید و ارسال شد به کانال.")

    elif data.startswith("admin_reject:"):
        user_id = int(data.split(":")[1])
        await context.bot.send_message(chat_id=user_id, text="❌ فرم شما توسط ادمین رد شد.")
        await q.message.edit_text("❌ فرم رد شد.")

# ================= LIKE HANDLER =================
async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    action, msg_id = data.split(":")
    msg_id = int(msg_id)
    user_id = q.from_user.id

    reactions = post_reactions.setdefault(msg_id, {"likes": set(), "dislikes": set()})

    if action == "like":
        reactions["dislikes"].discard(user_id)
        reactions["likes"].add(user_id)
    elif action == "dislike":
        reactions["likes"].discard(user_id)
        reactions["dislikes"].add(user_id)

    await q.message.edit_reply_markup(reply_markup=reaction_keyboard(msg_id))

# ================= DELETE =================
async def delete_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text("❌ فرم حذف شد.", reply_markup=None)

# ================= ANON CHAT =================
anon_sessions = {}
reply_sessions = {}

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
                                       text=f"📩 پیام ناشناس از کاربر:\n\n{msg_text}",
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

    # هندلر فرم نظرسنجی
    form_handler = ConversationHandler(
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
        fallbacks=[CallbackQueryHandler(start, pattern="^start$")],
        per_chat=True, per_message=False
    )

    # ترتیب هندلرها بسیار حیاتی است
    app.add_handler(CommandHandler("start", start))
    
    # اضافه کردن سیستم ثبت گروه (اگر فایل موجود باشد)
    if group_conv:
        app.add_handler(group_conv)
        app.add_handler(CallbackQueryHandler(admin_group_decision, pattern="^(g_pub|g_rej|join_req|acc_join|rej_join|report_g):"))
    
    app.add_handler(form_handler)
    
    # دکمه‌های عمومی
    app.add_handler(CallbackQueryHandler(submit_form_callback, pattern="^submit_form$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    
    # مدیریت پیام‌های متفرقه
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    print("🚀 Bot Started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
