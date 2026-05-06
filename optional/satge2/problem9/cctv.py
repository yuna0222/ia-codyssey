"""
cctv.py - 화성 기지 CCTV 이미지 뷰어
좌/우 방향키로 이미지를 탐색한다.
"""

import os
import zipfile
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


class MasImageHelper:
    """CCTV 이미지 목록 관리 및 ZIP 압축 해제를 담당하는 클래스."""

    EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    DEFAULT_FOLDER = 'CCTV'
    DEFAULT_ZIP = 'cctv.zip'

    def __init__(self, folder=DEFAULT_FOLDER, zip_path=DEFAULT_ZIP):
        """폴더가 없으면 ZIP을 해제한 뒤 이미지 목록을 로드한다."""
        if not os.path.exists(folder):
            self._extract(zip_path)
        if not os.path.exists(folder):
            raise FileNotFoundError(
                f'ZIP 해제 후에도 {folder} 폴더를 찾을 수 없습니다. '
                'ZIP 파일 안에 CCTV 폴더가 있는지 확인해 주세요.'
            )
        self.files = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(self.EXTENSIONS)  # 이미지 형식 아닌 건 무시
        )
        if not self.files:
            raise ValueError(f'이미지 파일이 없습니다: {folder}')
        self.index = 0

    # ── 내부 유틸 ──────────────────────────────────────────────
    def _extract(self, zip_path):
        """ZIP 파일을 현재 디렉터리에 압축 해제한다."""
        if not os.path.exists(zip_path):
            raise FileNotFoundError(
                f'CCTV 폴더와 ZIP 파일({zip_path}) 모두 찾을 수 없습니다. '
                f'{self.DEFAULT_ZIP} 파일을 이 스크립트와 같은 폴더에 넣어 주세요.'
            )
        with zipfile.ZipFile(zip_path, 'r') as z:
            names = z.namelist()
            # 폴더 구조 없이 파일만 있으면 DEFAULT_FOLDER 안에 직접 해제
            has_folder = any('/' in n for n in names)
            target = '.' if has_folder else self.DEFAULT_FOLDER
            os.makedirs(target, exist_ok=True)
            z.extractall(target)
        print(f'압축 해제 완료: {zip_path} → {target}')

    # ── 탐색 ───────────────────────────────────────────────────
    def move(self, step):
        """인덱스를 step만큼 이동한다 (순환)."""
        self.index = (self.index + step) % len(self.files)

    # ── 현재 이미지 정보 ───────────────────────────────────────
    def current_image(self):
        """현재 이미지를 PIL Image로 반환한다."""
        try:
            return Image.open(self.files[self.index])
        except (OSError, SyntaxError):
            raise OSError(f'이미지를 열 수 없습니다: {self.files[self.index]}')

    def status(self):
        """'파일명 (현재/전체)' 형식의 상태 문자열을 반환한다."""
        name = os.path.basename(self.files[self.index])
        return f'{name}  ({self.index + 1} / {len(self.files)})'


