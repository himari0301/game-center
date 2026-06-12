# game2048_app.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from database import save_record

game2048_bp = Blueprint("game2048", __name__)

@game2048_bp.route("/2048")
def game2048():
    return render_template("game2048.html")

@game2048_bp.route("/2048/save", methods=["POST"])
def save_2048():
    data = request.json
    score = data.get("score", 0)
    difficulty = "normal"
    if current_user.is_authenticated:
        save_record(current_user.id, "2048", difficulty, score)
    return jsonify({"success": True})

@game2048_bp.route("/2048/howto")
def game2048_howto():
    return render_template("game2048_howto.html")