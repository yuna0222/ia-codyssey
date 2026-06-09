"""
mars_weather_summary.py - 화성 날씨 데이터 MySQL 저장

문제 5: 내일 날씨는 맑음
- mars_weathers_data.csv를 읽어 MySQL mars_weather 테이블에 저장한다.
- 보너스: MySQLHelper 클래스로 DB 연결 및 쿼리를 캡슐화한다.
"""

import csv
import sys

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print('[오류] mysql-connector-python 패키지가 필요합니다.')
    print('  pip install mysql-connector-python')
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''          # 본인의 MySQL 비밀번호 입력
DB_NAME = 'mars_mission'
CSV_FILE = 'mars_weathers_data.csv'


# ─────────────────────────────────────────────────────────────────
# 보너스: MySQLHelper 클래스
# ─────────────────────────────────────────────────────────────────

class MySQLHelper:
    """MySQL 연결 및 쿼리 실행을 캡슐화하는 헬퍼 클래스."""

    def __init__(self, host, user, password, database=None):
        """
        MySQL 연결을 초기화한다.

        연결 실패 시 서버 시작 안내를 출력하고 사용자 확인 후
        최대 3회 재시도한다.

        Args:
            host (str): MySQL 서버 주소
            user (str): 사용자 이름
            password (str): 비밀번호
            database (str): 사용할 데이터베이스 이름 (없으면 None)
        """
        kwargs = dict(host=host, user=user, password=password)
        if database:
            kwargs['database'] = database

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self.connection = mysql.connector.connect(**kwargs)
                self.cursor = self.connection.cursor()
                target = f'{host}/{database}' if database else host
                print(f'[DB] {target} 연결 성공')
                return
            except MySQLError as e:
                print(f'[DB 연결 실패] {e}')
                if attempt == max_retries:
                    print('[DB] 최대 재시도 횟수 초과. 종료합니다.')
                    sys.exit(1)
                print()
                print('  MySQL 서버를 시작한 뒤 Enter를 누르세요.')
                print('    Mac  : brew services start mysql')
                print('    Linux: sudo systemctl start mysql')
                print('    Win  : net start mysql')
                print(f'  (재시도 {attempt}/{max_retries - 1})')
                input('  준비되면 Enter: ')

    def execute(self, query, params=None):
        """
        단일 쿼리를 실행한다.

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple): 바인딩할 파라미터 (없으면 None)
        """
        try:
            self.cursor.execute(query, params or ())
        except MySQLError as e:
            print(f'[쿼리 실행 실패] {e}')
            print(f'  쿼리: {query.strip()}')
            sys.exit(1)

    def execute_many(self, query, data):
        """
        동일한 쿼리를 여러 행 데이터에 반복 실행한다.

        Args:
            query (str): 실행할 SQL 쿼리
            data (list[tuple]): 각 행의 파라미터 목록
        """
        try:
            for params in data:
                self.cursor.execute(query, params)
        except MySQLError as e:
            print(f'[데이터 삽입 실패] {e}')
            self.connection.rollback()
            print('  변경 사항을 롤백했습니다.')
            sys.exit(1)

    def commit(self):
        """변경 사항을 커밋한다."""
        try:
            self.connection.commit()
        except MySQLError as e:
            print(f'[커밋 실패] {e}')
            self.connection.rollback()
            sys.exit(1)

    def fetchall(self):
        """마지막 쿼리의 전체 결과를 반환한다."""
        try:
            return self.cursor.fetchall()
        except MySQLError as e:
            print(f'[조회 실패] {e}')
            sys.exit(1)

    def close(self):
        """커서와 연결을 닫는다."""
        try:
            self.cursor.close()
            self.connection.close()
            print('[DB] 연결 종료')
        except MySQLError as e:
            print(f'[연결 종료 실패] {e}')


