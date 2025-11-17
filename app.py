from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import mysql.connector

app = Flask(__name__)
app.secret_key = "super_secret_key_2025"  # ✅ Ensure this exists, or session won't persist

# ✅ Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="11d41F@0031",
    database="CMS"
)
cursor = db.cursor(dictionary=True)



# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll = request.form.get('roll')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        branch = request.form.get('branch')

        if password != confirm:
            flash("Passwords do not match ❌", "danger")
            return redirect(url_for('register'))

        cursor.execute("SELECT * FROM register WHERE roll=%s OR email=%s", (roll, email))
        if cursor.fetchone():
            flash("User already exists ❌", "danger")
            return redirect(url_for('register'))

        now = datetime.now()
        cursor.execute("""
            INSERT INTO register (roll, name, email, password, branch, last_login, last_logout)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (roll, name, email, password, branch, now, None))
        db.commit()

        flash(f"Account created successfully ✅ Welcome, {name}!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor.execute("SELECT * FROM register WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        if user:
            # ✅ Save user info in session (must have secret_key)
            session['user_id'] = user['id']
            session['roll'] = user['roll']
            session['name'] = user['name']
            session['email'] = user['email']

            now = datetime.now()
            cursor.execute("UPDATE register SET last_login=%s WHERE id=%s", (now, user['id']))
            db.commit()

            flash(f"Welcome back, {user['name']} ✅", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password ❌", "danger")
            return redirect(url_for('login'))

    # ✅ If already logged in, go directly to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    return render_template('login.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    # ✅ Verify session first
    if 'user_id' not in session:
        flash("Please login to access dashboard ❌", "warning")
        return redirect(url_for('login'))

    user_name = session.get('name')
    roll = session.get('roll')
    email = session.get('email')

    # ✅ Renders dashboard.html successfully
    return render_template('dashboard.html', name=user_name, roll=roll, email=email)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    if 'user_id' in session:
        now = datetime.now()
        cursor.execute("UPDATE register SET last_logout=%s WHERE id=%s", (now, session['user_id']))
        db.commit()

    session.clear()
    flash("Logged out successfully ✅", "success")
    return redirect(url_for('login'))



# ---------------- STUDENTS ----------------
@app.route('/students')
def students_view():
    cursor = db.cursor()  # Make sure you create a cursor here
    cursor.execute("SELECT roll, name, email, branch FROM register")
    students = cursor.fetchall()  # This returns list of tuples: [(roll, name, email, branch), ...]
    return render_template('students.html', students=students)



# Display courses page
@app.route('/courses', methods=['GET'])
def courses():
    cursor.execute("""
        SELECT course_code, course_name, credits, faculty, duration, description
        FROM courses
    """)
    courses_data = cursor.fetchall()  # This returns a list of dicts if DictCursor is used

    # Convert DB dicts to list of dicts for JS
    courses_list = [
        {
            "code": row["course_code"],
            "name": row["course_name"],
            "credits": row["credits"],
            "faculty": row["faculty"],
            "duration": row["duration"],
            "description": row["description"]
        }
        for row in courses_data
    ]

    return render_template('courses.html', courses=courses_list)

# API route to add a course dynamically
@app.route('/add_course', methods=['POST'])
def add_course():
    data = request.json
    cursor.execute("""
        INSERT INTO courses (course_code, course_name, credits, faculty, duration, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data['code'], data['name'], data['credits'], 
        data['faculty'], data['duration'], data['description']
    ))
    db.commit()
    return jsonify({"status": "success", "message": "Course added!"})





@app.route('/fees', methods=['GET', 'POST'])
def fees():
    student = None
    installments = []

    # --------------------------------------
    # 1️⃣ SEARCH FEES
    # --------------------------------------
    if request.method == 'POST' and request.form.get("search"):

        roll = request.form.get('roll', '').strip()
        name = request.form.get('name', '').strip()

        if not roll and not name:
            flash("Please enter Roll No or Name ⚠️", "warning")
            return redirect(url_for('fees'))

        cursor.execute("""
            SELECT 
                f.student_name, 
                f.student_roll, 
                f.email, 
                f.total_fee,
                COALESCE(SUM(i.paid_fee), 0) AS paid_fee,
                f.total_fee - COALESCE(SUM(i.paid_fee), 0) AS balance,
                MAX(i.payment_date) AS last_payment
            FROM fees f
            LEFT JOIN fees_installments i 
                ON f.student_roll = i.student_roll
            WHERE (%s != '' AND f.student_roll LIKE %s)
               OR (%s != '' AND f.student_name LIKE %s)
            GROUP BY f.student_name, f.student_roll, f.email, f.total_fee
        """, (roll, '%' + roll + '%', name, '%' + name + '%'))

        student = cursor.fetchone()

        if not student:
            flash("No student found ❌", "danger")
            return redirect(url_for('fees'))

        # Fetch installment history
        cursor.execute("""
            SELECT installment_no, paid_fee, payment_date 
            FROM fees_installments 
            WHERE student_roll=%s 
            ORDER BY installment_no ASC
        """, (student[1],))
        installments = cursor.fetchall()

    # --------------------------------------
    # 2️⃣ PAY FEES
    # --------------------------------------
    elif request.method == 'POST' and request.form.get("pay"):

        pay_roll = request.form.get('pay_roll', '').strip()
        pay_amount = request.form.get('pay_amount', '').strip()

        if not pay_roll or not pay_amount:
            flash("Enter Roll No and Amount ⚠️", "warning")
            return redirect(url_for('fees'))

        try:
            pay_amount = float(pay_amount)
        except:
            flash("Invalid fee amount ❌", "danger")
            return redirect(url_for('fees'))

        cursor.execute("SELECT student_name, email, total_fee FROM fees WHERE student_roll=%s", (pay_roll,))
        student_data = cursor.fetchone()

        if not student_data:
            flash("Student not found ❌", "danger")
            return redirect(url_for('fees'))

        cursor.execute("SELECT MAX(installment_no) FROM fees_installments WHERE student_roll=%s", (pay_roll,))
        last = cursor.fetchone()
        installment_no = (last[0] if last and last[0] else 0) + 1

        cursor.execute("""
            INSERT INTO fees_installments (student_roll, paid_fee, installment_no, payment_date)
            VALUES (%s, %s, %s, %s)
        """, (pay_roll, pay_amount, installment_no, datetime.now()))

        db.commit()

        flash(f"Payment Successful! Installment {installment_no} of ₹{pay_amount} added ✅", "success")
        return redirect(url_for('fees'))

    return render_template('fees.html', student=student, installments=installments)






