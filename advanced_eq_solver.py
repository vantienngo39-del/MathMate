import sympy


def solve(expression: str) -> dict:
    cleaned = expression.replace("^", "**").strip()
    if "=" in cleaned:
        lhs_s, rhs_s = cleaned.split("=", 1)
        lhs = sympy.sympify(lhs_s)
        rhs = sympy.sympify(rhs_s)
    else:
        lhs = sympy.sympify(cleaned)
        rhs = sympy.Integer(0)

    eq = sympy.Eq(lhs, rhs)
    all_vars = sorted(eq.free_symbols, key=lambda s: s.name)
    if not all_vars:
        raise ValueError("Biểu thức không chứa biến để giải.")

    target_var = sympy.Symbol("x") if sympy.Symbol("x") in all_vars else all_vars[0]
    other_vars = [v for v in all_vars if v != target_var]

    steps: list[str] = [f"Phương trình đã cho: {lhs} = {rhs}"]

    # Tìm điều kiện mẫu khác 0 nếu có phân thức chứa biến
    denoms = []
    for sub in sympy.preorder_traversal(lhs - rhs):
        if sub.is_Pow and sub.exp.is_negative:
            denoms.append(sub.base)
    if denoms:
        conds = [f"{d} ≠ 0" for d in denoms]
        steps.append("Điều kiện xác định (mẫu khác 0): " + ", ".join(conds) + ".")

    if other_vars:
        steps.append(
            f"Coi {target_var} là ẩn chính và {', '.join(str(v) for v in other_vars)} là tham số/biến phụ."
        )

    moved = sympy.simplify(lhs - rhs)
    steps.append(f"Chuyển vế và rút gọn: ({moved}) = 0")

    sols = sympy.solve(sympy.Eq(moved, 0), target_var)
    if not sols:
        steps.append(f"Kết luận: Không tìm được nghiệm theo {target_var}.")
        return {
            "steps": steps,
            "short_answer": "Vô nghiệm",
            "latex_short": "\\text{Vô nghiệm}",
            "latex_full": f"{sympy.latex(eq)} \\Rightarrow \\text{{Vô nghiệm}}",
        }

    formatted = [f"{target_var} = {s}" for s in sols]
    steps.append("Giải theo biến chính thu được: " + ", ".join(formatted) + ".")
    short_ans = ", ".join(formatted)
    latex_short = ", ".join(f"{sympy.latex(target_var)} = {sympy.latex(s)}" for s in sols)
    return {
        "steps": steps,
        "short_answer": short_ans,
        "latex_short": latex_short,
        "latex_full": f"{sympy.latex(eq)} \\Rightarrow {latex_short}",
    }
