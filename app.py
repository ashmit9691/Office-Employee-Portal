from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


# Initialize the database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    # ✅ New logins table to store login activity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')

    # seed one default admin if none exists
    cursor.execute('SELECT 1 FROM admins LIMIT 1')
    if not cursor.fetchone():
        cursor.execute(
            'INSERT INTO admins (username, password) VALUES (?, ?)',
            ('admin', 'admin123')
        )
        conn.commit()
        print('✅ Default admin seeded (admin / admin123)')

    conn.commit()
    conn.close()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()

# Save user to database in users table
def save_user(username, email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                   (username, email, password))
    conn.commit()
    conn.close()

# Save user to database in admins table
def save_admin(username, password):
    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO admins (username, password) VALUES (?, ?)',
            (username, password)
        )
        conn.commit()


# Routes
@app.route("/")
def index():                 
    return render_template("index.html")

@app.route('/Employee_Login', methods=['GET'])
def signup_form():
    return render_template('SignUp_LogIn_Form.html')

@app.route('/Employee_login', methods=['POST'])
def register_submit():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if username and email and password:
        save_user(username, email, password)
        print(f"Saved: {username}, {email}, {password}")
    else:
        print("Some fields were empty!")

    return redirect(url_for('signup_form'))

@app.route('/admin', methods=['GET'])
def admin_form():
    return render_template('admin_login.html')

@app.route('/admin_dashboard', methods=['POST'])
def admin_dashboard_form():
    return render_template('admin_dashboard.html')

@app.route('/admin_login', methods=['POST'])
def admin_login_form():
    username = request.form.get('username')
    password = request.form.get('password')

    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM admins WHERE username=? AND password=?",
            (username, password)
        )
        admin = cur.fetchone()

    if admin:
        print(f"✅ Admin logged in: {username}")
        return redirect(url_for('admin_dashboard'))
    else:
        print("❌ Invalid admin credentials")
        return redirect(url_for('admin_form'))

@app.route("/admin_dashboard")
def admin_dashboard():                
    return render_template("admin_dashboard.html")

@app.route('/users')
def view_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return render_template('users.html', users=users)

@app.route('/login', methods=['POST'])
def login_submit():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()

    if user:
        # ✅ Append login info to logins table
        cursor.execute('INSERT INTO logins (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        print(f"Login recorded for {username}")
        return redirect(url_for('view_users'))
    else:
        conn.close()
        print("Invalid login.")
        return redirect(url_for('signup_form'))
    

@app.route('/login_history')
def login_history():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, password, login_time FROM logins ORDER BY login_time DESC')
    logins = cursor.fetchall()
    conn.close()

    return render_template('login_history.html', logins=logins)




if __name__ == '__main__':
    init_db()  # initialize the database when app starts
    app.run(debug=True)    

print(app.url_map)

