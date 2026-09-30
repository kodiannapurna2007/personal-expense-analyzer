from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from config import DB_CONFIG
from werkzeug.security import generate_password_hash, check_password_hash
from prediction import predict_next_month_expense

app = Flask(__name__)

app.secret_key = "personal-expense-analyzer-secret-key"


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():
    connection = mysql.connector.connect(**DB_CONFIG)
    return connection


# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return "Personal Expense Analyzer is running!"


# ==============================
# TEST DATABASE
# ==============================

@app.route("/test-db")
def test_database():

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")

        database_name = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return f"Database connected successfully!<br>Database: {database_name}"

    except mysql.connector.Error as error:

        return f"Database connection failed: {error}"


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        hashed_password = generate_password_hash(password)

        try:

            connection = get_db_connection()

            cursor = connection.cursor()

            query = """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
            """

            values = (
                name,
                email,
                hashed_password
            )

            cursor.execute(query, values)

            connection.commit()

            cursor.close()
            connection.close()

            return "Registration successful! You can now login."

        except mysql.connector.Error as error:

            return f"Registration failed: {error}"

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)


        # --------------------------------
        # TOTAL EXPENSES
        # --------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = %s
        """, (user_id,))

        total_expenses = cursor.fetchone()["total"]


        # --------------------------------
        # CURRENT MONTH EXPENSES
        # --------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = %s
            AND MONTH(expense_date) = MONTH(CURDATE())
            AND YEAR(expense_date) = YEAR(CURDATE())
        """, (user_id,))

        monthly_expenses = cursor.fetchone()["total"]


        # --------------------------------
        # TRANSACTION COUNT
        # --------------------------------

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM expenses
            WHERE user_id = %s
        """, (user_id,))

        transaction_count = cursor.fetchone()["count"]


        # --------------------------------
        # TOP CATEGORY
        # --------------------------------

        cursor.execute("""
            SELECT
                category,
                SUM(amount) AS total
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        """, (user_id,))

        top_result = cursor.fetchone()

        if top_result:

            top_category = top_result["category"]

        else:

            top_category = "No expenses"


        # --------------------------------
        # MONTHLY BUDGET
        # --------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS budget
            FROM budgets
            WHERE user_id = %s
            AND month = MONTH(CURDATE())
            AND year = YEAR(CURDATE())
        """, (user_id,))

        monthly_budget = cursor.fetchone()["budget"]


        # --------------------------------
        # REMAINING BUDGET
        # --------------------------------

        remaining_budget = monthly_budget - monthly_expenses


        # --------------------------------
        # RECENT EXPENSES
        # --------------------------------

        cursor.execute("""
            SELECT
                expense_date,
                category,
                amount,
                payment_method
            FROM expenses
            WHERE user_id = %s
            ORDER BY expense_date DESC
            LIMIT 5
        """, (user_id,))

        recent_expenses = cursor.fetchall()


        cursor.close()

        connection.close()


        # --------------------------------
        # SEND DATA TO DASHBOARD
        # --------------------------------

        return render_template(
            "dashboard.html",

            user_name=session["user_name"],

            total_expenses=total_expenses,

            monthly_expenses=monthly_expenses,

            transaction_count=transaction_count,

            top_category=top_category,

            recent_expenses=recent_expenses,

            monthly_budget=monthly_budget,

            remaining_budget=remaining_budget
        )


    except mysql.connector.Error as error:

        return f"Dashboard error: {error}"


# ==============================
# ADD EXPENSE
# ==============================

@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        amount = request.form["amount"]

        category = request.form["category"]

        expense_date = request.form["expense_date"]

        payment_method = request.form["payment_method"]

        description = request.form["description"]

        user_id = session["user_id"]


        try:

            connection = get_db_connection()

            cursor = connection.cursor()


            query = """
                INSERT INTO expenses
                (
                    user_id,
                    amount,
                    category,
                    expense_date,
                    payment_method,
                    description
                )
                VALUES
                (%s, %s, %s, %s, %s, %s)
            """


            values = (
                user_id,
                amount,
                category,
                expense_date,
                payment_method,
                description
            )


            cursor.execute(query, values)

            connection.commit()

            cursor.close()

            connection.close()


            return redirect(url_for("dashboard"))


        except mysql.connector.Error as error:

            return f"Failed to add expense: {error}"


    return render_template("add_expense.html")


# ==============================
# EXPENSE HISTORY
# ==============================

