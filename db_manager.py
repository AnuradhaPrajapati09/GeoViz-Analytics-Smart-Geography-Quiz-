import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "user_stats.db"

def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # 1. Stats Table (Aggregates)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            continent TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0
        )
    """)
    
    # 2. History Table (Detailed Logs) - NEW!
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            question_country TEXT,
            selected_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER
        )
    """)
    
    conn.commit()
    conn.close()

def update_user_stat(continent, is_correct):
    conn = get_conn()
    c = conn.cursor()
    
    # Check if continent exists
    c.execute("SELECT * FROM stats WHERE continent = ?", (continent,))
    row = c.fetchone()
    
    if row is None:
        attempts = 1
        correct = 1 if is_correct else 0
        c.execute("INSERT INTO stats (continent, attempts, correct) VALUES (?, ?, ?)", 
                  (continent, attempts, correct))
    else:
        c.execute("""
            UPDATE stats 
            SET attempts = attempts + 1, 
                correct = correct + ? 
            WHERE continent = ?
        """, (1 if is_correct else 0, continent))
        
    conn.commit()
    conn.close()

def log_attempt(question, selected, correct_ans, is_correct):
    """Saves the specific details of a quiz attempt."""
    conn = get_conn()
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO history (timestamp, question_country, selected_answer, correct_answer, is_correct)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, question, selected, correct_ans, 1 if is_correct else 0))
    conn.commit()
    conn.close()

def get_all_stats():
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT * FROM stats", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    
    stats_dict = {}
    if not df.empty:
        for _, row in df.iterrows():
            stats_dict[row['continent']] = {
                'attempts': row['attempts'],
                'correct': row['correct']
            }
    return stats_dict

def get_history_log():
    """Fetches the last 50 attempts for the dashboard."""
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT timestamp, question_country, selected_answer, correct_answer, is_correct FROM history ORDER BY id DESC LIMIT 50", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df
def get_profile_stats():
    """Calculate comprehensive profile statistics."""
    conn = get_conn()
    
    # Get aggregated stats
    stats = get_all_stats()
    
    # Calculate totals
    total_attempts = sum(d['attempts'] for d in stats.values())
    total_correct = sum(d['correct'] for d in stats.values())
    global_accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0
    
    # Most visited continent
    most_visited = None
    max_attempts = 0
    for continent, data in stats.items():
        if data['attempts'] > max_attempts:
            max_attempts = data['attempts']
            most_visited = continent
    
    # Get streak and achievements data
    try:
        history_df = pd.read_sql("SELECT * FROM history ORDER BY id ASC", conn)
        
        # Calculate current streak
        current_streak = 0
        if not history_df.empty:
            for _, row in history_df.iloc[::-1].iterrows():
                if row['is_correct'] == 1:
                    current_streak += 1
                else:
                    break
        
        # Best streak
        best_streak = 0
        temp_streak = 0
        if not history_df.empty:
            for _, row in history_df.iterrows():
                if row['is_correct'] == 1:
                    temp_streak += 1
                    best_streak = max(best_streak, temp_streak)
                else:
                    temp_streak = 0
        
        # Perfect scores count
        perfect_scores = 0
        if not history_df.empty:
            # Group by date and check if all attempts on that date were correct
            history_df['date'] = pd.to_datetime(history_df['timestamp']).dt.date
            for date, group in history_df.groupby('date'):
                if len(group) >= 5 and group['is_correct'].all():
                    perfect_scores += 1
        
        # Unique countries attempted
        unique_countries = history_df['question_country'].nunique() if not history_df.empty else 0
        
    except:
        current_streak = 0
        best_streak = 0
        perfect_scores = 0
        unique_countries = 0
    
    conn.close()
    
    return {
        'total_games': total_attempts,
        'total_correct': total_correct,
        'best_accuracy': global_accuracy,
        'most_visited_continent': most_visited or 'None',
        'current_streak': current_streak,
        'best_streak': best_streak,
        'perfect_scores': perfect_scores,
        'unique_countries': unique_countries
    }
