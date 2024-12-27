from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import mysql.connector
from datetime import datetime
import cv2
import mediapipe as mp
from index import process_resume
from flask_bcrypt import Bcrypt
import logging


app = Flask(__name__)
app.secret_key = "prasad"
bcrypt = Bcrypt(app)

# MySQL Configuration for Skill Test
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "2003",
    "database": "TEST_PLATFORM"
}
@app.route('/registeration', methods=['GET', 'POST'])
def registeration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('registeration'))
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO userslogin (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('Error: ' + str(err), 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('auth.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM userslogin WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('welcome'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('auth.html')

@app.route('/')
def home():
    return render_template('auth.html')  # Main Homepage with navigation
@app.route('/welcome')
def welcome():
    if 'user_id' in session:
        return render_template('index.html', username=session.get('username'))
    else:
        flash("Please log in to access this page.", "danger")
        return redirect(url_for('login'))

# Resume Upload Configuration
app.config["UPLOAD_FOLDER"] = "./uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

# Mock Job Data
MOCK_JOB_DATA = [
    {"title": "Software Engineer", "company": "TechCorp", "location": "Remote", "role": "Developer"},
    {"title": "Data Scientist", "company": "DataCo", "location": "New York", "role": "Analyst"},
    {"title": "DevOps Engineer", "company": "CloudOps", "location": "San Francisco", "role": "Developer"},
    {"title": "UI/UX Designer", "company": "DesignHub", "location": "Remote", "role": "Designer"},
    {"title": "AI Researcher", "company": "InnovAI", "location": "Boston", "role": "Analyst"},
]


# Utility function to connect to the database
def connect_db():
    return mysql.connector.connect(**db_config)


# Allowed file checker
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Fetch questions based on difficulty from the database
def fetch_questions(difficulty):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, question_text, options FROM questions WHERE difficulty = %s", (difficulty,))
    questions = cursor.fetchall()
    # print("Fetched Questions:", questions)
    cursor.close()
    conn.close()
    return questions


# Save user answers to the database
def save_answers(user_id, answers):
    conn = connect_db()
    cursor = conn.cursor()
    for question_id, submitted_answer in answers.items():
        cursor.execute(
            "INSERT INTO answers (question_id, user_id, submitted_answer) VALUES (%s, %s, %s)",
            (question_id, user_id, submitted_answer)
        )
    conn.commit()
    cursor.close()
    conn.close()


# Save user information during registration
def save_user(username, email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id


# Routes
#
# @app.route('/')
# def home():
#     return render_template('index.html')  # Main Homepage with navigation


# Resume Upload & Job Search
@app.route('/resume-upload', methods=["GET", "POST"])
def resume_upload():
    return render_template('resume.html', message="Upload your resume and find jobs.")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("resume")
    difficulty = request.headers.get("difficulty", "Medium")

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Only .pdf, .jpg or .jpeg files are supported!"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        questions = process_resume(file_path, difficulty)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(file_path)

    return jsonify({"questions": questions})


@app.route('/jobfit', methods=["POST"])
def jobfit():
    data = request.get_json()
    role = data.get("role", "")
    location = data.get("location", "")

    # Filter jobs based on role and location
    jobs = MOCK_JOB_DATA
    if role:
        jobs = [job for job in jobs if role.lower() in job["role"].lower()]
    if location:
        jobs = [job for job in jobs if location.lower() in job["location"].lower()]

    return jsonify({"jobs": jobs})


# Skill Test
@app.route('/skill-test')
def skill_test():
    return render_template('test.html', message="Start your skill-based test.")

@app.route("/get-questions", methods=["POST"])
def get_questions():
    difficulty = request.json.get("difficulty", "Medium")
    session["start_time"] = datetime.now()
    session["cheat_attempts"] = 0
    questions = fetch_questions(difficulty)
    return jsonify({"questions": questions})



@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "Username and email are required."}), 400

    try:
        user_id = save_user(username, email)
        session["user_id"] = user_id  # Store user ID in  session
        return jsonify({"user_id": user_id, "message": "Registration successful."})
    except Exception as e:
        return jsonify({"error": f"Error during registration: {e}"}), 500


@app.route('/submit-answers', methods=["POST"])
def submit_answers():
    if "user_id" not in session:
        return jsonify({"error": "User not registered."}), 403

    data = request.get_json()
    user_id = session["user_id"]
    answers = data.get("answers")

    if not answers:
        return jsonify({"error": "No answers submitted."}), 400

    try:
        save_answers(user_id, answers)
        return jsonify({"message": "Answers submitted successfully."})
    except Exception as e:
        return jsonify({"error": f"Error during answer submission: {e}"}), 500


@app.route('/check-cheating', methods=["POST"])
def check_cheating():
    action = request.json.get("action")
    user_id = session.get("user_id", None)

    if not user_id:
        return jsonify({"error": "User not logged in."}), 403

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cheating_logs (user_id, action, timestamp) VALUES (%s, %s, NOW())",
            (user_id, action)
        )
        conn.commit()

        if action == "toggle":
            session["cheat_attempts"] = session.get("cheat_attempts", 0) + 1
            if session["cheat_attempts"] > 3:
                cursor.close()
                conn.close()
                return jsonify({
                    "cheating_detected": True,
                    "message": "Test auto-submitted due to multiple tab switches."
                })

        cursor.close()
        conn.close()
        return jsonify({"cheating_detected": False})
    except Exception as e:
        return jsonify({"error": f"Error logging cheating activity: {e}"}), 500



@app.route('/live_interview')
def live_interview():
    return render_template('ihome.html', message="Welcome to the live interview section.")

# Live Interview
# Initialize MediaPipe Face Mesh and drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

# Global variables for storing user details
user_details = {"username": "", "email": ""}

# Video capture function (starts/stops only when required)
def generate_frames():
    cap = cv2.VideoCapture(0)

    with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
    ) as face_mesh:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            # Convert the image to RGB for MediaPipe processing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)

            # Draw the face mesh landmarks on the frame
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles
                        .get_default_face_mesh_tesselation_style()
                    )
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(
                            color=(0, 255, 0), thickness=1
                        )
                    )

            # Encode frame as JPEG for streaming
            _, buffer = cv2.imencode('.jpg', cv2.flip(image, 1))
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()



@app.route('/user_details', methods=['POST'])
def user_details_submit():
    global user_details
    user_details['username'] = request.form.get('username')
    user_details['email'] = request.form.get('email')
    return redirect(url_for('ready_check'))

@app.route('/ready_check')
def ready_check():
    return render_template('ready_check.html', username=user_details['username'])

@app.route('/start_interview')
def start_interview():
    return render_template('interview.html', username=user_details['username'])

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end_meeting', methods=['POST'])
def end_meeting():
    feedback = request.form.get('feedback')
    print(f"Feedback received: {feedback}")
    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))  # Redirect to the login page


if __name__ == '__main__':
    app.run(debug=True, port=8000)