@app.route("/expenses")
def expenses():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]


    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)


        query = """
            SELECT
                expense_id,
                amount,
                category,
                expense_date,
                payment_method,
                description
            FROM expenses
            WHERE user_id = %s
            ORDER BY expense_date DESC
        """


        cursor.execute(query, (user_id,))

        expenses = cursor.fetchall()


        cursor.close()

        connection.close()


        return render_template(
            "expenses.html",
            expenses=expenses
        )


    except mysql.connector.Error as error:

        return f"Failed to load expenses: {error}"


# ==============================
# EDIT EXPENSE
# ==============================

@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]


    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)


        cursor.execute("""
            SELECT *
            FROM expenses
            WHERE expense_id = %s
            AND user_id = %s
        """, (expense_id, user_id))


        expense = cursor.fetchone()


        if not expense:

            cursor.close()

            connection.close()

            return "Expense not found!"


        if request.method == "POST":

            amount = request.form["amount"]

            category = request.form["category"]

            expense_date = request.form["expense_date"]

            payment_method = request.form["payment_method"]

            description = request.form["description"]


            update_query = """
                UPDATE expenses
                SET
                    amount = %s,
                    category = %s,
                    expense_date = %s,
                    payment_method = %s,
                    description = %s
                WHERE expense_id = %s
                AND user_id = %s
            """


            values = (
                amount,
                category,
                expense_date,
                payment_method,
                description,
                expense_id,
                user_id
            )


            cursor.execute(update_query, values)

            connection.commit()


            cursor.close()

            connection.close()


            return redirect(url_for("expenses"))


        cursor.close()

        connection.close()


        return render_template(
            "edit_expense.html",
            expense=expense
        )


    except mysql.connector.Error as error:

        return f"Failed to edit expense: {error}"


# ==============================
# DELETE EXPENSE
# ==============================

@app.route("/delete-expense/<int:expense_id>")
def delete_expense(expense_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]


    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        cursor.execute("""
            DELETE FROM expenses
            WHERE expense_id = %s
            AND user_id = %s
        """, (expense_id, user_id))


        connection.commit()


        cursor.close()

        connection.close()


        return redirect(url_for("expenses"))


    except mysql.connector.Error as error:

        return f"Failed to delete expense: {error}"


