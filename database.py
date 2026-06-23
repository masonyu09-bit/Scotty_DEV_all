import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 데이터베이스 파일 경로
DB_PATH = Path(__file__).parent / "echodrive.db"

def get_connection():
    """데이터베이스 연결"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = get_connection()
    cursor = conn.cursor()

    # 약점 저장 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weaknesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        phrase TEXT NOT NULL,
        timestamp REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed INTEGER DEFAULT 0
    )
    """)

    # 학습 진행도 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        video_id TEXT NOT NULL,
        day INTEGER NOT NULL,
        completed INTEGER DEFAULT 0,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 사용자 설정 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        preferred_mode TEXT DEFAULT 'Echoing',
        daily_minutes INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def save_weakness(user_id: str, phrase: str, timestamp: float) -> Dict[str, Any]:
    """약점 저장"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO weaknesses (user_id, phrase, timestamp)
        VALUES (?, ?, ?)
        """, (user_id, phrase, timestamp))
        conn.commit()
        weakness_id = cursor.lastrowid
        return {"id": weakness_id, "status": "saved"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_weaknesses(user_id: str) -> List[Dict[str, Any]]:
    """사용자의 약점 목록 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, user_id, phrase, timestamp, created_at, reviewed
        FROM weaknesses
        WHERE user_id = ?
        ORDER BY created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_unreviewd_weaknesses(user_id: str) -> List[Dict[str, Any]]:
    """검토 안 된 약점만 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, user_id, phrase, timestamp, created_at, reviewed
        FROM weaknesses
        WHERE user_id = ? AND reviewed = 0
        ORDER BY created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def mark_weakness_as_reviewed(weakness_id: int) -> Dict[str, Any]:
    """약점을 검토 완료로 표시"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE weaknesses
        SET reviewed = 1
        WHERE id = ?
        """, (weakness_id,))
        conn.commit()
        return {"id": weakness_id, "status": "reviewed"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_learning_progress(user_id: str, video_id: str, day: int) -> Dict[str, Any]:
    """학습 진행도 저장"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO learning_progress (user_id, video_id, day, completed, completed_at)
        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        """, (user_id, video_id, day))
        conn.commit()
        progress_id = cursor.lastrowid
        return {"id": progress_id, "status": "saved"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_learning_progress(user_id: str, video_id: str) -> List[Dict[str, Any]]:
    """학습 진행도 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, user_id, video_id, day, completed, completed_at, created_at
        FROM learning_progress
        WHERE user_id = ? AND video_id = ?
        ORDER BY day ASC
        """, (user_id, video_id))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_user_settings(user_id: str) -> Dict[str, Any]:
    """사용자 설정 조회"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, user_id, preferred_mode, daily_minutes, created_at, updated_at
        FROM user_settings
        WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            # 설정이 없으면 기본값으로 생성
            cursor.execute("""
            INSERT INTO user_settings (user_id, preferred_mode, daily_minutes)
            VALUES (?, 'Echoing', 5)
            """, (user_id,))
            conn.commit()
            cursor.execute("""
            SELECT id, user_id, preferred_mode, daily_minutes, created_at, updated_at
            FROM user_settings
            WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row)
    finally:
        conn.close()

def update_user_settings(user_id: str, preferred_mode: str = None, daily_minutes: int = None) -> Dict[str, Any]:
    """사용자 설정 업데이트"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if preferred_mode and daily_minutes:
            cursor.execute("""
            UPDATE user_settings
            SET preferred_mode = ?, daily_minutes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """, (preferred_mode, daily_minutes, user_id))
        elif preferred_mode:
            cursor.execute("""
            UPDATE user_settings
            SET preferred_mode = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """, (preferred_mode, user_id))
        elif daily_minutes:
            cursor.execute("""
            UPDATE user_settings
            SET daily_minutes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """, (daily_minutes, user_id))

        conn.commit()
        return get_user_settings(user_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
