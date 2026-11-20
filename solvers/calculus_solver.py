import sympy


def solve(expression: str) -> dict:
    cleaned = expression.replace("^", "**").strip()
    lower = cleaned.lower()

    if lower.startswith("diff "):
        body = cleaned[5:].strip()
        parts = [p.strip() for p in body.rsplit(",", 1)]
        expr = sympy.sympify(parts[0])
        var = sympy.Symbol(parts[1]) if len(parts) == 2 and parts[1] else sympy.Symbol("x")

        steps = [
            f"Biểu thức cần tính đạo hàm: f({var}) = {expr}",
            f"Áp dụng quy tắc đạo hàm theo biến {var}: d/d{var} [{expr}]",
        ]
        deriv = sympy.simplify(sympy.diff(expr, var))
        steps.append(f"Kết quả đạo hàm: {deriv}")

        return {
            "steps": steps,
            "short_answer": str(deriv),
            "latex_short": sympy.latex(deriv),
            "latex_full": f"\\frac{{d}}{{d{sympy.latex(var)}}}\\left({sympy.latex(expr)}\\right) = {sympy.latex(deriv)}",
        }

    if lower.startswith("int "):
        body = cleaned[4:].strip()
        parts = [p.strip() for p in body.split(",")]
        expr = sympy.sympify(parts[0])
        var = sympy.Symbol(parts[1]) if len(parts) >= 2 and parts[1] else sympy.Symbol("x")

        # Tích phân xác định: int expr, var, a, b
        if len(parts) >= 4:
            a = sympy.sympify(parts[2])
            b = sympy.sympify(parts[3])
            antideriv = sympy.integrate(expr, var)
            val_b = sympy.simplify(antideriv.subs(var, b))
            val_a = sympy.simplify(antideriv.subs(var, a))
            ans = sympy.simplify(val_b - val_a)

            steps = [
                f"Tính tích phân xác định của f({var}) = {expr} trên đoạn [{a}, {b}].",
                f"Bước 1 — Tìm một nguyên hàm: F({var}) = {antideriv}.",
                f"Bước 2 — Tính giá trị tại cận trên b = {b}: F({b}) = {val_b}.",
                f"Bước 3 — Tính giá trị tại cận dưới a = {a}: F({a}) = {val_a}.",
                f"Bước 4 — Áp dụng công thức F(b) - F(a) = ({val_b}) - ({val_a}) = {ans}.",
            ]
            return {
                "steps": steps,
                "short_answer": str(ans),
                "latex_short": sympy.latex(ans),
                "latex_full": f"\\int_{{{sympy.latex(a)}}}^{{{sympy.latex(b)}}} \\left({sympy.latex(expr)}\\right) d{sympy.latex(var)} = {sympy.latex(ans)}",
            }

        # Tích phân bất định: int expr, var
        antideriv = sympy.integrate(expr, var)
        steps = [
            f"Tính nguyên hàm / tích phân bất định của {expr} theo biến {var}.",
            f"Nguyên hàm tìm được: F({var}) = {antideriv}.",
            f"Kết luận: ∫ ({expr}) d{var} = {antideriv} + C.",
        ]
        short_ans = f"{antideriv} + C"
        return {
            "steps": steps,
            "short_answer": short_ans,
            "latex_short": f"{sympy.latex(antideriv)} + C",
            "latex_full": f"\\int \\left({sympy.latex(expr)}\\right) d{sympy.latex(var)} = {sympy.latex(antideriv)} + C",
        }

    raise ValueError("Cú pháp hợp lệ: 'diff <biểu thức>, <biến>' hoặc 'int <biểu thức>, <biến>[, a, b]'.")
