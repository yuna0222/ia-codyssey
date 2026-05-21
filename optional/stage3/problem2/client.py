# -*- coding: utf-8 -*-
"""
TCP/IP 멀티쓰레드 채팅 클라이언트
"""

import socket
import threading


def receive_messages(client_socket):
    """서버로부터 메시지를 수신하여 출력한다."""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print('서버와의 연결이 끊어졌습니다.')
                break
            print(data.decode('utf-8'))
        except OSError:
            print('서버와의 연결이 끊어졌습니다.')
            break


def connect_to_server(host):
    """서버에 연결을 시도하고 실패 시 사용자에게 포트를 입력받는다."""
    port = 999

    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((host, port))
            return client_socket
        except (PermissionError, ConnectionRefusedError, OSError):
            client_socket.close()
            user_input = input(
                f'포트 {port}번 연결 실패. 다른 포트 번호 입력 (Enter: 9999): '
            ).strip()
            port = int(user_input) if user_input.isdigit() else 9999


def run_client():
    """채팅 클라이언트를 실행한다."""
    host = socket.gethostname()
    client_socket = connect_to_server(host)

    nickname = input('닉네임을 입력하세요: ').strip()
    client_socket.send(nickname.encode('utf-8'))

    # 수신 쓰레드 시작
    recv_thread = threading.Thread(
        target=receive_messages,
        args=(client_socket,),
        daemon=True
    )
    recv_thread.start()

    print('채팅을 시작합니다. 종료하려면 /종료 를 입력하세요.')
    print('귓속말: /귓속말 닉네임 메시지')

    while True:
        try:
            message = input()
            if not message:
                continue

            client_socket.send(message.encode('utf-8'))

            if message == '/종료':
                break
        except (BrokenPipeError, OSError):
            print('서버와의 연결이 끊어졌습니다.')
            break
        except EOFError:
            break

    client_socket.close()
    print('채팅을 종료합니다.')


if __name__ == '__main__':
    run_client()