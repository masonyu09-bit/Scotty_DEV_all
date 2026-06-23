"""
데이터베이스 상태 확인 스크립트
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "echodrive.db"


def print_table_info(table_name: str):
    """테이블 정보 출력"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n{'='*70}")
    print(f"📊 {table_name.upper()} 테이블")
    print(f"{'='*70}")

    # 테이블 크기
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    count = cursor.fetchone()['count']
    print(f"📈 레코드 수: {count}개")

    if count == 0:
        print("(데이터 없음)")
        conn.close()
        return

    # 샘플 데이터
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
    rows = cursor.fetchall()

    if rows:
        print(f"\n📋 최근 데이터 (상위 5개):")
        print("-" * 70)
        for row in rows:
            print(dict(row))

    conn.close()


def check_database():
    """전체 데이터베이스 상태 확인"""
    print("\n" + "="*70)
    print("🔍 AI EchoDrive 데이터베이스 상태 확인")
    print("="*70)

    # 데이터베이스 파일 확인
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        return

    print(f"✅ 데이터베이스 위치: {DB_PATH}")
    print(f"✅ 파일 크기: {DB_PATH.stat().st_size / 1024:.2f} KB")
    print(f"✅ 마지막 수정: {datetime.fromtimestamp(DB_PATH.stat().st_mtime)}")

    # 테이블 목록
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\n📑 테이블 목록 ({len(tables)}개):")
    for table in tables:
        print(f"   - {table}")

    # 각 테이블 정보
    for table in tables:
        print_table_info(table)

    # 통계
    print(f"\n{'='*70}")
    print("📊 통계")
    print(f"{'='*70}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 사용자 통계
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    print(f"👥 전체 사용자: {user_count}명")

    # 약점 통계
    cursor.execute("SELECT COUNT(*) as count FROM weaknesses")
    weakness_count = cursor.fetchone()['count']
    print(f"📝 저장된 약점: {weakness_count}개")

    cursor.execute("SELECT COUNT(*) as count FROM weaknesses WHERE reviewed = 0")
    unreviewd_count = cursor.fetchone()['count']
    print(f"   - 검토 대기: {unreviewd_count}개")

    cursor.execute("SELECT COUNT(*) as count FROM weaknesses WHERE reviewed = 1")
    reviewed_count = cursor.fetchone()['count']
    print(f"   - 검토 완료: {reviewed_count}개")

    # 학습 진행도 통계
    cursor.execute("SELECT COUNT(DISTINCT video_id) as count FROM learning_progress")
    video_count = cursor.fetchone()['count']
    print(f"🎓 학습한 영상: {video_count}개")

    cursor.execute("SELECT COUNT(*) as count FROM learning_progress WHERE completed = 1")
    completed_count = cursor.fetchone()['count']
    print(f"   - 완료한 학습: {completed_count}개")

    conn.close()

    # 사용자별 상세 통계
    print(f"\n{'='*70}")
    print("👤 사용자별 상세 통계")
    print(f"{'='*70}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        u.user_id,
        u.email,
        COUNT(DISTINCT w.id) as weakness_count,
        COUNT(DISTINCT lp.video_id) as video_count,
        COUNT(DISTINCT CASE WHEN lp.completed = 1 THEN lp.id END) as completed_days,
        u.created_at
    FROM users u
    LEFT JOIN weaknesses w ON u.user_id = w.user_id
    LEFT JOIN learning_progress lp ON u.user_id = lp.user_id
    GROUP BY u.user_id
    ORDER BY u.created_at DESC
    """)

    for row in cursor.fetchall():
        print(f"\n👤 {row['user_id']}")
        print(f"   📧 이메일: {row['email'] or '없음'}")
        print(f"   📝 약점: {row['weakness_count']}개")
        print(f"   🎓 학습 영상: {row['video_count']}개")
        print(f"   ✅ 완료한 학습: {row['completed_days']}개")
        print(f"   📅 가입일: {row['created_at']}")

    conn.close()

    print(f"\n{'='*70}")
    print("✅ 데이터베이스 확인 완료!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    check_database()
