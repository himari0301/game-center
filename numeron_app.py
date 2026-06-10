# numeron_app.py
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from database import save_record
import random

numeron_bp = Blueprint("numeron", __name__)

DIFFICULTY = {
    "easy":   {"digits": 4, "label": "やさしい（4桁）"},
    "normal": {"digits": 5, "label": "ふつう（5桁）"},
    "hard":   {"digits": 7, "label": "むずかしい（7桁）"},
}

@numeron_bp.route("/numeron")
def numeron():
    return render_template("numeron.html")

@numeron_bp.route("/numeron/start", methods=["POST"])
def numeron_start():
    difficulty = request.json.get("difficulty", "easy")
    digits = DIFFICULTY[difficulty]["digits"]
    numbers = list(range(10))
    random.shuffle(numbers)
    answer = numbers[:digits]
    session["numeron_answer"] = answer
    session["numeron_difficulty"] = difficulty
    session["numeron_attempts"] = []
    return jsonify({"message": f"{digits}桁の数字を当ててください", "digits": digits})

@numeron_bp.route("/numeron/guess", methods=["POST"])
def numeron_guess():
    data = request.json
    user_guess = data.get("guess", "")
    answer = session.get("numeron_answer", [])
    difficulty = session.get("numeron_difficulty", "easy")
    digits = DIFFICULTY[difficulty]["digits"]

    if len(user_guess) != digits:
        return jsonify({"error": f"{digits}桁で入力してください"})
    if not user_guess.isdigit():
        return jsonify({"error": "数字のみ入力してください"})

    guess_list = [int(x) for x in user_guess]
    if len(set(guess_list)) != digits:
        return jsonify({"error": "重複しない数字を入力してください"})

    eat = sum(a == g for a, g in zip(answer, guess_list))
    bite = sum(g in answer for g in guess_list) - eat
    attempts = session.get("numeron_attempts", [])
    attempts.append({"guess": user_guess, "eat": eat, "bite": bite})
    session["numeron_attempts"] = attempts

    if eat == digits:
        if current_user.is_authenticated:
            save_record(current_user.id, "numeron", difficulty, len(attempts))
        return jsonify({
            "eat": eat, "bite": bite, "clear": True,
            "attempts": len(attempts),
            "answer": "".join(map(str, answer))
        })

    return jsonify({"eat": eat, "bite": bite, "clear": False, "attempts": len(attempts)})