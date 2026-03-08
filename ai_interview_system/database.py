import os
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash

# path to SQLite database
DB_PATH = os.getenv('DATABASE_PATH', 'database.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            questions TEXT,
            answers TEXT,
            scores TEXT,
            feedback TEXT,
            overall_score REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )
    conn.commit()
    conn.close()


def create_user(name: str, email: str, password: str) -> int:
    conn = get_db()
    c = conn.cursor()
    password_hash = generate_password_hash(password)
    c.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    conn.commit()
    return c.lastrowid


def get_user_by_email(email: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    return c.fetchone()


def get_user_by_id(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return c.fetchone()


def save_interview(user_id: int, role: str, difficulty: str,
                   questions: list, answers: list,
                   scores: list, feedback: dict, overall_score: float) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT INTO interviews (user_id, role, difficulty, questions, answers, scores, feedback, overall_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            user_id,
            role,
            difficulty,
            json.dumps(questions),
            json.dumps(answers),
            json.dumps(scores),
            json.dumps(feedback),
            overall_score,
        )
    )
    conn.commit()
    return c.lastrowid


def get_interviews(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM interviews WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    return c.fetchall()


def get_interview_count(user_id: int) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) as cnt FROM interviews WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    return row['cnt'] if row else 0


def update_user_profile(user_id: int, name: str, email: str):
    """Update user's name and email."""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, user_id))
    conn.commit()


def update_user_password(user_id: int, new_password: str):
    """Update user's password."""
    conn = get_db()
    c = conn.cursor()
    password_hash = generate_password_hash(new_password)
    c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
    conn.commit()


def get_interview_details(interview_id: int, user_id: int):
    """Get detailed information about a specific interview."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM interviews WHERE id = ? AND user_id = ?', (interview_id, user_id))
    return c.fetchone()


def get_progress_stats(user_id: int):
    """Get aggregated progress statistics."""
    conn = get_db()
    c = conn.cursor()
    
    # Get all interviews
    c.execute('SELECT * FROM interviews WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    interviews = c.fetchall()
    
    if not interviews:
        return {
            'total_interviews': 0,
            'average_score': 0,
            'best_score': 0,
            'worst_score': 0,
            'total_questions': 0,
            'by_role': {},
            'by_difficulty': {}
        }
    
    total_interviews = len(interviews)
    scores = [float(item['overall_score']) if item['overall_score'] else 0 for item in interviews]
    average_score = sum(scores) / len(scores) if scores else 0
    best_score = max(scores) if scores else 0
    worst_score = min(scores) if scores else 0
    
    # Count by role and difficulty
    by_role = {}
    by_difficulty = {}
    total_questions = 0
    
    for interview in interviews:
        role = interview['role']
        difficulty = interview['difficulty']
        
        if role not in by_role:
            by_role[role] = {'count': 0, 'total_score': 0, 'avg_score': 0}
        by_role[role]['count'] += 1
        by_role[role]['total_score'] += interview['overall_score'] or 0
        
        if difficulty not in by_difficulty:
            by_difficulty[difficulty] = {'count': 0, 'total_score': 0, 'avg_score': 0}
        by_difficulty[difficulty]['count'] += 1
        by_difficulty[difficulty]['total_score'] += interview['overall_score'] or 0
        
        try:
            questions_list = json.loads(interview['questions']) if interview['questions'] else []
            total_questions += len(questions_list)
        except:
            pass
    
    # Calculate averages
    for role in by_role:
        if by_role[role]['count'] > 0:
            by_role[role]['avg_score'] = round(by_role[role]['total_score'] / by_role[role]['count'], 2)
    
    for difficulty in by_difficulty:
        if by_difficulty[difficulty]['count'] > 0:
            by_difficulty[difficulty]['avg_score'] = round(by_difficulty[difficulty]['total_score'] / by_difficulty[difficulty]['count'], 2)
    
    return {
        'total_interviews': total_interviews,
        'average_score': round(average_score, 2),
        'best_score': best_score,
        'worst_score': worst_score,
        'total_questions': total_questions,
        'by_role': by_role,
        'by_difficulty': by_difficulty
    }
