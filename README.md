# Telegram CRM Bot 🤖

A production-ready Telegram bot that works as a mini CRM system for businesses, providing lead collection, management, and analytics capabilities.

## 🌟 Features

### User Features
- **Multi-language Support** - English and Russian interfaces
- **Lead Collection** - Structured conversation flow to collect:
  - Full name
  - Phone number (with Telegram contact button)
  - Service type selection
  - Project description
- **Professional UX** - Business-style tone with clear navigation
- **Input Validation** - Ensures data quality at each step

### Lead Management
- **Automatic Qualification** - Classifies leads as HOT/WARM/COLD based on:
  - Service type
  - Keywords in description
  - Description length
- **Real-time Notifications** - Admins receive instant notifications for new leads
- **Quick Actions** - Mark leads as contacted or archived with inline buttons

### Admin Features
- **Admin Dashboard** - Comprehensive admin panel with commands:
  - `/admin` - Admin menu
  - `/leads` - View recent leads
  - `/stats` - Analytics and statistics
  - `/export` - Export leads to CSV
  - `/broadcast` - Send messages to all users
- **Analytics** - Track:
  - Total leads
  - Leads today
  - Leads this week
  - Breakdown by status (HOT/WARM/COLD)

### Automation
- **Smart Reminders** - Automatic notifications to admins:
  - 1-hour reminder if lead not contacted
  - 24-hour urgent reminder if still not contacted
- **Background Jobs** - Runs checks every 10 minutes

### Database
- **SQLite by Default** - Easy setup with no external dependencies
- **PostgreSQL Ready** - Switch to PostgreSQL for production
- **Clean Architecture** - Abstraction layer for easy database changes

## 📁 Project Structure

```
bot1/
├── bot.py                 # Main bot file with automation
├── config.py              # Configuration and translations
├── database.py            # Database abstraction layer
├── handlers/
│   ├── __init__.py
│   ├── user.py           # User interaction handlers
│   └── admin.py          # Admin command handlers
├── requirements.txt       # Python dependencies
├── Procfile              # Railway.app deployment config
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Your Telegram ID (from [@userinfobot](https://t.me/userinfobot))

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   TOKEN=your_bot_token_here
   ADMIN_IDS=123456789,987654321
   DATABASE_URL=sqlite:///crm_bot.db
   TIMEZONE=UTC
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TOKEN` | Yes | Telegram Bot Token from @BotFather | `1234567890:ABCdefGHI...` |
| `ADMIN_IDS` | Yes | Comma-separated admin Telegram IDs | `123456789,987654321` |
| `DATABASE_URL` | No | Database connection string | `sqlite:///crm_bot.db` |
| `TIMEZONE` | No | Timezone for timestamps | `UTC` or `Europe/Moscow` |

### Getting Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the token provided

### Getting Your Telegram ID

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Send `/start` command
3. Copy your ID number

## 🌐 Deployment

### Railway.app (Recommended)

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Create a new project** from GitHub repository

3. **Add environment variables** in Railway dashboard:
   - `TOKEN` - Your bot token
   - `ADMIN_IDS` - Your admin IDs

4. **Deploy** - Railway will automatically detect the Procfile and deploy

### VPS Deployment

1. **SSH into your VPS**

2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git
   ```

3. **Clone repository**
   ```bash
   git clone <your-repo-url>
   cd bot1
   ```

4. **Install Python packages**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

6. **Run with systemd** (keeps bot running)
   
   Create `/etc/systemd/system/telegram-bot.service`:
   ```ini
   [Unit]
   Description=Telegram CRM Bot
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/bot1
   ExecStart=/usr/bin/python3 /path/to/bot1/bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

## 💡 Usage

### For Users

1. Start the bot: `/start`
2. Select language (English/Russian)
3. Choose "Leave a Request"
4. Follow the conversation flow
5. Submit your lead

### For Admins

| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel |
| `/leads` | View 10 most recent leads |
| `/stats` | View analytics dashboard |
| `/export` | Download all leads as CSV |
| `/broadcast <message>` | Send message to all users |

### Lead Qualification

Leads are automatically classified:

- **🔥 HOT** - Contains urgent keywords: "urgent", "asap", "immediately", "срочно"
- **🌡 WARM** - Contains planning keywords or detailed description (20+ words)
- **❄️ COLD** - Standard inquiries

## 🛠️ Customization

### Adding New Services

Edit [`config.py`](config.py):

```python
SERVICES = {
    'en': [
        'Web Development',
        'Your New Service',  # Add here
        # ...
    ],
    'ru': [
        'Веб-разработка',
        'Ваша новая услуга',  # Add here
        # ...
    ]
}
```

### Modifying Translations

All text is in [`config.py`](config.py) under `TRANSLATIONS` dictionary:

```python
TRANSLATIONS = {
    'en': {
        'welcome': 'Your custom welcome message',
        # ...
    },
    'ru': {
        'welcome': 'Ваше приветственное сообщение',
        # ...
    }
}
```

### Adjusting Reminder Times

Edit [`config.py`](config.py):

```python
FIRST_REMINDER_DELAY = 3600    # 1 hour (in seconds)
SECOND_REMINDER_DELAY = 86400  # 24 hours (in seconds)
```

### Switching to PostgreSQL

1. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. Update [`database.py`](database.py) to use PostgreSQL adapter (SQLAlchemy recommended)

## 📊 Database Schema

### Leads Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `telegram_id` | INTEGER | User's Telegram ID |
| `telegram_username` | TEXT | Username (optional) |
| `name` | TEXT | Full name |
| `phone` | TEXT | Phone number |
| `service` | TEXT | Selected service |
| `description` | TEXT | Project description |
| `status` | TEXT | HOT/WARM/COLD |
| `language` | TEXT | User's language |
| `contacted` | INTEGER | 0 or 1 |
| `archived` | INTEGER | 0 or 1 |
| `created_at` | TIMESTAMP | Lead creation time |
| `contacted_at` | TIMESTAMP | When contacted |
| `first_reminder_sent` | INTEGER | Reminder flag |
| `second_reminder_sent` | INTEGER | Reminder flag |

## 🔒 Security

- Admin-only commands are protected
- Environment variables for sensitive data
- No hardcoded credentials
- Input validation on all user inputs

## 📝 License

This project is provided as-is for educational and commercial use.

## 🤝 Support

For issues or questions:
1. Check the configuration in `.env`
2. Review logs for error messages
3. Ensure bot token is valid
4. Verify admin IDs are correct

## 🎯 Future Enhancements

Potential improvements:
- [ ] Multiple admin roles (viewer, manager, admin)
- [ ] Lead assignment to specific managers
- [ ] Email notifications
- [ ] Integration with CRM systems (HubSpot, Salesforce)
- [ ] Payment integration
- [ ] Appointment scheduling
- [ ] Custom fields per service
- [ ] Lead scoring algorithm
- [ ] Chatbot responses with AI

## 📞 Contact

Built with ❤️ using Python and python-telegram-bot

---

**Ready to deploy?** Just add your `TOKEN` and `ADMIN_IDS` to `.env` and run!
