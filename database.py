"""
Database module for Telegram CRM Bot
Handles all database operations with abstraction layer
"""

import sqlite3
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import re


class Database:
    """Database abstraction layer for CRM bot"""
    
    def __init__(self, db_url: str = 'sqlite:///crm_bot.db'):
        """
        Initialize database connection
        
        Args:
            db_url: Database URL (SQLite or PostgreSQL)
        """
        # For now, support SQLite (easily extendable to PostgreSQL)
        self.db_path = db_url.replace('sqlite:///', '')
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create leads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    telegram_username TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    service TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    contacted INTEGER DEFAULT 0,
                    archived INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contacted_at TIMESTAMP,
                    first_reminder_sent INTEGER DEFAULT 0,
                    second_reminder_sent INTEGER DEFAULT 0
                )
            ''')
            
            # Create user preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    telegram_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_lead(self, telegram_id: int, telegram_username: Optional[str], 
                  name: str, phone: str, service: str, description: str, 
                  status: str, language: str = 'en') -> int:
        """
        Save a new lead to the database
        
        Returns:
            Lead ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leads (
                    telegram_id, telegram_username, name, phone, 
                    service, description, status, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, telegram_username, name, phone, service, 
                  description, status, language))
            
            return cursor.lastrowid
    
    def get_lead(self, lead_id: int) -> Optional[Dict]:
        """Get lead by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_recent_leads(self, limit: int = 10, archived: bool = False) -> List[Dict]:
        """
        Get recent leads
        
        Args:
            limit: Number of leads to return
            archived: Whether to include archived leads
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM leads'
            if not archived:
                query += ' WHERE archived = 0'
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            cursor.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_contacted(self, lead_id: int) -> bool:
        """Mark lead as contacted"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads 
                SET contacted = 1, contacted_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (lead_id,))
            
            return cursor.rowcount > 0
    
    def archive_lead(self, lead_id: int) -> bool:
        """Archive a lead"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leads 
                SET archived = 1 
                WHERE id = ?
            ''', (lead_id,))
            
            return cursor.rowcount > 0
    
    def get_stats(self) -> Dict:
        """Get CRM statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total leads
            cursor.execute('SELECT COUNT(*) as count FROM leads WHERE archived = 0')
            total = cursor.fetchone()['count']
            
            # Today's leads
            cursor.execute('''
                SELECT COUNT(*) as count FROM leads 
                WHERE DATE(created_at) = DATE('now') AND archived = 0
            ''')
            today = cursor.fetchone()['count']
            
            # This week's leads
            cursor.execute('''
                SELECT COUNT(*) as count FROM leads 
                WHERE DATE(created_at) >= DATE('now', '-7 days') AND archived = 0
            ''')
            this_week = cursor.fetchone()['count']
            
            # By status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM leads 
                WHERE archived = 0
                GROUP BY status
            ''')
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total': total,
                'today': today,
                'this_week': this_week,
                'by_status': by_status
            }
    
    def get_uncontacted_leads(self, hours: int) -> List[Dict]:
        """
        Get leads that haven't been contacted for X hours
        
        Args:
            hours: Number of hours since creation
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate timestamp threshold
            threshold = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT * FROM leads 
                WHERE contacted = 0 
                AND archived = 0
                AND datetime(created_at) <= ?
                ORDER BY created_at ASC
            ''', (threshold.strftime('%Y-%m-%d %H:%M:%S'),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_reminder_sent(self, lead_id: int, reminder_type: int):
        """
        Mark that a reminder was sent for a lead
        
        Args:
            lead_id: Lead ID
            reminder_type: 1 for first reminder, 2 for second
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if reminder_type == 1:
                cursor.execute('''
                    UPDATE leads 
                    SET first_reminder_sent = 1 
                    WHERE id = ?
                ''', (lead_id,))
            elif reminder_type == 2:
                cursor.execute('''
                    UPDATE leads 
                    SET second_reminder_sent = 1 
                    WHERE id = ?
                ''', (lead_id,))
    
    def export_to_csv(self, filename: str = 'leads_export.csv') -> str:
        """
        Export all leads to CSV file
        
        Returns:
            Filename of exported file
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, service, description, 
                       status, telegram_username, created_at, contacted 
                FROM leads 
                ORDER BY created_at DESC
            ''')
            
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow([
                    'ID', 'Name', 'Phone', 'Service', 'Description', 
                    'Status', 'Telegram', 'Created', 'Contacted'
                ])
                
                # Data
                for row in rows:
                    writer.writerow([
                        row['id'], row['name'], row['phone'], 
                        row['service'], row['description'], row['status'],
                        row['telegram_username'] or 'N/A', 
                        row['created_at'], 
                        'Yes' if row['contacted'] else 'No'
                    ])
            
            return filename
    
    def save_user_language(self, telegram_id: int, language: str):
        """Save user's language preference"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (telegram_id, language)
                VALUES (?, ?)
            ''', (telegram_id, language))
    
    def get_user_language(self, telegram_id: int) -> str:
        """Get user's language preference"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT language FROM user_preferences 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            row = cursor.fetchone()
            return row['language'] if row else 'en'


def classify_lead(service: str, description: str, hot_keywords: List[str], 
                  warm_keywords: List[str]) -> str:
    """
    Classify lead as HOT, WARM, or COLD based on service and description
    
    Args:
        service: Selected service
        description: User's description
        hot_keywords: List of keywords indicating hot leads
        warm_keywords: List of keywords indicating warm leads
    
    Returns:
        Lead status: 'HOT', 'WARM', or 'COLD'
    """
    description_lower = description.lower()
    
    # Check for hot keywords
    if any(keyword.lower() in description_lower for keyword in hot_keywords):
        return 'HOT'
    
    # Check for warm keywords
    if any(keyword.lower() in description_lower for keyword in warm_keywords):
        return 'WARM'
    
    # Check description length (longer = more serious)
    if len(description.split()) > 20:
        return 'WARM'
    
    return 'COLD'
