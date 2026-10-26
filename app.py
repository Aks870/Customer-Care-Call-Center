
from flask import (
    Flask, render_template_string, redirect,
    url_for, request, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)

DATABASE = "customer_care.db"

# Local development key only.
# Production deployment mein ise environment variable se set karein.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "local-development-only-change-before-deployment"
)


# ---------------- DATABASE ----------------

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                phone TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_to TEXT NOT NULL
            )
        """)

        # Add a users table without deleting existing calls.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # Create demo accounts only if they do not already exist.
        demo_users = [
            ("junior", "junior123", "junior"),
            ("senior", "senior123", "senior")
        ]

        for username, password, role in demo_users:
            existing_user = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing_user is None:
                connection.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                """, (
                    username,
                    generate_password_hash(password),
                    role
                ))

        # Add sample calls only if the calls table is empty.
        count = connection.execute(
            "SELECT COUNT(*) FROM calls"
        ).fetchone()[0]

        if count == 0:
            connection.executemany("""
                INSERT INTO calls
                (customer, phone, issue, status, assigned_to)
                VALUES (?, ?, ?, ?, ?)
            """, [
                (
                    "Rahul Kumar",
                    "98765XXXXX",
                    "Payment deducted but order not confirmed.",
                    "Waiting",
                    "Junior Executive"
                ),
                (
                    "Priya Sharma",
                    "98764XXXXX",
                    "Unable to reset account password.",
                    "Waiting",
                    "Junior Executive"
                ),
                (
                    "Amit Verma",
                    "98763XXXXX",
                    "Refund has not been received.",
                    "Waiting",
                    "Junior Executive"
                )
            ])


# ---------------- AUTHENTICATION ----------------

def login_required(role=None):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if "username" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash("You do not have permission to access that page.", "error")

                if session.get("role") == "senior":
                    return redirect(url_for("senior_dashboard"))

                return redirect(url_for("home"))

            return view_function(*args, **kwargs)

        return wrapped_view
    return decorator


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Care Login</title>
    {{ css|safe }}
</head>
<body>
<header>
    <h1>Customer Care — Staff Login</h1>
</header>

<main>
    <section class="card login-card">
        <h2>Welcome Back</h2>
        <p>Log in with your staff account to continue.</p>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="{{ 'error' if category == 'error' else 'success' }}">
                    {{ message }}
                </div>
            {% endfor %}
        {% endwith %}

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        <form method="post" action="{{ url_for('login') }}">
            <div class="form-group">
                <label for="username">Username</label>
                <input
                    type="text"
                    id="username"
                    name="username"
                    maxlength="100"
                    autocomplete="username"
                    required
                    autofocus
                >
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input
                    type="password"
                    id="password"
                    name="password"
                    autocomplete="current-password"
                    required
                >
            </div>

            <button class="receive" type="submit">Log In</button>
        </form>

        <hr>
        <p><strong>Demo accounts for local testing</strong></p>
        <p>Junior: <code>junior</code> / <code>junior123</code></p>
        <p>Senior: <code>senior</code> / <code>senior123</code></p>
    </section>