# --------------------- ADD MARKS FORM ---------------------
@app.route('/addmarks', methods=['GET', 'POST'])
def add_marks():
    if request.method == 'POST':
        roll = request.form.get('roll', '').strip()
        course = request.form.get('course', '').strip()
        branch = request.form.get('branch', '').strip()
        marks_raw = request.form.get('marks', '').strip()

        if not (roll and course and branch and marks_raw):
            flash("All fields are required.", "danger")
            return redirect(url_for('add_marks'))

        try:
            marks = int(marks_raw)
            if marks < 0 or marks > 100:
                raise ValueError("Marks must be between 0 and 100.")
        except Exception as e:
            flash(f"Invalid marks value: {e}", "danger")
            return redirect(url_for('add_marks'))

        try:
            cursor.execute("SELECT roll FROM register WHERE roll=%s", (roll,))
            student = cursor.fetchone()

            if not student:
                flash("Student not found in REGISTER table! Please register first.", "danger")
            else:
                cursor.execute("""
                    INSERT INTO marks (roll, course, branch, marks)
                    VALUES (%s, %s, %s, %s)
                """, (roll, course, branch, marks))
                db.commit()
                flash("Marks added successfully ✅", "success")

        except Exception as e:
            db.rollback()
            flash(f"Database error while adding marks: {e}", "danger")

        return redirect(url_for('add_marks'))

    return render_template('marks.html')

  


# --------------------- SEARCH STUDENT MARKS ---------------------
@app.route('/marks', methods=['GET', 'POST'])
def marks_page():
    student = None
    marks = []
    summary = None

    if request.method == 'POST':
        roll = request.form.get('roll', '').strip()
        email = request.form.get('email', '').strip()

        if not (roll and email):
            flash("Roll and Email are required.", "danger")
            return redirect(url_for('marks_page'))

        try:
            # FIXED COLUMN NAMES: register table uses roll, name, branch, email
            cursor.execute("""
                SELECT roll, name, branch, email 
                FROM register
                WHERE roll=%s AND email=%s
            """, (roll, email))

            student = cursor.fetchone()

            if student:
                cursor.execute("""
                    SELECT course, branch, marks 
                    FROM marks 
                    WHERE roll=%s
                """, (roll,))
                data = cursor.fetchall()

                for row in data:
                    course = row["course"]
                    branch = row["branch"]
                    score = int(row["marks"])

                    if 75 <= score <= 98:
                        grade = "A+"
                        message = "Excellent performance! Keep it up."
                    elif 60 <= score < 75:
                        grade = "B"
                        message = "Good score! You can do even better."
                    elif 40 <= score < 55:
                        grade = "C"
                        message = "Average performance. Needs improvement."
                    else:
                        grade = "D"
                        message = "Fail — Please study harder."

                    marks.append({
                        "course": course,
                        "branch": branch,
                        "marks": score,
                        "grade": grade,
                        "message": message
                    })

                if marks:
                    total = sum(m['marks'] for m in marks)
                    percentage = round(total / len(marks), 2)
                    result = "PASS" if percentage >= 40 else "FAIL"

                    summary = {
                        "total": total,
                        "percentage": percentage,
                        "result": result
                    }

            else:
                flash("No student found in REGISTER table ❌", "danger")

        except Exception as e:
            flash(f"Database error while searching: {e}", "danger")

    return render_template('marks.html', student=student, marks=marks, summary=summary)

@app.route('/student/<roll>')
def student_profile(roll):
    cursor.execute("SELECT roll, name FROM register WHERE roll = %s", (roll,))
    student = cursor.fetchone()

    if not student:
        return "Student not found"

    return render_template("marks.html", student=student)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
