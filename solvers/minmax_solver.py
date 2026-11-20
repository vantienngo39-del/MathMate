import sympy


def solve(expression: str) -> dict:
    parts = [p.strip().replace("^", "**") for p in expression.split(",") if p.strip()]
    if not parts:
        raise ValueError("Vui lòng nhập hàm số cần tìm giá trị lớn nhất / nhỏ nhất.")

    x = sympy.Symbol("x")
    f = sympy.sympify(parts[0])
    steps: list[str] = [f"Xét hàm số: f(x) = {f}"]

    has_interval = len(parts) >= 3
    a_val = b_val = None
    if has_interval:
        a_val = sympy.sympify(parts[1])
        b_val = sympy.sympify(parts[2])
        if a_val > b_val:
            a_val, b_val = b_val, a_val
        steps.append(f"Khoảng / đoạn khảo sát: [{a_val}, {b_val}].")
    else:
        steps.append("Khảo sát hàm số trên tập số thực (hoặc miền xác định tự nhiên).")

    df = sympy.diff(f, x)
    steps.append(f"Tính đạo hàm cấp 1: f'(x) = {df}")

    crit_pts = sympy.solve(sympy.Eq(df, 0), x)
    steps.append(f"Giải phương trình f'(x) = 0 ⇒ các điểm nghi ngờ cực trị: {crit_pts if crit_pts else 'Không có'}.")

    candidates: list[tuple[str, sympy.Expr]] = []
    if has_interval and a_val is not None and b_val is not None:
        candidates.append(("biên trái x = " + str(a_val), a_val))
        candidates.append(("biên phải x = " + str(b_val), b_val))
        for pt in crit_pts:
            if pt.is_real and a_val <= pt <= b_val:
                candidates.append((f"điểm tới hạn x = {pt}", pt))
    else:
        for pt in crit_pts:
            if pt.is_real:
                candidates.append((f"điểm tới hạn x = {pt}", pt))

    evaluated: list[tuple[str, sympy.Expr, sympy.Expr]] = []
    for label, pt in candidates:
        val = sympy.simplify(f.subs(x, pt))
        evaluated.append((label, pt, val))
        steps.append(f"Tính f({pt}) tại {label}: f({pt}) = {val}.")

    real_vals = [item[2] for item in evaluated if item[2].is_real]
    min_str = max_str = None

    if real_vals:
        min_val = min(real_vals)
        max_val = max(real_vals)
        min_pts = [str(item[1]) for item in evaluated if item[2] == min_val]
        max_pts = [str(item[1]) for item in evaluated if item[2] == max_val]
        min_str = f"Min = {min_val} (tại x = {', '.join(min_pts)})"
        max_str = f"Max = {max_val} (tại x = {', '.join(max_pts)})"
        steps.append(f"So sánh các giá trị thu được ⇒ {min_str}; {max_str}.")
    else:
        steps.append("Không tìm được giá trị cực trị hữu hạn rõ ràng trên miền xét.")

    summary_parts = [p for p in (min_str, max_str) if p]
    short_ans = " | ".join(summary_parts) if summary_parts else "Không có cực trị hữu hạn"
    latex_short = sympy.latex(f)
    return {
        "steps": steps,
        "short_answer": short_ans,
        "latex_short": latex_short,
        "latex_full": f"f(x) = {latex_short} \\Rightarrow \\text{{{short_ans}}}",
    }
