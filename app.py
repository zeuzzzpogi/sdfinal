from flask import Flask, render_template, request, redirect, session, url_for, flash
import json
from quiz_db import init_db, save_question
from quiz_db import save_student_answer
import sqlite3
from exam_db import init_db, save_question
from exam_db import save_student_answer
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file


def generate_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Quiz Score Report")

    pdf.setFont("Helvetica", 12)
    y = height - 80
    pdf.drawString(50, y, "Student ID")
    pdf.drawString(150, y, "Date")
    pdf.drawString(300, y, "Total Score")
    pdf.drawString(400, y, "Partial Score")
    y -= 20

    for row in data:
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, str(row[0]))
        pdf.drawString(150, y, str(row[1]))
        pdf.drawString(300, y, str(row[2]))
        pdf.drawString(400, y, str(row[3]))
        y -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='quiz_scores.pdf', mimetype='application/pdf')


app = Flask(__name__)
app.secret_key = 'secretkey'

# Initialize the database
init_db()

admin_users = {
    "alexakate": {
        "name": "Alexa Kate B. Mamato",
        "email": "alexa@example.com",
        "password": "yourpassword123"
    },
    "desserei": {
        "name": "Ma. Desserei C. Emaas",
        "email": "desserei@example.com",
        "password": "01234567"
    }
}

student_users = {}

@app.route('/')
def home():
    if 'admin_name' in session:
        return redirect(url_for('admin_home'))
    else:
        return render_template('select_role.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']
        user = admin_users.get(admin_id)
        if user and user['password'] == password:
            session['admin_name'] = user['name']
            return redirect(url_for('admin_home'))
        else:
            flash("Invalid Admin ID or Password. Please try again.")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    reset_stage = False
    admin_info = None
    if request.method == 'POST':
        if 'username' in request.form:
            username = request.form['username']
            if username in admin_users:
                session['reset_user'] = username
                admin_info = admin_users[username]
                reset_stage = True
            else:
                flash("No account found with that username.")
                return redirect(url_for('forgot_password'))
        else:
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if new_password != confirm_password:
                flash("Passwords do not match.")
                reset_stage = True
                admin_info = admin_users.get(session.get('reset_user'))
            else:
                admin_users[session['reset_user']]['password'] = new_password
                flash("Password successfully reset.")
                session.pop('reset_user', None)
                return redirect(url_for('admin_login'))

    return render_template(
        'admin_forgot_password.html',
        reset_stage=reset_stage,
        admin_info=admin_info
    )

@app.route('/admin/home')
def admin_home():
    admin_name = session.get('admin_name', 'Admin')
    return render_template('admin_home.html', admin_name=admin_name)

@app.route('/attendance')
def attendance_page():
    return render_template('index.html', active_tab='attendance')

@app.route('/quiz')
def quiz_page():
    return render_template('quiz_page.html')

@app.route('/exam')
def exam_page():
    return render_template('index.html', active_tab='exam')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', records=records)

records = []
student_number = 1

