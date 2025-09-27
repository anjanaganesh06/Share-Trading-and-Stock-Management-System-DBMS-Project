from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from config import Config
from flask import jsonify
from functools import wraps
import yfinance as yf
from werkzeug.security import check_password_hash
from MySQLdb.cursors import DictCursor

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key'

# Initialize MySQL
mysql = MySQL(app)


# Admin Required Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('unauthorized'))  # Redirect to unauthorized page
        return f(*args, **kwargs)
    return decorated_function

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            print("Not logged in!")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Unauthorized Route (for when a user tries to access restricted pages)
@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')  # You can create this template

# # Login Route
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         username = request.form['username'].strip()  # Strip leading/trailing spaces
#         password = request.form['password'].strip()  # Strip leading/trailing spaces

#         # Check credentials in the database
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE username = %s", (username,))
#         user = cur.fetchone()
#         print(user)
#         cur.close()

#         if user:
#             # Check if the provided password matches
#             if user[3] == password:  # Plain text password comparison
#                 session['logged_in'] = True
#                 session['username'] = user[1]  # Assuming index 1 is username
#                 session['role'] = user[5]  # Store user role (admin or user)
#                 flash('You have been logged in!', 'success')
#                 print(f"Session data: {session}")  # Debug session data

#                 # Redirect based on the role
#                 if user[5] == 'admin':  # If the user is an admin
#                     return redirect(url_for('admin_dashboard'))  # Admin Dashboard
#                 else:
#                     return redirect(url_for('user_dashboard'))  # Regular user services

           
#         else:
#             error = 'Invalid credentials. Please try again.'
#             flash(error, 'danger')

#     return render_template('login.html', error=error)


# Admin Dashboard Route (only accessible by admin)
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')  # Create an HTML template for the admin dashboard

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')
# Sign Up Route

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         username = request.form['username'].strip()
#         password = request.form['password'].strip()

#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM users WHERE username = %s", (username,))
#         user = cur.fetchone()
#         cur.close()

#         if user and user[3] == password:  # Plain text check
#             session['logged_in'] = True
#             session['username'] = user[1]
#             session['role'] = user[5]
#             print(user[5])
#             # 🔑 Get numeric userID from users
#             users_userID = user[0]  # e.g. 12

#             # 🔑 Map it to real business user_id (U003)
#             cur = mysql.connection.cursor()
#             cur.execute("SELECT user_id FROM user WHERE userID = %s", (users_userID,))
#             profile = cur.fetchone()
#             cur.close()

#             if not profile:
#                 flash("Profile not found for this account", "danger")
#                 return redirect(url_for('login'))

#             # ✅ Store real U003 in session
#             session['user_id'] = profile[0]

#             flash("You have been logged in!", "success")

#             if session['role'] == 'admin':
#                 return redirect(url_for('admin_dashboard'))
#             else:
#                 return redirect(url_for('user_dashboard'))
#         else:
#             error = 'Invalid credentials. Please try again.'
#             flash(error, 'danger')

#     return render_template('login.html', error=error)
from MySQLdb.cursors import DictCursor

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Query users table
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user:
            if user['password'] == password:
                session['logged_in'] = True
                session['username'] = user['username']
                session['role'] = user['role'].strip().lower()

                flash("You have been logged in!", "success")
                print(f"DEBUG role = {session['role']}, userID = {user['userID']}")

                # If admin → go directly to admin dashboard (no need for U003 mapping)
                if session['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))

                # Else → map to U003 style ID for trading
                cur = mysql.connection.cursor(DictCursor)
                cur.execute("SELECT user_id FROM user WHERE userID = %s", (user['userID'],))
                profile = cur.fetchone()
                cur.close()

                if not profile:
                    flash("Profile not found for this account", "danger")
                    return redirect(url_for('login'))

                session['user_id'] = profile['user_id']

                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    cur = mysql.connection.cursor()

    # Fetch all names from the user table for the dropdown
    cur.execute("SELECT name FROM user")
    names = [row[0] for row in cur.fetchall()]  # Extracting names as a list

    if request.method == 'POST':
        selected_name = request.form['name']  # Dropdown name selection
        username = request.form['username'].strip()  # Strip leading/trailing spaces
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # Check if the username already exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            error = "Username already exists. Please choose a different one."
        else:
            # Insert new user into the database with plain text password
            cur.execute("INSERT INTO users (username, email, password, name, role) VALUES (%s, %s, %s, %s, %s)",
                        (username, email, password, selected_name, 'user'))  # Default role is 'user'
            mysql.connection.commit()

            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))  # Redirect to the login page after signup

        cur.close()

    return render_template('signup.html', error=error, names=names)



# Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Clear the username from session
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))


@app.route('/services_provided')
@login_required  # Ensure the user must be logged in to access this page
def services_provided():
    return render_template('services.html')

@app.route('/manage_users')
def manage_users():
    # Render the page for managing users (Add, View, Edit)
    return render_template('manage_users.html')

