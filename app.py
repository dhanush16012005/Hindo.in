import os
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime  # Add this import


# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Set up the Flask app
app = Flask(__name__)
app.secret_key = 'a3f5e8d5a1c3b4e6f7d8c9a0b2c4d6e8'  # Replace with your generated secret key

# Set the absolute path to the database in the instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath(os.path.join('instance', 'hindo.db'))}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)

def get_db_connection():
    db_path = os.path.abspath(os.path.join('instance', 'hindo.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def send_email(to_email, password):
    from_email = "mukilan987654321@gmail.com"
    from_password = "vovk dshr wxjt tglv"
    subject = "Your New Password"
    body = f"Your new password is: {password}"
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.close()
        print(f"Email sent to {to_email}")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return render_template("index.html", logged_in=False)
    curr_user = User.query.get(session['user_id'])
    return render_template("index.html", logged_in=True, curr_user=curr_user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/student_dashboard')

@app.route('/meeting')
def meeting():
    if 'user_id' not in session:
        flash('You need to login first.', 'error')
        return redirect('/login_page')

    user_email = session.get('user_email')
    user_name = session.get('user_name')
    return render_template("meeting.html", user_email=user_email, user_name=user_name)

@app.route('/join', methods=['GET', 'POST'])
def join_meeting():
    if 'user_id' not in session:
        flash('You need to login first.', 'error')
        return redirect('/login_page')

    if request.method == 'POST':
        meeting_id = request.form.get('room_id')
        return redirect(f'/meeting?roomID={meeting_id}')
    return render_template("join_meeting.html")

@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"Login attempt for email: {email}")  # Debug: Log email

        # Special case for admin login
        if email == 'deepakvaroon@gmail.com' and password == 'deepakvaroon123':
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        conn = get_db_connection()
        c = conn.cursor()

        # Check students database
        c.execute('SELECT * FROM students WHERE email = ?', (email,))
        student = c.fetchone()

        print(f"Student found: {student}")  # Debug: Log student query result

        if student:
            if student['password'] == password:
                session['user_id'] = student['id']
                session['user_email'] = student['email']
                session['user_name'] = student['email'].split('@')[0]  # Extract username from email
                session['user_role'] = 'student'
                flash('Login successful!', 'success')
                conn.close()
                return redirect(url_for('student_dashboard'))
            else:
                print("Incorrect password for student")  # Debug: Incorrect password
                flash('Incorrect password. Please try again.', 'error')
                conn.close()
                return redirect(url_for('login_page'))

        # Check recruited_table for teachers
        c.execute('SELECT * FROM recruited_table WHERE email = ?', (email,))
        recruited_teacher = c.fetchone()

        print(f"Recruited teacher found: {recruited_teacher}")  # Debug: Log recruited teacher query result

        if recruited_teacher:
            if recruited_teacher['password'] == password:
                session['user_id'] = recruited_teacher['id']
                session['user_email'] = recruited_teacher['email']
                session['teacher_id'] = recruited_teacher['id']
                session['user_name'] = recruited_teacher['email'].split('@')[0]
                session['user_role'] = 'teacher'
                flash('Login successful!', 'success')
                conn.close()
                return redirect(url_for('instructor_dashboard'))
            else:
                print("Incorrect password for recruited teacher")  # Debug: Incorrect password
                flash('Incorrect password. Please try again.', 'error')
                conn.close()
                return redirect(url_for('login_page'))

        flash('Incorrect email or password. Please try again.', 'error')
        conn.close()
        return redirect(url_for('login_page'))

    return render_template('login_page.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    student_row = conn.execute('SELECT * FROM students WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if student_row is None:
        return 'Student not found!', 404

    student = dict(student_row)
    return render_template('student_dashboard.html', student=student)

@app.route('/instructor_dashboard')
def instructor_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM recruited_table WHERE id = ?', (user_id,))
    teacher = c.fetchone()

    # Fetch students studying under the instructor
    c.execute('SELECT * FROM students WHERE teacher_id = ?', (user_id,))
    students = c.fetchall()

    # Fetch the instructor's schedule
    c.execute('SELECT * FROM batches WHERE teacher_id = ?', (user_id,))
    schedule = c.fetchall()

    conn.close()

    if not teacher:
        flash('User not found.', 'error')
        return redirect(url_for('login_page'))

    return render_template('instructor_dashboard.html', teacher=teacher, students=students, schedule=schedule)


@app.route('/profile')
def profile_page():
    if 'user_id' not in session:
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    role = session.get('user_role')

    conn = get_db_connection()
    c = conn.cursor()

    if role == 'student':
        c.execute('SELECT * FROM students WHERE id = ?', (user_id,))
        user = c.fetchone()
    elif role == 'teacher':
        c.execute('SELECT * FROM recruited_table WHERE id = ?', (user_id,))
        user = c.fetchone()
    else:
        flash('Invalid user role.', 'error')
        return redirect(url_for('login_page'))

    conn.close()

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login_page'))

    return render_template('profile.html', user=user, role=role)

@app.route('/student_registration', methods=['GET', 'POST'])
def registration_page():
    course_payment_links = {
        "Basic Hindi Reading and Writing Course": "https://rzp.io/l/FA4CWR0Mm",
        "spoken Hindi": "https://rzp.io/l/ZQ6Pbrn",
        "Prathamic": "https://rzp.io/l/1GtocpCIot",
        "Madhyama": "https://rzp.io/l/dDRYRWtik",
        "RashtraBasha": "https://rzp.io/l/EGWMUZh",
        "praveshika": "https://rzp.io/l/nM5sgp8S7",
        "visharadh poorvardh": "https://rzp.io/l/S4Os8issJQ",
        "visharadh uttarardh": "https://rzp.io/l/Nc1pkX9i",
        "praveen poorvardh": "https://rzp.io/l/vrVMBEMK",
        "praveen uttarardh": "https://rzp.io/l/1NsqenxMW"
    }

    if request.method == 'POST':
        try:
            email = request.form['email']
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM students WHERE email = ?', (email,))
            existing_student = c.fetchone()

            if existing_student:
                conn.close()
                flash('User already exists. Try with a different email.', 'error')
                return redirect(url_for('registration_page'))
            
            fullname = request.form['fullname']
            dob = request.form['dob']
            gender = request.form['gender']
            status = request.form['status']
            institution = request.form['institution']
            language_proficiency = request.form['language_proficiency']
            course = request.form['course']
            active_batch_combined = request.form['active_batch']
            
            if active_batch_combined:
                batch_id, start_time, teacher_id = active_batch_combined.split('-')
                start_time = start_time.strip()
                teacher_id = teacher_id.strip()
            else:
                batch_id, start_time, teacher_id = None, None, None
            
            preferred_time = request.form['preferred_time']
            exam_preference = request.form['exam_preference']
            phone = request.form['phone']
            state = request.form['state']
            district = request.form['district']
            consent = 1 if 'consent' in request.form else 0

            # Generate and store the random password
            password = generate_random_password()

            # Insert statement with all 18 columns
            c.execute('''
                INSERT INTO students (fullname, dob, gender, status, institution, language_proficiency, course, batch_id, start_time, preferred_time, exam_preference, email, phone, state, district, consent, password, teacher_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fullname, dob, gender, status, institution, language_proficiency, course, batch_id, start_time, preferred_time, exam_preference, email, phone, state, district, consent, password, teacher_id))
            conn.commit()

            # Send email with the password
            send_email(email, password)

            conn.close()
            flash('Registration successful! Please check your email for your password.', 'success')

            # Redirect to the payment page based on the selected course
            payment_link = course_payment_links.get(course)
            if (payment_link):
                return redirect(payment_link)
            else:
                flash('No payment link found for the selected course.', 'error')
                return redirect(url_for('login_page'))

        except sqlite3.IntegrityError as e:
            conn.close()
            flash(f'SQLite Integrity Error: {str(e)}', 'error')
            return redirect(url_for('registration_page'))

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            flash(f'Unexpected error: {str(e)}', 'error')
            return redirect(url_for('registration_page'))

    return render_template('student_registration.html')


@app.route('/teacher_register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM teachers WHERE email = ?', (email,))
        existing_teacher = c.fetchone()

        if existing_teacher:
            conn.close()
            flash('Teacher already exists. Try with a different email.', 'error')
            return redirect(url_for('register_page'))
        
        fullname = request.form['fullname']
        qualification = request.form['qualification']
        language_proficiency = ', '.join(request.form.getlist('language_proficiency'))
        experience = request.form['experience']
        specializations = request.form['specializations']
        institution = request.form['institution']
        availability_from = request.form['availability_from']
        availability_to = request.form['availability_to']
        phone = request.form['phone']
        district = request.form['district']
        consent = 1 if 'consent' in request.form else 0

        # Generate and store the random password
        password = generate_random_password()

        try:
            c.execute('''
                INSERT INTO teachers (fullname, qualification, language_proficiency, experience, specializations, institution, availability_from, availability_to, email, phone, district, consent, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fullname, qualification, language_proficiency, experience, specializations, institution, availability_from, availability_to, email, phone, district, consent, password))
            conn.commit()

            # Send email with the password
            
            
        except sqlite3.IntegrityError as e:
            conn.close()
            flash(f'User already exists or an error occurred: {e}', 'error')
            return redirect(url_for('register_page'))
        
        conn.close()
        flash('Registration successful! Please check your email for your password and wait for admin approval.', 'success')
        return redirect(url_for('login_page'))
    
    return render_template('teacher_register.html')

@app.route('/send_passwords', methods=['POST'])
def send_passwords():
    email = request.form['email']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE email = ?', (email,))
    existing_student = c.fetchone()
    conn.close()
    
    if existing_student:
        flash('Password already sent to this email.')
    else:
        password = generate_random_password()
        send_email(email, password)
        # Store the email and password in the database
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO students (email, password)
                VALUES (?, ?)
            ''', (email, password))
            conn.commit()
            flash('Password sent to email.')
        except sqlite3.IntegrityError:
            flash('User already exists. Use a different email.')
        conn.close()
    
    return redirect(url_for('login_page'))

@app.route('/admin_dashboard')
def admin_dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM teachers')
    teachers = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', teachers=teachers)

@app.route('/recruit_teacher/<int:teacher_id>', methods=['POST'])
def recruit_teacher(teacher_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM teachers WHERE id = ?', (teacher_id,))
    teacher = c.fetchone()
    if teacher:
        password = generate_random_password()

        try:
            c.execute('''
                INSERT INTO recruited_table (id, fullname, email, qualification, language_proficiency, experience, specializations, institution, availability_from, availability_to, phone, district, consent, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (teacher['id'], teacher['fullname'], teacher['email'], teacher['qualification'], teacher['language_proficiency'], teacher['experience'], teacher['specializations'], teacher['institution'], teacher['availability_from'], teacher['availability_to'], teacher['phone'], teacher['district'], teacher['consent'], password))
            conn.commit()
            c.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
            conn.commit()

            send_email(teacher['email'], password)
            
            response = {'status': 'success', 'message': 'Teacher recruited successfully.'}
        except sqlite3.IntegrityError as e:
            response = {'status': 'error', 'message': f'Teacher already recruited. {str(e)}'}
        except Exception as e:
            response = {'status': 'error', 'message': str(e)}
        finally:
            conn.close()
    else:
        response = {'status': 'error', 'message': 'Teacher not found.'}
    return jsonify(response)

@app.route('/unrecruit_teacher/<int:teacher_id>', methods=['POST'])
def unrecruit_teacher(teacher_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Delete the teacher from the recruited_table
        c.execute('DELETE FROM recruited_table WHERE id = ?', (teacher_id,))
        # Insert the teacher back into the teachers table
        c.execute('SELECT * FROM recruited_table WHERE id = ?', (teacher_id,))
        recruited_teacher = c.fetchone()
        if recruited_teacher:
            c.execute('''
                INSERT INTO teachers (id, fullname, email, qualification, language_proficiency, experience, specializations, institution, availability_from, availability_to, phone, district, consent, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (recruited_teacher['id'], recruited_teacher['fullname'], recruited_teacher['email'], recruited_teacher['qualification'], recruited_teacher['language_proficiency'], recruited_teacher['experience'], recruited_teacher['specializations'], recruited_teacher['institution'], recruited_teacher['availability_from'], recruited_teacher['availability_to'], recruited_teacher['phone'], recruited_teacher['district'], recruited_teacher['consent'], recruited_teacher['password']))
            conn.commit()
        conn.commit()
        response = {'status': 'success', 'message': 'Teacher unrecruited and deleted successfully.'}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
    finally:
        conn.close()
    return jsonify(response)

@app.route('/api/get_teachers', methods=['GET'])
def get_teachers():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM teachers')
    teachers = c.fetchall()
    conn.close()
    return jsonify({'teachers': [dict(teacher) for teacher in teachers]})


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

@app.route('/PrivacyPolicy')
def PrivacyPolicy():
    return render_template('privacy_policy.html')

@app.route('/TermsCondition')
def TermsCondition():
    return render_template('terms_conditions.html')

@app.route('/FAQs')
def FAQs():
    return render_template('Faq.html')

@app.route('/otherpolicies')
def otherpolicies():
    return render_template('other_policies.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/course1')
def course1():
    return render_template('course1.html')

@app.route('/course2')
def course2():
    return render_template('course2.html')

@app.route('/course3')
def course3():
    return render_template('course3.html')

@app.route('/course4')
def course4():
    return render_template('course4.html')

@app.route('/course5')
def course5():
    return render_template('course5.html')

@app.route('/course6')
def course6():
    return render_template('course6.html')

@app.route('/course7')
def course7():
    return render_template('course7.html')

@app.route('/course8')
def course8():
    return render_template('course8.html')

@app.route('/course9')
def course9():
    return render_template('course9.html')

@app.route('/course10')
def course10():
    return render_template('course10.html')

@app.route('/DBHPS')
def dbhps_page():
    return render_template('DBHPS.html')

@app.route('/create_batch', methods=['POST'])
def create_batch():
    print("Received request to create batch")
    batch_id = request.form['batch_id']
    course_name = request.form['batch-course-name']
    teacher_name = request.form['teacher-name']
    teacher_id = request.form['teacher-id']
    start_date = request.form['start-date']
    end_date = request.form['end-date']
    start_time = request.form['start-time']
    end_time = request.form['end-time']
    class_limit = request.form['class-limit']
    course_price = request.form['course-price']

    print(f"Batch ID: {batch_id}, Course Name: {course_name}, Teacher Name: {teacher_name}, Teacher ID: {teacher_id}")
    print(f"Start Date: {start_date}, End Date: {end_date}, Start Time: {start_time}, End Time: {end_time}")
    print(f"Class Limit: {class_limit}, Course Price: {course_price}")

    conn = get_db_connection()
    c = conn.cursor()

    try:
        # Insert new batch into the batches table
        c.execute('''
            INSERT INTO batches (batch_id, course_name, teacher_name, teacher_id, start_date, end_date, start_time, end_time, class_limit, course_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (batch_id, course_name, teacher_name, teacher_id, start_date, end_date, start_time, end_time, class_limit, course_price))
        conn.commit()
        print("Batch inserted successfully")

        # Check for matching students in the students table
        c.execute('SELECT * FROM students WHERE course = ?', (course_name,))
        matching_students = c.fetchall()
        print(f"Matching Students: {matching_students}")

        if matching_students:
            # Filter out students already assigned to other instructors for the same course
            unassigned_students = []
            for student in matching_students:
                c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'instructor_%'")
                instructor_tables = c.fetchall()

                assigned = False
                for table in instructor_tables:
                    table_name = table['name']
                    if course_name in table_name:  # Check if the table is for the same course
                        c.execute(f'SELECT * FROM {table_name} WHERE student_id = ?', (student['id'],))
                        if c.fetchone():
                            assigned = True
                            break

                if not assigned:
                    unassigned_students.append(student)

            # Limit to 2 students per instructor
            unassigned_students = unassigned_students[:2]
            print(f"Unassigned Students: {unassigned_students}")

            if unassigned_students:
                # Create a new table for the instructor if it doesn't exist
                instructor_table_name = f'instructor_{teacher_id}_{course_name.replace(" ", "_")}'
                c.execute(f'''
                    CREATE TABLE IF NOT EXISTS {instructor_table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        student_name TEXT,
                        student_email TEXT,
                        FOREIGN KEY (student_id) REFERENCES students(id)
                    )
                ''')
                conn.commit()  # Ensure the table is created

                # Insert unassigned students into the instructor's table
                for student in unassigned_students:
                    c.execute(f'''
                        INSERT INTO {instructor_table_name} (student_id, student_name, student_email)
                        VALUES (?, ?, ?)
                    ''', (student['id'], student['fullname'], student['email']))
                conn.commit()  # Commit after inserting students

        flash('Batch created and students assigned successfully!', 'success')
    except sqlite3.IntegrityError as e:
        flash('Error creating batch: {}'.format(e), 'error')
    except Exception as e:
        flash('Unexpected error occurred: {}'.format(e), 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/publish', methods=['POST'])
def publish_course():
    course_name = request.json['course_name']
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO publish (course_name) VALUES (?)', (course_name,))
        conn.commit()
        response = {'status': 'success', 'message': 'Course published successfully.'}
    except sqlite3.IntegrityError:
        response = {'status': 'error', 'message': 'Course is already published.'}
    conn.close()
    return jsonify(response)

@app.route('/unpublish', methods=['POST'])
def unpublish_course():
    course_name = request.json['course_name']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM publish WHERE course_name = ?', (course_name,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Course unpublished successfully.'})

@app.route('/api/get_published_courses', methods=['GET'])
def get_published_courses():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT course_name FROM publish')
    courses = c.fetchall()
    conn.close()
    return jsonify({'courses': [course['course_name'] for course in courses]})

@app.route('/api/get_active_batches', methods=['GET'])
def get_active_batches():
    course_name = request.args.get('course')
    conn = get_db_connection()
    c = conn.cursor()
    
    # Select all batches for the given course
    c.execute('''
        SELECT batch_id, start_time, teacher_id
        FROM batches
        WHERE course_name = ?
    ''', (course_name,))
    batches = c.fetchall()
    conn.close()
    
    return jsonify({'batches': [{'batch_id': batch['batch_id'], 'start_time': batch['start_time'], 'teacher_id': batch['teacher_id']} for batch in batches]})

@app.route('/api/instructor_courses', methods=['GET'])
def get_instructor_courses():
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 401

    teacher_id = session['user_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM batches WHERE teacher_id = ?', (teacher_id,))
    courses = c.fetchall()
    conn.close()

    return jsonify({'status': 'success', 'courses': [dict(course) for course in courses]})


@app.route('/api/instructor_details/<int:teacher_id>', methods=['GET'])
def get_instructor_details(teacher_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM recruited_table WHERE id = ?', (teacher_id,))
    instructor = c.fetchone()
    conn.close()

    if instructor:
        return jsonify({
            'status': 'success',
            'instructor': {
                'fullname': instructor['fullname'],
                'email': instructor['email'],
                'qualification': instructor['qualification'],
                'experience': instructor['experience'],
                'specializations': instructor['specializations'],
                'institution': instructor['institution'],
                'availability_start': instructor['availability_from'],
                'availability_end': instructor['availability_to'],
                'phone': instructor['phone'],
                'district': instructor['district']
            }
        })
    else:
        return jsonify({'status': 'error', 'message': 'Instructor not found'}), 404
    
@app.route('/api/student_details/<int:student_id>', methods=['GET'])
def get_student_details(student_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = c.fetchone()
    conn.close()

    if student:
        return jsonify({
            'status': 'success',
            'student': {
                'fullname': student['fullname'],
                'email': student['email'],
                'dob': student['dob'],
                'gender': student['gender'],
                'status': student['status'],
                'institution': student['institution'],
                'language_proficiency': student['language_proficiency'],
                'course': student['course'],
                'batch_id': student['batch_id'],
                'preferred_time': student['preferred_time'],
                'exam_preference': student['exam_preference'],
                'phone': student['phone'],
                'state': student['state'],
                'district': student['district']
            }
        })
    else:
        return jsonify({'status': 'error', 'message': 'Student not found'}), 404


@app.route('/dashboard_upload', methods=['GET'])
def dashboard_upload():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    course_name = request.args.get('course_name')
    batch_id = request.args.get('batch_id')

    if not course_name or not batch_id:
        flash('Missing parameters', 'error')
        return redirect(url_for('instructor_dashboard'))

    teacher_id = session.get('teacher_id')

    if not teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login_page'))

    return render_template('dashboard_upload.html', course_name=course_name, batch_id=batch_id, teacher_id=teacher_id)

@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 401

    teacher_id = session['user_id']
    course_name = request.form.get('course_name')
    batch_id = request.form.get('batch_id')
    title = request.form.get('title')
    text = request.form.get('text')
    drive_link = request.form.get('drive_link')

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM batches WHERE teacher_id = ? AND course_name = ? AND batch_id = ?', (teacher_id, course_name, batch_id))
        batch = c.fetchone()

        if batch:
            c.execute('''
                INSERT INTO announcements (teacher_id, batch_id, course_name, title, announcement, drive_link, date)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (teacher_id, batch_id, course_name, title, text, drive_link))
            conn.commit()
            response = {'status': 'success', 'message': 'Announcement posted successfully.'}
        else:
            response = {'status': 'error', 'message': 'Batch not found or unauthorized.'}
    except Exception as e:
        conn.rollback()
        response = {'status': 'error', 'message': 'Failed to create announcement', 'details': str(e)}
        print(f"Error posting announcement: {e}")
    finally:
        conn.close()
    return jsonify(response)

@app.route('/get_announcements', methods=['GET'])
def get_announcements():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 401

    course_name = request.args.get('course_name')
    batch_id = request.args.get('batch_id')
    teacher_id = session.get('teacher_id')

    if not course_name or not batch_id or not teacher_id:
        return jsonify({'status': 'error', 'message': 'Missing course_name, batch_id, or teacher_id'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        query = 'SELECT * FROM announcements WHERE course_name = ? AND batch_id = ? AND teacher_id = ?'
        c.execute(query, (course_name, batch_id, teacher_id))
        rows = c.fetchall()

        announcements = [dict(row) for row in rows]
        response = {'status': 'success', 'announcements': announcements}
    except Exception as e:
        response = {'status': 'error', 'message': 'Failed to fetch announcements', 'details': str(e)}
    finally:
        conn.close()
    return jsonify(response)

@app.route('/student_announcements')
def student_announcements():
    if 'user_id' not in session or session.get('user_role') != 'student':
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT course, batch_id, teacher_id FROM students WHERE id = ?', (user_id,))
    student = c.fetchone()
    conn.close()

    if not student:
        flash('Student details not found.', 'error')
        return redirect(url_for('student_dashboard'))

    course_name = student['course']
    batch_id = student['batch_id']
    teacher_id = student['teacher_id']

    return render_template('student_announcement.html', course_name=course_name, batch_id=batch_id, teacher_id=teacher_id)


@app.route('/get_student_announcements', methods=['GET'])
def get_student_announcements():
    if 'user_id' not in session or session.get('user_role') != 'student':
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 401

    course_name = request.args.get('course_name')
    batch_id = request.args.get('batch_id')
    teacher_id = request.args.get('teacher_id')

    if not course_name or not batch_id or not teacher_id:
        return jsonify({'status': 'error', 'message': 'Missing course_name, batch_id, or teacher_id'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        query = 'SELECT * FROM announcements WHERE course_name = ? AND batch_id = ? AND teacher_id = ?'
        c.execute(query, (course_name, batch_id, teacher_id))
        rows = c.fetchall()

        announcements = [dict(row) for row in rows]
        response = {'status': 'success', 'announcements': announcements}
    except Exception as e:
        response = {'status': 'error', 'message': 'Failed to fetch announcements', 'details': str(e)}
    finally:
        conn.close()
    return jsonify(response)

@app.route('/admin_announcement', methods=['POST'])
def admin_announcement():
    data = request.get_json()
    title = data['title']
    announcement = data['announcement']
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO adminannouncement (title, announcement, date)
            VALUES (?, ?, ?)
        ''', (title, announcement, date))
        conn.commit()
        response = {'status': 'success', 'message': 'Announcement saved successfully.'}
    except Exception as e:
        conn.rollback()
        response = {'status': 'error', 'message': 'Failed to save announcement', 'details': str(e)}
    finally:
        conn.close()
    return jsonify(response)

@app.route('/get_admin_announcements', methods=['GET'])
def get_admin_announcements():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM adminannouncement ORDER BY date DESC')
        rows = c.fetchall()
        announcements = [dict(row) for row in rows]
        response = {'status': 'success', 'announcements': announcements}
    except Exception as e:
        response = {'status': 'error', 'message': 'Failed to fetch announcements', 'details': str(e)}
    finally:
        conn.close()
    return jsonify(response)

@app.route('/api/get_teacher_profiles', methods=['GET'])
def get_teacher_profiles():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('SELECT id, fullname AS name, email FROM recruited_table')
    teachers = c.fetchall()

    c.execute('SELECT fullname AS name, email FROM students')
    students = c.fetchall()

    conn.close()

    return jsonify({
        'teachers': [dict(teacher) for teacher in teachers],
        'students': [dict(student) for student in students]
    })

@app.route('/delete_admin_announcement/<int:announcement_id>', methods=['DELETE'])
def delete_admin_announcement(announcement_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM adminannouncement WHERE id = ?', (announcement_id,))
        conn.commit()
        response = {'status': 'success', 'message': 'Announcement deleted successfully.'}
    except Exception as e:
        response = {'status': 'error', 'message': 'Failed to delete announcement', 'details': str(e)}
    finally:
        conn.close()
    return jsonify(response)



if __name__ == '__main__':
    with app.app_context():
        conn = get_db_connection()
        c = conn.cursor()
        # Create students table
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                status TEXT NOT NULL,
                institution TEXT NOT NULL,
                language_proficiency TEXT,
                course TEXT,
                batch_id TEXT,
                start_time TEXT,
                preferred_time TEXT,
                exam_preference TEXT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                state TEXT,
                district TEXT,
                consent INTEGER NOT NULL,
                password TEXT ,
                teacher_id TEXT
            )
        ''')
        # Create teachers table
        c.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                qualification TEXT NOT NULL,
                language_proficiency TEXT,
                experience TEXT,
                specializations TEXT,
                institution TEXT,
                availability_from TEXT,
                availability_to TEXT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                district TEXT,
                consent INTEGER NOT NULL,
                password TEXT 
            )
        ''')

        # Create announcements table
        c.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                batch_id TEXT NOT NULL,
                course_name TEXT NOT NULL,
                title TEXT NOT NULL,
                announcement TEXT NOT NULL,
                drive_link TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES recruited_table(id),
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
            )
        ''')

        # Create feedback table
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                feedback TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Create meetings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                meeting_date TEXT NOT NULL,
                meeting_time TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Create instructor information table
        c.execute('''
            CREATE TABLE IF NOT EXISTS instructor_information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER,
                bio TEXT NOT NULL,
                achievements TEXT,
                courses TEXT,
                FOREIGN KEY (teacher_id) REFERENCES recruited_table(id)
            )
        ''')

        # Create batches table
        c.execute('''
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                course_name TEXT NOT NULL,
                teacher_name TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                class_limit INTEGER NOT NULL,
                course_price TEXT NOT NULL
            )
        ''')

        # Create publish table
        c.execute('''
            CREATE TABLE IF NOT EXISTS publish (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL UNIQUE
            )
        ''')

        # Create studentcourse table
        c.execute('''
            CREATE TABLE IF NOT EXISTS studentcourse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                fullname TEXT NOT NULL,
                course TEXT NOT NULL,
                batch_id TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Create course_batch_count table
        c.execute('''
            CREATE TABLE IF NOT EXISTS course_batch_count (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                batch_id TEXT NOT NULL,
                student_count INTEGER NOT NULL,
                teacher_id TEXT NOT NULL
            )
        ''')
        # Create recruited_table
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruited_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fullname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                qualification TEXT NOT NULL,
                language_proficiency TEXT,
                experience TEXT,
                specializations TEXT,
                institution TEXT,
                availability_from TEXT,
                avail4ability_to TEXT,
                phone TEXT,
                district TEXT,
                consent INTEGER,
                password TEXT
            )
        ''')

        # Create adminannouncement table
        c.execute('''
            CREATE TABLE IF NOT EXISTS adminannouncement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                announcement TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')

        conn.close()
    app.run(debug=True)
