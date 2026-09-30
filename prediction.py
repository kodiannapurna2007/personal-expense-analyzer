import mysql.connector
import pandas as pd
from sklearn.linear_model import LinearRegression

from config import DB_CONFIG


# =====================================
# GET MONTHLY EXPENSE DATA
# =====================================

def get_monthly_expenses(user_id):

    connection = mysql.connector.connect(**DB_CONFIG)

    query = """
        SELECT
            YEAR(expense_date) AS year,
            MONTH(expense_date) AS month,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id = %s
        GROUP BY
            YEAR(expense_date),
            MONTH(expense_date)
        ORDER BY
            YEAR(expense_date),
            MONTH(expense_date)
    """

    df = pd.read_sql(
        query,
        connection,
        params=(user_id,)
    )

    connection.close()

    return df


# =====================================
# PREDICT NEXT MONTH EXPENSE
# =====================================

def predict_next_month_expense(user_id):

    df = get_monthly_expenses(user_id)

    print("\nMonthly Expense Data:")
    print(df)


    # Need at least 2 months
    if len(df) < 2:

        return {
            "success": False,
            "message": "At least 2 months of expense data are required for prediction."
        }


    # ---------------------------------
    # Create month number
    # ---------------------------------

    df["month_number"] = range(1, len(df) + 1)


    # ---------------------------------
    # Prepare training data
    # ---------------------------------

    X = df[["month_number"]]

    y = df["total"]


    # ---------------------------------
    # Create Linear Regression model
    # ---------------------------------

    model = LinearRegression()

    model.fit(X, y)


    # ---------------------------------
    # Predict next month
    # ---------------------------------

    next_month_number = len(df) + 1

    prediction = model.predict(
        [[next_month_number]]
    )[0]


    # Prevent negative prediction
    if prediction < 0:
        prediction = 0


    return {
        "success": True,
        "prediction": round(float(prediction), 2)
    }


# =====================================
# TEST MODEL
# =====================================

if __name__ == "__main__":

    # Your current user ID
    user_id = 2

    result = predict_next_month_expense(user_id)

    print("\nPrediction Result:")

    if result["success"]:

        print(
            f"Predicted next month expense: ₹{result['prediction']}"
        )

    else:

        print(result["message"])