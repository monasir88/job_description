from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load .env file variables
load_dotenv()

# Initialize OpenAI client using API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

questions = [
    "1. What title or role are you looking for?",
    "2. What tasks will the person have to solve?",
    "3. Will the work be done at your location, remotely, or a mix?",
    "4. Approximately how many hours per week – and for how long?",
    "5. Do you have any other wishes or requirements for the person's background and skills?"
]

sessions = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.form.get("user_id")
    user_input = request.form.get("message")

    if user_id not in sessions:
        sessions[user_id] = {"answers": [], "q_index": 0}

    session_data = sessions[user_id]

    # Save previous answer
    if session_data["q_index"] > 0:
        session_data["answers"].append(user_input)

    # Ask next question
    if session_data["q_index"] < len(questions):
        question = questions[session_data["q_index"]]
        session_data["q_index"] += 1
        return jsonify({"reply": question, "done": False})

    # All answers collected → Generate ad
    job_posting = generate_job_posting(session_data["answers"])
    del sessions[user_id]
    return jsonify({"reply": job_posting, "done": True})


def generate_job_posting(answers):
    prompt = f"""
You are a specialist in writing job postings for freelance and temp positions within marketing, communication, design and digital roles.
You always use the 3rd person (not “you”), avoid buzzwords and generic phrases, and follow the provided structure exactly.

OUTPUT FORMAT: Return the ad as valid HTML with proper tags for:
- Bold text using <b>
- Bulleted lists using <ul> and <li>
- Paragraphs using <p>
- Headings using <h2>

Here is the ad structure to follow:

<h2><b>[Heading: affiliation (freelance, temporary or both), title, type of company, city/area]</b></h2>
<p>[Introduction: What is being sought. For what type of company. Location. Collaboration type (remote, on location, or a mix)]</p>
<ul>
    <li><b>Scope:</b> [Days or hours per week or month]</li>
    <li><b>Start:</b> [Start date or approx. start]</li>
    <li><b>Period:</b> [Period, how long will the collaboration last?]</li>
</ul>
<p>[Section 1: Describe the tasks that the person will be required to solve, as well as the role]</p>
<p>[Section 2: Describe the background the person should have, experience, industry background, skills]</p>
<p><b>Competencies/work areas:</b></p>
<ul>
    <li>[Bullet 1: Key task or skill]</li>
    <li>[Bullet 2: Key task or skill]</li>
    <li>[Bullet 3: Key task or skill]</li>
    <li>[Bullet 4: Key task or skill]</li>
</ul>
<p>[Section 3: Any other conditions or skills that are a plus but not a requirement]</p>
<p>Please apply if you meet the criteria and are interested.</p>
<p>Best regards<br>Carsten Bjerregaard</p>

Use the answers below to fill in this structure:

1. Title/Role: {answers[0]}
2. Tasks: {answers[1]}
3. Location/Collaboration: {answers[2]}
4. Hours & Period: {answers[3]}
5. Background/Requirements: {answers[4]}

Important:
- Do NOT wrap the output in ```html``` or any other code block formatting.
- Return only clean HTML so it can be displayed directly on a webpage without extra processing.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    app.run(debug=True)
