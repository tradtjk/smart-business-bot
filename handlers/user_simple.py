# -*- coding: utf-8 -*-
"""User handlers for CRM Bot"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from config import Config, get_text
from database import Database, classify_lead
import logging

logger = logging.getLogger(__name__)
db = None  # Will be initialized later
LANGUAGE, NAME, PHONE, SERVICE, DESCRIPTION = range(5)

def init_db():
    global db
    if db is None:
        db = Database(Config.DATABASE_URL)
    return db

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    keyboard = [[KeyboardButton('English'), KeyboardButton('Russian')]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Welcome! Select language:', reply_markup=reply_markup)
    return LANGUAGE

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    lang = 'en' if 'English' in update.message.text else 'ru'
    db.save_user_language(update.effective_user.id, lang)
    context.user_data['language'] = lang
    keyboard = [
        [KeyboardButton(get_text(lang, 'leave_request'))],
        [KeyboardButton(get_text(lang, 'about_services'))]
    ]
    await update.message.reply_text(get_text(lang, 'main_menu'), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    lang = db.get_user_language(update.effective_user.id)
    if get_text(lang, 'leave_request') in update.message.text:
        return await start_lead(update, context)
    await update.message.reply_text(get_text(lang, 'about_text'))

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    lang = db.get_user_language(update.effective_user.id)
    keyboard = [
        [KeyboardButton(get_text(lang, 'leave_request'))],
        [KeyboardButton(get_text(lang, 'about_services'))]
    ]
    await update.message.reply_text(get_text(lang, 'main_menu'), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def start_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    lang = db.get_user_language(update.effective_user.id)
    context.user_data['language'] = lang
    await update.message.reply_text(get_text(lang, 'ask_name'))
    return NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    context.user_data['name'] = update.message.text
    lang = context.user_data.get('language', 'en')
    keyboard = [[KeyboardButton(get_text(lang, 'share_phone'), request_contact=True)]]
    await update.message.reply_text(get_text(lang, 'ask_phone'), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone
    lang = context.user_data.get('language', 'en')
    services = Config.SERVICES[lang]
    keyboard = [[KeyboardButton(s)] for s in services]
    await update.message.reply_text(get_text(lang, 'ask_service'), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SERVICE

async def receive_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    context.user_data['service'] = update.message.text
    lang = context.user_data.get('language', 'en')
    await update.message.reply_text(get_text(lang, 'ask_description'))
    return DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    user = update.effective_user
    lang = context.user_data.get('language', 'en')
    description = update.message.text
    status = classify_lead(context.user_data['service'], description, Config.HOT_KEYWORDS, Config.WARM_KEYWORDS)
    lead_id = db.save_lead(user.id, user.username, context.user_data['name'], context.user_data['phone'], 
                          context.user_data['service'], description, status, lang)
    await notify_admins(context, lead_id)
    await update.message.reply_text(get_text(lang, 'thank_you'), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, lead_id: int):
    init_db()
    lead = db.get_lead(lead_id)
    if lead:
        msg = f"NEW LEAD\\nName: {lead['name']}\\nPhone: {lead['phone']}\\nService: {lead['service']}\\nStatus: {lead['status']}"
        keyboard = [[InlineKeyboardButton("Contacted", callback_data=f"contact_{lead_id}")]]
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, msg, reply_markup=InlineKeyboardMarkup(keyboard))
            except: pass

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    query = update.callback_query
    await query.answer()
    if query.data.startswith('contact_'):
        lead_id = int(query.data.split('_')[1])
        db.mark_contacted(lead_id)
        await query.edit_message_text(query.message.text + "\\n\\nContacted!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

lead_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_selected)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, receive_phone)],
        SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_service)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
