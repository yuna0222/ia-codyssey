"""
mars_weather_summary.py - 화성 날씨 데이터 MySQL 저장

문제 5: 내일 날씨는 맑음
- mars_weathers_data.csv를 읽어 MySQL mars_weather 테이블에 저장한다.
- 보너스: MySQLHelper 클래스로 DB 연결 및 쿼리를 캡슐화한다.
"""

import csv
import subprocess
import sys
import time

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print('[오류] mysql-connector-python 패키지가 필요합니다.')
    print('  pip install mysql-connector-python')
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# MySQL 서버 시작 및 DB 초기화
# ─────────────────────────────────────────────────────────────────

def ensure_mysql_running():
    """
    MySQL 서버가 실행 중인지 확인하고, 꺼져 있으면 자동으로 시작한다.
    brew services를 통해 제어하며, Mac 환경에서만 동작한다.
    """
    print('[MySQL] 서버 상태 확인 중...')

    # 현재 상태를 먼저 출력
    status_result = subprocess.run(
        ['brew', 'services', 'list'],
        capture_output=True,
        text=True
    )
    for line in status_result.stdout.splitlines():
        if 'mysql' in line:
            print(f'  현재 상태: {line.strip()}')
            break

    # 현재 실행 여부 확인
    result = subprocess.run(
        ['brew', 'services', 'list'],
        capture_output=True,
        text=True
    )

    if 'mysql' not in result.stdout:
        print('[MySQL] mysql이 설치되어 있지 않습니다.')
        print('  아래 명령어로 설치해주세요:')
        print('  brew install mysql')
        sys.exit(1)

    # 실행 중인지 확인 (started 상태)
    mysql_running = any(
        'mysql' in line and 'started' in line
        for line in result.stdout.splitlines()
    )

    if mysql_running:
        print('[MySQL] 서버가 이미 실행 중입니다.')
        return

    # 서버 시작
    print('[MySQL] 서버를 시작합니다...')
    start_result = subprocess.run(
        ['brew', 'services', 'start', 'mysql'],
        capture_output=True,
        text=True
    )

    if start_result.returncode != 0:
        print(f'[MySQL] 시작 실패: {start_result.stderr.strip()}')
        sys.exit(1)

    # 서버가 완전히 뜰 때까지 최대 10초 대기
    for i in range(10):
        time.sleep(1)
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=DB_PASSWORD
            )
            conn.close()
            print('[MySQL] 서버 시작 완료')
            return
        except MySQLError:
            print(f'  대기 중... ({i + 1}초)')

    print('[MySQL] 서버 시작 시간 초과. 직접 확인해주세요.')
    sys.exit(1)


def ensure_database():
    """
    데이터베이스가 없으면 자동으로 생성한다.
    database 없이 root로 접속하여 CREATE DATABASE를 실행한다.
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(
            f'CREATE DATABASE IF NOT EXISTS {DB_NAME}'
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f'[DB] 데이터베이스 \'{DB_NAME}\' 준비 완료')
    except MySQLError as e:
        print(f'[DB] 데이터베이스 생성 실패: {e}')
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# 보너스: MySQLHelper 클래스
# ─────────────────────────────────────────────────────────────────

class MySQLHelper:
    """MySQL 연결 및 쿼리 실행을 캡슐화하는 헬퍼 클래스."""

    def __init__(self, host, user, password, database):
        """
        MySQL 연결을 초기화한다.

        Args:
            host (str): MySQL 서버 주소
            user (str): 사용자 이름
            password (str): 비밀번호
            database (str): 사용할 데이터베이스 이름
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.connection.cursor()
            print(f'[DB] {host}/{database} 연결 성공')
        except MySQLError as e:
            print(f'[DB 연결 실패] {e}')
            sys.exit(1)

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
# 테이블 생성
# ─────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS mars_weather (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    mars_date  DATETIME NOT NULL,
    temp       INT,
    storm      INT
)
'''


def create_table(db):
    """mars_weather 테이블이 없으면 생성한다."""
    db.execute(CREATE_TABLE_SQL)
    db.commit()
    print('[DB] mars_weather 테이블 준비 완료')


# ─────────────────────────────────────────────────────────────────
# CSV 읽기
# ─────────────────────────────────────────────────────────────────

def read_csv(file_path):
    """
    CSV 파일을 읽어 (mars_date, temp, storm) 튜플 목록으로 반환한다.

    CSV 컬럼: weather_id, mars_date, temp, stom(storm 오타)
    weather_id는 AUTO_INCREMENT이므로 읽지 않는다.

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
                    storm = int(row['stom'])   # CSV 오타 컬럼명
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

    Args:
        db (MySQLHelper): DB 헬퍼 인스턴스
        rows (list[tuple]): (mars_date, temp, storm) 목록
    """
    db.execute_many(INSERT_SQL, rows)
    db.commit()
    print(f'[DB] {len(rows)}개 행 삽입 완료')


# ─────────────────────────────────────────────────────────────────
# 결과 확인
# ─────────────────────────────────────────────────────────────────

def print_summary(db):
    """저장된 데이터의 요약 정보를 출력한다."""
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

    print()
    print('=== 화성 날씨 데이터 요약 ===')
    print(f'  총 데이터 수  : {total}개')
    print(f'  기간          : {date_range[0]} ~ {date_range[1]}')
    print(f'  평균 기온     : {float(temp_info[0]):.1f}°C')
    print(f'  최저 / 최고   : {temp_info[1]}°C / {temp_info[2]}°C')
    print(f'  폭풍 위험일   : {storm_count}일 (storm >= 70)')


# ─────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''          # 본인의 MySQL 비밀번호 입력
DB_NAME = 'mars_mission'
CSV_FILE = 'mars_weathers_data.csv'


# ─────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────

def stop_mysql():
    """
    MySQL 서버를 종료한다.
    brew services를 통해 제어하며, Mac 환경에서만 동작한다.
    이미 꺼져 있으면 메시지만 출력하고 넘어간다.
    """
    print('[MySQL] 서버 종료 중...')

    result = subprocess.run(
        ['brew', 'services', 'stop', 'mysql'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f'[MySQL] 종료 실패: {result.stderr.strip()}')
        return

    # 완전히 꺼질 때까지 최대 5초 대기
    for i in range(5):
        time.sleep(1)
        check = subprocess.run(
            ['brew', 'services', 'list'],
            capture_output=True,
            text=True
        )
        mysql_stopped = any(
            'mysql' in line and 'started' not in line
            for line in check.stdout.splitlines()
        )
        if mysql_stopped:
            print('[MySQL] 서버 종료 완료')
            return
        print(f'  종료 대기 중... ({i + 1}초)')

    print('[MySQL] 종료를 확인하지 못했습니다. 직접 확인해주세요.')


def main():
    """전체 실행 흐름을 관리한다."""
    # 1. MySQL 서버 자동 시작
    ensure_mysql_running()

    # 2. 데이터베이스 자동 생성
    ensure_database()

    # 3. 테이블 생성 및 데이터 삽입
    db = MySQLHelper(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        create_table(db)
        rows = read_csv(CSV_FILE)
        insert_data(db, rows)
        print_summary(db)
    finally:
        db.close()

    # 4. MySQL 서버 종료 여부 확인
    answer = input('\nMySQL 서버를 종료할까요? [Y/n]: ').strip().lower()
    if answer in ('', 'y'):
        stop_mysql()
    else:
        print('[MySQL] 서버를 계속 실행합니다.')


if __name__ == '__main__':
    main()