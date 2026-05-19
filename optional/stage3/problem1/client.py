# -*- coding: utf-8 -*-
"""
TCP/IP 소켓 통신 클라이언트
"""

import socket


def connect_to_server(host):
    """서버에 연결을 시도하고 실패 시 사용자에게 포트를 입력받는다."""
    port = 999

    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((host, port))
            return client_socket
        except PermissionError:
            client_socket.close()
            print(f'포트 {port}번은 root 권한이 필요합니다.')
            print('  - 1024 미만 포트(예: 999)를 사용하려면 sudo로 실행하세요.')
            print('  - 포트 번호를 입력하거나 Enter를 누르면 기본 포트(9999)를 사용합니다.')
            user_input = input('포트 번호 입력: ').strip()
            port = int(user_input) if user_input.isdigit() else 9999
        except (ConnectionRefusedError, OSError) as e:
            client_socket.close()
            print(f'포트 {port}번으로 연결할 수 없습니다. ({e})')
            print('서버에서 사용 중인 포트를 입력하거나 Enter를 누르면 기본 포트(9999)를 사용합니다.')
            user_input = input('포트 번호 입력: ').strip()
            port = int(user_input) if user_input.isdigit() else 9999


def run_client():
    """TCP/IP 소켓 클라이언트를 실행한다."""
    host = socket.gethostname()

    # 서버에 연결
    client_socket = connect_to_server(host)

    # 서버로부터 연결 확인 메시지 수신
    connect_msg = client_socket.recv(1024).decode('utf-8')
    print(connect_msg)

    # 메시지 송수신 루프
    while True:
        message = input('메시지를 입력하세요 (종료: quit): ')

        client_socket.send(message.encode('utf-8'))

        response = client_socket.recv(1024).decode('utf-8')

        if response.lower() == 'quit':
            print('서버와의 연결을 종료합니다.')
            break

        print(f'서버 응답: {response}')

    client_socket.close()


if __name__ == '__main__':
    run_client()