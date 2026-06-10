# countdown_app.py
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from database import save_record
import random
import re

countdown_bp = Blueprint("countdown", __name__)

DIFFICULTY = {
    "easy":   {"label": "やさしい",   "pool": list(range(1, 10)),   "target_range": (10, 100)},
    "normal": {"label": "ふつう",     "pool": list(range(1, 26)),   "target_range": (100, 300)},
    "hard":   {"label": "むずかしい", "pool": list(range(1, 101)),  "target_range": (100, 999)},
}

def calc_3(a, b, c):
    results = []
    checks = [
        (a + b + c,       f"{a} + {b} + {c}"),
        (a + b - c,       f"{a} + {b} - {c}"),
        (a - b + c,       f"{a} - {b} + {c}"),
        (a * b + c,       f"{a} × {b} + {c}"),
        (a * b - c,       f"{a} × {b} - {c}"),
        (a + b * c,       f"{a} + {b} × {c}"),
        (a - b * c,       f"{a} - {b} × {c}"),
        ((a + b) * c,     f"( {a} + {b} ) × {c}"),
        ((a - b) * c,     f"( {a} - {b} ) × {c}"),
        (a * b * c,       f"{a} × {b} × {c}"),
    ]
    if c != 0:
        if a * b % c == 0:
            checks.append((a * b // c, f"{a} × {b} ÷ {c}"))
        if (a + b) % c == 0:
            checks.append(((a + b) // c, f"( {a} + {b} ) ÷ {c}"))
    for v, expr in checks:
        if v is not None and v > 0:
            results.append((v, expr))
    return results

def calc_4(a, b, c, d):
    results = []
    checks = [
        (a + b + c + d,         f"{a} + {b} + {c} + {d}"),
        (a * b + c + d,         f"{a} × {b} + {c} + {d}"),
        (a * b + c - d,         f"{a} × {b} + {c} - {d}"),
        (a * b - c + d,         f"{a} × {b} - {c} + {d}"),
        (a * b * c + d,         f"{a} × {b} × {c} + {d}"),
        (a * b * c - d,         f"{a} × {b} × {c} - {d}"),
        ((a + b) * (c + d),     f"( {a} + {b} ) × ( {c} + {d} )"),
        ((a + b) * c + d,       f"( {a} + {b} ) × {c} + {d}"),
        ((a + b) * c - d,       f"( {a} + {b} ) × {c} - {d}"),
        ((a - b) * c + d,       f"( {a} - {b} ) × {c} + {d}"),
        ((a - b) * (c + d),     f"( {a} - {b} ) × ( {c} + {d} )"),
        (a * b + c * d,         f"{a} × {b} + {c} × {d}"),
        (a * b - c * d,         f"{a} × {b} - {c} × {d}"),
        ((a + b + c) * d,       f"( {a} + {b} + {c} ) × {d}"),
        ((a + b - c) * d,       f"( {a} + {b} - {c} ) × {d}"),
        (a * (b + c) + d,       f"{a} × ( {b} + {c} ) + {d}"),
        (a * (b + c) - d,       f"{a} × ( {b} + {c} ) - {d}"),
        (a * (b - c) + d,       f"{a} × ( {b} - {c} ) + {d}"),
        (a * (b + c + d),       f"{a} × ( {b} + {c} + {d} )"),
        (a * (b + c - d),       f"{a} × ( {b} + {c} - {d} )"),
    ]
    for v, expr in checks:
        if v is not None and v > 0:
            results.append((v, expr))
    return results

def generate_puzzle(difficulty):
    pool = DIFFICULTY[difficulty]["pool"]
    t_min, t_max = DIFFICULTY[difficulty]["target_range"]

    for _ in range(200):
        numbers = random.choices(pool, k=6)

        for i in range(6):
            for j in range(6):
                for k in range(6):
                    for l in range(6):
                        if len({i,j,k,l}) < 4:
                            continue
                        a,b,c,d = numbers[i],numbers[j],numbers[k],numbers[l]
                        for v, expr in calc_4(a,b,c,d):
                            if t_min <= v <= t_max:
                                return numbers, v, expr

        for i in range(6):
            for j in range(6):
                for k in range(6):
                    if len({i,j,k}) < 3:
                        continue
                    a,b,c = numbers[i],numbers[j],numbers[k]
                    for v, expr in calc_3(a,b,c):
                        if t_min <= v <= t_max:
                            return numbers, v, expr

    numbers = random.choices(pool, k=6)
    target = random.randint(t_min, t_max)
    return numbers, target, "解答例を見つけられませんでした"

@countdown_bp.route("/countdown")
def countdown():
    return render_template("countdown.html")

@countdown_bp.route("/countdown/start", methods=["POST"])
def countdown_start():
    difficulty = request.json.get("difficulty", "easy")
    numbers, target, solution = generate_puzzle(difficulty)
    session["countdown_numbers"] = numbers
    session["countdown_target"] = target
    session["countdown_difficulty"] = difficulty
    session["countdown_solution"] = solution
    session["countdown_start_time"] = 60
    return jsonify({
        "numbers": numbers,
        "target": target,
        "time_limit": 60
    })

@countdown_bp.route("/countdown/check", methods=["POST"])
def countdown_check():
    data = request.json
    expression = data.get("expression", "").strip()
    target = session.get("countdown_target", 0)
    numbers = session.get("countdown_numbers", [])
    difficulty = session.get("countdown_difficulty", "easy")
    time_left = data.get("time_left", 0)

    allowed = set("0123456789+-*/() ")
    if not all(c in allowed for c in expression):
        return jsonify({"error": "使える記号は ＋ － × ÷ （ ） のみです"})

    used_numbers = [int(n) for n in re.findall(r'\d+', expression)]

    available = numbers.copy()
    for n in used_numbers:
        if n in available:
            available.remove(n)
        else:
            return jsonify({"error": f"{n} は使えない数字です"})

    try:
        result = int(eval(expression))
    except ZeroDivisionError:
        return jsonify({"error": "0で割ることはできません"})
    except Exception:
        return jsonify({"error": "計算式が正しくありません"})

    if result == target:
        # 使用秒数を計算（60秒 - 残り時間）
        used_seconds = 60 - time_left
        if current_user.is_authenticated:
            save_record(current_user.id, "countdown", difficulty, used_seconds)
        return jsonify({
            "result": result,
            "clear": True,
            "used_seconds": used_seconds
        })

    return jsonify({
        "result": result,
        "clear": False,
        "diff": abs(result - target)
    })

@countdown_bp.route("/countdown/solution", methods=["GET"])
def countdown_solution():
    solution = session.get("countdown_solution", "解答例を見つけられませんでした")
    target = session.get("countdown_target", 0)
    return jsonify({
        "solution": solution,
        "target": target
    })