import math
import sympy


def solve(expression: str) -> dict:
    parts = [p.strip().replace("^", "**") for p in expression.split(",") if p.strip()]
    if len(parts) < 2:
        raise ValueError("Cần nhập ít nhất 2 số hoặc 2 biểu thức cách nhau bởi dấu phẩy (,).")

    steps: list[str] = [f"Danh sách đầu vào gồm {len(parts)} phần tử: {', '.join(parts)}."]

    # Thử nhánh số nguyên trước
    try:
        nums = [int(sympy.sympify(p)) for p in parts]
        abs_nums = [abs(n) for n in nums]
        steps.append("Nhận diện bài toán tìm ƯCLN (GCD) và BCNN (LCM) của dãy số nguyên.")

        for n in abs_nums:
            factors = sympy.factorint(n)
            f_str = " · ".join(f"{k}^{v}" if v > 1 else f"{k}" for k, v in factors.items()) if factors else str(n)
            steps.append(f"Phân tích {n} ra thừa số nguyên tố: {f_str}.")

        cur_gcd = abs_nums[0]
        cur_lcm = abs_nums[0]
        for nxt in abs_nums[1:]:
            prev_gcd = cur_gcd
            cur_gcd = math.gcd(cur_gcd, nxt)
            cur_lcm = math.lcm(cur_lcm, nxt) if hasattr(math, "lcm") else (cur_lcm * nxt // math.gcd(cur_lcm, nxt))
            steps.append(f"Cập nhật với {nxt}: GCD({prev_gcd}, {nxt}) = {cur_gcd}, LCM = {cur_lcm}.")

        short_ans = f"GCD = {cur_gcd} | LCM = {cur_lcm}"
        latex_short = f"\\gcd = {cur_gcd},\\; \\operatorname{{lcm}} = {cur_lcm}"
        latex_full = f"\\gcd({', '.join(map(str, abs_nums))}) = {cur_gcd},\\quad \\operatorname{{lcm}} = {cur_lcm}"
        return {
            "steps": steps,
            "short_answer": short_ans,
            "latex_short": latex_short,
            "latex_full": latex_full,
        }
    except Exception:
        pass

    # Nhánh đa thức / biểu thức đại số
    polys = [sympy.sympify(p) for p in parts]
    steps.append("Nhận diện bài toán tìm GCD và LCM của các biểu thức/đa thức.")
    g = sympy.gcd(polys[0], polys[1])
    l = sympy.lcm(polys[0], polys[1])
    for p in polys[2:]:
        g = sympy.gcd(g, p)
        l = sympy.lcm(l, p)

    steps.append(f"Ước chung lớn nhất (GCD): {g}")
    steps.append(f"Bội chung nhỏ nhất (LCM): {l}")

    short_ans = f"GCD = {g} | LCM = {l}"
    latex_short = f"\\gcd = {sympy.latex(g)},\\; \\operatorname{{lcm}} = {sympy.latex(l)}"
    latex_full = f"\\gcd = {sympy.latex(g)},\\quad \\operatorname{{lcm}} = {sympy.latex(l)}"
    return {
        "steps": steps,
        "short_answer": short_ans,
        "latex_short": latex_short,
        "latex_full": latex_full,
    }
