import importlib
import json
import re
import sys
from pathlib import Path

# Cho phép chuyển đổi số nguyên cực lớn sang chuỗi không giới hạn (BigInt)
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from updater import APP_VERSION, apply_update_and_restart, check_for_update
except Exception:
    APP_VERSION = "1.0.0"

    def check_for_update(current_version: str = APP_VERSION):
        return None

    def apply_update_and_restart(zip_url: str) -> None:
        raise RuntimeError("Thiếu module updater.py")


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_runtime_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_icon_path() -> Path | None:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "icon.ico")
        candidates.append(Path(sys.executable).resolve().parent / "icon.ico")
    candidates.append(get_base_dir() / "icon.ico")
    candidates.append(Path(__file__).resolve().parent / "icon.ico")

    for p in candidates:
        if p.exists():
            return p
    return None


TABS = [
    ("equation", "Phương trình"),
    ("factor", "Phân tích nhân tử"),
    ("system", "Hệ phương trình"),
    ("extremum", "Giá trị lớn nhất / nhỏ nhất"),
    ("calculus", "Đạo hàm & Tích phân"),
    ("bigint", "Số lớn (BigInt)"),
]

PLACEHOLDERS = {
    "equation": "VD: x^2 - 5*x + 6 = 0 hoặc 2*x + 4 = 10",
    "factor": "VD: x^3 - 1 hoặc x^2 + 5*x + 6",
    "system": "VD: x + y = 5; 2*x - y = 1",
    "extremum": "VD: min x^2 + 4*x + 7 trên [-5, 5]",
    "calculus": "VD: diff sin(x)*x^2 hoặc integrate x^2 from 0 to 3",
    "bigint": "VD: fact 5000 hoặc fibo 20000 hoặc 2^10000",
}

QUICK_SNIPPETS = [
    ("+", " + "),
    ("-", " - "),
    ("*", " * "),
    ("/", " / "),
    ("^", "^"),
    ("=", " = "),
    ("(", "("),
    (")", ")"),
    ("fact", "fact "),
    ("fibo", "fibo "),
    ("diff", "diff "),
    ("integrate", "integrate "),
    ("min", "min "),
]


def format_pretty_math(text: str) -> str:
    if not text:
        return ""
    s = str(text)
    s = s.replace("**", "^")
    return s


def format_readable_latex(latex_str: str) -> str:
    if not latex_str:
        return ""
    s = str(latex_str).strip()
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\cdot", "·").replace("\\times", "×")
    return s


def wrap_for_display(text: str, max_run: int = 80) -> str:
    """Chèn xuống dòng mềm cho các chuỗi không có khoảng trắng quá dài để tránh tràn ngang."""
    if not text:
        return ""
    parts = text.split("\n")
    wrapped_lines: list[str] = []
    pattern = re.compile(rf"(\S{{{max_run}}})")
    for line in parts:
        if len(line) > max_run:
            line = pattern.sub(r"\1\n", line)
        wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


