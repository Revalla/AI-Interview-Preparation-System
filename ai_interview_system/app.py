from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# local modules
import database
import llm_service


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Use environment variable for security

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Make sure database exists
database.init_db()

# note: llm_service will configure the OpenAI key on import
# use the imported service for all model interactions


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, name, email, password_hash):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash

# user persistence is managed via SQLite in database.py
# (load_users/save_users JSON helpers have been removed)

@login_manager.user_loader
def load_user(user_id):
    # user_id is stored as string by Flask-Login, convert to int
    try:
        row = database.get_user_by_id(int(user_id))
    except Exception:
        return None
    if row:
        return User(row['id'], row['name'], row['email'], row['password_hash'])
    return None

@app.route('/')
def index():
    """Show a simple landing page or redirect authenticated users."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration using the SQLite database."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing = database.get_user_by_email(email)
        if existing:
            flash('Email already registered')
            return redirect(url_for('signup'))

        user_id = database.create_user(name, email, password)
        row = database.get_user_by_id(user_id)
        user = User(row['id'], row['name'], row['email'], row['password_hash'])
        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login against the SQLite database."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        row = database.get_user_by_email(email)
        if row and check_password_hash(row['password_hash'], password):
            user = User(row['id'], row['name'], row['email'], row['password_hash'])
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid email or password')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the interview dashboard and include past sessions."""
    history = database.get_interviews(current_user.id)
    return render_template('dashboard.html', name=current_user.name, history=history)

@app.route('/profile')
@login_required
def profile():
    """Render the user profile page with statistics."""
    interview_count = database.get_interview_count(current_user.id)
    return render_template('profile.html', name=current_user.name, email=current_user.email,
                           interview_count=interview_count)

@app.route('/start_interview', methods=['POST'])
@login_required
def start_interview():
    """Start a new interview session by requesting questions from the LLM."""
    role = request.form['role']
    difficulty = request.form['difficulty']

    # ask the language model to generate a short list of questions
    questions = llm_service.generate_questions(role, difficulty, count=5)
    if not questions:
        flash('Unable to generate interview questions. Please try again later.')
        return redirect(url_for('dashboard'))

    session['role'] = role
    session['difficulty'] = difficulty
    session['questions'] = questions
    session['evaluations'] = []
    session['current_index'] = 0

    return redirect(url_for('interview'))

@app.route('/interview')
@login_required
def interview():
    """Render the interview page with current question."""
    if 'questions' not in session:
        return redirect(url_for('dashboard'))
    
    questions = session['questions']
    current_index = session['current_index']
    
    if current_index >= len(questions):
        return redirect(url_for('finish_interview'))
    
    question = questions[current_index]
    return render_template('interview.html', question=question, index=current_index + 1, total=len(questions))

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """Submit answer for current question, evaluate it, and progress."""
    if 'questions' not in session:
        return redirect(url_for('dashboard'))

    answer = request.form['answer']
    questions = session['questions']
    current_index = session['current_index']
    question = questions[current_index]

    # ask the LLM to evaluate the given answer
    eval_result = llm_service.evaluate_answer(
        question,
        answer,
        role=session.get('role'),
        difficulty=session.get('difficulty')
    )

    # pack everything into evaluations list
    record = {
        'question': question,
        'answer': answer,
        **eval_result
    }
    session['evaluations'].append(record)

    # Move to next question
    session['current_index'] += 1

    if session['current_index'] >= len(questions):
        return redirect(url_for('finish_interview'))

    return redirect(url_for('interview'))

@app.route('/finish_interview')
@login_required
def finish_interview():
    """Compile the final report, persist the interview, and render results."""
    if 'evaluations' not in session:
        return redirect(url_for('dashboard'))

    evaluations = session['evaluations']
    role = session.get('role')
    difficulty = session.get('difficulty')

    # ask LLM to produce consolidated feedback
    feedback = llm_service.generate_final_feedback(evaluations, role, difficulty)

    # persist to database so history is available later
    questions = [ev['question'] for ev in evaluations]
    answers = [ev['answer'] for ev in evaluations]
    scores = [ev.get('score', 0) for ev in evaluations]
    overall = feedback.get('overall_score', 0)
    try:
        database.save_interview(current_user.id, role, difficulty,
                                questions, answers, scores,
                                feedback, overall)
    except Exception as e:
        print(f"Failed to save interview record: {e}")

    # clear session state used for the running interview
    for k in ('questions', 'evaluations', 'current_index', 'role', 'difficulty'):
        session.pop(k, None)

    # pass evaluations to the template so answers are displayed
    return render_template('result.html', feedback=feedback, answers=evaluations)

