# -*- coding: utf-8 -*-
"""
HTTP 웹 서버 - index.html 제공 및 접속 로그 출력
"""

import http.server
import datetime
import os
import urllib.request
import json


PORT = 8080


def get_location_by_ip(ip_address):
    """IP 주소로 위치 정보를 가져온다. (보너스)"""
    try:
        url = f'http://ip-api.com/json/{ip_address}'
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'success':
                return f"{data.get('country', '')} {data.get('city', '')}"
    except Exception:
        pass
    return '위치 정보 없음'


class MyHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP 요청을 처리하는 핸들러 클래스."""

    def do_GET(self):
        """GET 요청을 처리한다."""
        # 접속 시간 및 IP 출력
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        client_ip = self.client_address[0]
        location = get_location_by_ip(client_ip)
        print(f'[접속 시간] {now}')
        print(f'[IP Address] {client_ip}')
        print(f'[위치 정보] {location}')
        print('-' * 40)

        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def serve_html(self):
        """index.html 파일을 읽어서 응답으로 전송한다."""
        html_path = 'index.html'

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read().encode('utf-8')
        except (FileNotFoundError, OSError):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'index.html not found')
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """기본 로그 출력을 비활성화한다. (직접 출력으로 대체)"""
        pass


def run_server():
    """HTTP 서버를 실행한다."""
    server_address = ('', PORT)

    try:
        httpd = http.server.HTTPServer(server_address, MyHttpRequestHandler)
    except OSError:
        print(f'포트 {PORT}번이 이미 사용 중입니다.')
        user_input = input('다른 포트 번호 입력 (Enter: 8888): ').strip()
        port = int(user_input) if user_input.isdigit() else 8888
        httpd = http.server.HTTPServer(('', port), MyHttpRequestHandler)
        print(f'HTTP 서버가 시작되었습니다. http://localhost:{port}')
    else:
        print(f'HTTP 서버가 시작되었습니다. http://localhost:{PORT}')

    print('종료하려면 Ctrl+C를 누르세요.')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버를 종료합니다.')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run_server()
