import sympy


def solve(expression: str) -> dict:
    x = sympy.Symbol("x")
    cleaned = expression.replace("^", "**").strip()
    if "=" in cleaned:
        lhs_str, rhs_str = cleaned.split("=", 1)
        lhs = sympy.sympify(lhs_str)
        rhs = sympy.sympify(rhs_str)
    else:
        lhs = sympy.sympify(cleaned)
        rhs = sympy.Integer(0)

    eq = sympy.Eq(lhs, rhs)
    expr = sympy.expand(lhs - rhs)
    steps: list[str] = [
        f"Chuyển vế và thu gọn phương trình về dạng: ({expr}) = 0"
    ]

    poly = sympy.Poly(expr, x) if expr.is_polynomial(x) else None
    sols = sympy.solve(sympy.Eq(expr, 0), x)

    if poly is not None:
        deg = poly.degree()
        steps.append(f"Xác định đây là đa thức bậc {deg} theo biến x.")

        if deg == 1:
            a = poly.coeff_monomial(x)
            b = poly.coeff_monomial(sympy.Integer(1))
            steps.append(f"Phương trình có dạng a·x + b = 0 với a = {a}, b = {b}.")
            if a != 0:
                steps.append(f"Chuyển vế: {a}·x = {-b} ⇒ x = ({-b})/({a}) = {sympy.simplify(-b / a)}.")

        elif deg == 2:
            a = poly.coeff_monomial(x**2)
            b = poly.coeff_monomial(x)
            c = poly.coeff_monomial(sympy.Integer(1))
            delta = sympy.simplify(b**2 - 4 * a * c)
            steps.append(f"Hệ số: a = {a}, b = {b}, c = {c}.")
            steps.append(f"Tính biệt thức Δ = b² - 4ac = ({b})² - 4·({a})·({c}) = {delta}.")
            if delta.is_real:
                if delta > 0:
                    steps.append("Vì Δ > 0 nên phương trình có 2 nghiệm phân biệt: x₁,₂ = (-b ± √Δ) / (2a).")
                elif delta == 0:
                    steps.append("Vì Δ = 0 nên phương trình có nghiệm kép: x = -b / (2a).")
                else:
                    steps.append("Vì Δ < 0 nên phương trình không có nghiệm thực (xét nghiệm phức nếu cần).")

        elif deg == 4 and set(poly.as_dict().keys()) <= {(4,), (2,), (0,)}:
            t = sympy.Symbol("t")
            a = poly.coeff_monomial(x**4)
            b = poly.coeff_monomial(x**2)
            c = poly.coeff_monomial(sympy.Integer(1))
            t_eq_expr = a * t**2 + b * t + c
            t_sols = sympy.solve(sympy.Eq(t_eq_expr, 0), t)
            steps.append(f"Nhận thấy đây là phương trình trùng phương: đặt t = x² (t ≥ 0 nếu tìm nghiệm thực).")
            steps.append(f"Phương trình theo t là: {t_eq_expr} = 0 ⇒ tìm được t ∈ {t_sols}.")
            for t_val in t_sols:
                x_from_t = sympy.solve(sympy.Eq(x**2, t_val), x)
                steps.append(f"Với t = {t_val} ⇒ x² = {t_val} ⇒ x ∈ {x_from_t}.")

        else:
            factored = sympy.factor(expr)
            if factored != expr:
                steps.append(f"Phân tích vế trái thành nhân tử: ({factored}) = 0.")
                steps.append("Cho từng nhân tử bằng 0 để tìm các giá trị của x.")

    if not sols:
        steps.append("Kết luận: Phương trình vô nghiệm.")
        short_ans = "Vô nghiệm"
        latex_short = "\\text{Vô nghiệm}"
    else:
        formatted_sols = [f"x = {s}" for s in sols]
        steps.append("Tập nghiệm tìm được: " + ", ".join(formatted_sols) + ".")
        short_ans = ", ".join(formatted_sols)
        latex_short = ", ".join(f"x = {sympy.latex(s)}" for s in sols)

    return {
        "steps": steps,
        "short_answer": short_ans,
        "latex_short": latex_short,
        "latex_full": f"{sympy.latex(eq)} \\Rightarrow {latex_short}",
    }
