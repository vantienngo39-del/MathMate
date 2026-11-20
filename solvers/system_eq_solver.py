import sympy


def solve(expression: str) -> dict:
    raw_eqs = [item.strip().replace("^", "**") for item in expression.split(";") if item.strip()]
    if not raw_eqs:
        raise ValueError("Vui lòng nhập các phương trình cách nhau bởi dấu chấm phẩy (;).")

    equations: list[sympy.Eq] = []
    symbols_set: set[sympy.Symbol] = set()
    steps: list[str] = [f"Hệ gồm {len(raw_eqs)} phương trình:"]

    for idx, raw in enumerate(raw_eqs, start=1):
        if "=" in raw:
            lhs_s, rhs_s = raw.split("=", 1)
            eq = sympy.Eq(sympy.sympify(lhs_s), sympy.sympify(rhs_s))
        else:
            eq = sympy.Eq(sympy.sympify(raw), 0)
        equations.append(eq)
        symbols_set |= eq.free_symbols
        steps.append(f"  ({idx}) {eq.lhs} = {eq.rhs}")

    vars_list = sorted(symbols_set, key=lambda s: s.name)
    if not vars_list:
        raise ValueError("Không tìm thấy biến số nào trong hệ phương trình.")

    steps.append("Các ẩn số cần tìm: " + ", ".join(str(v) for v in vars_list) + ".")
    sol = sympy.solve(equations, vars_list, dict=True)

    if not sol:
        steps.append("Kết luận: Hệ phương trình vô nghiệm.")
        return {
            "steps": steps,
            "short_answer": "Vô nghiệm",
            "latex_short": "\\text{Vô nghiệm}",
            "latex_full": "\\text{Hệ vô nghiệm}",
        }

    formatted_groups: list[str] = []
    latex_groups: list[str] = []
    for item in sol:
        pairs = [f"{v} = {item[v]}" for v in vars_list if v in item]
        l_pairs = [f"{sympy.latex(v)} = {sympy.latex(item[v])}" for v in vars_list if v in item]
        steps.append("Nghiệm tìm được: " + ", ".join(pairs) + ".")
        formatted_groups.append(", ".join(pairs))
        latex_groups.append(", ".join(l_pairs))

    short_ans = " ; ".join(formatted_groups)
    latex_short = " ; ".join(latex_groups)
    return {
        "steps": steps,
        "short_answer": short_ans,
        "latex_short": latex_short,
        "latex_full": latex_short,
    }
