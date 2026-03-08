# AI Interview Preparation System

A comprehensive Flask-based interview preparation platform with AI-powered feedback and user authentication.

## Features

### Authentication
- User registration and login
- Secure password hashing
- Session management

### Multiple Job Roles
- AI/ML Engineer
- Data Scientist
- Software Developer
- Frontend Developer
- Backend Developer
- Full Stack Developer
- Data Analyst
- DevOps Engineer
- Cyber Security Analyst
- Product Manager
- UX/UI Designer
- QA Engineer
- Data Engineer
- Cloud Engineer
- Mobile App Developer
- System Administrator
- Business Analyst
- Project Manager
- Technical Support Engineer
- Machine Learning Engineer
- Blockchain Developer
- Game Developer
- Cyber Security Analyst

### Interview Sessions
- Easy, Medium, and Hard difficulty levels
- Technical and HR questions
- One question at a time format
- Progress tracking

### LLM-Driven Content
- All interview questions are generated dynamically by a large language model (no predefined list)
- Answers are evaluated in real time by the LLM with scores, strengths, weaknesses, and a model answer

### AI-Powered Feedback
- Comprehensive evaluation using OpenAI GPT
- Individual question scores
- Overall performance metrics
- Strengths and weaknesses analysis
- Personalized improvement suggestions
- Study area recommendations

### Professional UI
- Modern, responsive design
- Separate pages for each functionality
- Professional interview simulator appearance

## Project Structure

```
ai_interview_system/
├── app.py                 # Flask backend with authentication and interview logic
├── database.py            # SQLite helper functions and schema initialization
├── llm_service.py         # Wrapper around LLM/API calls (OpenAI, HF)
├── .env                   # Environment variables (API keys, SECRET_KEY)
├── requirements.txt       # Python dependencies
├── database.db            # SQLite database file (created at runtime)
├── templates/             # HTML templates
│   ├── signup.html
│   ├── login.html
│   ├── dashboard.html
│   ├── interview.html
│   ├── result.html
│   ├── profile.html
│   └── index.html         # simple landing page
└── static/                # CSS and assets
    ├── style.css
```

## Setup

1. **Clone or download the project**

2. **Create a virtual environment:**
```bash
python -m venv .venv
```

3. **Activate the virtual environment:**
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables:**
- Copy `.env` and add your OpenAI API key (or other LLM provider key)
- Generate a secure `SECRET_KEY` for Flask sessions

6. **Populate the database (first run only):**
The SQLite database file (`database.db`) will be created automatically when the app starts. If you need to reset it, delete the file and restart the application.

7. **Run the application:**
```bash
python app.py
```

7. **Open [http://127.0.0.1:5000](http://localhost:5000) in your browser**

## Usage

1. **Sign Up:** Create a new account with name, email, and password
2. **Login:** Access your account
3. **Dashboard:** Select job role and difficulty level
4. **Interview:** Answer questions one by one
5. **Results:** View comprehensive AI-generated feedback

## API Keys

- **OpenAI API Key:** Required for AI-powered feedback. Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **SECRET_KEY:** Generate a random string for Flask sessions

## Technologies Used

- **Backend:** Python Flask
- **Authentication:** Flask-Login
- **AI Evaluation:** OpenAI GPT-3.5
- **Frontend:** HTML, CSS, JavaScript
- **Data Storage:** SQLite database (via `database.py`)

## Contributing

Feel free to contribute by adding more questions, improving the UI, or enhancing the AI evaluation logic.