# @app.route('/manage_users_for_users')
# def manage_users_for_users():
#     # Render the page for managing users (Add, View, Edit)
#     return render_template('manage_users_for_user.html')
# Assuming MySQL is initialized as 'mysql'
@app.route('/manage_users_for_user')
@login_required
def manage_users_for_user():
    # Get the logged-in user's username from the session
    username = session.get('username')
    if not username:
        flash("Please log in to access this page", "warning")
        return redirect(url_for('login'))

    # Query to get the user's name based on the username from 'users' table
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM users WHERE username = %s", (username,))
    user_info = cursor.fetchone()

    # If the user has no associated name, redirect back or show an error
    if not user_info:
        flash("User not found.", "error")
        return redirect(url_for('dashboard'))

    # Extract the name for the specific user
    user_name = user_info[0]

    # Now, query the 'user' table for details specific to this user's name
    query = """
        SELECT u.user_id, u.risk_profile, u.name, u.account_id, u.acc_type, u.account_details, 
               u.acc_status, u.opening_date, e.email_id, p.phone_no
        FROM user u
        LEFT JOIN user_emailid e ON u.user_id = e.user_id
        LEFT JOIN user_phno p ON u.user_id = p.user_id
        WHERE u.name = %s
    """
    cursor.execute(query, (user_name,))
    result = cursor.fetchall()
    cursor.close()

    # Process the result as in 'view_users' to organize data by (user_id, account_id) composite key
    users = {}
    for row in result:
        (
            user_id, risk_profile, name, account_id, acc_type, account_details, 
            acc_status, opening_date, email_id, phone_no
        ) = row

        key = (user_id, account_id)

        # Initialize entry if not already present
        if key not in users:
            users[key] = {
                "user_id": user_id,
                "risk_profile": risk_profile,
                "name": name,
                "account_id": account_id,
                "acc_type": acc_type,
                "account_details": account_details,
                "acc_status": acc_status,
                "opening_date": opening_date,
                "emails": set(),
                "phones": set()
            }

        # Add email and phone numbers to the sets
        if email_id:
            users[key]["emails"].add(email_id)
        if phone_no:
            users[key]["phones"].add(phone_no)

    # Convert sets to lists for easier rendering in the template
    for user in users.values():
        user["emails"] = list(user["emails"])
        user["phones"] = list(user["phones"])

    # Render the template with the specific user's data
    return render_template('manage_users_for_user.html', users=users.values())  
@app.route('/manage_portfolios_for_user', methods=['GET', 'POST'])
@login_required
def manage_portfolios_for_user():
    # Get the logged-in user's username from the session
    username = session.get('username')
    if not username:
        flash("Please log in to access this page", "warning")
        return redirect(url_for('login'))

    # Query to get the user's name based on the username from 'users' table
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM users WHERE username = %s", (username,))
    user_info = cursor.fetchone()

    # If the user has no associated name, redirect back or show an error
    if not user_info:
        flash("User not found.", "error")
        return redirect(url_for('dashboard'))

    # Extract the name for the specific user
    user_name = user_info[0]

    # Now, query the 'portfolio' table for details specific to this user's name
    query = """
    SELECT p.portfolio_id, p.user_id, p.portfolio_value, p.portfolio_name, p.risk_level,
           p.created_date, COUNT(c.stock_id) AS stock_count, p.portfolio_status, u.name AS user_name
    FROM portfolio p
    LEFT JOIN contains c ON p.portfolio_id = c.portfolio_id
    LEFT JOIN user u ON p.user_id = u.user_id
    WHERE p.user_id = (SELECT user_id FROM user WHERE name = %s)
    GROUP BY p.portfolio_id, u.name  -- Add 'u.name' to the GROUP BY clause
"""

    cursor.execute(query, (user_name,))
    portfolios = cursor.fetchall()
    cursor.close()

    # Process the result to organize data by (user_id, portfolio_id) composite key
    portfolios_dict = {}
    for row in portfolios:
        (
            portfolio_id, user_id, portfolio_value, portfolio_name, risk_level,
            created_date, stock_count, portfolio_status, user_name
        ) = row

        key = (user_id, portfolio_id)

        # Initialize entry if not already present
        if key not in portfolios_dict:
            portfolios_dict[key] = {
                "portfolio_id": portfolio_id,
                "user_id": user_id,
                "user_name": user_name,
                "portfolio_value": portfolio_value,
                "portfolio_name": portfolio_name,
                "risk_level": risk_level,
                "created_date": created_date,
                "stock_count": stock_count,
                "portfolio_status": portfolio_status
            }

    # Convert portfolios_dict values to list for easier rendering in the template
    portfolios_list = list(portfolios_dict.values())

    # Get the filter option (if any)
    filter_option = request.args.get('filter', 'all')

    if filter_option == 'max_stocks' and portfolios_list:
        # Sort by stock_count in descending order and pick the ones with the max stock_count
        max_stock_count = max(portfolio['stock_count'] for portfolio in portfolios_list)
        portfolios_list = [portfolio for portfolio in portfolios_list if portfolio['stock_count'] == max_stock_count]

    # Render the template with the portfolios data
    return render_template('manage_portfolio_for_users.html', portfolios=portfolios_list, filter_option=filter_option)

