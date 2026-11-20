import sympy


def solve(expression: str) -> dict:
    x = sympy.Symbol("x")
    cleaned = expression.replace("^", "**").strip()
    expr = sympy.sympify(cleaned)

    steps: list[str] = [f"Biểu thức ban đầu: {expr}"]
    expanded = sympy.expand(expr)
    if expanded != expr:
        steps.append(f"Khai triển / thu gọn biểu thức về dạng chuẩn: {expanded}")

    factored = sympy.factor(expanded)
    if factored == expanded:
        steps.append("Biểu thức không thể phân tích thêm thành nhân tử trên trường số hiện tại.")
    else:
        if expanded.is_polynomial(x):
            deg = sympy.Poly(expanded, x).degree()
            if deg == 2:
                steps.append("Xét đa thức bậc 2 theo x: tìm nghiệm hoặc dùng hằng đẳng thức để tách nhân tử.")
            elif deg == 3:
                steps.append("Xét đa thức bậc 3 theo x: nhẩm nghiệm / nhóm hạng tử hoặc áp dụng hằng đẳng thức lập phương.")
            elif deg == 4:
                steps.append("Xét đa thức bậc 4 theo x: tách tích các đa thức bậc nhỏ hơn.")
        steps.append(f"Phân tích thành nhân tử thu được: {factored}")

    return {
        "steps": steps,
        "short_answer": str(factored),
        "latex_short": sympy.latex(factored),
        "latex_full": f"{sympy.latex(expr)} = {sympy.latex(factored)}",
    }