@app.route('/download_report', methods=['POST'])
@login_required
def download_report():
    """Generate a PDF report from posted feedback and answers."""
    feedback = request.form.get('feedback')
    answers_json = request.form.get('answers')
    try:
        feedback = json.loads(feedback)
        answers = json.loads(answers_json)
    except Exception:
        flash('Failed to parse report data')
        return redirect(url_for('dashboard'))

    # create PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, y, 'Interview Performance Report')
    y -= 30
    p.setFont('Helvetica', 12)
    p.drawString(40, y, f"User: {current_user.name} ({current_user.email})")
    y -= 20
    p.drawString(40, y, f"Total Questions: {feedback.get('total_questions')}")
    y -= 20
    p.drawString(40, y, f"Overall Score: {feedback.get('overall_score')}/10")
    y -= 30

    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, 'Question Scores:')
    y -= 20
    p.setFont('Helvetica', 12)
    for idx, score in enumerate(feedback.get('question_scores', []), start=1):
        p.drawString(60, y, f"{idx}. {score}/10")
        y -= 18
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 20
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, 'Strengths:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in feedback.get('strengths', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 20
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, 'Weaknesses:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in feedback.get('weaknesses', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 20
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, 'Suggestions:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in feedback.get('suggestions', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40
    y -= 20
    p.setFont('Helvetica-Bold', 14)
    p.drawString(40, y, 'Study Areas:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in feedback.get('study_areas', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 40

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='interview_report.pdf',
        mimetype='application/pdf'
    )

@app.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    """User account settings - change password."""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify old password
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('account_settings'))

        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('account_settings'))

        # Check password strength
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('account_settings'))

        # Update password
        database.update_user_password(current_user.id, new_password)
        flash('Password updated successfully!', 'success')
        return redirect(url_for('account_settings'))

    return render_template('account_settings.html', name=current_user.name, email=current_user.email)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile information."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        if not name or not email:
            flash('Name and email are required', 'error')
            return redirect(url_for('edit_profile'))

        # Check if email already exists (but allow current email)
        existing = database.get_user_by_email(email)
        if existing and existing['id'] != current_user.id:
            flash('Email is already in use', 'error')
            return redirect(url_for('edit_profile'))

        # Update profile
        database.update_user_profile(current_user.id, name, email)
        current_user.name = name
        current_user.email = email
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('edit_profile'))

    return render_template('edit_profile.html', name=current_user.name, email=current_user.email)


@app.route('/progress')
@login_required
def view_progress():
    """View progress statistics."""
    stats = database.get_progress_stats(current_user.id)
    return render_template('progress.html', name=current_user.name, stats=stats)


@app.route('/interview_history')
@login_required
def interview_history():
    """View complete interview history."""
    interviews = database.get_interviews(current_user.id)
    return render_template('interview_history.html', name=current_user.name, interviews=interviews)


@app.route('/interview_details/<int:interview_id>')
@login_required
def interview_details(interview_id):
    """View detailed results of a specific interview."""
    interview = database.get_interview_details(interview_id, current_user.id)
    if not interview:
        flash('Interview not found', 'error')
        return redirect(url_for('interview_history'))

    # Parse JSON fields
    questions = json.loads(interview['questions']) if interview['questions'] else []
    answers = json.loads(interview['answers']) if interview['answers'] else []
    scores = json.loads(interview['scores']) if interview['scores'] else []
    feedback = json.loads(interview['feedback']) if interview['feedback'] else {}

    return render_template('interview_details.html', 
                          name=current_user.name,
                          interview=interview,
                          questions=questions,
                          answers=answers,
                          scores=scores,
                          feedback=feedback)


# feedback generation now lives in llm_service.generate_final_feedback
# the old implementation has been removed.
if __name__ == '__main__':
    app.run(debug=True)
