"""
Configuration module for Telegram CRM Bot
Loads all settings from environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Main configuration class"""
    
    # Bot settings - Debug ALL env vars
    print("=== ALL ENVIRONMENT VARIABLES ===")
    for key, value in os.environ.items():
        print(f"  {key}={value[:20] if len(value) > 20 else value}")
    print("=================================")
    
    TOKEN = os.getenv('TOKEN') or os.getenv('BOT_TOKEN')
    if not TOKEN:
        raise ValueError("TOKEN environment variable is required")
    
    # Admin settings
    ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
    ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]
    
    if not ADMIN_IDS:
        raise ValueError("ADMIN_IDS environment variable is required (comma-separated)")
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crm_bot.db')
    
    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    
    # Reminder settings (in seconds)
    FIRST_REMINDER_DELAY = 3600  # 1 hour
    SECOND_REMINDER_DELAY = 86400  # 24 hours
    
    # Services list
    SERVICES = {
        'en': [
            'Web Development',
            'Mobile App',
            'SEO & Marketing',
            'Design',
            'Consulting',
            'Other'
        ],
        'ru': [
            'Веб-разработка',
            'Мобильное приложение',
            'SEO и маркетинг',
            'Дизайн',
            'Консультация',
            'Другое'
        ]
    }
    
    # Lead qualification keywords
    HOT_KEYWORDS = ['urgent', 'asap', 'immediately', 'срочно', 'важно', 'быстро']
    WARM_KEYWORDS = ['soon', 'planning', 'interested', 'скоро', 'планирую', 'интересует']
    
    # Conversation states
    STATE_LANGUAGE = 0
    STATE_NAME = 1
    STATE_PHONE = 2
    STATE_SERVICE = 3
    STATE_DESCRIPTION = 4
    
    # Translations
    TRANSLATIONS = {
    'en': {
        'welcome': "👋 Welcome to our Business Bot!\n\nWe help businesses grow with professional services.\n\nPlease select your language:",
        'main_menu': "📋 Main Menu\n\nHow can we help you today?",
        'leave_request': '📝 Leave a Request',
        'contact_manager': '👤 Contact Manager',
        'about_services': 'ℹ️ About Services',
        'ask_name': 'Please enter your full name:',
        'ask_phone': 'Please share your phone number using the button below:',
        'ask_service': 'Which service are you interested in?',
        'ask_description': 'Please provide a brief description of your task or project:',
        'share_phone': '📱 Share Phone Number',
        'back': '⬅️ Back',
        'cancel': '❌ Cancel',
        'thank_you': '✅ Thank you! Your request has been submitted.\n\nOur manager will contact you shortly.',
        'error': '❌ An error occurred. Please try again.',
        'invalid_input': '⚠️ Invalid input. Please try again.',
        'about_text': 'ℹ️ About Our Services\n\n• Web Development\n• Mobile Applications\n• SEO & Marketing\n• Professional Design\n• Business Consulting\n\nContact us for a free consultation!',
        'manager_contact': '👤 Contact Manager\n\nYou can reach our manager:\n📱 @your_manager_username\n\nOr leave a request and we\'ll contact you!',
        'admin_menu': '🔧 Admin Panel\n\nUse commands:\n/leads - View recent leads\n/stats - Analytics\n/export - Export to CSV',
        'new_lead_title': '🔔 NEW LEAD',
        'lead_status': 'Status',
        'contacted': '✅ Contacted',
        'archive': '🗄 Archive',
        'stats_title': '📊 CRM Statistics',
        'total_leads': 'Total leads',
        'today': 'Today',
        'this_week': 'This week',
        'by_status': 'By status',
        'no_leads': 'No leads yet.',
        'lead_marked': 'Lead marked as contacted',
        'lead_archived': 'Lead archived',
        'reminder_1h': '⏰ REMINDER: Lead not contacted for 1 hour!',
        'reminder_24h': '⚠️ URGENT: Lead not contacted for 24 hours!',
    },
    'ru': {
        'welcome': "👋 Добро пожаловать в наш Бизнес-Бот!\n\nМы помогаем бизнесу расти с помощью профессиональных услуг.\n\nПожалуйста, выберите язык:",
        'main_menu': "📋 Главное меню\n\nЧем мы можем вам помочь?",
        'leave_request': '📝 Оставить заявку',
        'contact_manager': '👤 Связаться с менеджером',
        'about_services': 'ℹ️ О наших услугах',
        'ask_name': 'Пожалуйста, введите ваше полное имя:',
        'ask_phone': 'Пожалуйста, поделитесь вашим номером телефона, используя кнопку ниже:',
        'ask_service': 'Какая услуга вас интересует?',
        'ask_description': 'Пожалуйста, кратко опишите вашу задачу или проект:',
        'share_phone': '📱 Поделиться номером',
        'back': '⬅️ Назад',
        'cancel': '❌ Отмена',
        'thank_you': '✅ Спасибо! Ваша заявка принята.\n\nНаш менеджер свяжется с вами в ближайшее время.',
        'error': '❌ Произошла ошибка. Пожалуйста, попробуйте снова.',
        'invalid_input': '⚠️ Некорректный ввод. Пожалуйста, попробуйте снова.',
        'about_text': 'ℹ️ О наших услугах\n\n• Веб-разработка\n• Мобильные приложения\n• SEO и маркетинг\n• Профессиональный дизайн\n• Бизнес-консультации\n\nСвяжитесь с нами для бесплатной консультации!',
        'manager_contact': '👤 Связь с менеджером\n\nВы можете связаться с нашим менеджером:\n📱 @your_manager_username\n\nИли оставьте заявку и мы свяжемся с вами!',
        'admin_menu': '🔧 Панель администратора\n\nИспользуйте команды:\n/leads - Просмотр заявок\n/stats - Статистика\n/export - Экспорт в CSV',
        'new_lead_title': '🔔 НОВАЯ ЗАЯВКА',
        'lead_status': 'Статус',
        'contacted': '✅ Связались',
        'archive': '🗄 Архивировать',
        'stats_title': '📊 Статистика CRM',
        'total_leads': 'Всего заявок',
        'today': 'Сегодня',
        'this_week': 'За неделю',
        'by_status': 'По статусу',
        'no_leads': 'Заявок пока нет.',
        'lead_marked': 'Заявка отмечена как обработанная',
        'lead_archived': 'Заявка архивирована',
        'reminder_1h': '⏰ НАПОМИНАНИЕ: С заявкой не связались уже час!',
        'reminder_24h': '⚠️ СРОЧНО: С заявкой не связались уже 24 часа!',
    }
}


def get_text(lang: str, key: str) -> str:
    """Get translated text by language and key"""
    return Config.TRANSLATIONS.get(lang, Config.TRANSLATIONS['en']).get(key, key)
