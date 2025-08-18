from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_cors import CORS
# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)
questions = [
    "1. Hvilken titel eller rolle søger du?</br><span>F.eks.: Marketingkoordinator, Tekstforfatter, Designer eller SoMe-specialist. Hvis du er i tvivl, kan du bare beskrive funktionen.</span>",
    "2. Hvilke opgaver skal personen løse?</br><span>F.eks.: Kampagneprojektledelse, E-mail marketing, Digital annoncering, Udarbejdelse af Content, LinkedIn marketing, Webanalyse, Websiteopdatering, Design, Marketingplanlægning etc.</span>",
    "3. Skal arbejdet udføres hos jer, remote, eller et mix?</br><span>Angiv om arbejdet skal udføres på jeres kontor, hjemmefra/remote – eller en kombination.</span>",
    "4. Hvor mange timer skal personen typisk sætte af pr. uge eller måned – og i hvor lang en periode?</br><span>Skriv et cirka timeforbrug pr. uge og hvor længe opgaven forventes at vare – f.eks.: 15-20 timer i 3 måneder.</span>",
    "5. Har du ellers nogle ønsker eller krav til personens baggrund og kompetencer?</br><span>Her kan du tilføje særlige krav eller ønsker – fx brancheerfaring, eller kendskab til bestemte værktøjer eller andet.</span>"
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

    # Store answer if not first question
    if session_data["q_index"] > 0:
        session_data["answers"].append(user_input)

    # Still have questions left
    if session_data["q_index"] < len(questions):
        question = questions[session_data["q_index"]]
        session_data["q_index"] += 1
        return jsonify({"reply": question, "done": False})

    # All questions answered → Generate job ad
    job_posting = generate_job_posting(session_data["answers"])
    del sessions[user_id]
    return jsonify({
        "reply": "",
        "job_html": job_posting,
        "done": True
    })

def generate_job_posting(answers):
    prompt = f"""
Du er en specialist i at skrive stillingsopslag til freelance- og vikarstillinger inden for marketing, kommunikation, design og digitale roller.
Du skriver annoncer, som følger en fast struktur med tydelige afsnit og professionel tone. 
Du bruger altid 3. person (ikke “du”), og undgår buzzwords og generiske vendinger.
Brug altid ordet "personen" om kandidaten – ikke konsulent/konsulenten osv.
Virksomheden nævnes ikke med navn, men med branche.
Der er kun 2 sæt bullets i opslaget.

OUTPUT FORMAT: Returnér annoncen som gyldig HTML uden ekstra kodeblokke. Brug:
- <b> til fed tekst
- <ul> og <li> til punktopstillinger
- <p> til afsnit
- <h2> til overskrifter

Følg denne præcise struktur:

<h2><b>[Tilknyningsform (freelance, vikar eller begge), titel, type virksomhed, by/område]</b></h2>
<p>[Indledning: Hvad der søges. Til hvilken type virksomhed. Beliggenhed. Samarbejdsform (remote, på lokation, eller et mix)]</p>
<ul>
    <li><b>Omfang:</b> [Dage eller timer per uge eller måned]</li>
    <li><b>Opstart:</b> [Opstartsdato eller ca. opstart]</li>
    <li><b>Periode:</b> [Periode, hvor længe varer samarbejdet?]</li>
</ul>
<p>[Afsnit 1: Opgaver som personen skal løse, samt evt. rollen]</p>
<p>[Afsnit 2: Baggrund og kompetencer personen gerne skal have, erfaring, branchebaggrund]</p>
<p><b>Kompetencer/arbejdsområder:</b></p>
<ul>
    <li>[Vigtig opgave eller kompetence]</li>
    <li>[Vigtig opgave eller kompetence]</li>
</ul>
<p>[Afsnit 3: Øvrige forhold eller kompetencer som er et plus men ikke et krav]</p>
<p>Søg gerne hvis du opfylder kriterierne og er interesseret.</p>
<p>Bedste hilsener<br>Carsten Bjerregaard</p>

Her er oplysningerne fra brugeren:

1. Titel/rolle: {answers[0]}
2. Opgaver: {answers[1]}
3. Lokation/samarbejdsform: {answers[2]}
4. Timer & periode: {answers[3]}
5. Baggrund/krav: {answers[4]}

Vigtige krav:
- Brug kun de oplysninger, brugeren har givet.
- Opfind aldrig detaljer.
- Hold dig til strukturen.
- Returnér kun ren HTML som kan indsættes direkte på en webside.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run(debug=True)
