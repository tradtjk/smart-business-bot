from telegram.constants import ParseMode
"""
Admin handlers for Telegram CRM Bot
Handles admin commands, statistics, and lead management
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config import Config, get_text
from database import Database
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Initialize database lazily  
db = None

def init_db():
    global db
    if db is None:
        db = Database(Config.DATABASE_URL)
    return db


def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in Config.ADMIN_IDS


def admin_only(func):
    """Decorator to restrict commands to admins only"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not is_admin(user.id):
            return
        return await func(update, context)
    return wrapper


@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu"""
    init_db()
    lang = db.get_user_language(update.effective_user.id)
    
    await update.message.reply_text(get_text(lang, 'admin_menu'))


@admin_only
async def show_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent leads"""
    init_db()
    user = update.effective_user
    lang = db.get_user_language(user.id)
    
    # Get recent leads
    leads = db.get_recent_leads(limit=10)
    
    if not leads:
        await update.message.reply_text(get_text(lang, 'no_leads'))
        return
    
    # Format leads
    message = "📋 **Recent Leads**\n\n"
    
    for lead in leads:
        status_emoji = {
            'HOT': '🔥',
            'WARM': '🌡',
            'COLD': '❄️'
        }
        
        contacted_emoji = '✅' if lead['contacted'] else '⏳'
        
        message += f"{status_emoji.get(lead['status'], '⚪️')} **Lead #{lead['id']}** {contacted_emoji}\n"
        message += f"👤 {lead['name']}\n"
        message += f"📱 {lead['phone']}\n"
        message += f"🔧 {lead['service']}\n"
        message += f"📝 {lead['description'][:50]}...\n"
        message += f"🕐 {lead['created_at']}\n"
        message += "─" * 30 + "\n\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


@admin_only
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show CRM statistics"""
    init_db()
    user = update.effective_user
    lang = db.get_user_language(user.id)
    
    stats = db.get_stats()
    
    message = f"📊 **{get_text(lang, 'stats_title')}**\n\n"
    message += f"📈 {get_text(lang, 'total_leads')}: **{stats['total']}**\n"
    message += f"📅 {get_text(lang, 'today')}: **{stats['today']}**\n"
    message += f"📆 {get_text(lang, 'this_week')}: **{stats['this_week']}**\n\n"
    
    if stats['by_status']:
        message += f"**{get_text(lang, 'by_status')}:**\n"
        for status, count in stats['by_status'].items():
            status_emoji = {
                'HOT': '🔥',
                'WARM': '🌡',
                'COLD': '❄️'
            }
            message += f"{status_emoji.get(status, '⚪️')} {status}: {count}\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


@admin_only
async def export_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export leads to CSV"""
    init_db()
    user = update.effective_user
    lang = db.get_user_language(user.id)
    
    try:
        # Export to CSV
        filename = db.export_to_csv()
        
        if not filename:
            await update.message.reply_text(get_text(lang, 'no_leads'))
            return
        
        # Send file
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename='leads_export.csv',
                caption='📊 Leads exported successfully'
            )
        
        # Clean up
        import os
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        await update.message.reply_text(get_text(lang, 'error'))


@admin_only
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Broadcast a message to all users (admin command)
    Usage: /broadcast Your message here
    """
    init_db()
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    
    # Get all unique telegram IDs from leads
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT telegram_id FROM leads')
        user_ids = [row['telegram_id'] for row in cursor.fetchall()]
    
    # Send message to all users
    success_count = 0
    fail_count = 0
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n"
        f"Sent: {success_count}\n"
        f"Failed: {fail_count}"
    )


# Admin command handlers
admin_handlers = [
    CommandHandler('admin', admin_menu),
    CommandHandler('leads', show_leads),
    CommandHandler('stats', show_stats),
    CommandHandler('export', export_leads),
    CommandHandler('broadcast', broadcast_message)
]