# ─────────────────────────────────────────────────────────────────
# DB / 테이블 초기화
# ─────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS mars_weather (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    mars_date  DATETIME NOT NULL,
    temp       INT,
    storm      INT
)
'''


def ensure_database():
    """데이터베이스가 없으면 자동으로 생성한다."""
    db = MySQLHelper(DB_HOST, DB_USER, DB_PASSWORD)
    try:
        db.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
        db.commit()
        print(f'[DB] 데이터베이스 \'{DB_NAME}\' 준비 완료')
    finally:
        db.close()


def create_table(db):
    """mars_weather 테이블이 없으면 생성한다."""
    db.execute(CREATE_TABLE_SQL)
    db.commit()
    print('[DB] mars_weather 테이블 준비 완료')


# ─────────────────────────────────────────────────────────────────
# CSV 읽기
# ─────────────────────────────────────────────────────────────────

# CSV 헤더의 storm 컬럼이 'stom'으로 오타 처리되어 있다.
CSV_STORM_COL = 'stom'


def read_csv(file_path):
    """
    CSV 파일을 읽어 (mars_date, temp, storm) 튜플 목록으로 반환한다.

    원본 CSV의 storm 컬럼명이 'stom'으로 오타 처리되어 있어
    CSV_STORM_COL 상수로 분리하여 명시적으로 처리한다.

    Args:
        file_path (str): CSV 파일 경로

    Returns:
        list[tuple]: (mars_date, temp, storm) 목록
    """
    import os
    if not os.path.exists(file_path):
        print(f'[CSV 오류] 파일을 찾을 수 없습니다: {file_path}')
        sys.exit(1)

    rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                try:
                    mars_date = row['mars_date']
                    temp = int(float(row['temp']))
                    # CSV 헤더 오타('stom')를 명시적으로 처리
                    storm = int(row[CSV_STORM_COL])
                    rows.append((mars_date, temp, storm))
                except (KeyError, ValueError) as e:
                    print(f'[CSV 경고] {i}번째 행 파싱 실패 → 건너뜀: {e}')
    except OSError as e:
        print(f'[CSV 오류] 파일 읽기 실패: {e}')
        sys.exit(1)

    if not rows:
        print('[CSV 오류] 읽어들인 데이터가 없습니다.')
        sys.exit(1)

    print(f'[CSV] {len(rows)}개 행 읽기 완료: {file_path}')
    return rows


# ─────────────────────────────────────────────────────────────────
# 데이터 삽입
# ─────────────────────────────────────────────────────────────────

INSERT_SQL = '''
INSERT INTO mars_weather (mars_date, temp, storm)
VALUES (%s, %s, %s)
'''


def insert_data(db, rows):
    """
    CSV에서 읽은 데이터를 INSERT 쿼리로 반복 실행하여 저장한다.

    삽입 전 TRUNCATE로 기존 데이터를 초기화하여 중복 적재를 방지한다.

    Args:
        db (MySQLHelper): DB 헬퍼 인스턴스
        rows (list[tuple]): (mars_date, temp, storm) 목록
    """
    db.execute('TRUNCATE TABLE mars_weather')
    db.execute_many(INSERT_SQL, rows)
    db.commit()
    print(f'[DB] {len(rows)}개 행 삽입 완료')


# ─────────────────────────────────────────────────────────────────
# 요약 조회 및 출력
# ─────────────────────────────────────────────────────────────────

def fetch_summary(db):
    """DB에서 요약 통계를 조회하여 딕셔너리로 반환한다."""
    db.execute('SELECT COUNT(*) FROM mars_weather')
    total = db.fetchall()[0][0]

    db.execute(
        'SELECT MIN(mars_date), MAX(mars_date) FROM mars_weather'
    )
    date_range = db.fetchall()[0]

    db.execute(
        'SELECT AVG(temp), MIN(temp), MAX(temp) FROM mars_weather'
    )
    temp_info = db.fetchall()[0]

    db.execute(
        'SELECT COUNT(*) FROM mars_weather WHERE storm >= 70'
    )
    storm_count = db.fetchall()[0][0]

    return {
        'total': total,
        'date_start': str(date_range[0]),
        'date_end': str(date_range[1]),
        'temp_avg': float(temp_info[0]),
        'temp_min': temp_info[1],
        'temp_max': temp_info[2],
        'storm_count': storm_count,
    }


def print_summary(summary):
    """요약 정보를 콘솔에 출력한다."""
    print()
    print('=== 화성 날씨 데이터 요약 ===')
    print(f'  총 데이터 수  : {summary["total"]}개')
    print(
        f'  기간          : {summary["date_start"]}'
        f' ~ {summary["date_end"]}'
    )
    print(f'  평균 기온     : {summary["temp_avg"]:.1f}°C')
    print(
        f'  최저 / 최고   : {summary["temp_min"]}°C'
        f' / {summary["temp_max"]}°C'
    )
    print(f'  폭풍 위험일   : {summary["storm_count"]}일 (storm >= 70)')


def save_summary_png(summary, file_path='mars_weather_summary.png'):
    """
    요약 정보를 PNG 이미지로 저장한다.

    make_png 모듈을 사용하며 외부 라이브러리 없이 동작한다.

    Args:
        summary (dict): fetch_summary()가 반환한 요약 딕셔너리
        file_path (str): 저장할 PNG 파일 경로
    """
    try:
        from make_png import draw_summary_image
    except ImportError:
        print('[PNG] make_png.py 파일이 같은 폴더에 있어야 합니다.')
        return
    draw_summary_image(summary, file_path)


# ─────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────

def main():
    """전체 실행 흐름을 관리한다."""
    # 1. 데이터베이스 자동 생성
    ensure_database()

    # 2. 테이블 생성 및 데이터 삽입
    db = MySQLHelper(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    try:
        create_table(db)
        rows = read_csv(CSV_FILE)
        insert_data(db, rows)
        summary = fetch_summary(db)
        print_summary(summary)
        save_summary_png(summary)
    finally:
        db.close()


if __name__ == '__main__':
    main()