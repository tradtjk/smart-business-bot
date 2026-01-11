"""
Main bot file for Telegram CRM Bot
Handles bot initialization, job scheduling, and automation
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from config import Config, get_text
from handlers.user import get_handlers as user_get_handlers

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def check_uncontacted_leads(context: ContextTypes.DEFAULT_TYPE):
    """
    Job to check for uncontacted leads and send reminders
    Runs every 10 minutes
    """
    from database import Database
    db = Database(Config.DATABASE_URL)
    
    logger.info("Checking for uncontacted leads...")
    
    # Check for 1-hour uncontacted leads
    one_hour_leads = db.get_uncontacted_leads(hours=1)
    
    for lead in one_hour_leads:
        # Skip if first reminder already sent
        if lead['first_reminder_sent']:
            continue
        
        # Send first reminder to admins
        await send_reminder_to_admins(context, lead, reminder_type=1)
        
        # Mark reminder as sent
        db.mark_reminder_sent(lead['id'], 1)
    
    # Check for 24-hour uncontacted leads
    twenty_four_hour_leads = db.get_uncontacted_leads(hours=24)
    
    for lead in twenty_four_hour_leads:
        # Skip if second reminder already sent
        if lead['second_reminder_sent']:
            continue
        
        # Send second reminder to admins
        await send_reminder_to_admins(context, lead, reminder_type=2)
        
        # Mark reminder as sent
        db.mark_reminder_sent(lead['id'], 2)


async def send_reminder_to_admins(context: ContextTypes.DEFAULT_TYPE, lead: dict, reminder_type: int):
    """
    Send reminder notification to admins
    
    Args:
        context: Telegram context
        lead: Lead dictionary
        reminder_type: 1 for 1-hour, 2 for 24-hour
    """
    lang = lead['language']
    
    # Get reminder message
    if reminder_type == 1:
        title = get_text(lang, 'reminder_1h')
    else:
        title = get_text(lang, 'reminder_24h')
    
    # Status emoji
    status_emoji = {
        'HOT': '🔥',
        'WARM': '🌡',
        'COLD': '❄️'
    }
    
    # Format message
    message = f"{title}\n\n"
    message += f"**Lead #{lead['id']}**\n"
    message += f"👤 {lead['name']}\n"
    message += f"📱 {lead['phone']}\n"
    message += f"🔧 {lead['service']}\n"
    message += f"📝 {lead['description']}\n\n"
    message += f"{status_emoji.get(lead['status'], '⚪️')} Status: {lead['status']}\n"
    if lead['telegram_username']:
        message += f"💬 @{lead['telegram_username']}\n"
    message += f"🕐 Created: {lead['created_at']}"
    
    # Send to all admins
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error sending reminder to admin {admin_id}: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates"""
    logger.error(f"Update {update} caused error {context.error}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    from database import Database
    db = Database(Config.DATABASE_URL)
    
    user = update.effective_user
    lang = db.get_user_language(user.id)
    
    if user.id in Config.ADMIN_IDS:
        help_text = """
🤖 **CRM Bot Commands**

**User Commands:**
/start - Start the bot
/help - Show this help message

**Admin Commands:**
/admin - Admin panel
/leads - View recent leads
/stats - View statistics
/export - Export leads to CSV
/broadcast <message> - Send message to all users

**Features:**
✅ Multi-language support (EN/RU)
✅ Lead collection and qualification
✅ Automatic reminders
✅ Analytics and export
✅ Admin notifications
        """
    else:
        help_text = get_text(lang, 'main_menu')
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


def main():
    """Main function to start the bot"""
    import asyncio
    import sys
    import pytz
    
    # Fix event loop for Python 3.14+
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Create and set event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.info("Starting Telegram CRM Bot...")
    
    try:
        # Create application with timezone
        tz = pytz.timezone(Config.TIMEZONE)
        application = (
            Application.builder()
            .token(Config.TOKEN)
            .job_queue(None)  # Disable job queue
            .build()
        )
        
        # Add handlers
        application.add_handler(CommandHandler('help', help_command))
        
        # Add user handlers
        for handler in user_get_handlers():
            application.add_handler(handler)
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Note: Job queue disabled for now - can be enabled later
        # job_queue = application.job_queue
        # if job_queue:
        #     job_queue.run_repeating(check_uncontacted_leads, interval=600, first=60)
        
        logger.info("Bot started successfully!")
        logger.info(f"Admin IDs: {Config.ADMIN_IDS}")
        logger.info(f"Database: {Config.DATABASE_URL}")
        
        # Start polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        loop.close()


if __name__ == '__main__':
    main()
