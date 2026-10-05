# AI Student Mentor

## Description
A personalized AI Academic Mentor application designed to help students learn effectively. This is Phase 1 of the project, which establishes the foundational web application architecture, user authentication, profile management, and a functional chat interface.

## Features (Phase 1)
- Modern, responsive landing page
- Student Registration & Login with secure password hashing
- Session-based Authentication
- Student Dashboard with progress tracking UI
- Profile Management
- Fully functional Chat UI with typing indicators and suggestions
- SQLite Database integration via SQLAlchemy
- Clean and extensible architecture ready for Phase 2 AI integration

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** HTML5, CSS3, JavaScript, FontAwesome
- **Database:** SQLite

## Folder Structure
```
AI-Student-Mentor/
├── app.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── database/              # SQLite database storage
├── models/                # SQLAlchemy models (user, etc.)
├── routes/                # Flask Blueprints (auth, dashboard, chat)
├── services/              # Business logic (ai_service)
├── templates/             # HTML templates
└── static/                # CSS, JS, and Images
```

## Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Environment Variables
Create a `.env` file in the root directory (refer to `.env.example`):
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database/database.db
```

## Database Initialization
The database is initialized automatically when you run the application for the first time.

## Run Command
Start the Flask development server:
```
python app.py
```
Then open your browser and navigate to `http://127.0.0.1:5000`

## Future Phases (Phase 2 & 3)
- Real AI chatbot integration (OpenAI/Anthropic)
- Voice input and Text-to-Speech
- AI question understanding and academic explanations
- Smart Quizzes generated from learning history
- Document upload and analysis
- Advanced learning analytics
