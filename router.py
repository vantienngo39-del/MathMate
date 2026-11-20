from solvers import (
    factor_solver,
    lcm_gcd_solver,
    equation_solver,
    system_eq_solver,
    advanced_eq_solver,
    minmax_solver,
    calculus_solver,
    bigint_solver,
)

TAB_SOLVER_MAP = {
    "FACTOR": factor_solver,
    "LCM_GCD": lcm_gcd_solver,
    "EQUATION": equation_solver,
    "SYSTEM_EQ": system_eq_solver,
    "ADVANCED_EQ": advanced_eq_solver,
    "MIN_MAX": minmax_solver,
    "CALCULUS": calculus_solver,
    "BIG_INT": bigint_solver,
}


def route_request(tab_key: str, expression: str, mode: str = "detailed") -> dict:
    """
    Kiểm tra tab đang mở -> gọi đúng file xử lý toán -> trả về dữ liệu cho giao diện.
    mode: "detailed" (lưu lịch sử, hiện các bước) | "quick" (không lưu lịch sử, hiện gọn)
    """
    clean_expr = (expression or "").strip()
    if not clean_expr:
        return {
            "status": "error",
            "mode": mode,
            "message": "Vui lòng nhập biểu thức hoặc bài toán cần giải.",
        }

    solver = TAB_SOLVER_MAP.get(tab_key)
    if solver is None:
        return {
            "status": "error",
            "mode": mode,
            "message": f"Không tìm thấy bộ xử lý cho tab: {tab_key}",
        }

    try:
        raw = solver.solve(clean_expr)
        short_ans = str(raw.get("short_answer", ""))
        steps = raw.get("steps", [])
        latex_short = str(raw.get("latex_short", short_ans))
        latex_full = str(raw.get("latex_full", short_ans))

        if mode == "quick":
            key_points = steps[-2:] if len(steps) >= 2 else steps
            return {
                "status": "success",
                "mode": "quick",
                "save_history": False,
                "short_answer": short_ans,
                "key_points": key_points,
                "latex": latex_short,
            }

        return {
            "status": "success",
            "mode": "detailed",
            "save_history": True,
            "short_answer": short_ans,
            "steps": steps,
            "latex": latex_full,
        }

    except Exception as exc:
        return {
            "status": "error",
            "mode": mode,
            "save_history": False,
            "message": f"Lỗi khi xử lý biểu thức: {exc}",
        }