# Route to edit a specific user
@app.route('/edit_users_for_user/<string:user_id>', methods=['GET', 'POST'])
def edit_users_for_user(user_id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        # Get updated user details from the form
        name = request.form['name']
        risk_profile = request.form['risk_profile']
        acc_type = request.form['acc_type']
        account_details = request.form['acc_details']
        acc_status = request.form['acc_status']
        opening_date = request.form['opening_date']

        # Update user table
        cursor.execute("""
            UPDATE user SET 
            name = %s, risk_profile = %s, acc_type = %s, 
            account_details = %s, acc_status = %s, opening_date = %s
            WHERE user_id = %s
        """, (name, risk_profile, acc_type, account_details, acc_status, opening_date, user_id))

        # Get emails and phones from the form
        emails = request.form.getlist('email')
        phones = request.form.getlist('phone')

        # Remove old emails and phones
        cursor.execute("DELETE FROM user_emailid WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM user_phno WHERE user_id = %s", (user_id,))

        # Insert new emails
        for email in emails:
            cursor.execute("INSERT INTO user_emailid (user_id, email_id) VALUES (%s, %s)", (user_id, email))

        # Insert new phones
        for phone in phones:
            cursor.execute("INSERT INTO user_phno (user_id, phone_no) VALUES (%s, %s)", (user_id, phone))

        # Commit the changes to the database
        mysql.connection.commit()
        cursor.close()

        flash('User updated successfully', 'success')

        # Redirect to the manage users page
        return redirect(url_for('manage_users_for_user'))

    # Fetch the user's current details
    cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    # Fetch the user's emails and phones
    cursor.execute("SELECT email_id FROM user_emailid WHERE user_id = %s", (user_id,))
    emails = [email[0] for email in cursor.fetchall()]

    cursor.execute("SELECT phone_no FROM user_phno WHERE user_id = %s", (user_id,))
    phones = [phone[0] for phone in cursor.fetchall()]

    cursor.close()

    # Pass the user's details, emails, and phones to the template
    return render_template('edit_users_for_user.html', user=user, emails=emails, phones=phones)

@app.route('/manage_stocks')
def manage_stocks():
    return render_template('manage_stocks.html')

@app.route('/manage_stocks_for_users')
def manage_stocks_user():
    return render_template('manage_stocks_for_user.html')

@app.route('/manage_portfolios')
def manage_portfolios():
    return render_template('manage_portfolios.html')



@app.route('/manage_orders')
def manage_orders():
    return render_template('manage_orders.html')

@app.route('/manage_orders_for_user')
def manage_orders_for_user():
    return render_template('manage_orders_for_user.html')

@app.route('/manage_transactions')
def manage_transactions():
    return render_template('manage_transactions.html')

@app.route('/manage_transactions_for_user')
def manage_transactions_for_user():
    return render_template('manage_transactions_users.html')

@app.route('/manage_exchanges')
def manage_exchanges():
    return render_template('manage_exchanges.html')


@app.route('/manage_exchanges_for_user')
def manage_exchanges_for_user():
    return render_template('manage_exchanges_for_user.html')


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        # Retrieve form data
        user_id = request.form['user_id']
        risk_profile = request.form['risk_profile']
        account_details = request.form['account_details']
        name = request.form['name']
        account_id = request.form.get('account_id', None)
        acc_type = request.form.get('acc_type', None)
        acc_status = request.form.get('acc_status', None)
        opening_date = request.form.get('opening_date', None)
        email_id = request.form.get('email_id', None)
        phone_no = request.form.get('phone_no', None)

        # Insert the user into MySQL
        cur = mysql.connection.cursor()
        
        # Insert data into the user table
        cur.execute(
            """
            INSERT INTO user (user_id, risk_profile, name, account_id, acc_type, account_details, acc_status, opening_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, risk_profile, name, account_id, acc_type, account_details, acc_status, opening_date)
        )

        # Insert email if provided
        if email_id:
            cur.execute(
                "INSERT INTO user_emailid (user_id, email_id) VALUES (%s, %s)",
                (user_id, email_id)
            )

        # Insert phone number if provided
        if phone_no:
            cur.execute(
                "INSERT INTO user_phno (user_id, phone_no) VALUES (%s, %s)",
                (user_id, phone_no)
            )

        # Commit changes and close the cursor
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('view_users'))

    # Render the form template if request method is GET
    return render_template('add_user.html')


def update_user_details(user_id, name, risk_profile, account_id, acc_type, account_details, acc_status, opening_date, email_id, phone_no):
    # Get a database connection
    connection = mysql.connection
    cursor = connection.cursor()

    try:
        # Call the stored procedure to update user details
        cursor.callproc('update_user_details', [
            user_id, name, risk_profile, account_id, acc_type, account_details, 
            acc_status, opening_date, email_id, phone_no
        ])
        connection.commit()  # Commit the transaction
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        cursor.close()  # Close cursor
        connection.close()  



@app.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        # Retrieve updated user details from the form
        name = request.form.get('name')
        risk_profile = request.form.get('risk_profile')
        acc_type = request.form.get('acc_type')
        acc_details = request.form.get('acc_details')
        acc_status = request.form.get('acc_status')
        opening_date = request.form.get('opening_date')

        # Update the main user table
        cursor.execute("""
            UPDATE user
            SET name = %s, risk_profile = %s, acc_type = %s, account_details = %s,
                acc_status = %s, opening_date = %s
            WHERE user_id = %s
        """, (name, risk_profile, acc_type, acc_details, acc_status, opening_date, user_id))

        # Emails: Process additions and deletions
        existing_emails = set(request.form.getlist('existing_email'))  # Emails currently stored in DB
        new_emails = set(request.form.getlist('email'))  # Emails from the form submission

        # Identify emails to delete and add
        emails_to_delete = existing_emails - new_emails
        emails_to_add = new_emails - existing_emails

        # Delete emails no longer present in the form
        for email in emails_to_delete:
            cursor.execute("DELETE FROM user_emailid WHERE user_id = %s AND email_id = %s", (user_id, email))

        # Add new emails
        for email in emails_to_add:
            if email.strip():  # Skip empty emails
                cursor.execute("INSERT INTO user_emailid (user_id, email_id) VALUES (%s, %s)", (user_id, email))

        # Phones: Process additions and deletions
        existing_phones = set(request.form.getlist('existing_phone'))  # Phones currently stored in DB
        new_phones = set(request.form.getlist('phone'))  # Phones from the form submission

        # Identify phones to delete and add
        phones_to_delete = existing_phones - new_phones
        phones_to_add = new_phones - existing_phones

        # Delete phones no longer present in the form
        for phone in phones_to_delete:
            cursor.execute("DELETE FROM user_phno WHERE user_id = %s AND phone_no = %s", (user_id, phone))

        # Add new phones
        for phone in phones_to_add:
            if phone.strip():  # Skip empty phone numbers
                cursor.execute("INSERT INTO user_phno (user_id, phone_no) VALUES (%s, %s)", (user_id, phone))

        # Commit the transaction
        mysql.connection.commit()
        cursor.close()

        # Redirect to a user list or detail page
        return redirect(url_for('view_users'))  # Assuming you have a `view_users` route to list users

    # For GET requests, fetch current user details
    cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    # Fetch existing emails and phone numbers for the user
    cursor.execute("SELECT email_id FROM user_emailid WHERE user_id = %s", (user_id,))
    emails = [row[0] for row in cursor.fetchall()]  # Get all emails

    cursor.execute("SELECT phone_no FROM user_phno WHERE user_id = %s", (user_id,))
    phones = [row[0] for row in cursor.fetchall()]  # Get all phone numbers

    cursor.close()

    # Render the template with current data
    return render_template('edit_user.html', user=user, emails=emails, phones=phones)



@app.route('/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE user_id=%s", (user_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('view_users'))

### User Email CRUD Operations ###
@app.route('/view_users')
@login_required
def view_users():
    cursor = mysql.connection.cursor()
    query = """
        SELECT u.user_id, u.risk_profile, u.name, u.account_id, u.acc_type, u.account_details, 
               u.acc_status, u.opening_date, e.email_id, p.phone_no
        FROM user u
        LEFT JOIN user_emailid e ON u.user_id = e.user_id
        LEFT JOIN user_phno p ON u.user_id = p.user_id
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()

    # Use a dictionary with composite keys of (user_id, account_id)
    users = {}
    for row in result:
        (
            user_id, risk_profile, name, account_id, acc_type, account_details, 
            acc_status, opening_date, email_id, phone_no
        ) = row

        # Use (user_id, account_id) as the composite key
        key = (user_id, account_id)

        # Initialize entry if not already present
        if key not in users:
            users[key] = {
                "user_id": user_id,
                "risk_profile": risk_profile,
                "name": name,
                "account_id": account_id,
                "acc_type": acc_type,
                "account_details": account_details,
                "acc_status": acc_status,
                "opening_date": opening_date,
                "emails": set(),
                "phones": set()
            }

        # Add email and phone numbers to the sets
        if email_id:
            users[key]["emails"].add(email_id)
        if phone_no:
            users[key]["phones"].add(phone_no)

    # Convert sets to lists for easier rendering in the template
    for user in users.values():
        user["emails"] = list(user["emails"])
        user["phones"] = list(user["phones"])

    # Render the template with users.values() to display all unique (user_id, account_id) pairs
    return render_template('view_users.html', users=users.values())



# Route to add an email for a user
@app.route('/add_email/<user_id>', methods=['GET', 'POST'])
@login_required
def add_email(user_id):
    if request.method == 'POST':
        email_id = request.form['email_id']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO user_emailid (user_id, email_id) VALUES (%s, %s)",
            (user_id, email_id)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('view_user_emails', user_id=user_id))
    return render_template('add_email.html', user_id=user_id)

# Route to view all emails of a user
@app.route('/view_user_emails/<user_id>')
@login_required
def view_user_emails(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user_emailid WHERE user_id = %s", (user_id,))
    emails = cur.fetchall()
    cur.close()
    return render_template('view_user_emails.html', user_id=user_id, emails=emails)

# Route to delete an email
@app.route('/delete_email/<user_id>/<email_id>', methods=['POST'])
@login_required
def delete_email(user_id, email_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_emailid WHERE user_id = %s AND email_id = %s", (user_id, email_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('view_user_emails', user_id=user_id))

### User Phone Number CRUD Operations ###

# Route to add a phone number for a user
@app.route('/add_phone/<user_id>', methods=['GET', 'POST'])
@login_required
def add_phone(user_id):
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO user_phno (user_id, phone_number) VALUES (%s, %s)",
            (user_id, phone_number)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('view_user_phones', user_id=user_id))
    return render_template('add_phone.html', user_id=user_id)

# Route to view all phone numbers of a user
@app.route('/view_user_phones/<user_id>')
@login_required
def view_user_phones(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user_phno WHERE user_id = %s", (user_id,))
    phones = cur.fetchall()
    cur.close()
    return render_template('view_user_phones.html', user_id=user_id, phones=phones)

# Route to delete a phone number
@app.route('/delete_phone/<user_id>/<phone_number>', methods=['POST'])
@login_required
def delete_phone(user_id, phone_number):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_phno WHERE user_id = %s AND phone_number = %s", (user_id, phone_number))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('view_user_phones', user_id=user_id))
import time
# Fetch and store stock data from yfinance
# def fetch_and_store_stock_data(symbol, exchange_id=None):
#     # Ensure exchange_id exists in the exchange table
#     if exchange_id:
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT 1 FROM exchange WHERE exchange_id = %s", (exchange_id,))
#         if cur.fetchone() is None:
#             # Insert exchange_id if it does not exist
#             cur.execute("INSERT INTO exchange (exchange_id) VALUES (%s)", (exchange_id,))
#             mysql.connection.commit()
#         cur.close()
    
#     # Rest of the code to fetch stock data from yfinance
#     stock = yf.Ticker(symbol)
#     try:
#         todays_data = stock.history(period='1d')
#     except Exception as e:
#         print(f"⚠️ Failed to fetch history for {symbol}: {e}")
#         todays_data = None
#     try:
#         # Safely fetch info
#         info = stock.info if hasattr(stock, "info") else {}
#     except Exception as e:
#         print(f"⚠️ Failed to fetch info for {symbol}: {e}")
#         info = {}
    
#     # Extract data fields
#     comp_name = stock.info.get('shortName', "N/A")[:30]
#     sector = stock.info.get('sector', "N/A")[:10]
#     total_shares = stock.info.get('sharesOutstanding', 0)
#     market_price = todays_data['Close'].iloc[0] if not todays_data.empty else 0
#     listing_date = stock.info.get('firstTradeDate', None)

#     # Insert fetched data into the MySQL database
#     try:
#         cur = mysql.connection.cursor()
#         cur.execute("""
#             INSERT INTO stock (stock_id, comp_name, sector, total_share, market_price, exchange_id, listing_date)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#             ON DUPLICATE KEY UPDATE
#                 comp_name = VALUES(comp_name),
#                 sector = VALUES(sector),
#                 total_share = VALUES(total_share),
#                 market_price = VALUES(market_price),
#                 exchange_id = VALUES(exchange_id),
#                 listing_date = VALUES(listing_date)
#         """, (symbol, comp_name, sector, total_shares, market_price, exchange_id, listing_date))
#         mysql.connection.commit()
#         cur.close()
#         print(f"✅ Stored stock {symbol}: {comp_name}, price={market_price}")

#     except Exception as e:
#       print(f"❌ DB insert failed for {symbol}: {e}")
#       time.sleep(1)  # delay in case of repeated calls
import yfinance as yf
import time

def fetch_and_store_stock_data(symbol, exchange_id=None):
    # (Your code to ensure exchange_id exists remains the same)
    if exchange_id:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1 FROM exchange WHERE exchange_id = %s", (exchange_id,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO exchange (exchange_id, country, exchange_name) VALUES (%s, %s, %s)", (exchange_id, 'USA', 'NASDAQ'))
            mysql.connection.commit()
        cur.close()

    stock = yf.Ticker(symbol)
    
    # Safely fetch data
    try:
        info = stock.info
        todays_data = stock.history(period='1d')
    except Exception as e:
        print(f"⚠️ Initial fetch failed for {symbol}: {e}")
        info = {}
        todays_data = None

    # --- ✅ THIS IS THE CRITICAL FIX ---
    # Check if the API returned valid data before proceeding.
    if not info or todays_data is None or todays_data.empty:
        print(f"❌ No valid data found for symbol '{symbol}'. It may be delisted. Aborting storage.")
        return # Exit the function gracefully

    # Extract data fields safely
    comp_name = info.get('shortName', "N/A")[:30]
    sector = info.get('sector', "N/A")[:10]
    total_shares = info.get('sharesOutstanding', 0)
    market_price = todays_data['Close'].iloc[0]
    listing_date = info.get('firstTradeDate', None)

    # (Your database insertion code remains the same)
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO stock (stock_id, comp_name, sector, total_share, market_price, exchange_id, listing_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                comp_name = VALUES(comp_name),
                sector = VALUES(sector),
                total_share = VALUES(total_share),
                market_price = VALUES(market_price),
                exchange_id = VALUES(exchange_id),
                listing_date = VALUES(listing_date)
        """, (symbol, comp_name, sector, total_shares, market_price, exchange_id, listing_date))
        mysql.connection.commit()
        cur.close()
        print(f"✅ Stored stock {symbol}: {comp_name}, price={market_price}")

    except Exception as e:
        print(f"❌ DB insert failed for {symbol}: {e}")
        time.sleep(1)


# Prepopulate stock data
with app.app_context():
    # In the "Prepopulate stock data" section
    fetch_and_store_stock_data(symbol="MSFT", exchange_id="NASDAQ")
    print("Stock data for Cidara Therapeutics prepopulated.")

### Stock CRUD Operations ###

@app.route('/view_order_stock', methods=['GET', 'POST'])
def view_order_form():
    order_details = None
    if request.method == 'POST':
        stock_id = request.form['stock_id']
        order_id = request.form['order_id']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT get_full_order_stock_details(%s, %s)", (stock_id, order_id))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            order_details_str = result[0]  # Retrieve as a string
            # Manual parsing to convert to a dictionary
            order_details = {}
            for item in order_details_str.split(', '):
                if ': ' in item:
                    key, value = item.split(': ', 1)
                    order_details[key.strip()] = value.strip()
            if not order_details:
                flash('No matching records found for the provided stock_id and order_id', 'warning')

    return render_template('view_order_details.html', order_details=order_details)



@app.route('/add_stock', methods=['GET', 'POST'])
@login_required
def add_stock():
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))

    # Establish a cursor for database interaction
    cursor = mysql.connection.cursor()

    # Fetch all exchange IDs from the 'exchange' table
    cursor.execute("SELECT exchange_id FROM exchange")
    exchanges = cursor.fetchall()

    # Handle form submission
    if request.method == 'POST':
        # Extract form data
        stock_id = request.form['stock_id']
        comp_name = request.form['comp_name']
        sector = request.form['sector']
        total_share = request.form['total_share']
        market_price = request.form['market_price']
        exchange_id = request.form['exchange_id']
        listing_date = request.form['listing_date']

        try:
            # Insert the new stock into the database
            cursor.execute("""
                INSERT INTO stock (stock_id, comp_name, sector, total_share, market_price, exchange_id, listing_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_id, comp_name, sector, total_share, market_price, exchange_id, listing_date))

            # Commit the transaction
            mysql.connection.commit()

            # Provide a success message to the user
            flash("Stock added successfully!", "success")
        except Exception as e:
            # Rollback in case of error and flash a message
            mysql.connection.rollback()
            flash(f"Error adding stock: {str(e)}", "danger")

        return redirect(url_for('view_stocks'))  # Redirect to the view stocks page after successful insertion

    # If it's a GET request, just render the form
    return render_template('add_stock.html', exchanges=exchanges)



@app.route('/view_stocks')
@login_required
def view_stocks():
    # Retrieve the filter option from query parameters (e.g., ?filter=above_500)
    filter_option = request.args.get('filter', 'all')  # Default to 'all' if no filter is provided
    
    cur = mysql.connection.cursor()
    
    # Use a nested query to filter stocks based on the selected option
    if filter_option == 'above_500':
        # Fetch stocks where the exchange has at least one stock with a market price > 500
        cur.execute("""
            SELECT * FROM stock 
            WHERE exchange_id IN (
                SELECT DISTINCT exchange_id FROM stock
                WHERE market_price > 500
            )
        """)
    else:
        # Fetch all stocks
        cur.execute("SELECT * FROM stock")
    
    stocks = cur.fetchall()
    cur.close()
    
    return render_template('view_stocks.html', stocks=stocks, filter_option=filter_option)

@app.route('/calculate_max_sector_price')
@login_required
def calculate_max_sector_price():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT sector, MAX(market_price) AS max_sector_price
        FROM stock
        GROUP BY sector
    """)
    max_sector_prices = cur.fetchall()
    cur.close()

    # Convert the results into a dictionary for easy access in JavaScript
    max_sector_prices_dict = {}
    for sector, max_sector_price in max_sector_prices:
        max_sector_prices_dict[sector] = max_sector_price

    return jsonify(max_sector_prices_dict)

# Route to edit stock details
@app.route('/edit_stock/<stock_id>', methods=['GET', 'POST'])
@login_required
def edit_stock(stock_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        comp_name = request.form['comp_name']
        sector = request.form['sector']
        total_share = request.form['total_share']
        market_price = request.form['market_price']
        exchange_id = request.form['exchange_id']
        listing_date = request.form['listing_date']

        cur.execute("""
            UPDATE stock SET comp_name=%s, sector=%s, total_share=%s, market_price=%s, exchange_id=%s, listing_date=%s
            WHERE stock_id=%s
        """, (comp_name, sector, total_share, market_price, exchange_id, listing_date, stock_id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('view_stocks'))
    else:
        cur.execute("SELECT * FROM stock WHERE stock_id=%s", (stock_id,))
        stock = cur.fetchone()
        cur.close()

        return render_template('edit_stock.html', stock=stock)
    
# Route to delete a stock entry
@app.route('/delete_stock/<stock_id>', methods=['POST'])
@login_required
def delete_stock_html(stock_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM stock WHERE stock_id=%s", (stock_id,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('view_stocks'))
    
### Portfolio CRUD Operations ###

@app.route('/add_portfolio', methods=['GET', 'POST'])
@login_required
def add_portfolio():
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        portfolio_id = request.form['portfolio_id']
        user_id = request.form['user_id']
        portfolio_value = request.form.get('portfolio_value', None)
        portfolio_name = request.form.get('portfolio_name', None)
        risk_level = request.form.get('risk_level', None)
        created_date = request.form.get('created_date', None)
        stock_id = request.form.get('stock_id', None)

        cur.execute(""" 
            INSERT INTO portfolio (portfolio_id, user_id, portfolio_value, portfolio_name, risk_level, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (portfolio_id, user_id, portfolio_value, portfolio_name, risk_level, created_date, stock_id))
        
        if stock_id:
            cur.execute("INSERT INTO contains (portfolio_id, stock_id) VALUES (%s, %s)", (portfolio_id, stock_id))
        
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('view_portfolios'))
    
    cur.execute("SELECT user_id, name FROM user")
    users = cur.fetchall()
    cur.execute("SELECT stock_id, comp_name FROM stock")
    stocks = cur.fetchall()
    cur.close()
    
    return render_template('add_portfolios.html', users=users, stocks=stocks)

@app.route('/edit_portfolio/<string:portfolio_id>', methods=['GET', 'POST'])
def edit_portfolio(portfolio_id):
    cursor = mysql.connection.cursor()

    # If the form is submitted (POST request), update the portfolio details
    if request.method == 'POST':
        user_id = request.form['user_id']
        portfolio_name = request.form['portfolio_name']
        risk_level = request.form['risk_level']
        portfolio_status = request.form['portfolio_status']
        stock_id = request.form['stock_id']
        created_date = request.form['created_date']  # Assuming the date is also updated

        # Update the portfolio data in the database
        cursor.execute("""
            UPDATE portfolio 
            SET user_id = %s,portfolio_name = %s, risk_level = %s, 
                portfolio_status = %s, created_date = %s
            WHERE portfolio_id = %s
        """, (user_id,portfolio_name, risk_level, portfolio_status,created_date, portfolio_id))

        # Commit the changes
        mysql.connection.commit()
        cursor.close()

        # Redirect to the page that shows all portfolios after successful update
        return redirect(url_for('view_portfolios'))

    # If it's a GET request, fetch the current portfolio details to show in the form
    cursor.execute("SELECT * FROM portfolio WHERE portfolio_id = %s", (portfolio_id,))
    portfolio = cursor.fetchone()

    # Fetch the list of user_ids and stock_ids for dropdowns
    cursor.execute("SELECT user_id FROM user")  # Assuming you have a users table
    users = cursor.fetchall()

    cursor.execute("SELECT stock_id FROM stock")  # Assuming you have a stock table
    stocks = cursor.fetchall()

    cursor.close()

    # Render the edit portfolio form
    return render_template('edit_portfolio.html', portfolio=portfolio, users=users, stocks=stocks)


@app.route('/view_portfolios', methods=['GET', 'POST'])
@login_required
def view_portfolios():
    filter_option = request.args.get('filter', 'all')  # Default to 'all'

    cur = mysql.connection.cursor()

    # Call the stored procedure to get portfolios ordered by stock count
    cur.callproc('get_portfolios_ordered_by_stocks')
    portfolios = cur.fetchall()

    # Determine the index of 'stock_count' in the result tuple
    # Assuming the order in SELECT: ..., COUNT(c.stock_id) AS stock_count, ...
    stock_count_index = 6  # Replace this with the actual index based on the procedure's SELECT

    if filter_option == 'max_stocks' and portfolios:
        # Get the maximum stock count (since portfolios are sorted by stock_count DESC)
        max_stock_count = portfolios[0][stock_count_index]

        # Filter all portfolios with stock_count equal to max_stock_count
        portfolios = [portfolio for portfolio in portfolios if portfolio[stock_count_index] == max_stock_count]

    cur.close()

    return render_template('view_portfolios.html', portfolios=portfolios, filter_option=filter_option)

@app.route('/delete_portfolio/<portfolio_id>', methods=['POST'])
@login_required
def delete_portfolio(portfolio_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM portfolio WHERE portfolio_id = %s", (portfolio_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('view_portfolios'))



@app.route('/update_user_status_for_user', methods=['POST'])
@login_required
def update_user_status_for_user():
    user_id = request.form['user_id']
    new_status = request.form['acc_status']  # This should come from the form

    # Check if the new status is a valid ENUM value
    valid_statuses = ['closed', 'active', 'pending']
    if new_status not in valid_statuses:
        flash(f'Invalid status: {new_status}', 'danger')
        return redirect(url_for('manage_users_for_user'))  # Redirect to the personalized user view

    # Proceed to update the user's status
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE user SET acc_status = %s WHERE user_id = %s", (new_status, user_id))
    mysql.connection.commit()
    cursor.close()

    flash(f'Your account status has been updated to {new_status}', 'success')
    
    # Redirect back to the personalized user view
    return redirect(url_for('manage_users_for_user'))


@app.route('/update_user_status', methods=['POST'])
def update_user_status():
    user_id = request.form['user_id']
    new_status = request.form['acc_status']  # This should come from the form

    # Check if the new status is a valid ENUM value
    valid_statuses = ['closed', 'active', 'pending']
    if new_status not in valid_statuses:
        flash(f'Invalid status: {new_status}', 'danger')
        return redirect(url_for('view_users'))  # Redirect to the users view

    # Proceed to update the user's status
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE user SET acc_status = %s WHERE user_id = %s", (new_status, user_id))
    mysql.connection.commit()
    cursor.close()

    flash(f'User {user_id} status updated to {new_status}', 'success')
    
    # Trigger to update portfolios will automatically run here due to the trigger in the database
    return redirect(url_for('view_users'))


@app.route('/view_exchanges')
@login_required
def view_exchanges():
    try:
        # Create a cursor to interact with the database
        cur = mysql.connection.cursor()
        
        # Execute a query to fetch all exchanges
        cur.execute("SELECT * FROM exchange")
        
        # Fetch all the rows from the executed query
        exchanges = cur.fetchall()
        
        # Debug: print the fetched exchanges
        print(f"Exchanges: {exchanges}")
        
    except Exception as e:
        # Print any exception that occurs during the query execution
        print(f"An error occurred: {e}")
        exchanges = []  # Fallback to an empty list if an error occurs
    finally:
        # Ensure the cursor is closed after the query execution
        cur.close()
    
    # Render the template with the list of exchanges
    return render_template('list_exchanges.html', exchanges=exchanges)

# Route to add a new exchange
@app.route('/add_exchange', methods=['GET', 'POST'])
def add_exchange():
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    if request.method == 'POST':
        exchange_id = request.form['exchange_id']
        currency = request.form['currency']
        exchange_name = request.form['exchange_name']
        country = request.form['country']
        operating_hours = request.form['operating_hours']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO exchange (exchange_id, currency, exchange_name, country, operating_hours)
            VALUES (%s, %s, %s, %s, %s)
        """, (exchange_id, currency, exchange_name, country, operating_hours))
        mysql.connection.commit()  # Commit the transaction
        cursor.close()
        return redirect(url_for('view_exchanges'))

    return render_template('add_exchange.html')

# Route to edit an exchange
@app.route('/edit_exchange/<string:exchange_id>', methods=['GET', 'POST'])
def edit_exchange(exchange_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cursor = mysql.connection.cursor()

    # Check if the form was submitted to update the exchange
    if request.method == 'POST':
        currency = request.form['currency']
        exchange_name = request.form['exchange_name']
        country = request.form['country']
        operating_hours = request.form['operating_hours']

        cursor.execute("""
            UPDATE exchange 
            SET currency = %s, exchange_name = %s, country = %s, operating_hours = %s
            WHERE exchange_id = %s
        """, (currency, exchange_name, country, operating_hours, exchange_id))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('view_exchanges'))

    # If it's a GET request, fetch the current exchange details to show in the form
    cursor.execute("SELECT * FROM exchange WHERE exchange_id = %s", (exchange_id,))
    exchange = cursor.fetchone()
    cursor.close()

    return render_template('edit_exchange.html', exchange=exchange)


# Route to delete an exchange
@app.route('/delete_exchange/<exchange_id>', methods=['GET','POST'])
def delete_exchange(exchange_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM exchange WHERE exchange_id = %s", (exchange_id,))
    mysql.connection.commit()  # Commit the transaction
    cursor.close()
    return redirect(url_for('view_exchanges'))
# Route to view transactions
@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        # Retrieve form data
        order_id = request.form['order_id']
        trans_id = request.form['trans_id']
        portfolio_id = request.form.get('portfolio_id', None)
        total_amt = request.form.get('total_amt', None)
        trans_type = request.form['trans_type']
        t_date = request.form['t_date']
        qty = request.form.get('qty', None)
        price_per_share = request.form.get('price_per_share', None)

        # Insert the transaction into the transaction table
        cur = mysql.connection.cursor()

        # Insert transaction into the transaction_ table
        cur.execute(
            """
            INSERT INTO transaction_ (order_id, trans_id, portfolio_id, total_amt, trans_type, t_date, qty, price_per_share)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (order_id, trans_id, portfolio_id, total_amt, trans_type, t_date, qty, price_per_share)
        )

        # Commit the changes and close the cursor
        mysql.connection.commit()
        cur.close()

        # Redirect to view_transactions page after successful addition
        return redirect(url_for('view_transactions'))

    # Render the form template if request method is GET
    return render_template('add_transaction.html')

@app.route('/view_transactions')
@login_required
def view_transactions():
    # Fetch all transactions from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM transaction_")
    transactions = cur.fetchall()
    cur.close()
    # Render the transactions view
    return render_template('view_transactions.html', transactions=transactions)

@app.route('/delete_transaction/<transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    if session.get('role') != 'admin':
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('user_dashboard'))
    try:
        # Create a cursor object to interact with the database
        cur = mysql.connection.cursor()
        
        # SQL query to delete the transaction based on the transaction_id
        cur.execute("DELETE FROM transaction_ WHERE trans_id = %s", (transaction_id,))
        
        # Commit the changes to the database
        mysql.connection.commit()
        
        # Close the cursor
        cur.close()
        
        # Redirect to the view_transactions page after successful deletion
        return redirect(url_for('view_transactions'))
    except Exception as e:
        # In case of error, print the error (you can handle this better with logging)
        print(f"Error deleting transaction: {e}")
        return redirect(url_for('view_transactions'))


@app.route('/update_portfolio_values', methods=['POST'])
@login_required
def update_portfolio_values():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT user_id FROM portfolio")
    user_ids = cur.fetchall()

    # Loop through each user_id and call the stored procedure
    for user_id in user_ids:
        try:
            # Call the stored procedure to update the portfolio value for each user
            cur.callproc('update_portfolio_value', [user_id[0]])
            mysql.connection.commit()  # Commit changes to the database
        except Exception as e:
            flash(f"Error updating portfolio for user {user_id[0]}: {str(e)}", 'warning')

    flash("Portfolio values updated successfully.", 'success')

    try:
        # In case of any database error during the process
        pass
    except mysql.connector.Error as err:
        flash(f"Database error: {str(err)}", 'warning')

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()

    return redirect(url_for('view_portfolios'))  # Redirect to the view portfolios page

import uuid # Add this import at the top of your file
import uuid # Add to the top of your app.py if it's not there
#
# --- 2. USER PORTFOLIO ROUTE (FINAL VERSION) ---
#
#
# --- 2. USER PORTFOLIO ROUTE (FINAL VERSION) ---
#
@app.route('/my_portfolio')
@login_required
def my_portfolio():
    # This route is for regular users.
    if session.get('role') == 'admin':
        return redirect(url_for('view_portfolios'))
    
    logged_in_user_id = session.get('user_id')
    
    if not logged_in_user_id:
        flash("Could not identify user. Please log in again.", "danger")
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor()
    
    # This query securely finds the user's portfolio by joining the tables
    # on the unique userID, which is the correct approach.
    cursor.execute("""
        SELECT p.portfolio_id, p.portfolio_name, p.portfolio_value, p.risk_level, 
               COUNT(c.stock_id) AS stock_count, p.portfolio_status, p.created_date
        FROM portfolio p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN contains c ON p.portfolio_id = c.portfolio_id
        WHERE u.user_id = %s

        GROUP BY p.portfolio_id
    """, (logged_in_user_id,))
    
    portfolios = cursor.fetchall()
    cursor.close()

    return render_template('my_portfolio.html', portfolios=portfolios)

#
# --- 3. TRADE EXECUTION ROUTE (FINAL VERSION) ---
#
@app.route('/execute_trade', methods=['POST'])
@login_required
def execute_trade():
    stock_id = request.form['stock_id']
    quantity = int(request.form['quantity'])
    action = request.form['action']
    logged_in_user_id = session['user_id']  # should now be like 'U003'
    print("Session user_id:", logged_in_user_id)

    cursor = mysql.connection.cursor()

    try:
        # 1. Find portfolio for this user
        cursor.execute("""
            SELECT p.portfolio_id 
            FROM portfolio p
            JOIN user u ON p.user_id = u.user_id 
            WHERE u.user_id = %s
            LIMIT 1
        """, (logged_in_user_id,))
        portfolio_result = cursor.fetchone()

        if not portfolio_result:
            raise Exception("Portfolio not found for your account.")
        portfolio_id = portfolio_result[0]
        print("Portfolio ID:", portfolio_id)

        # 2. Get stock price
        cursor.execute("SELECT market_price FROM stock WHERE stock_id = %s", (stock_id,))
        stock_row = cursor.fetchone()
        if not stock_row:
            raise Exception(f"Stock {stock_id} not found.")
        market_price = stock_row[0]
        print("Market price:", market_price)

        # 3. Get account balance
        cursor.execute("SELECT balance FROM trading_account WHERE user_id = %s", (logged_in_user_id,))
        bal_row = cursor.fetchone()
        if not bal_row:
            raise Exception(f"No trading account found for {logged_in_user_id}")
        balance = bal_row[0]
        print("Balance before trade:", balance)

        # 4. Calculate cost
        total_cost = quantity * market_price
        print("Total cost:", total_cost)

        # --- Validation ---
        if action == 'Sell':
            cursor.execute("SELECT quantity FROM contains WHERE portfolio_id = %s AND stock_id = %s", 
                           (portfolio_id, stock_id))
            holding = cursor.fetchone()
            if not holding or holding[0] < quantity:
                raise Exception("You do not own enough shares to sell.")

        if action == 'Buy' and balance < total_cost:
            raise Exception("Insufficient funds to complete this purchase.")

        # --- Insert order + transaction ---
        order_id = str(uuid.uuid4())[:15]
        trans_id = str(uuid.uuid4())[:15]

        cursor.execute("""
            INSERT INTO order_table (order_id, order_type, qty, price, order_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, action, quantity, market_price, 'COMPLETED'))
        print("Order insert rows:", cursor.rowcount)
        # ✅ NEW: Insert into buy_sell
        cursor.execute("""
          INSERT INTO buy_sell (stock_id, order_id)
          VALUES (%s, %s)
          """, (stock_id, order_id))
        print("Buy_sell insert rows:", cursor.rowcount)

        cursor.execute("""
            INSERT INTO transaction_ (order_id, trans_id, portfolio_id, total_amt, trans_type, t_date, qty, price_per_share)
            VALUES (%s, %s, %s, %s, %s, CURDATE(), %s, %s)
        """, (order_id, trans_id, portfolio_id, total_cost, action, quantity, market_price))
        print("Transaction insert rows:", cursor.rowcount)

        # --- Update balances and holdings ---
        if action == 'Buy':
            cursor.execute("UPDATE trading_account SET balance = balance - %s WHERE user_id = %s", 
                           (total_cost, logged_in_user_id))
            print("Balance update rows (Buy):", cursor.rowcount)

            cursor.execute("""
                INSERT INTO contains (portfolio_id, stock_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """, (portfolio_id, stock_id, quantity))
            print("Contains upsert rows:", cursor.rowcount)

        else:  # Sell
            cursor.execute("UPDATE trading_account SET balance = balance + %s WHERE user_id = %s", 
                           (total_cost, logged_in_user_id))
            print("Balance update rows (Sell):", cursor.rowcount)

            cursor.execute("UPDATE contains SET quantity = quantity - %s WHERE portfolio_id = %s AND stock_id = %s", 
                           (quantity, portfolio_id, stock_id))
            print("Contains update rows:", cursor.rowcount)

        # 5. Update portfolio total value
        cursor.callproc('update_portfolio_value', [portfolio_id])
        print("Portfolio value procedure executed.")

        mysql.connection.commit()
        flash("Trade successfully executed!", "success")

    except Exception as e:
        print("Trade error:", str(e))  # Debug: log error
        mysql.connection.rollback()
        flash(f"Trade failed: {str(e)}", "danger")

    finally:
        cursor.close()

    return redirect(url_for('my_portfolio'))


if __name__ == '__main__':
    app.run(port=5002, debug=True)  # Start the Flask app on port 5001
