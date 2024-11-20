from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import bcrypt

# Initialize Flask App
app = Flask(__name__)
app.secret_key = '240-677-713'  # Change this to a more secure secret key for production

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'bookshop'

# Initialize MySQL Connection
connection = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB'],
    cursorclass=pymysql.cursors.DictCursor,
)

# Routes

# Home Route: Displays all books (for both users and admins)
@app.route('/')
def index():
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM books")
        books = cur.fetchall()
    return render_template('index.html', books=books)

# Register Route: Allows users to register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        role = request.form.get('role', 'user')  # Default to 'user' if no role is provided

        with connection.cursor() as cur:
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                        (username, email, password, role))
            connection.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

# Login Route: Allows users to log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        with connection.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

            if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
                # Store user info in session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']  # Store the role in the session

                # Check if user is an admin
                if user['role'] == 'admin':
                    session['is_admin'] = True
                    return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
                else:
                    session['is_admin'] = False
                    return redirect(url_for('user_home'))  # Redirect to user home page
    return render_template('login.html')

# Admin Dashboard Route: Shows admin-specific content
@app.route('/admin/dashboard')
def admin_dashboard():
    # Ensure only admins can access this route
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))  # Redirect to login if the user is not an admin

    return render_template('admin_dashboard.html')

# User Home Route: Allows regular users to see books
@app.route('/user_home')
def user_home():
    # Ensure only regular users can access this route
    if 'is_admin' not in session or session['is_admin']:
        return redirect(url_for('login'))  # Redirect to login if the user is an admin

    with connection.cursor() as cur:
        cur.execute("SELECT * FROM books")
        books = cur.fetchall()
    
    return render_template('user_home.html', books=books)

# Admin Add Book Route: Allows admin users to add books
@app.route('/admin/add_book', methods=['GET', 'POST'])
def add_book():
    # Ensure only admins can access this route
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))  # Redirect to login if the user is not an admin

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publisher = request.form['publisher']

        with connection.cursor() as cur:
            cur.execute("INSERT INTO books (title, author, publisher) VALUES (%s, %s, %s)", (title, author, publisher))
            connection.commit()

        return redirect(url_for('index'))

    return render_template('add_book.html')

# Logout Route: Logs the user out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
