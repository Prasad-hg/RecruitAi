import re
from pdfminer.high_level import extract_text
import requests

predefined_skills = [
    # Original skills
    "Python", "JavaScript", "Java", "C#", "C++", "HTML", "CSS", "React.js",
    "Node.js", "Angular", "SQL", "Docker", "Kubernetes", "Git", "AWS",
    "Azure", "Machine Learning", "TensorFlow", "Scikit-learn", "PyTorch",
    "Data Science", "Terraform", "Ansible", "Linux", "Prometheus", "Grafana",
    "CloudFormation", "Nagios", "Jenkins", "Shell Script", "Bash", "AgroCD",

    # Additional skills (expanded list)

    # Programming Languages
    "Ruby", "PHP", "Swift", "R", "Go", "TypeScript", "Kotlin", "Perl",
    "MATLAB", "Scala", "Rust", "Julia",

    # Web Development
    "Django", "Flask", "ASP.NET", "Bootstrap", "Tailwind CSS",
    "Next.js", "Nuxt.js",

    # Mobile Development
    "React Native", "Flutter", "Xamarin", "Ionic", "Cordova",

    # Data Science & Machine Learning
    "Keras", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter Notebook",
    "OpenCV", "Dask", "NLTK", "SpaCy", "H2O.ai", "Apache Spark", "Hadoop",

    # Cloud Computing
    "Google Cloud Platform (GCP)", "IBM Cloud", "Oracle Cloud", "DigitalOcean",
    "Linode", "Heroku",

    # DevOps & CI/CD
    "GitLab CI/CD", "CircleCI", "Travis CI", "Chef", "Puppet",

    # Cybersecurity
    "Penetration Testing", "Vulnerability Assessment", "Ethical Hacking",
    "Wireshark", "Metasploit", "Nessus", "OWASP", "Burp Suite",
    "Firewall Management", "SIEM",

    # Database Management
    "NoSQL", "MySQL", "PostgreSQL", "MongoDB", "Cassandra", "Redis",
    "SQLite", "Microsoft SQL Server", "Oracle DB", "Firebase",

    # Big Data
    "Apache Hive", "Apache Kafka", "Google BigQuery",

    # Artificial Intelligence
    "Deep Learning", "Reinforcement Learning", "Natural Language Processing",
    "Computer Vision", "Generative AI", "AI Model Deployment (ONNX, TensorFlow Serving)",

    # Tools & Utilities
    "SVN", "PowerShell", "zsh", "Vim", "Emacs", "Visual Studio Code",
    "Eclipse", "IntelliJ IDEA", "Notepad++",

    # Project Management & Collaboration
    "Jira", "Trello", "Asana", "Slack", "Microsoft Teams", "Confluence",
    "Monday.com",

    # Soft Skills
    "Team Leadership", "Communication", "Problem-Solving", "Agile Methodology",
    "Scrum Framework", "Kanban",

    # Emerging Technologies
    "Blockchain", "Ethereum", "Hyperledger", "Solidity", "Web3.js",
    "Internet of Things (IoT)", "Quantum Computing"
]


def extract_text_from_pdf(pdf_path):
    """
    Extracts raw text from the PDF using pdfminer.
    """
    try:
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def clean_text(text):
    """
    Cleans the extracted text by removing unnecessary characters and normalizing spacing.
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s*-\s*', ' ', text)
    text = re.sub(r'\bJava\s*Script\b', 'JavaScript', text)
    text = re.sub(r'\bTensor\s*Flow\b', 'TensorFlow', text)
    return text.strip()

def extract_matching_skills(text):
    """
    Matches predefined skills within the extracted text.
    """
    matched_skills = []
    text = re.sub(r'\s*[-,;|]\s*', ' ', text)
    for skill in predefined_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            matched_skills.append(skill)
    return matched_skills

def generate_questions(skills, difficulty="Medium", max_questions=5):
    """
    Sends extracted skills to the Gemini API to generate technical questions.
    """
    api_key = "AIzaSyBSHOvlw-0cFfL0oDzwhXU32RPcF4iY7jM"
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

    prompt = f"Generate up to {max_questions} technical interview questions for a {difficulty} role based on the following skills: {', '.join(skills)}."
    prompt += " The questions should be simple and clear, without any unnecessary labels, formatting, or information in parentheses. Return only the question text without references to the skills and also dont provide the question numbers"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()

        questions = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        if questions:

            questions_list = questions.split("\n\n")[:max_questions]
            cleaned_questions = []

            for question in questions_list:
                cleaned_question = re.sub(r"^\d+\.\s*\*\*[^*]+\*\*\s*:", "", question).strip()

                cleaned_questions.append(cleaned_question)

            return cleaned_questions
        else:
            print("No questions found in the response.")
            return []

    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def process_resume(pdf_path, difficulty="Medium"):
    """
    Main function to process a resume, extract skills, and generate questions.
    """
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        raise Exception("No text extracted from the resume.")

    cleaned_text = clean_text(extracted_text)
    matched_skills = extract_matching_skills(cleaned_text)

    if not matched_skills:
        raise Exception("No skills found in the resume.")

    questions = generate_questions(matched_skills, difficulty)
    if not questions:
        raise Exception("No questions analyzed")

    return questions
