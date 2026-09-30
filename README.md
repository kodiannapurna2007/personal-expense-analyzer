# 💰 Personal Expense Analyzer

A simple web-based application that helps users **track expenses, manage monthly budgets, analyze spending patterns, and predict future expenses**.

The project combines **Web Development, Database Management, and Data Science** to provide a practical solution for personal expense management.

---

## 📌 Why I Built This

Managing daily expenses manually can be difficult, especially when it comes to understanding where money is being spent.

I built this project to make expense management easier by allowing users to:

- Track their daily expenses
- Set monthly budgets
- Understand spending patterns
- Analyze expenses using charts
- Get an estimate of next month's expenses
- Receive useful spending insights

The main goal is to help users **track, plan, and manage their spending more effectively**.

---

## ✨ Features

### 🔐 User Registration & Login
- Create a user account
- Secure login using password hashing
- Session-based authentication

### 💸 Add Expense
Users can record:
- Amount
- Category
- Date
- Payment method
- Description

### 📋 Expense History
- View all recorded expenses
- Edit existing expenses
- Delete expenses

### 🎯 Monthly Budget
- Set a budget for each month
- Select different months
- Compare monthly expenses with the budget
- Track remaining or exceeded budget

### 📊 Analytics
Provides visual information about spending through:
- Category-wise expense charts
- Monthly spending charts
- Total spending information

### 🤖 Expense Prediction
Uses **Machine Learning** to estimate the user's next month's expenses based on previous monthly spending data.

### 💡 Spending Insights
Provides simple insights about:
- Spending patterns
- Monthly expenses
- Budget status
- Remaining budget

---

## 🛠️ Technologies Used

### Frontend
- HTML
- CSS
- JavaScript
- Chart.js

### Backend
- Python
- Flask

### Database
- MySQL

### Data Science & Machine Learning
- Pandas
- NumPy
- Scikit-learn
- Linear Regression

### Tools
- VS Code
- Git
- GitHub

---

## 🏗️ Project Structure

```text
PERSONAL_EXPENSE_ANALYZER/
│
├── venv/
│
├── app.py
├── config.py
├── prediction.py
├── .env
├── requirements.txt
│
└── templates/
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── add_expense.html
    ├── expenses.html
    ├── edit_expense.html
    ├── budget.html
    ├── analytics.html
    ├── prediction.html
    ├── insights.html
    └── logout.html  
