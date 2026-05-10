from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import json, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mentecalma-secret-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///mentecalma.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── MODELS ─────────────────────────────────────────────────

class User(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    email     = db.Column(db.String(150), unique=True, nullable=False)
    password  = db.Column(db.String(200), nullable=False)
    child_name= db.Column(db.String(100))
    start_date= db.Column(db.Date, default=date.today)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)
    checkins  = db.relationship("Checkin", backref="user", lazy=True)

class Checkin(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date      = db.Column(db.Date, nullable=False)
    mood      = db.Column(db.Integer)   # 1-4
    focus     = db.Column(db.Integer)   # 1-4
    sleep     = db.Column(db.Integer)   # 1-4
    foods     = db.Column(db.Text, default="[]")  # JSON list
    notes     = db.Column(db.Text)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

# ── AUTH DECORATOR ──────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── HELPERS ─────────────────────────────────────────────────

def get_day_number(start_date):
    diff = (date.today() - start_date).days + 1
    return max(1, min(30, diff))

def get_week_name(day):
    if day <= 7:  return "Semana 1 — Adaptação"
    if day <= 14: return "Semana 2 — Consolidação"
    if day <= 21: return "Semana 3 — Intensificação"
    return "Semana 4 — Manutenção"

def calc_streak(checkins):
    dates = {c.date for c in checkins}
    streak = 0
    d = date.today()
    while d in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak

def generate_insight(mood, focus, sleep, foods, days):
    if not days:
        return "Comece seu primeiro check-in para ver insights! 🌱"
    parts = []
    if mood >= 3:   parts.append("humor positivo 😊")
    elif mood > 0:  parts.append("humor pode melhorar — observe os alimentos 🥗")
    if focus >= 3:  parts.append("foco acima da média 🎯")
    elif focus > 0: parts.append("foco precisa de atenção — café proteico ajuda 🍳")
    if sleep >= 3:  parts.append("sono excelente ✨")
    elif sleep > 0: parts.append("sono irregular — tente o chá da calma 🌙")
    if foods >= 7:  parts.append("protocolo bem seguido 💪")
    elif foods > 0: parts.append(f"média {int(foods)}/10 alimentos — inclua mais!")
    return ", ".join(parts) + "." if parts else "Continue registrando para ver insights! 🌿"

# ── ROUTES ──────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        name       = request.form.get("name","").strip()
        email      = request.form.get("email","").strip().lower()
        password   = request.form.get("password","")
        child_name = request.form.get("child_name","").strip()

        if not name or not email or not password:
            error = "Preencha todos os campos obrigatórios."
        elif User.query.filter_by(email=email).first():
            error = "Este e-mail já está cadastrado."
        elif len(password) < 6:
            error = "A senha deve ter pelo menos 6 caracteres."
        else:
            user = User(
                name=name, email=email,
                password=generate_password_hash(password),
                child_name=child_name,
                start_date=date.today()
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            error = "E-mail ou senha incorretos."
        else:
            session["user_id"]   = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user     = User.query.get(session["user_id"])
    checkins = Checkin.query.filter_by(user_id=user.id).all()
    today_ci = Checkin.query.filter_by(user_id=user.id, date=date.today()).first()
    day_num  = get_day_number(user.start_date)
    streak   = calc_streak(checkins)
    total    = len(checkins)
    pct      = round((total / 30) * 100)
    return render_template("dashboard.html",
        user=user, today_ci=today_ci, day_num=day_num,
        week_name=get_week_name(day_num), streak=streak,
        total=total, pct=pct
    )

@app.route("/checkin", methods=["GET","POST"])
@login_required
def checkin():
    user     = User.query.get(session["user_id"])
    day_num  = get_day_number(user.start_date)
    today_ci = Checkin.query.filter_by(user_id=user.id, date=date.today()).first()

    if request.method == "POST":
        foods_list = request.form.getlist("foods")
        if today_ci:
            today_ci.mood  = int(request.form.get("mood", 0))
            today_ci.focus = int(request.form.get("focus", 0))
            today_ci.sleep = int(request.form.get("sleep", 0))
            today_ci.foods = json.dumps(foods_list)
            today_ci.notes = request.form.get("notes","")
        else:
            ci = Checkin(
                user_id=user.id, date=date.today(),
                mood=int(request.form.get("mood",0)),
                focus=int(request.form.get("focus",0)),
                sleep=int(request.form.get("sleep",0)),
                foods=json.dumps(foods_list),
                notes=request.form.get("notes","")
            )
            db.session.add(ci)
        db.session.commit()
        return redirect(url_for("dashboard"))

    existing_foods = json.loads(today_ci.foods) if today_ci else []
    return render_template("checkin.html",
        day_num=day_num, today_ci=today_ci, existing_foods=existing_foods
    )

@app.route("/history")
@login_required
def history():
    user     = User.query.get(session["user_id"])
    checkins = Checkin.query.filter_by(user_id=user.id)\
                            .order_by(Checkin.date.desc()).all()
    entries  = []
    for ci in checkins:
        n = (ci.date - user.start_date).days + 1
        entries.append({
            "day": max(1, min(30, n)),
            "date": ci.date.strftime("%d/%m/%Y"),
            "mood": ci.mood, "focus": ci.focus, "sleep": ci.sleep,
            "foods_count": len(json.loads(ci.foods or "[]")),
            "notes": ci.notes
        })
    return render_template("history.html", entries=entries)

@app.route("/progress")
@login_required
def progress():
    user     = User.query.get(session["user_id"])
    checkins = Checkin.query.filter_by(user_id=user.id)\
                            .order_by(Checkin.date.asc()).limit(14).all()
    if not checkins:
        return render_template("progress.html", has_data=False)

    def safe_avg(lst): return round(sum(lst)/len(lst), 1) if lst else 0
    moods  = [c.mood  for c in checkins if c.mood]
    foci   = [c.focus for c in checkins if c.focus]
    sleeps = [c.sleep for c in checkins if c.sleep]
    foods  = [len(json.loads(c.foods or "[]")) for c in checkins]
    am, af, as_, afd = safe_avg(moods), safe_avg(foci), safe_avg(sleeps), safe_avg(foods)

    chart = []
    for i, ci in enumerate(checkins):
        n = (ci.date - user.start_date).days + 1
        chart.append({"day": max(1,n), "mood": ci.mood or 0, "focus": ci.focus or 0})

    return render_template("progress.html",
        has_data=True, avg_mood=am, avg_focus=af,
        avg_sleep=as_, avg_foods=round(afd,1),
        chart=json.dumps(chart), days=len(checkins),
        insight=generate_insight(am, af, as_, afd, len(checkins))
    )

# ── INIT ────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
