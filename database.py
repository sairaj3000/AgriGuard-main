import sqlite3
import os
from datetime import datetime

DATABASE_FILE = 'agriguard.db'

def init_database():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Owners table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owners (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            samples INTEGER DEFAULT 0,
            face_data BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            confidence REAL NOT NULL,
            action TEXT NOT NULL,
            image_path TEXT,
            owner_name TEXT,
            is_owner BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_key TEXT UNIQUE NOT NULL,
            stat_value INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Active intrusions table (for unique tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_intrusions (
            intrusion_type TEXT PRIMARY KEY,
            last_seen REAL NOT NULL,
            telegram_sent BOOLEAN DEFAULT 0,
            last_action REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_type ON detections(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_created ON detections(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at)')
    
    # Insert default settings
    default_settings = {
        'confidenceThreshold': '0.5',
        'actionCooldown': '3',
        'intrusionTimeout': '10',
        'faceThreshold': '70',
        'faceRecognition': 'true',
        'telegramAlerts': 'true',
        'arduinoPort': 'COM3',
        'cameraIndex': '0',
        'telegramBotToken': '',
        'telegramChatId': ''
    }
    
    for key, value in default_settings.items():
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES (?, ?)
        ''', (key, value))
    
    # Insert default statistics
    default_stats = {
        'total': 0,
        'birds': 0,
        'humans': 0,
        'elephants': 0,
        'wildAnimals': 0,
        'ownerDetections': 0
    }
    
    for key, value in default_stats.items():
        cursor.execute('''
            INSERT OR IGNORE INTO statistics (stat_key, stat_value) 
            VALUES (?, ?)
        ''', (key, value))
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_FILE, check_same_thread=False)

# Database helper functions
class DB:
    @staticmethod
    def get_setting(key, default=None):
        """Get a setting value"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    @staticmethod
    def set_setting(key, value):
        """Set a setting value"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at) 
            VALUES (?, ?, ?)
        ''', (key, str(value), datetime.now()))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all_settings():
        """Get all settings as dictionary"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Convert string values to appropriate types
        if 'confidenceThreshold' in settings:
            settings['confidenceThreshold'] = float(settings['confidenceThreshold'])
        if 'actionCooldown' in settings:
            settings['actionCooldown'] = int(settings['actionCooldown'])
        if 'intrusionTimeout' in settings:
            settings['intrusionTimeout'] = int(settings['intrusionTimeout'])
        if 'faceThreshold' in settings:
            settings['faceThreshold'] = int(settings['faceThreshold'])
        if 'cameraIndex' in settings:
            settings['cameraIndex'] = int(settings['cameraIndex'])
        if 'faceRecognition' in settings:
            settings['faceRecognition'] = settings['faceRecognition'].lower() == 'true'
        if 'telegramAlerts' in settings:
            settings['telegramAlerts'] = settings['telegramAlerts'].lower() == 'true'
        
        return settings
    
    @staticmethod
    def update_settings(settings_dict):
        """Update multiple settings"""
        conn = get_connection()
        cursor = conn.cursor()
        for key, value in settings_dict.items():
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at) 
                VALUES (?, ?, ?)
            ''', (key, str(value), datetime.now()))
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_owner(owner_id, name, samples, face_data):
        """Add or update owner"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO owners (id, name, samples, face_data, updated_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (owner_id, name, samples, face_data, datetime.now()))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_owners():
        """Get all owners"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, samples, 
                   strftime('%Y-%m-%d %H:%M', created_at) as date 
            FROM owners ORDER BY created_at DESC
        ''')
        owners = [{'id': row[0], 'name': row[1], 'samples': row[2], 'date': row[3]} 
                  for row in cursor.fetchall()]
        conn.close()
        return owners
    
    @staticmethod
    def get_owner_face_data(owner_id):
        """Get owner's face recognition data"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT face_data FROM owners WHERE id = ?', (owner_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    @staticmethod
    def delete_owner(owner_id):
        """Delete owner"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM owners WHERE id = ?', (owner_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_detection(det_type, confidence, action, image_path='', owner_name=None, is_owner=False):
        """Add detection record"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO detections (type, confidence, action, image_path, owner_name, is_owner) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (det_type, confidence, action, image_path, owner_name, is_owner))
        conn.commit()
        conn.close()
        
        # Update statistics
        if is_owner:
            DB.increment_stat('ownerDetections')
        else:
            DB.increment_stat('total')
            if det_type == 'bird':
                DB.increment_stat('birds')
            elif det_type == 'person':
                DB.increment_stat('humans')
            elif det_type == 'elephant':
                DB.increment_stat('elephants')
            elif det_type == 'wild_animal':
                DB.increment_stat('wildAnimals')
    
    @staticmethod
    def get_detections(limit=50):
        """Get recent detections"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, type, confidence, action, image_path, owner_name, 
                   strftime('%Y-%m-%d %H:%M:%S', created_at) as timestamp
            FROM detections 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        detections = []
        for row in cursor.fetchall():
            detections.append({
                'id': row[0],
                'type': row[1],
                'confidence': row[2],
                'action': row[3],
                'image': row[4],
                'owner_name': row[5],
                'timestamp': row[6]
            })
        conn.close()
        return detections
    
    @staticmethod
    def add_log(level, message):
        """Add log entry"""
        conn = get_connection()
        cursor = conn.cursor()

        # Insert log
        cursor.execute('''
            INSERT INTO logs (level, message) 
            VALUES (?, ?)
        ''', (level, message))
        conn.commit()
        conn.close()

        # Cleanup old logs (use new connection)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM logs 
            WHERE id NOT IN (
                SELECT id FROM logs 
                ORDER BY created_at DESC 
                LIMIT 1000
            )
        ''')
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_logs(limit=100):
        """Get recent logs"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, level, message, 
                   strftime('%H:%M:%S', created_at) as timestamp
            FROM logs 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'level': row[1],
                'message': row[2],
                'timestamp': row[3]
            })
        conn.close()
        return logs
    
    @staticmethod
    def clear_logs():
        """Clear all logs"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM logs')
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_stats():
        """Get statistics"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stat_key, stat_value FROM statistics')
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return stats
    
    @staticmethod
    def increment_stat(stat_key):
        """Increment a statistic"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE statistics 
            SET stat_value = stat_value + 1, 
                updated_at = ? 
            WHERE stat_key = ?
        ''', (datetime.now(), stat_key))
        conn.commit()
        conn.close()
    
    @staticmethod
    def reset_stats():
        """Reset all statistics to 0"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE statistics SET stat_value = 0')
        conn.commit()
        conn.close()
    
    @staticmethod
    def set_active_intrusion(intrusion_type, last_seen, telegram_sent=False, last_action=None):
        """Set or update active intrusion"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO active_intrusions 
            (intrusion_type, last_seen, telegram_sent, last_action, updated_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (intrusion_type, last_seen, telegram_sent, last_action, datetime.now()))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_active_intrusions():
        """Get all active intrusions"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT intrusion_type, last_seen, telegram_sent, last_action 
            FROM active_intrusions
        ''')
        intrusions = {}
        for row in cursor.fetchall():
            intrusions[row[0]] = {
                'last_seen': row[1],
                'telegram_sent': row[2],
                'last_action': row[3]
            }
        conn.close()
        return intrusions
    
    @staticmethod
    def remove_active_intrusion(intrusion_type):
        """Remove active intrusion"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM active_intrusions WHERE intrusion_type = ?', (intrusion_type,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def clear_active_intrusions():
        """Clear all active intrusions"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM active_intrusions')
        conn.commit()
        conn.close()

if __name__ == '__main__':
    print("Initializing database...")
    init_database()
    print("Database ready!")