@app.route('/admin/add', methods=["POST"])
def add_student():
    global student_number
    student_id = f"{student_number:05d}"
    name = request.form['name']
    attendance = request.form['attendance']
    quiz_score = int(request.form['quiz_score'])
    exam_score = int(request.form['exam_score'])

    records.append({
        "id": student_id,
        "name": name,
        "attendance": attendance,
        "quiz_score": quiz_score,
        "exam_score": exam_score
    })
    student_number += 1
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<student_id>')
def delete(student_id):
    global records
    records = [r for r in records if r["id"] != student_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<student_id>', methods=["GET", "POST"])
def edit(student_id):
    record = next((r for r in records if r["id"] == student_id), None)
    if request.method == "POST":
        if record:
            record["name"] = request.form["name"]
            record["attendance"] = request.form["attendance"]
            record["quiz_score"] = int(request.form["quiz_score"])
            record["exam_score"] = int(request.form["exam_score"])
        return redirect(url_for('admin_dashboard'))
    return render_template("edit.html", record=record)

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match")
        else:
            admin_users[username] = {
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password
            }
            return redirect(url_for('admin_home'))
    return render_template('admin_signup.html')

@app.route('/student_logout')
def student_logout():
    session.clear()
    flash("Student logged out successfully.")
    return redirect(url_for('student_login'))  # or wherever your student login page is

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    flash("Admin logged out successfully.")
    return redirect(url_for('admin_login'))  # or wherever your admin login page is

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        user = student_users.get(student_id)
        if user and user['password'] == password:
            session['student_name'] = user['full_name']
            session['student_id'] = student_id
            return redirect(url_for('student_home'))
        else:
            flash('Invalid username or password')
    return render_template('student_login.html')

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        school_email = request.form['school_email']
        student_id = request.form['student_id']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match")
        else:
            student_users[student_id] = {
                "full_name": full_name,
                "school_email": school_email,
                "username": username,
                "password": password
            }
            return redirect(url_for('student_login'))
    return render_template('student_signup.html')

@app.route('/student/home')
def student_home():
    student_name = session.get('student_name', 'Student')
    return render_template('student_home.html', student_name=student_name)

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        questions = request.form.getlist('questions[]')
        question_types = request.form.getlist('types[]')
        options_list = request.form.getlist('options[]')
        answers = request.form.getlist('answers[]')

        for i in range(len(questions)):
            q_type = question_types[i]
            q_text = questions[i]
            options = json.dumps(options_list[i].split(',')) if q_type == "mcq" else None
            answer = answers[i]
            save_question(q_type, q_text, options, answer)

        flash("Quiz successfully created!")
        return redirect(url_for('create_quiz'))

    return render_template('create_quiz.html')


@app.route('/export_quizzes')
def export_quiz_data():
    export_type = request.args.get('type', 'csv')  # Default to CSV
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM quiz_scores
        GROUP BY student_id, submission_date
    ''')
    data = c.fetchall()
    conn.close()

    if export_type == 'pdf':
        return generate_pdf(data)
    else:
        return generate_csv(data)

@app.route('/submit_answers', methods=['POST'])
def submit_answers():
    student_id = request.form['student_id']
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('SELECT * FROM quiz')
    questions = c.fetchall()

    for question in questions:
        q_id = question[0]
        q_type = question[1]
        correct_answer = question[4]
        submitted_answer = request.form.get(f'q_{q_id}', '')

        if q_type == 'mcq':
            is_correct = 1 if submitted_answer.strip().lower() == correct_answer.strip().lower() else 0
            score = 1 if is_correct else 0
            graded = 1
        else:
            is_correct = None
            score = 0
            graded = 0  # Manual grading needed

        save_student_answer(student_id, q_id, submitted_answer, is_correct, score, graded)

    conn.close()
    flash("Your answers have been submitted successfully.")
    return redirect(url_for('home'))  # Later redirect to student results page

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if request.method == 'POST':
        questions = request.form.getlist('questions[]')
        question_types = request.form.getlist('types[]')
        options_list = request.form.getlist('options[]')
        answers = request.form.getlist('answers[]')

        for i in range(len(questions)):
            q_type = question_types[i]
            q_text = questions[i]
            options = json.dumps(options_list[i].split(',')) if q_type == "mcq" else None
            answer = answers[i]
            save_question(q_type, q_text, options, answer)

        flash("Exam successfully created!")
        return redirect(url_for('create_exam'))

    return render_template('create_exam.html')


@app.route('/export_exams')
def export():
    export_type = request.args.get('type', 'csv')  # Default to CSV
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM exam_scores
        GROUP BY student_id, submission_date
    ''')
    data = c.fetchall()
    conn.close()

    if export_type == 'pdf':
        return generate_pdf(data)
    else:
        return generate_csv(data)

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    student_id = request.form['student_id']
    conn = sqlite3.connect('exam.db')
    c = conn.cursor()
    c.execute('SELECT * FROM exam')
    questions = c.fetchall()

    for question in questions:
        q_id = question[0]
        q_type = question[1]
        correct_answer = question[4]
        submitted_answer = request.form.get(f'q_{q_id}', '')

        if q_type == 'mcq':
            is_correct = 1 if submitted_answer.strip().lower() == correct_answer.strip().lower() else 0
            score = 1 if is_correct else 0
            graded = 1
        else:
            is_correct = None
            score = 0
            graded = 0  # Manual grading needed

        save_student_answer(student_id, q_id, submitted_answer, is_correct, score, graded)

    conn.close()
    flash("Your answers have been submitted successfully.")
    return redirect(url_for('home'))  # Later redirect to student results page

@app.route('/view_records')
def view_records():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        SELECT student_id, submission_date,
               SUM(CASE WHEN graded = 1 THEN score ELSE 0 END) as total_score,
               SUM(CASE WHEN is_correct = 1 THEN score ELSE 0 END) as partial_score
        FROM quiz_scores
        GROUP BY student_id, submission_date
    ''')
    data = c.fetchall()
    conn.close()

    records = []
    for row in data:
        records.append({
            "student_id": row[0],
            "submission_date": row[1],
            "total_score": row[2],
            "partial_score": row[3]
        })

    return render_template('view_records.html', records=records)


@app.route('/grade_answer', methods=['POST'])
def grade_answer():
    score_id = request.form['score_id']
    new_score = request.form['score']

    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        UPDATE quiz_scores
        SET score = ?, graded = 1
        WHERE id = ?
    ''', (new_score, score_id))
    conn.commit()
    conn.close()

    flash("Answer graded successfully!")
    return redirect(url_for('view_records'))

import pandas as pd
from flask import make_response

def generate_csv(data):
    df = pd.DataFrame(data, columns=['Student ID', 'Date', 'Total Score', 'Partial Score'])
    response = make_response(df.to_csv(index=False))
    response.headers['Content-Disposition'] = 'attachment; filename=quiz_scores.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


if __name__ == '__main__':
    app.run(debug=True)