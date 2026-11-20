import math
import sys
import sympy

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


def _nth_prime(n: int) -> int:
    if n < 1:
        raise ValueError("Chỉ số số nguyên tố phải >= 1.")
    count = 0
    candidate = 1
    while count < n:
        candidate += 1
        if sympy.isprime(candidate):
            count += 1
    return candidate


def _fibonacci_fast(n: int) -> int:
    if n < 0:
        raise ValueError("Chỉ số Fibonacci phải >= 0.")

    def _fib_pair(k: int) -> tuple[int, int]:
        if k == 0:
            return (0, 1)
        a, b = _fib_pair(k >> 1)
        c = a * ((b << 1) - a)
        d = a * a + b * b
        if k & 1:
            return (d, c + d)
        return (c, d)

    return _fib_pair(n)[0]


def solve(expression: str) -> dict:
    parts = expression.strip().split()
    if len(parts) != 2:
        raise ValueError("Cú pháp hợp lệ: fibo <n> | fact <n> | prime <n> | factors <số nguyên>.")

    cmd = parts[0].lower()
    arg = int(parts[1])

    if cmd == "fibo":
        val = _fibonacci_fast(arg)
        val_str = str(val)
        digits = len(val_str.lstrip("-"))
        steps = [
            f"Tính số Fibonacci F({arg}) bằng thuật toán Fast Doubling (O(log n)).",
            f"Kết quả là số nguyên lớn có {digits} chữ số.",
        ]
        return {
            "steps": steps,
            "short_answer": val_str,
            "latex_short": val_str,
            "latex_full": f"F_{{{arg}}} = {val_str}",
        }

    if cmd == "fact":
        if arg < 0:
            raise ValueError("Giai thừa chỉ áp dụng cho số nguyên không âm.")
        val = math.factorial(arg)
        val_str = str(val)
        digits = len(val_str)
        steps = [
            f"Tính giai thừa {arg}! = 1 × 2 × ... × {arg}.",
            f"Giá trị {arg}! có tổng cộng {digits} chữ số.",
        ]
        return {
            "steps": steps,
            "short_answer": val_str,
            "latex_short": val_str,
            "latex_full": f"{arg}! = {val_str}",
        }

    if cmd == "prime":
        val = _nth_prime(arg)
        val_str = str(val)
        steps = [
            f"Tìm số nguyên tố thứ {arg} trong dãy số nguyên tố (2, 3, 5, 7, ...).",
            f"Số nguyên tố thứ {arg} là {val_str}.",
        ]
        return {
            "steps": steps,
            "short_answer": val_str,
            "latex_short": val_str,
            "latex_full": f"p_{{{arg}}} = {val_str}",
        }

    if cmd == "factors":
        if abs(arg) < 2:
            raise ValueError("Cần nhập số nguyên có giá trị tuyệt đối >= 2 để phân tích thừa số nguyên tố.")
        fac_dict = sympy.factorint(abs(arg))
        terms = [f"{p}^{e}" if e > 1 else f"{p}" for p, e in sorted(fac_dict.items())]
        prefix = "-1 × " if arg < 0 else ""
        ans_str = prefix + " × ".join(terms)
        steps = [
            f"Phân tích số {arg} thành tích các thừa số nguyên tố.",
            f"Các thừa số nguyên tố thu được: {ans_str}.",
        ]
        return {
            "steps": steps,
            "short_answer": ans_str,
            "latex_short": ans_str,
            "latex_full": f"{arg} = {ans_str}",
        }

    raise ValueError("Lệnh không hợp lệ. Dùng: fibo, fact, prime hoặc factors.")