class CCTVViewer:
    """tkinter 기반 CCTV 이미지 뷰어 GUI."""

    # 캔버스 크기
    W, H = 860, 600
    # 색상
    BG = '#1a1a2e'
    BG_CANVAS = '#16213e'
    COLOR_ACCENT = '#e94560'
    COLOR_INFO = '#a8dadc'
    COLOR_HINT = '#555577'
    # 텍스트
    TITLE = '화성 기지 CCTV 뷰어'
    TITLE_LABEL = '🔴 화성 기지 CCTV'
    HINT_LABEL = '← 이전   |   → 다음'
    # 버튼 색상
    BTN_BG = '#333333'
    BTN_FG = 'white'

    def __init__(self, root, helper):
        """윈도우·위젯을 구성하고 첫 이미지를 표시한다."""
        self.helper = helper
        self._build_ui(root)
        self._show()

    # ── UI 구성 ────────────────────────────────────────────────
    def _build_ui(self, root):
        """윈도우, 캔버스, 버튼, 레이블을 생성한다."""
        root.title(self.TITLE)
        root.configure(bg=self.BG)
        root.resizable(False, False)

        # 제목
        tk.Label(root, text=self.TITLE_LABEL,
                 font=('Arial', 15, 'bold'),
                 fg=self.COLOR_ACCENT, bg=self.BG).pack(pady=(10, 0))

        # 이미지 캔버스
        self.canvas = tk.Canvas(root, width=self.W, height=self.H,
                                bg=self.BG_CANVAS, highlightthickness=2,
                                highlightbackground=self.COLOR_ACCENT)
        self.canvas.pack(pady=8)

        # 하단 버튼 · 상태 레이블
        bar = tk.Frame(root, bg=self.BG)
        bar.pack(pady=4)

        # Canvas 버튼 생성 헬퍼 (맥/윈도우 색상 일관성 보장)
        def make_btn(parent, text, command, width=120):
            """Canvas로 직접 그린 버튼."""
            c = tk.Canvas(parent, width=width, height=42,
                          bg=self.BG, highlightthickness=0, cursor='hand2')
            rect = c.create_rectangle(0, 0, width, 42,
                                      fill=self.BTN_BG, outline='')
            label = c.create_text(width // 2, 21, text=text,
                                  fill=self.BTN_FG,
                                  font=('Arial', 13, 'bold'))
            # 클릭
            c.tag_bind(rect, '<Button-1>', lambda e: command())
            c.tag_bind(label, '<Button-1>', lambda e: command())
            return c

        make_btn(bar, '◀  이전', lambda: self._nav(-1)).grid(
            row=0, column=0, padx=12)
        self.lbl = tk.Label(bar, text='', width=28,
                            font=('Arial', 12),
                            fg=self.COLOR_INFO, bg=self.BG)
        self.lbl.grid(row=0, column=1)
        make_btn(bar, '다음  ▶', lambda: self._nav(+1)).grid(
            row=0, column=2, padx=12)

        # 키보드 단축키 안내 레이블
        tk.Label(root, text=self.HINT_LABEL,
                 font=('Arial', 9), fg=self.COLOR_HINT, bg=self.BG).pack(pady=(4, 6))

        # 방향키 바인딩
        root.bind('<Left>', lambda e: self._nav(-1))
        root.bind('<Right>', lambda e: self._nav(+1))

    # ── 이미지 표시 ────────────────────────────────────────────
    def _show(self):
        """현재 이미지를 캔버스 크기에 맞춰 표시하고 상태를 갱신한다."""
        try:
            img = self.helper.current_image()
        except OSError as e:
            self.lbl.config(text=f'오류: {e}')
            return
        img.thumbnail((self.W, self.H), Image.LANCZOS)  # 비율 유지 리사이즈
        self._photo = ImageTk.PhotoImage(img)  # GC 방지용 참조 보관
        self.canvas.delete('all')
        self.canvas.create_image(self.W // 2, self.H // 2,
                                 anchor='center', image=self._photo)
        self.lbl.config(text=self.helper.status())

    # ── 탐색 ───────────────────────────────────────────────────
    def _nav(self, step):
        """step 방향으로 이동 후 이미지를 새로 표시한다."""
        self.helper.move(step)
        self._show()


def main():
    """MasImageHelper와 CCTVViewer를 초기화하고 이벤트 루프를 시작한다."""
    try:
        helper = MasImageHelper()  # ZIP 해제 + 이미지 목록 로드
    except (FileNotFoundError, ValueError) as e:
        # ZIP 파일 또는 이미지가 없을 때 GUI 에러 창으로 안내 후 종료
        root = tk.Tk()
        root.withdraw()  # 빈 메인 윈도우 숨김
        messagebox.showerror('오류', str(e))
        return

    root = tk.Tk()
    CCTVViewer(root, helper)  # GUI 구성 + 첫 이미지 표시
    root.mainloop()


if __name__ == '__main__':
    main()