def route_request(tab_key: str, expr: str, mode: str = "detail") -> dict:
    """
    Điều hướng bài toán tới router.py nếu có, hoặc tự dò module trong thư mục solvers/.
    """
    # 1. Thử dùng router.py nếu tồn tại
    try:
        router_mod = importlib.import_module("router")
        for fn_name in ("route_request", "solve", "dispatch"):
            fn = getattr(router_mod, fn_name, None)
            if callable(fn):
                res = fn(tab_key, expr, mode)
                if isinstance(res, dict):
                    return res
                return {
                    "status": "ok",
                    "short_answer": str(res),
                    "steps": [],
                    "key_points": [],
                    "latex": expr,
                }
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        return {"status": "error", "message": f"Lỗi bộ điều hướng: {exc}"}

    # 2. Thử gọi trực tiếp module trong solvers/<tab_key>.py
    module_candidates = [
        f"solvers.{tab_key}",
        f"solvers.{tab_key}_solver",
        f"solvers.solve_{tab_key}",
    ]
    for mod_name in module_candidates:
        try:
            mod = importlib.import_module(mod_name)
            for fn_name in ("solve", "solve_problem", "run", "calculate"):
                fn = getattr(mod, fn_name, None)
                if callable(fn):
                    try:
                        out = fn(expr, mode=mode)
                    except TypeError:
                        out = fn(expr)
                    if isinstance(out, dict):
                        return out
                    return {
                        "status": "ok",
                        "short_answer": str(out),
                        "steps": [str(out)],
                        "key_points": [],
                        "latex": expr,
                    }
        except ModuleNotFoundError:
            continue
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # 3. Fallback tính toán cơ bản với SymPy / math nếu chưa có solver riêng
    try:
        import math
        import sympy as sp

        clean = expr.strip()
        lower = clean.lower()

        if lower.startswith("fact "):
            n = int(clean.split(maxsplit=1)[1].strip())
            if n < 0:
                return {"status": "error", "message": "Giai thừa chỉ áp dụng cho số nguyên >= 0."}
            val = math.factorial(n)
            s_val = str(val)
            return {
                "status": "ok",
                "short_answer": s_val,
                "steps": [
                    f"Tính {n}! bằng thuật toán giai thừa tối ưu của Python.",
                    f"Kết quả gồm {len(s_val)} chữ số.",
                ],
                "key_points": [f"Số chữ số: {len(s_val)}"],
                "latex": f"{n}!",
            }

        if lower.startswith("fibo "):
            n = int(clean.split(maxsplit=1)[1].strip())
            if n < 0:
                return {"status": "error", "message": "Chỉ số Fibonacci phải >= 0."}
            a, b = 0, 1
            for _ in range(n):
                a, b = b, a + b
            s_val = str(a)
            return {
                "status": "ok",
                "short_answer": s_val,
                "steps": [
                    f"Tính số Fibonacci thứ F({n}) với F(0) = 0, F(1) = 1.",
                    f"Kết quả gồm {len(s_val)} chữ số.",
                ],
                "key_points": [f"Chỉ số: F({n})", f"Số chữ số: {len(s_val)}"],
                "latex": f"F_{{{n}}}",
            }

        x = sp.Symbol("x")
        parsed = sp.sympify(clean.replace("^", "**"))
        ans_str = str(parsed)
        return {
            "status": "ok",
            "short_answer": ans_str,
            "steps": [f"Biểu thức đầu vào: {clean}", f"Rút gọn / tính giá trị: {ans_str}"],
            "key_points": [],
            "latex": sp.latex(parsed),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc) or "Không thể xử lý biểu thức."}


STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

QFrame#HeaderBar {
    background-color: #111827;
    border-bottom: 1px solid #1e293b;
}

QLabel#AppTitle {
    color: #38bdf8;
    font-size: 18px;
    font-weight: 700;
}

QLabel#AppSubtitle {
    color: #94a3b8;
    font-size: 12px;
}

QListWidget#TabList {
    background-color: #111827;
    border: none;
    border-right: 1px solid #1e293b;
    padding: 8px;
    outline: none;
}

QListWidget#TabList::item {
    padding: 11px 14px;
    margin-bottom: 4px;
    border-radius: 8px;
    color: #cbd5e1;
}

QListWidget#TabList::item:selected {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
}

QListWidget#TabList::item:hover:!selected {
    background-color: #1e293b;
}

QPushButton.ModeBtn {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton.ModeBtn:checked {
    background-color: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
}

QFrame#InputBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
}

QLineEdit.MathInput {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
}

QLineEdit.MathInput:focus {
    border-color: #38bdf8;
}

QPushButton.SendBtn {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 700;
}

QPushButton.SendBtn:hover {
    background-color: #0ea5e9;
}

QPushButton.SnippetBtn {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton.SnippetBtn:hover {
    background-color: #334155;
    border-color: #38bdf8;
}

QFrame.UserBubble {
    background-color: #1d4ed8;
    border-radius: 12px;
    padding: 12px 14px;
}

QFrame.BotBubble, QFrame.QuickCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px;
}

