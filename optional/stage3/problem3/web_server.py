# -*- coding: utf-8 -*-
"""
HTTP 웹 서버
http.server 라이브러리를 사용하여 간단한 웹 서버를 구현한다.
"""

import http.server
import os

PORT = 8080


class MyHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP 요청을 처리하는 핸들러 클래스."""

    def do_GET(self):
        """GET 요청을 처리한다."""
        # 이미지 요청 처리 (보너스)
        if self.path.startswith('/images/'):
            self.serve_image()
        else:
            self.serve_html()

    def serve_html(self):
        """HTML 페이지를 응답으로 전송한다."""
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My HTTP Server</title>
</head>
<body>
    <h1>It is my HTTP server</h1>
    <img src="/images/mars.png" alt="Mars" style="max-width:400px;">
</body>
</html>'''

        content = html_content.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_image(self):
        """이미지 파일을 응답으로 전송한다. (보너스)"""
        image_path = self.path.lstrip('/')

        if not os.path.exists(image_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Image not found')
            return

        ext = os.path.splitext(image_path)[1].lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')

        with open(image_path, 'rb') as f:
            image_data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(image_data)))
        self.end_headers()
        self.wfile.write(image_data)

    def log_message(self, format, *args):
        """접속 로그를 출력한다."""
        print(f'[접속] {self.address_string()} - {format % args}')


def run_server():
    """HTTP 서버를 실행한다."""
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, MyHttpRequestHandler)
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
