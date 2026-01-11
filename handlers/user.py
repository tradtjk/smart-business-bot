from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import Database
from config import Config

db = None

def init_db():
    global db
    if db is None:
        db = Database()

def get_text(lang, key):
    return Config.TRANSLATIONS.get(lang, Config.TRANSLATIONS['en']).get(key, key)

# States
STATE_NONE = 'none'
STATE_NAME = 'name'
STATE_PHONE = 'phone'
STATE_SERVICE = 'service'
STATE_DESCRIPTION = 'description'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    context.user_data['state'] = STATE_NONE
    context.user_data['language'] = 'en'
    user_id = update.effective_user.id
    db.save_user_language(user_id, 'en')
    keyboard = [
        [KeyboardButton('👤 User')],
        [KeyboardButton('👑 Admin Panel (Demo)')]
    ]
    await update.message.reply_text(
        'Welcome to Smart Business Assistant 👋\n\nPlease choose your role:', 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state', STATE_NONE)
    
    # === CANCEL BUTTON ===
    if '❌' in text:
        context.user_data['state'] = STATE_NONE
        await update.message.reply_text('Cancelled.')
        return await show_role_menu(update, context)
    
    # === BACK BUTTON ===
    if '⬅️' in text:
        context.user_data['state'] = STATE_NONE
        return await show_role_menu(update, context)
    
    # === CONVERSATION STATES ===
    if state == STATE_NAME:
        context.user_data['name'] = text
        context.user_data['state'] = STATE_PHONE
        await update.message.reply_text('Enter your phone number:')
        return
    
    if state == STATE_PHONE:
        context.user_data['phone'] = text
        context.user_data['state'] = STATE_SERVICE
        services = Config.SERVICES.get('en', Config.SERVICES['en'])
        keyboard = [[KeyboardButton(s)] for s in services]
        keyboard.append([KeyboardButton('❌ Cancel')])
        await update.message.reply_text('Select service:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return
    
    if state == STATE_SERVICE:
        context.user_data['service'] = text
        context.user_data['state'] = STATE_DESCRIPTION
        keyboard = [[KeyboardButton('❌ Cancel')]]
        await update.message.reply_text('Describe your task or project:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return
    
    if state == STATE_DESCRIPTION:
        # Save lead
        desc = text
        status = 'COLD'
        for kw in ['urgent', 'asap', 'important', 'quickly']:
            if kw in desc.lower():
                status = 'HOT'
                break
        if status == 'COLD':
            for kw in ['soon', 'planning', 'interested']:
                if kw in desc.lower():
                    status = 'WARM'
                    break
        
        lead_id = db.save_lead(
            telegram_id=user_id,
            telegram_username=update.effective_user.username,
            name=context.user_data.get('name', ''),
            phone=context.user_data.get('phone', ''),
            service=context.user_data.get('service', ''),
            description=desc,
            status=status,
            language='en'
        )
        
        context.user_data['state'] = STATE_NONE
        await update.message.reply_text('✅ Thank you! Your request has been submitted.\nOur manager will contact you shortly.')
        
        # Notify admins
        lead = db.get_lead(lead_id)
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🆕 New Lead #{lead_id}\n\n"
                    f"👤 Name: {lead['name']}\n"
                    f"📞 Phone: {lead['phone']}\n"
                    f"🔧 Service: {lead['service']}\n"
                    f"📝 Description: {lead['description']}\n"
                    f"🌡️ Status: {lead['status']}"
                )
            except:
                pass
        
        return await show_role_menu(update, context)
    
    # === MAIN MENU BUTTONS ===
    
    # User button -> Show user menu
    if '👤' in text:
        context.user_data['state'] = STATE_NONE
        return await show_user_menu(update, context)
    
    # Admin button - доступно всем в демо-режиме
    if '👑' in text or 'Admin' in text:
        return await show_admin_panel(update, context)
    
    # === USER MENU BUTTONS ===
    
    # Leave request button -> Start collecting info
    if '📝' in text:
        context.user_data['state'] = STATE_NAME
        keyboard = [[KeyboardButton('❌ Cancel')]]
        await update.message.reply_text('Enter your name:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return
    
    # About button
    if 'ℹ️' in text:
        await update.message.reply_text(get_text('en', 'about_text'))
        return
    
    # === ADMIN PANEL BUTTONS ===
    
    if '📋' in text and 'Leads' in text:
        return await admin_show_leads(update, context)
    
    if '📊' in text:
        return await admin_show_stats(update, context)
    
    if '💾' in text:
        return await admin_export_leads(update, context)
    
    # === FALLBACK ===
    return await show_role_menu(update, context)

# === MENU FUNCTIONS ===

async def show_role_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton('👤 User')],
        [KeyboardButton('👑 Admin Panel (Demo)')]
    ]
    await update.message.reply_text(
        'Welcome to Smart Business Assistant 👋\n\nPlease choose your role:',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton('📝 Leave Request')],
        [KeyboardButton('ℹ️ About Us')],
        [KeyboardButton('⬅️ Back')]
    ]
    await update.message.reply_text('📋 User Menu\n\nWhat would you like to do?', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton('📋 View Leads'), KeyboardButton('📊 Statistics')],
        [KeyboardButton('💾 Export CSV')],
        [KeyboardButton('⬅️ Back')]
    ]
    await update.message.reply_text('👑 Admin Panel (DEMO)\n\nSelect an option:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# === ADMIN FUNCTIONS ===

async def admin_show_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    leads = db.get_recent_leads(limit=10)
    if not leads:
        await update.message.reply_text('No leads yet')
        return
    
    for lead in leads:
        msg = f"🆔 #{lead['id']}\n👤 Name: {lead['name']}\n📞 Phone: {lead['phone']}\n🔧 Service: {lead['service']}\n📝 Description: {lead['description']}\n🌡️ Status: {lead['status']}\n📅 Date: {lead['created_at']}"
        await update.message.reply_text(msg)

async def admin_show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    stats = db.get_stats()
    by_status = stats.get('by_status', {})
    msg = f"📊 Statistics\n\nTotal leads: {stats['total']}\nToday: {stats['today']}\nThis week: {stats['this_week']}\n\nBy status:\n🔥 HOT: {by_status.get('HOT', 0)}\n🌡️ WARM: {by_status.get('WARM', 0)}\n❄️ COLD: {by_status.get('COLD', 0)}"
    await update.message.reply_text(msg)

async def admin_export_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    filename = db.export_to_csv()
    with open(filename, 'rb') as f:
        await update.message.reply_document(document=f, filename='leads.csv', caption='📁 CSV file with leads')

def get_handlers():
    return [
        CommandHandler('start', start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    ]
