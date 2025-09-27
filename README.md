# Share-Trading-and-Stock-Management-System-DBMS-Project

# 📈 Share Trading and Stock Management System

A full-stack **share trading and portfolio management platform** built with **Python (Flask)**, **MySQL**, and **Bootstrap**, simulating core stock exchange functionalities including **user registration/login, trading (buy/sell orders), and portfolio management**.

---

## 🔑 Features

### 👤 User Management
- Secure **registration and login** with unique usernames & encrypted passwords.
- CRUD operations:
  - Add user
  - Edit user details
  - Update account status (Active ↔ Closed)
  - Delete user (cascade deletes applied)
- Role-based authentication (`login_required` in Flask).

### 💹 Trading (Buy/Sell Orders)
- Users can place **Buy** and **Sell** orders:
  - Supports **market orders**, **limit orders**, and basic validations.
  - Order execution updates:
    - `order_table`
    - `buy_sell` (stock linked to order)
    - `transaction_` (records transaction details)
- Balance management:
  - **Buy**: Deduct balance from `trading_account`.
  - **Sell**: Credit balance to `trading_account`.
- Automatic portfolio update via stored procedure.

### 📊 Portfolio Management
- Create and manage **multiple portfolios** per user.
- Track:
  - Current holdings (via `contains`)
  - Portfolio value (auto-updated via procedure)
  - Risk level, diversification, ROI
- View portfolios ordered by stock count with filter options.

### 🛢️ Database Features
- **Stored Function**: `get_full_order_stock_details(stock_id, order_id)`
  - Retrieves full details of a stock + its linked order.
- **Stored Procedure**: `update_portfolio_value`
  - Recalculates total portfolio value after every trade.
- **Stored Procedure**: `get_portfolios_ordered_by_stocks`
  - Lists portfolios sorted by stock count.
- **Trigger**: Ensures portfolio status matches user account status.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: MySQL


---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.x
- MySQL
- Flask (`pip install flask flask-mysqldb`)
- MySQL Connector JAR (if integrating with Java)

### Steps
```bash
# Clone the repository
git clone https://github.com/your-username/share-trading-system.git
cd share-trading-system



# Configure MySQL connection in Flask app
# (update host, user, password, db in app.py)

# Run the app
python app.py