</main>
</body>
</html>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        if session.get("role") == "senior":
            return redirect(url_for("senior_dashboard"))
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_connection() as connection:
            user = connection.execute("""
                SELECT username, password_hash, role
                FROM users
                WHERE username = ?
            """, (username,)).fetchone()

        if (
            user
            and user["role"] in ("junior", "senior")
            and check_password_hash(user["password_hash"], password)
        ):
            # Remove any old session data before logging in.
            session.clear()
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "senior":
                return redirect(url_for("senior_dashboard"))

            return redirect(url_for("home"))

        error = "Invalid username or password."

    return render_template_string(
        LOGIN_PAGE,
        css=CSS,
        error=error
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------- SHARED CSS ----------------

CSS = """
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5f9;
    color: #1e293b;
}

header {
    background: #1e3a8a;
    color: white;
    padding: 20px 25px;
}

header h1 {
    margin: 0;
    font-size: 24px;
}

.header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}

.header-user {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    font-size: 14px;
}

.header-user form { margin: 0; }

.header-user button {
    padding: 8px 12px;
    background: #334155;
}

main {
    max-width: 1000px;
    margin: 30px auto;
    padding: 0 18px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,.06);
}

.details {
    line-height: 1.9;
    overflow-wrap: anywhere;
}

.status {
    display: inline-block;
    padding: 7px 10px;
    border-radius: 7px;
    background: #fef3c7;
    color: #92400e;
    font-size: 13px;
    font-weight: bold;
}

.actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin-top: 18px;
}

button, .button-link {
    display: inline-block;
    border: 0;
    padding: 11px 15px;
    border-radius: 7px;
    color: white;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
    font-size: 14px;
}

button:hover, .button-link:hover { opacity: .85; }

.receive { background: #2563eb; }
.resolve { background: #15803d; }
.transfer { background: #c2410c; }
.add { background: #0f766e; }

a {
    color: #1d4ed8;
    text-decoration: none;
}

a:hover { text-decoration: underline; }

.summary {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
}

.summary div {
    flex: 1;
    min-width: 140px;
    background: white;
    padding: 16px;
    border-radius: 10px;
}

.summary strong {
    display: block;
    font-size: 24px;
    margin-bottom: 5px;
}

.form-group { margin-bottom: 16px; }

.form-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 7px;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 11px;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    font-family: Arial, sans-serif;
    font-size: 15px;
    background: white;
}

.form-group textarea {
    min-height: 100px;
    resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: 2px solid #93c5fd;
    border-color: #2563eb;
}

.error, .success {
    padding: 12px;
    border-radius: 7px;
    margin-bottom: 15px;
}

.error {
    background: #fee2e2;
    color: #991b1b;
}

.success {
    background: #dcfce7;
    color: #166534;
}

.search-form {
    display: grid;
    grid-template-columns: 2fr 1fr auto auto;
    gap: 12px;
    align-items: end;
}

.search-form .form-group { margin-bottom: 0; }

.login-card {
    max-width: 480px;
    margin: 30px auto;
}

.login-card button[type="submit"] {
    width: 100%;
}

hr {
    border: 0;
    border-top: 1px solid #e2e8f0;
    margin: 22px 0;
}

@media (max-width: 650px) {
    header h1 { font-size: 20px; }
    .card { padding: 17px; }
    .search-form { grid-template-columns: 1fr; }
}
</style>
"""


# ---------------- DASHBOARD TEMPLATE ----------------

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {{ css|safe }}
</head>
<body>

<header>
    <div class="header-row">
        <h1>{{ title }}</h1>
        <div class="header-user">
            <span>Logged in: {{ username }}</span>
            <form action="/logout" method="post">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</header>

<main>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="{{ 'error' if category == 'error' else 'success' }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endwith %}

    <div class="summary">
        <div>
            <strong>{{ calls|length }}</strong>
            Total Calls
        </div>
        <div>
            <strong>{{ calls|selectattr('status', 'equalto', 'Waiting')|list|length }}</strong>
            Waiting
        </div>
        <div>
            <strong>{{ calls|selectattr('status', 'equalto', 'In Progress')|list|length }}</strong>
            In Progress
        </div>
        <div>
            <strong>{{ calls|selectattr('status', 'equalto', 'Transferred to Senior')|list|length }}</strong>
            Escalated
        </div>
    </div>

    {% if senior %}
        <p><a href="/">← Junior Dashboard</a></p>
    {% else %}
        <div class="actions" style="margin-bottom: 20px;">
            <a class="button-link add" href="/new-call">+ Add New Call</a>
            <a href="/history">Call History & Search →</a>
            <a href="/senior">Senior Dashboard →</a>
        </div>
    {% endif %}

    {% for call in calls %}
        <section class="card">
            <h2>Call #{{ call.id }} — {{ call.customer }}</h2>

            <p>
                <strong>Status:</strong>
                <span class="status">{{ call.status }}</span>
            </p>

            <div class="details">
                <div><strong>Phone:</strong> {{ call.phone }}</div>
                <div><strong>Assigned To:</strong> {{ call.assigned_to }}</div>
                <div><strong>Issue:</strong> {{ call.issue }}</div>
            </div>

            <div class="actions">
                {% if not senior %}

                    {% if call.status == "Waiting" %}
                        <form action="/receive/{{ call.id }}" method="post">
                            <button class="receive" type="submit">Receive Call</button>
                        </form>

                    {% elif call.status == "In Progress" %}
                        <form action="/resolve/{{ call.id }}" method="post">
                            <button class="resolve" type="submit">Resolve Call</button>
                        </form>

                        <form action="/transfer/{{ call.id }}" method="post">
                            <button class="transfer" type="submit">Transfer to Senior</button>
                        </form>

                    {% elif call.status == "Transferred to Senior" %}
                        <span>Transferred to Senior Executive.</span>

                    {% else %}
                        <span>Call closed successfully.</span>
                    {% endif %}

                {% else %}

                    {% if call.status == "Transferred to Senior" %}
                        <form action="/senior-resolve/{{ call.id }}" method="post">
                            <button class="resolve" type="submit">Resolve & Close Call</button>
                        </form>

                    {% elif call.status == "Resolved" %}
                        <span>Call resolved and closed.</span>

                    {% elif call.status == "Waiting" %}
                        <span>Not yet received by Junior Executive.</span>

                    {% else %}
                        <span>Currently handled by Junior Executive.</span>
                    {% endif %}

                {% endif %}
            </div>
        </section>
    {% else %}
        <section class="card"><p>No customer calls available.</p></section>
    {% endfor %}
</main>
</body>
</html>
"""


# ---------------- NEW CUSTOMER FORM ----------------

NEW_CALL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Customer Call</title>
    {{ css|safe }}
</head>
<body>
<header>
    <div class="header-row">
        <h1>Customer Care — New Customer Call</h1>
        <div class="header-user">
            <span>Logged in: {{ username }}</span>
            <form action="/logout" method="post">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</header>

<main>
    <section class="card">
        <h2>Customer Details Form</h2>
        <p>Enter the customer's information and complaint.</p>

        {% if error %}<div class="error">{{ error }}</div>{% endif %}

        <form action="/new-call" method="post">
            <div class="form-group">
                <label for="customer">Customer Name</label>
                <input type="text" id="customer" name="customer"
                       value="{{ customer }}" maxlength="100" required>
            </div>

            <div class="form-group">
                <label for="phone">Phone Number</label>
                <input type="tel" id="phone" name="phone"
                       value="{{ phone }}" maxlength="20" required>
            </div>

            <div class="form-group">
                <label for="issue">Customer Complaint</label>
                <textarea id="issue" name="issue"
                          maxlength="1000" required>{{ issue }}</textarea>
            </div>

            <div class="actions">
                <button class="add" type="submit">Create Customer Call</button>
                <a href="/">Cancel</a>
            </div>
        </form>
    </section>
</main>
</body>
</html>
"""


# ---------------- CALL HISTORY PAGE ----------------

HISTORY_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Call History & Search</title>
    {{ css|safe }}
</head>
<body>
<header>
    <div class="header-row">
        <h1>Customer Care — Call History</h1>
        <div class="header-user">
            <span>Logged in: {{ username }}</span>
            <form action="/logout" method="post">
                <button type="submit">Logout</button>
            </form>
        </div>
    </div>
</header>

<main>
    <div class="actions" style="margin-bottom: 20px;">
        <a href="/">← Junior Dashboard</a>
        <a href="/senior">Senior Dashboard →</a>
    </div>

    <section class="card">
        <h2>Search Customer Calls</h2>

        <form action="/history" method="get" class="search-form">
            <div class="form-group">
                <label for="q">Search by ID, name, phone or complaint</label>
                <input type="text" id="q" name="q"
                       value="{{ search_text }}"
                       placeholder="Enter customer name or Call ID">
            </div>

            <div class="form-group">
                <label for="status">Filter by Status</label>
                <select id="status" name="status">
                    {% for option in statuses %}
                        <option value="{{ option }}"
                            {% if selected_status == option %}selected{% endif %}>
                            {{ option }}
                        </option>
                    {% endfor %}
                </select>
            </div>

            <button class="receive" type="submit">Search</button>
            <a class="button-link add" href="/history">Clear</a>
        </form>

        <p>Matching calls: <strong>{{ calls|length }}</strong></p>
    </section>

    {% for call in calls %}
        <section class="card">
            <h2>Call #{{ call.id }} — {{ call.customer }}</h2>
            <p><strong>Status:</strong> <span class="status">{{ call.status }}</span></p>
            <div class="details">
                <div><strong>Phone:</strong> {{ call.phone }}</div>
                <div><strong>Assigned To:</strong> {{ call.assigned_to }}</div>
                <div><strong>Complaint:</strong> {{ call.issue }}</div>
            </div>
        </section>
    {% else %}
        <section class="card">
            <p>No matching calls found. Try a different search.</p>
        </section>
    {% endfor %}
</main>
</body>
</html>
"""


# ---------------- DASHBOARD ROUTES ----------------

def show_dashboard(is_senior=False):
    return render_template_string(
        PAGE,
        title=(
            "Customer Care — Senior Executive"
            if is_senior
            else "Customer Care — Junior Executive"
        ),
        calls=get_all_calls(),
        senior=is_senior,
        username=session.get("username", ""),
        css=CSS
    )


@app.route("/")
@login_required(role="junior")
def home():
    return show_dashboard()


@app.route("/senior")
@login_required(role="senior")
def senior_dashboard():
    return show_dashboard(is_senior=True)


# ---------------- CALL HISTORY ----------------

@app.route("/history")
@login_required(role="junior")
def call_history():
    search_text = request.args.get("q", "").strip()
    selected_status = request.args.get("status", "All")

    statuses = [
        "All",
        "Waiting",
        "In Progress",
        "Transferred to Senior",
        "Resolved"
    ]

    if selected_status not in statuses:
        selected_status = "All"

    calls = search_calls(search_text, selected_status)

    return render_template_string(
        HISTORY_PAGE,
        css=CSS,
        calls=calls,
        search_text=search_text,
        selected_status=selected_status,
        statuses=statuses,
        username=session.get("username", "")
    )


def get_all_calls():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM calls ORDER BY id DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def find_call(call_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM calls WHERE id = ?",
            (call_id,)
        ).fetchone()

    return dict(row) if row else None


def update_call(call_id, status, assigned_to=None):
    with get_connection() as connection:
        if assigned_to is None:
            connection.execute(
                "UPDATE calls SET status = ? WHERE id = ?",
                (status, call_id)
            )
        else:
            connection.execute("""
                UPDATE calls
                SET status = ?, assigned_to = ?
                WHERE id = ?
            """, (status, assigned_to, call_id))


def search_calls(search_text="", selected_status="All"):
    query = "SELECT * FROM calls WHERE 1=1"
    parameters = []

    if search_text:
        term = search_text.strip()

        # Numeric input: search by exact Call ID only
        if term.isdigit():
            query += " AND id = ?"
            parameters.append(int(term))

        # Text input: search customer, phone, or issue
        else:
            query += """
                AND (
                    customer LIKE ?
                    OR phone LIKE ?
                    OR issue LIKE ?
                )
            """
            pattern = f"%{term}%"
            parameters.extend([pattern, pattern, pattern])

    allowed_statuses = [
        "Waiting",
        "In Progress",
        "Transferred to Senior",
        "Resolved"
    ]

    if selected_status in allowed_statuses:
        query += " AND status = ?"
        parameters.append(selected_status)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]



# ---------------- CALL ACTIONS ----------------

@app.route("/receive/<int:call_id>", methods=["POST"])
@login_required(role="junior")
def receive_call(call_id):
    call = find_call(call_id)

    if call and call["status"] == "Waiting":
        update_call(call_id, "In Progress")

    return redirect(url_for("home"))


@app.route("/resolve/<int:call_id>", methods=["POST"])
@login_required(role="junior")
def resolve_call(call_id):
    call = find_call(call_id)

    if call and call["status"] == "In Progress":
        update_call(call_id, "Resolved")

    return redirect(url_for("home"))


@app.route("/transfer/<int:call_id>", methods=["POST"])
@login_required(role="junior")
def transfer_call(call_id):
    call = find_call(call_id)

    if call and call["status"] == "In Progress":
        update_call(
            call_id,
            "Transferred to Senior",
            "Senior Executive"
        )

    return redirect(url_for("home"))


@app.route("/senior-resolve/<int:call_id>", methods=["POST"])
@login_required(role="senior")
def senior_resolve_call(call_id):
    call = find_call(call_id)

    if call and call["status"] == "Transferred to Senior":
        update_call(call_id, "Resolved")

    return redirect(url_for("senior_dashboard"))


# ---------------- NEW CUSTOMER CALL ----------------

@app.route("/new-call", methods=["GET", "POST"])
@login_required(role="junior")
def new_call():
    error = None
    customer = ""
    phone = ""
    issue = ""

    if request.method == "POST":
        customer = request.form.get("customer", "").strip()
        phone = request.form.get("phone", "").strip()
        issue = request.form.get("issue", "").strip()

        if not customer or not phone or not issue:
            error = "Please fill in all three fields."

        elif not any(character.isdigit() for character in phone):
            error = "Please enter a valid phone number."

        elif not any(character.isalpha() for character in customer):
            error = "Please enter a valid customer name."

        else:
            with get_connection() as connection:
                connection.execute("""
                    INSERT INTO calls
                    (customer, phone, issue, status, assigned_to)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    customer,
                    phone,
                    issue,
                    "Waiting",
                    "Junior Executive"
                ))

            return redirect(url_for("home"))

    return render_template_string(
        NEW_CALL_PAGE,
        css=CSS,
        error=error,
        customer=customer,
        phone=phone,
        issue=issue,
        username=session.get("username", "")
    )


# ---------------- START APPLICATION ----------------

init_db()


if __name__ == "__main__":
    app.run(debug=True)