# ==============================
# BUDGET
# ==============================
@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    from datetime import datetime

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Get selected month
    if request.method == "POST":
        selected_month = int(
            request.form.get("month", current_month)
        )
    else:
        selected_month = int(
            request.args.get("month", current_month)
        )

    # Validate month
    if selected_month < 1 or selected_month > 12:
        selected_month = current_month

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # -------------------------------
    # SAVE / UPDATE MONTHLY BUDGET
    # -------------------------------
    if request.method == "POST":

        amount = request.form.get("amount")

        if amount:
            cursor.execute(
                """
                INSERT INTO budgets
                (user_id, month, year, amount)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    amount = %s
                """,
                (
                    user_id,
                    selected_month,
                    current_year,
                    amount,
                    amount
                )
            )

            connection.commit()

    # -------------------------------
    # GET MONTHLY BUDGET
    # -------------------------------
    cursor.execute(
        """
        SELECT amount
        FROM budgets
        WHERE user_id = %s
        AND month = %s
        AND year = %s
        """,
        (
            user_id,
            selected_month,
            current_year
        )
    )

    budget_result = cursor.fetchone()

    if budget_result:
        # Convert Decimal to float
        monthly_budget = float(
            budget_result["amount"] or 0
        )
    else:
        monthly_budget = 0.0

    # -------------------------------
    # GET MONTHLY EXPENSES
    # -------------------------------
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s
        AND MONTH(expense_date) = %s
        AND YEAR(expense_date) = %s
        """,
        (
            user_id,
            selected_month,
            current_year
        )
    )

    expense_result = cursor.fetchone()

    # Convert Decimal to float
    monthly_expenses = float(
        expense_result["total"] or 0
    )

    # -------------------------------
    # GET CATEGORY-WISE EXPENSES
    # -------------------------------
    cursor.execute(
        """
        SELECT
            category,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id = %s
        AND MONTH(expense_date) = %s
        AND YEAR(expense_date) = %s
        GROUP BY category
        ORDER BY total DESC
        """,
        (
            user_id,
            selected_month,
            current_year
        )
    )

    category_data = cursor.fetchall()

    # Convert Decimal category totals to float
    for item in category_data:
        item["total"] = float(
            item["total"] or 0
        )

    cursor.close()
    connection.close()

    # -------------------------------
    # MONTH NAMES
    # -------------------------------
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    selected_month_name = month_names[selected_month - 1]

    # -------------------------------
    # RENDER BUDGET PAGE
    # -------------------------------
    return render_template(
        "budget.html",
        monthly_budget=monthly_budget,
        monthly_expenses=monthly_expenses,
        category_data=category_data,
        selected_month=selected_month,
        selected_month_name=selected_month_name,
        current_year=current_year
    )

# ==============================
# ANALYTICS
# ==============================

@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # --------------------------------
        # CATEGORY-WISE SPENDING
        # --------------------------------

        cursor.execute("""
            SELECT
                category,
                SUM(amount) AS total
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY total DESC
        """, (user_id,))

        category_data = cursor.fetchall()


        # --------------------------------
        # MONTHLY SPENDING
        # --------------------------------

        cursor.execute("""
            SELECT
                YEAR(expense_date) AS year,
                MONTH(expense_date) AS month,
                DATE_FORMAT(
                    MIN(expense_date),
                    '%M %Y'
                ) AS month_name,
                SUM(amount) AS total
            FROM expenses
            WHERE user_id = %s
            GROUP BY
                YEAR(expense_date),
                MONTH(expense_date)
            ORDER BY
                YEAR(expense_date),
                MONTH(expense_date)
        """, (user_id,))

        monthly_data = cursor.fetchall()


        cursor.close()
        connection.close()


        return render_template(
            "analytics.html",
            category_data=category_data,
            monthly_data=monthly_data
        )


    except mysql.connector.Error as error:

        return f"Analytics error: {error}"

# ==============================
# EXPENSE PREDICTION
# ==============================

@app.route("/prediction")
def prediction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    result = predict_next_month_expense(user_id)

    return render_template(
        "prediction.html",
        result=result
    )

# ==============================
# SPENDING INSIGHTS
# ==============================

@app.route("/insights")
def insights():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ------------------------------
        # Total expenses
        # ------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = %s
        """, (user_id,))

        total_expenses = cursor.fetchone()["total"]


        # ------------------------------
        # Current month expenses
        # ------------------------------

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = %s
            AND MONTH(expense_date) = MONTH(CURDATE())
            AND YEAR(expense_date) = YEAR(CURDATE())
        """, (user_id,))

        monthly_expenses = cursor.fetchone()["total"]


        # ------------------------------
        # Highest spending category
        # ------------------------------

        cursor.execute("""
            SELECT
                category,
                SUM(amount) AS total
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        """, (user_id,))

        highest_category = cursor.fetchone()


        # ------------------------------
        # Monthly budget
        # ------------------------------

        cursor.execute("""
            SELECT amount
            FROM budgets
            WHERE user_id = %s
            AND month = MONTH(CURDATE())
            AND year = YEAR(CURDATE())
        """, (user_id,))

        budget_result = cursor.fetchone()


        if budget_result:
            monthly_budget = budget_result["amount"]
        else:
            monthly_budget = 0


        # ------------------------------
        # Remaining budget
        # ------------------------------

        remaining_budget = monthly_budget - monthly_expenses


        # ------------------------------
        # Budget status
        # ------------------------------

        if monthly_budget == 0:

            budget_status = "No budget set for this month."

        elif remaining_budget >= 0:

            budget_status = "You are within your monthly budget."

        else:

            budget_status = "You have exceeded your monthly budget."


        # ------------------------------
        # Category message
        # ------------------------------

        if highest_category:

            category_message = (
                f"Your highest spending category is "
                f"{highest_category['category']} "
                f"with spending of ₹{highest_category['total']}."
            )

        else:

            category_message = "No expense data available."


        cursor.close()
        connection.close()


        return render_template(
            "insights.html",
            total_expenses=total_expenses,
            monthly_expenses=monthly_expenses,
            monthly_budget=monthly_budget,
            remaining_budget=remaining_budget,
            budget_status=budget_status,
            category_message=category_message
        )


    except mysql.connector.Error as error:

        return f"Insights error: {error}"


# ==============================
# LOGOUT
# ==============================

@app.route("/logout", methods=["GET", "POST"])
def logout():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        session.clear()

        return redirect(url_for("login"))

    return render_template(
        "logout.html",
        user_email=session.get("user_email")
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == "__main__":

    app.run(debug=True)