QTextEdit.BubbleScrollBox {
    background-color: #0f172a;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
"""


class UpdateCheckThread(QThread):
    update_found = pyqtSignal(dict)

    def run(self) -> None:
        info = check_for_update(APP_VERSION)
        if isinstance(info, dict) and info.get("zip_url"):
            self.update_found.emit(info)


class DetailedWorkspace(QWidget):
    def __init__(self, tab_key: str, placeholder: str):
        super().__init__()
        self.tab_key = tab_key
        self.placeholder = placeholder
        self.history_file = get_runtime_data_dir() / f"history_{self.tab_key}.json"
        self._build_ui()
        self._load_history()

    def _build_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.Widget)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        info_lbl = QLabel("Chế độ giải chi tiết (từng bước & lưu lịch sử)")
        info_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")

        clear_btn = QPushButton("Xóa lịch sử", self)
        clear_btn.setProperty("class", "SnippetBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_history)

        top_bar.addWidget(info_lbl)
        top_bar.addStretch()
        top_bar.addWidget(clear_btn)
        layout.addLayout(top_bar)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget(self.scroll_area)
        self.chat_container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 6, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area, stretch=1)

        input_frame = QFrame(self)
        input_frame.setObjectName("InputBar")
        in_layout = QHBoxLayout(input_frame)
        in_layout.setContentsMargins(12, 10, 12, 10)
        in_layout.setSpacing(10)

        self.input_edit = QLineEdit(input_frame)
        self.input_edit.setProperty("class", "MathInput")
        self.input_edit.setPlaceholderText(self.placeholder)
        self.input_edit.returnPressed.connect(self.solve_detailed)

        self.send_btn = QPushButton("Giải chi tiết", input_frame)
        self.send_btn.setProperty("class", "SendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.solve_detailed)

        in_layout.addWidget(self.input_edit, stretch=1)
        in_layout.addWidget(self.send_btn)
        layout.addWidget(input_frame)

    def _add_user_bubble(self, expr: str) -> None:
        bubble = QFrame(self.chat_container)
        bubble.setProperty("class", "UserBubble")
        bubble.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(4, 2, 4, 2)

        lbl = QLabel(wrap_for_display(f"Bài toán: {expr}"), bubble)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        lbl.setStyleSheet("color: #ffffff; font-weight: 600;")
        b_layout.addWidget(lbl)

        # Chèn trước stretch cuối cùng
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def _add_bot_bubble(self, res: dict) -> None:
        bubble = QFrame(self.chat_container)
        bubble.setProperty("class", "BotBubble")
        bubble.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
        b_layout = QVBoxLayout(bubble)
        b_layout.setSpacing(8)

        if res.get("status") == "error":
            err_lbl = QLabel(wrap_for_display(f"Lỗi: {res.get('message', '')}"), bubble)
            err_lbl.setWordWrap(True)
            err_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            err_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            err_lbl.setStyleSheet("color: #f87171; font-weight: 700;")
            b_layout.addWidget(err_lbl)
        else:
            ans_pretty = format_pretty_math(res.get("short_answer", ""))
            if len(ans_pretty) > 400:
                ans_hdr = QLabel("Kết quả (số dài — cuộn trong khung bên dưới):", bubble)
                ans_hdr.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 15px;")
                b_layout.addWidget(ans_hdr)

                ans_box = QTextEdit(bubble)
                ans_box.setReadOnly(True)
                ans_box.setProperty("class", "BubbleScrollBox")
                ans_box.setMinimumHeight(120)
                ans_box.setMaximumHeight(200)
                ans_box.setPlainText(wrap_for_display(ans_pretty))
                b_layout.addWidget(ans_box)
            else:
                ans_lbl = QLabel(wrap_for_display(f"Đáp án: {ans_pretty}"), bubble)
                ans_lbl.setWordWrap(True)
                ans_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                ans_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                ans_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 15px;")
                b_layout.addWidget(ans_lbl)

            steps = [format_pretty_math(str(s)) for s in res.get("steps", []) if str(s).strip()]
            if steps:
                steps_text = "\n".join(f"{i + 1}. {st}" for i, st in enumerate(steps))
                if len(steps_text) > 500 or len(steps) > 5:
                    steps_box = QTextEdit(bubble)
                    steps_box.setReadOnly(True)
                    steps_box.setProperty("class", "BubbleScrollBox")
                    steps_box.setMinimumHeight(130)
                    steps_box.setMaximumHeight(240)
                    steps_box.setPlainText(wrap_for_display(steps_text))
                    b_layout.addWidget(steps_box)
                else:
                    steps_lbl = QLabel(wrap_for_display(steps_text), bubble)
                    steps_lbl.setWordWrap(True)
                    steps_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    steps_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                    steps_lbl.setStyleSheet("color: #e2e8f0;")
                    b_layout.addWidget(steps_lbl)

            latex_clean = format_readable_latex(res.get("latex", ""))
            if latex_clean:
                lx_lbl = QLabel(wrap_for_display(f"Biểu thức: {latex_clean}"), bubble)
                lx_lbl.setWordWrap(True)
                lx_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lx_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                lx_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
                b_layout.addWidget(lx_lbl)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def _scroll_to_bottom(self) -> None:
        QApplication.processEvents()
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def solve_detailed(self) -> None:
        expr = self.input_edit.text().strip()
        if not expr:
            return
        self.input_edit.clear()

        res = route_request(self.tab_key, expr, mode="detail")
        self._add_user_bubble(expr)
        self._add_bot_bubble(res)
        self._save_entry(expr, res)
        self._scroll_to_bottom()

    def _save_entry(self, expr: str, res: dict) -> None:
        items: list[dict] = []
        if self.history_file.exists():
            try:
                items = json.loads(self.history_file.read_text(encoding="utf-8"))
                if not isinstance(items, list):
                    items = []
            except Exception:
                items = []
        items.append({"expr": expr, "res": res})
        items = items[-50:]
        try:
            self.history_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_history(self) -> None:
        if not self.history_file.exists():
            return
        try:
            items = json.loads(self.history_file.read_text(encoding="utf-8"))
            if not isinstance(items, list):
                return
            for entry in items:
                expr = str(entry.get("expr", ""))
                res = entry.get("res", {})
                if expr and isinstance(res, dict):
                    self._add_user_bubble(expr)
                    self._add_bot_bubble(res)
        except Exception:
            pass

    def clear_history(self) -> None:
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        if self.history_file.exists():
            try:
                self.history_file.unlink()
            except Exception:
                pass


class QuickWorkspace(QWidget):
    def __init__(self, tab_key: str, placeholder: str):
        super().__init__()
        self.tab_key = tab_key
        self.placeholder = placeholder
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.Widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        input_frame = QFrame(self)
        input_frame.setObjectName("InputBar")
        in_layout = QHBoxLayout(input_frame)
        in_layout.setContentsMargins(12, 10, 12, 10)
        in_layout.setSpacing(10)

        self.input_edit = QLineEdit(input_frame)
        self.input_edit.setProperty("class", "MathInput")
        self.input_edit.setPlaceholderText(self.placeholder)
        self.input_edit.returnPressed.connect(self.solve_quick)

        self.send_btn = QPushButton("Giải nhanh", input_frame)
        self.send_btn.setProperty("class", "SendBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.solve_quick)

        in_layout.addWidget(self.input_edit, stretch=1)
        in_layout.addWidget(self.send_btn)
        layout.addWidget(input_frame)

        keypad = QGridLayout()
        keypad.setSpacing(6)
        cols = 7
        for idx, (label, snippet) in enumerate(QUICK_SNIPPETS):
            btn = QPushButton(label, self)
            btn.setProperty("class", "SnippetBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, s=snippet: self._insert_snippet(s))
            keypad.addWidget(btn, idx // cols, idx % cols)

        clr_btn = QPushButton("Xóa ô", self)
        clr_btn.setProperty("class", "SnippetBtn")
        clr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clr_btn.clicked.connect(self.input_edit.clear)
        keypad.addWidget(clr_btn, len(QUICK_SNIPPETS) // cols, len(QUICK_SNIPPETS) % cols)

        layout.addLayout(keypad)

        self.result_card = QFrame(self)
        self.result_card.setProperty("class", "QuickCard")
        self.result_card.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Maximum)
        self.result_card.setVisible(False)
        self.res_layout = QVBoxLayout(self.result_card)
        self.res_layout.setSpacing(8)

        self.ans_label = QLabel(self.result_card)
        self.ans_label.setWordWrap(True)
        self.ans_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.ans_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.ans_label.setStyleSheet(
            'color: #38bdf8; font-family: "Segoe UI", Arial, sans-serif; font-size: 16px; font-weight: 700;'
        )

        self.long_ans_box = QTextEdit(self.result_card)
        self.long_ans_box.setReadOnly(True)
        self.long_ans_box.setProperty("class", "BubbleScrollBox")
        self.long_ans_box.setMinimumHeight(130)
        self.long_ans_box.setMaximumHeight(220)
        self.long_ans_box.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.long_ans_box.setVisible(False)

        self.summary_label = QLabel(self.result_card)
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.summary_label.setStyleSheet('color: #e2e8f0; font-family: "Segoe UI", Arial, sans-serif;')

        self.latex_label = QLabel(self.result_card)
        self.latex_label.setWordWrap(True)
        self.latex_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.latex_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.latex_label.setStyleSheet(
            'color: #94a3b8; font-family: "Segoe UI", Arial, sans-serif; font-size: 12px;'
        )

        self.res_layout.addWidget(self.ans_label)
        self.res_layout.addWidget(self.long_ans_box)
        self.res_layout.addWidget(self.summary_label)
        self.res_layout.addWidget(self.latex_label)
        layout.addWidget(self.result_card)

        layout.addStretch()

    def _insert_snippet(self, snippet: str) -> None:
        self.input_edit.insert(snippet)
        self.input_edit.setFocus()

    def solve_quick(self) -> None:
        expr = self.input_edit.text().strip()
        if not expr:
            return

        res = route_request(self.tab_key, expr, mode="quick")
        self.result_card.setVisible(True)

        if res.get("status") == "error":
            self.long_ans_box.setVisible(False)
            self.ans_label.setVisible(True)
            self.ans_label.setText(wrap_for_display(f"Lỗi: {res.get('message', '')}"))
            self.ans_label.setStyleSheet(
                'color: #f87171; font-family: "Segoe UI", Arial, sans-serif; font-size: 15px; font-weight: 700;'
            )
            self.summary_label.setText("")
            self.latex_label.setText("")
            return

        ans_pretty = format_pretty_math(res.get("short_answer", ""))
        self.ans_label.setStyleSheet(
            'color: #38bdf8; font-family: "Segoe UI", Arial, sans-serif; font-size: 16px; font-weight: 700;'
        )

        if len(ans_pretty) > 400:
            self.ans_label.setText("Kết quả (số dài — cuộn trong khung bên dưới):")
            self.long_ans_box.setVisible(True)
            self.long_ans_box.setPlainText(wrap_for_display(ans_pretty))
        else:
            self.long_ans_box.setVisible(False)
            self.ans_label.setText(wrap_for_display(f"Kết quả: {ans_pretty}"))

        points = [format_pretty_math(str(p)) for p in res.get("key_points", [])]
        self.summary_label.setText(wrap_for_display("Tóm tắt: " + " | ".join(points) if points else ""))

        latex_clean = format_readable_latex(res.get("latex", ""))
        self.latex_label.setText(
            wrap_for_display(f"Biểu thức: {latex_clean}  •  (Không lưu lịch sử)")
        )


class MathMateWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"MathMate v{APP_VERSION}")
        self.resize(1040, 680)
        self.setMinimumSize(780, 520)

        self._update_thread: UpdateCheckThread | None = None
        self.detailed_widgets: dict[str, DetailedWorkspace] = {}
        self.quick_widgets: dict[str, QuickWorkspace] = {}

        self._build_ui()
        self._start_update_check()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame(root)
        header.setObjectName("HeaderBar")
        header.setFixedHeight(62)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 8, 20, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_lbl = QLabel(f"MathMate  ·  v{APP_VERSION}", header)
        title_lbl.setObjectName("AppTitle")
        sub_lbl = QLabel("Trợ lý giải toán & tính toán số nguyên lớn", header)
        sub_lbl.setObjectName("AppSubtitle")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        self.btn_detail = QPushButton("Giải chi tiết", header)
        self.btn_detail.setCheckable(True)
        self.btn_detail.setChecked(True)
        self.btn_detail.setProperty("class", "ModeBtn")
        self.btn_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detail.clicked.connect(lambda: self._switch_mode("detail"))

        self.btn_quick = QPushButton("Giải nhanh", header)
        self.btn_quick.setCheckable(True)
        self.btn_quick.setProperty("class", "ModeBtn")
        self.btn_quick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick.clicked.connect(lambda: self._switch_mode("quick"))

        h_layout.addLayout(title_box)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_detail)
        h_layout.addWidget(self.btn_quick)
        main_layout.addWidget(header)

        # Splitter trái (danh mục) - phải (không gian làm việc)
        splitter = QSplitter(Qt.Orientation.Horizontal, root)

        self.tab_list = QListWidget(splitter)
        self.tab_list.setObjectName("TabList")
        self.tab_list.setFixedWidth(230)
        for _key, title in TABS:
            QListWidgetItem(title, self.tab_list)
        self.tab_list.setCurrentRow(0)
        self.tab_list.currentRowChanged.connect(self._on_tab_changed)

        self.mode_stack = QStackedWidget(splitter)
        self.detail_stack = QStackedWidget(self.mode_stack)
        self.quick_stack = QStackedWidget(self.mode_stack)

        for key, _title in TABS:
            ph = PLACEHOLDERS.get(key, "Nhập biểu thức toán học...")
            d_page = DetailedWorkspace(key, ph)
            q_page = QuickWorkspace(key, ph)
            self.detailed_widgets[key] = d_page
            self.quick_widgets[key] = q_page
            self.detail_stack.addWidget(d_page)
            self.quick_stack.addWidget(q_page)

        self.mode_stack.addWidget(self.detail_stack)  # index 0: detail
        self.mode_stack.addWidget(self.quick_stack)   # index 1: quick

        splitter.addWidget(self.tab_list)
        splitter.addWidget(self.mode_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, stretch=1)

    def _on_tab_changed(self, row: int) -> None:
        if row < 0:
            return
        self.detail_stack.setCurrentIndex(row)
        self.quick_stack.setCurrentIndex(row)

    def _switch_mode(self, mode: str) -> None:
        is_detail = mode == "detail"
        self.btn_detail.setChecked(is_detail)
        self.btn_quick.setChecked(not is_detail)
        self.mode_stack.setCurrentIndex(0 if is_detail else 1)

    def _start_update_check(self) -> None:
        self._update_thread = UpdateCheckThread(self)
        self._update_thread.update_found.connect(self._prompt_update)
        self._update_thread.start()

    def _prompt_update(self, info: dict) -> None:
        version = str(info.get("version", "mới"))
        zip_url = str(info.get("zip_url", ""))
        if not zip_url:
            return

        msg = (
            f"Đã có phiên bản MathMate {version} "
            f"(phiên bản hiện tại: {APP_VERSION}).\n\n"
            "Bạn có muốn tải và cập nhật ngay bây giờ không?"
        )
        reply = QMessageBox.question(
            self,
            "Cập nhật MathMate",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                apply_update_and_restart(zip_url)
                self.close()
            except Exception as exc:
                QMessageBox.warning(self, "Lỗi cập nhật", f"Không thể cập nhật:\n{exc}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLESHEET)

    icon_path = get_icon_path()
    if icon_path is not None:
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    window = MathMateWindow()
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
