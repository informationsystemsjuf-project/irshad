import os
import json
import re
import requests
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

# ── Config ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

AT_RISK_GRADES = ["F", "D"]

ALLOWED_RESOURCE_DOMAINS = [
    "coursera.org",
    "www.coursera.org",
    "khanacademy.org",
    "www.khanacademy.org",
    "edx.org",
    "www.edx.org",
    "ocw.mit.edu",
    "www.ocw.mit.edu",
]

RESOURCE_MAP_BY_CODE = {
    "CS101": {"title": "Python for Everybody", "url": "https://www.coursera.org/specializations/python"},
    "CS102": {"title": "Python for Everybody", "url": "https://www.coursera.org/specializations/python"},
    "CS103": {"title": "How Computers Work", "url": "https://www.coursera.org/learn/how-computers-work"},
    "CS201": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "CS202": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "CS205": {"title": "Introduction to Linux", "url": "https://www.edx.org/learn/linux"},
    "CS206": {"title": "Computer Communications", "url": "https://www.coursera.org/specializations/computer-communications"},
    "CS301": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "CS302": {"title": "Software Processes and Agile Practices", "url": "https://www.coursera.org/learn/software-processes-and-agile-practices"},
    "CS303": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "CS304": {"title": "Fundamentals of Network Communication", "url": "https://www.coursera.org/learn/fundamentals-network-communications"},
    "CS305": {"title": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning"},
    "CS306": {"title": "CS50's Web Programming with Python and JavaScript", "url": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-web-programming-with-python-and-javascript"},
    "CS307": {"title": "Computer Communications", "url": "https://www.coursera.org/specializations/computer-communications"},
    "CS308": {"title": "Computer Science", "url": "https://www.khanacademy.org/computing/computer-science"},
    "CS309": {"title": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning"},
    "CS310": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "CS311": {"title": "Software Processes and Agile Practices", "url": "https://www.coursera.org/learn/software-processes-and-agile-practices"},
    "CS312": {"title": "Computer Communications", "url": "https://www.coursera.org/specializations/computer-communications"},
    "CS401": {"title": "Fundamentals of Network Communication", "url": "https://www.coursera.org/learn/fundamentals-network-communications"},
    "CS402": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "CS403": {"title": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning"},
    "CS404": {"title": "CS50's Web Programming with Python and JavaScript", "url": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-web-programming-with-python-and-javascript"},
    "CS405": {"title": "Computer Science", "url": "https://www.khanacademy.org/computing/computer-science"},
    "MATH201": {"title": "Calculus 2", "url": "https://www.khanacademy.org/math/calculus-2"},
    "MATH301": {"title": "Linear Algebra", "url": "https://www.khanacademy.org/math/linear-algebra"},
    "STAT201": {"title": "Statistics and Probability", "url": "https://www.khanacademy.org/math/statistics-probability"},
}

RESOURCE_MAP_BY_TOPIC = {
    "python": {"title": "Python for Everybody", "url": "https://www.coursera.org/specializations/python"},
    "programming": {"title": "Python for Everybody", "url": "https://www.coursera.org/specializations/python"},
    "computer science": {"title": "Computer Science", "url": "https://www.khanacademy.org/computing/computer-science"},
    "intro to cs": {"title": "How Computers Work", "url": "https://www.coursera.org/learn/how-computers-work"},
    "data structures": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "algorithms": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "analysis of algorithms": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "discrete": {"title": "Data Structures and Algorithms", "url": "https://www.coursera.org/specializations/data-structures-algorithms"},
    "operating system": {"title": "Introduction to Linux", "url": "https://www.edx.org/learn/linux"},
    "operating systems": {"title": "Introduction to Linux", "url": "https://www.edx.org/learn/linux"},
    "database": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "databases": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "sql": {"title": "Databases and SQL for Data Science with Python", "url": "https://www.coursera.org/learn/sql-data-science"},
    "network": {"title": "Fundamentals of Network Communication", "url": "https://www.coursera.org/learn/fundamentals-network-communications"},
    "networks": {"title": "Fundamentals of Network Communication", "url": "https://www.coursera.org/learn/fundamentals-network-communications"},
    "computer networks": {"title": "Fundamentals of Network Communication", "url": "https://www.coursera.org/learn/fundamentals-network-communications"},
    "software engineering": {"title": "Software Processes and Agile Practices", "url": "https://www.coursera.org/learn/software-processes-and-agile-practices"},
    "software": {"title": "Software Processes and Agile Practices", "url": "https://www.coursera.org/learn/software-processes-and-agile-practices"},
    "web": {"title": "CS50's Web Programming with Python and JavaScript", "url": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-web-programming-with-python-and-javascript"},
    "web development": {"title": "CS50's Web Programming with Python and JavaScript", "url": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-web-programming-with-python-and-javascript"},
    "machine learning": {"title": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning"},
    "artificial intelligence": {"title": "Machine Learning Specialization", "url": "https://www.coursera.org/specializations/machine-learning"},
    "linear algebra": {"title": "Linear Algebra", "url": "https://www.khanacademy.org/math/linear-algebra"},
    "calculus": {"title": "Calculus 2", "url": "https://www.khanacademy.org/math/calculus-2"},
    "statistics": {"title": "Statistics and Probability", "url": "https://www.khanacademy.org/math/statistics-probability"},
    "probability": {"title": "Statistics and Probability", "url": "https://www.khanacademy.org/math/statistics-probability"},
}

DEFAULT_RESOURCE = {
    "title": "Computer Science",
    "url": "https://www.khanacademy.org/computing/computer-science"
}

# ── Error helpers ───────────────────────────────────────────────────
def api_error_response(message, code=500):
    return jsonify({
        "error": {
            "code": int(code),
            "message": str(message).strip()
        }
    }), int(code)

def gemini_error_response(exc, default_code=503):
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None) or default_code
    try:
        code = int(code)
    except Exception:
        code = default_code

    msg = str(exc).strip() or "Gemini request failed"

    return jsonify({
        "error": {
            "code": code,
            "message": msg
        }
    }), code

# ── Core logic ──────────────────────────────────────────────────────
def assess_risk(student):
    failed = [c for c in student["courses"] if c["grade"] in AT_RISK_GRADES]
    gpa = float(student["gpa"])
    if gpa < 2.0 or len(failed) >= 3:
        return "خطر عالٍ", failed
    elif gpa < 2.5 or len(failed) >= 1:
        return "خطر متوسط", failed
    else:
        return "آمن", failed


def build_prompt(student, risk_level, failed_courses):
    failed_list = "\n".join(
        [f"- {c['course_code']} | {c['course_name']} | الدرجة: {c['grade']}" for c in failed_courses]
    ) or "لا توجد مواد متعثرة"

    return f"""
أنت مستشار أكاديمي.

بيانات الطالب:
الاسم: {student['student_name']}
الرقم الجامعي: {student['student_id']}
التخصص: {student['major']}
الفصل الدراسي: {student['semester']}
المعدل التراكمي: {student['gpa']}
مستوى الخطر: {risk_level}

المواد المتعثرة:
{failed_list}

المطلوب:
1) academic_status:
- مختصر جدًا
- سطران كحد أقصى

2) recommendations:
لكل مادة متعثرة فقط:
- course_code
- course_name
- grade
- study_plan:
  قائمة من 4 عناصر فقط
  Week 1, Week 2, Week 3, Week 4
  كل أسبوع عنوان قصير فقط
  بدون شرح طويل
  بدون فقرات

3) general_advice:
- مختصر جدًا
- سطران أو ثلاثة فقط

مهم جدًا:
- لا تُرجع أي روابط
- لا تُرجع أي مصادر
- لا تستخدم markdown
- لا تضف أي نص خارج JSON
- لا تكتب شرح طويل

أجب فقط بصيغة JSON بهذا الشكل:
{{
  "student_id": "{student['student_id']}",
  "student_name": "{student['student_name']}",
  "risk_level": "{risk_level}",
  "academic_status": "...",
  "recommendations": [
    {{
      "course_code": "...",
      "course_name": "...",
      "grade": "...",
      "study_plan": [
        "Week 1: ...",
        "Week 2: ...",
        "Week 3: ...",
        "Week 4: ..."
      ]
    }}
  ],
  "general_advice": "..."
}}
""".strip()


def call_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
        ),
    )
    return response.text


def parse_response(raw_text):
    clean = (raw_text or "").strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        if len(parts) >= 3:
            clean = parts[1]
        clean = clean.replace("json", "", 1).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start == -1 or end <= 0:
            raise ValueError("Gemini response is not valid JSON")
        return json.loads(clean[start:end])


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def is_allowed_domain(url):
    try:
        hostname = urlparse(url).netloc.lower()
        return any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_RESOURCE_DOMAINS)
    except Exception:
        return False


def verify_url(url, timeout=10):
    if not url or not is_allowed_domain(url):
        return False

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        if 200 <= resp.status_code < 400:
            return True
    except Exception:
        pass

    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
        if 200 <= resp.status_code < 400:
            return True
    except Exception:
        pass

    return False


def get_resource_from_map(course_code, course_name):
    if course_code in RESOURCE_MAP_BY_CODE:
        return RESOURCE_MAP_BY_CODE[course_code]

    course_name_norm = normalize_text(course_name)
    for key, resource in RESOURCE_MAP_BY_TOPIC.items():
        if key in course_name_norm:
            return resource

    return None


def build_resource_prompt(course_code, course_name):
    return f"""
أنت مساعد أكاديمي دقيق جدًا.

أعطني موردًا تعليميًا واحدًا فقط لهذه المادة:
- course_code: {course_code}
- course_name: {course_name}

الشروط:
- يجب أن يكون الرابط من واحد فقط من هذه المواقع:
  coursera.org
  khanacademy.org
  edx.org
  ocw.mit.edu
- لا تستخدم YouTube
- لا تستخدم أي موقع آخر
- اختر صفحة دورة أو صفحة تعلم حقيقية ومباشرة
- لا تختلق رابطًا
- إن لم تكن متأكدًا، أرجع url فارغًا

أجب فقط بصيغة JSON:
{{
  "title": "...",
  "url": "https://..."
}}
""".strip()


def generate_resource_with_gemini(course_code, course_name, max_attempts=3):
    for _ in range(max_attempts):
        prompt = build_resource_prompt(course_code, course_name)
        raw = call_gemini(prompt)
        data = parse_response(raw)

        title = (data.get("title") or "").strip()
        url = (data.get("url") or "").strip()

        if title and url and verify_url(url):
            return {"title": title, "url": url}

    return None


def attach_resources(result):
    for rec in result.get("recommendations", []):
        course_code = (rec.get("course_code") or "").strip()
        course_name = (rec.get("course_name") or "").strip()

        resource = get_resource_from_map(course_code, course_name)

        if resource and verify_url(resource["url"]):
            rec["resources"] = [resource]
            rec["resource_source"] = "map"
            continue

        generated = generate_resource_with_gemini(course_code, course_name)
        if generated:
            rec["resources"] = [generated]
            rec["resource_source"] = "generated_verified"
            continue

        if verify_url(DEFAULT_RESOURCE["url"]):
            rec["resources"] = [DEFAULT_RESOURCE]
            rec["resource_source"] = "default_fallback"
        else:
            rec["resources"] = []
            rec["resource_source"] = "none"

    return result


def sanitize_result_structure(result):
    result["academic_status"] = (result.get("academic_status") or "").strip()
    result["general_advice"] = (result.get("general_advice") or "").strip()

    cleaned = []
    for rec in result.get("recommendations", []):
        study_plan = rec.get("study_plan", [])
        if not isinstance(study_plan, list):
            study_plan = []

        study_plan = [str(x).strip() for x in study_plan if str(x).strip()][:4]

        while len(study_plan) < 4:
            study_plan.append(f"Week {len(study_plan)+1}: مراجعة أساسية")

        cleaned.append({
            "course_code": (rec.get("course_code") or "").strip(),
            "course_name": (rec.get("course_name") or "").strip(),
            "grade": (rec.get("grade") or "").strip(),
            "study_plan": study_plan
        })

    result["recommendations"] = cleaned
    return result


def analyze_one_student(student):
    risk_level, failed_courses = assess_risk(student)
    prompt = build_prompt(student, risk_level, failed_courses)

    raw = call_gemini(prompt)
    result = parse_response(raw)

    result.setdefault("student_id", student["student_id"])
    result.setdefault("student_name", student["student_name"])
    result.setdefault("risk_level", risk_level)
    result.setdefault("recommendations", [])
    result.setdefault("academic_status", "")
    result.setdefault("general_advice", "")

    result = sanitize_result_structure(result)
    result = attach_resources(result)

    return result


def validate_student_payload(student):
    required_fields = ["student_id", "student_name", "major", "semester", "gpa", "courses"]
    for field in required_fields:
        if field not in student:
            return False, f"Missing field: {field}"

    if not isinstance(student["courses"], list):
        return False, "Field 'courses' must be a list"

    course_fields = ["course_code", "course_name", "grade", "credit_hours"]
    for idx, course in enumerate(student["courses"]):
        if not isinstance(course, dict):
            return False, f"courses[{idx}] must be an object"
        for field in course_fields:
            if field not in course:
                return False, f"Missing field in courses[{idx}]: {field}"

    return True, "ok"

# ── Routes ──────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "student-advising-api",
        "status": "running",
        "endpoint": "/analyze-student",
        "method": "POST"
    })


@app.route("/analyze-student", methods=["POST"])
def analyze_student_api():
    data = request.get_json(silent=True)

    if not data:
        return api_error_response("Invalid or missing JSON body", 400)

    is_valid, message = validate_student_payload(data)
    if not is_valid:
        return api_error_response(message, 400)

    try:
        result = analyze_one_student(data)
        return jsonify(result), 200
    except Exception as e:
        return gemini_error_response(e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
