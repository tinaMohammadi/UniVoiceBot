import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= CONFIG =================
GROUP_CHANNEL_ID = "@classLink_online" # آیدی کانال را اینجا وارد کنید
ADMIN_ID = 7997819976
CHANNEL_TAG = "@UniVoiceHub"

# استفاده از دیکشنری برای مدیریت داده‌ها (جلوگیری از سنگین شدن دکمه)
temp_data = {}

G_RULES, G_NAME, G_PROF, G_ID, G_BOT_ADD = range(100, 105)

async def start_group_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("➕ افزودن گروه جدید", callback_data="g_add")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text("لطفاً برای ثبت گروه اقدام کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return G_RULES

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton("✅ پذیرش قوانین", callback_data="g_accept")]]
    await update.callback_query.message.edit_text("📜 قوانین ثبت گروه کلاسی را بپذیرید.", reply_markup=InlineKeyboardMarkup(keyboard))
    return G_NAME

async def ask_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📍 نام درس:")
    return G_PROF

async def ask_g_prof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_name"] = update.message.text
    await update.message.reply_text(f"📍 نام استاد درس {update.message.text}:")
    return G_ID

async def ask_g_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_prof"] = update.message.text
    await update.message.reply_text("📍 شماره مشخصه درس:")
    return G_BOT_ADD

async def ask_g_bot_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["g_id"] = update.message.text
    owner_id = update.effective_user.id
    ref_id = str(random.randint(1000, 9999)) # کد کوتاه برای شناسایی داده
    
    # ذخیره داده‌ها در حافظه موقت ربات
    temp_data[ref_id] = {
        "owner_id": owner_id,
        "name": context.user_data["g_name"],
        "prof": context.user_data["g_prof"],
        "id": context.user_data["g_id"]
    }
    
    admin_text = (f"🔔 **درخواست گروه جدید**\n\n"
                  f"📚 درس: {context.user_data['g_name']}\n"
                  f"👨‍🏫 استاد: {context.user_data['g_prof']}\n"
                  f"🔢 مشخصه: {context.user_data['g_id']}\n"
                  f"👤 صاحب: `{owner_id}`")
    
    # دکمه تایید فقط کد کوتاه شناسایی را حمل می‌کند (برای جلوگیری از خطای طولانی بودن)
    keyboard = [[InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"g_pub:{ref_id}")],
                [InlineKeyboardButton("❌ رد", callback_data=f"g_rej:{owner_id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    await update.message.reply_text("✅ درخواست شما ارسال شد. پس از تایید ادمین، گروه در کانال منتشر می‌شود.")
    return ConversationHandler.END

async def admin_group_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    action = parts[0]
    
    if action == "g_pub":
        ref_id = parts[1]
        data = temp_data.get(ref_id)
        
        if data:
            # دکمه‌های کانال (توکن حذف شده و فقط دیتای ضروری منتقل می‌شود)
            channel_kb = [[InlineKeyboardButton("📥 درخواست عضویت", callback_data=f"join_req:{data['owner_id']}:{ref_id}")],
                          [InlineKeyboardButton("🚩 گزارش", callback_data=f"report_g:{ref_id}")]]
            
            # پیام نهایی برای کانال (بدون توکن و آیدی صاحب)
            channel_text = (f"📚 **گروه کلاسی جدید**\n\n"
                           f"📖 درس: {data['name']}\n"
                           f"👨‍🏫 استاد: {data['prof']}\n"
                           f"🔢 مشخصه: {data['id']}\n\n"
                           f"🆔 {CHANNEL_TAG}")
            
            await context.bot.send_message(chat_id=GROUP_CHANNEL_ID, text=channel_text, reply_markup=InlineKeyboardMarkup(channel_kb), parse_mode="Markdown")
            await context.bot.send_message(chat_id=data['owner_id'], text=f"✅ گروه شما برای درس {data['name']} تایید و در کانال منتشر شد.")
            await q.message.edit_text("✅ پیام با موفقیت در کانال منتشر شد.")
            # داده‌ها را از حافظه پاک نمی‌کنیم تا دکمه درخواست عضویت کار کند
        else:
            await q.answer("❌ خطا: داده‌های این گروه منقضی شده است.", show_alert=True)

    elif action == "join_req":
        owner_id = parts[1]
        ref_id = parts[2]
        user = q.from_user
        data = temp_data.get(ref_id)
        
        if data:
            owner_kb = [[InlineKeyboardButton("✅ پذیرش", callback_data=f"acc_join:{user.id}:{ref_id}"),
                         InlineKeyboardButton("❌ رد", callback_data=f"rej_join:{user.id}")]]
            
            msg = (f"✳️ یک درخواست عضویت برای درس **{data['name']}** دریافت شد:\n\n"
                   f"👤 کاربر: [{user.first_name}](tg://user?id={user.id})\n"
                   f"🆔 یوزرنیم: @{user.username if user.username else 'نامشخص'}\n\n"
                   "⚠️ شما می‌توانید از طریق دکمه زیر این کاربر را تایید کنید.")
            
            await context.bot.send_message(chat_id=owner_id, text=msg, reply_markup=InlineKeyboardMarkup(owner_kb), parse_mode="Markdown")
            await q.answer("✅ درخواست شما برای صاحب گروه ارسال شد.", show_alert=True)

    elif action == "acc_join":
        target_id = parts[1]
        ref_id = parts[2]
        data = temp_data.get(ref_id)
        g_name = data['name'] if data else "درس انتخابی"
        
        await context.bot.send_message(chat_id=target_id, text=f"✅ درخواست عضویت شما در گروه **{g_name}** تایید شد!")
        await q.edit_message_text("✅ کاربر تایید شد و پیام خوش‌آمدگویی برایش ارسال گردید.")

    elif action == "report_g":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚩 گزارش تخلف دریافت شد.\nکد ارجاع: {parts[1]}\nگزارش دهنده: {q.from_user.id}")
        await q.answer("گزارش شما برای ادمین ارسال شد.", show_alert=True)
