# Student Advising API

AI-powered academic advisor using Gemini. Analyzes student risk level, generates study plans, and attaches learning resources.

## Endpoint

**POST** `/analyze-student`

```json
{
  "student_id": "12345",
  "student_name": "Ahmed",
  "major": "CS",
  "semester": "Fall 2025",
  "gpa": 1.8,
  "courses": [
    {
      "course_code": "CS201",
      "course_name": "Data Structures",
      "grade": "F",
      "credit_hours": 3
    }
  ]
}
```

## Deploy on Render

1. Push this repo to GitHub
2. Render → New → Web Service → connect repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
5. Add env var: `GEMINI_API_KEY`
6. Deploy
