import os
import fitz  # PyMuPDF
import spacy
import google.generativeai as genai
import streamlit as st

# ✅ Google Gemini AI API Key
genai.configure(api_key="AIzaSyA1r-fmE3Q2LiDzFdiabESKCEObCgsoeEc")

# ✅ Load spaCy NLP Model
nlp = spacy.load("en_core_web_sm")

# ✅ Global Companies & Roles Dictionary
companies = {
    "TCS": ["Prime Role", "Digital Role", "Ninja Role"],
    "Infosys": ["SE Role", "Digital Specialist", "Power Programmer"],
    "Wipro": ["Project Engineer", "Elite Role", "Turbo Role"],
    "Cognizant": ["GenC", "GenC Next", "GenC Elevate"],
    "HCL": ["Software Engineer", "Tech Lead", "Graduate Trainee"],
    "Accenture": ["Associate Software Engineer", "Advanced App Developer", "Software Developer"],
    "Capgemini": ["Software Engineer", "Tech Consultant", "AI Specialist"],
    "IBM": ["Data Scientist", "Cloud Engineer", "Software Developer"],
    "Deloitte": ["Analyst", "Consultant", "Data Engineer"],
    "EY": ["Technology Consultant", "Risk Analyst", "Data Analyst"],
    "KPMG": ["Cybersecurity Analyst", "Business Analyst", "Technology Advisor"],
    "Amazon": ["Software Developer", "Data Engineer", "Cloud Architect"],
    "Microsoft": ["Software Engineer", "AI Engineer", "Cloud Developer"],
    "Google": ["AI Researcher", "ML Engineer", "Software Engineer"],
    "Apple": ["iOS Developer", "Machine Learning Engineer", "Security Engineer"]
}

# ✅ Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return "\n".join([page.get_text("text") for page in doc]).strip()
    except Exception as e:
        st.error(f"❌ Error extracting text: {e}")
        return ""

# ✅ Analyze Resume
def analyze_resume(text):
    doc = nlp(text)
    skills = {"python", "java", "sql", "machine learning", "data analysis", "cloud computing", "cybersecurity", "devops"}
    extracted_skills = [token.text for token in doc if token.text.lower() in skills]
    projects = [sent.text for sent in doc.sents if "project" in sent.text.lower()]
    certifications = [sent.text for sent in doc.sents if "certification" in sent.text.lower()]
    extracurricular = [sent.text for sent in doc.sents if any(word in sent.text.lower() for word in ["volunteer", "club", "sports", "hackathon"])]
    return {
        "Skills": extracted_skills,
        "Projects": projects,
        "Certifications": certifications,
        "Extracurricular": extracurricular
    }

# ✅ Google Gemini Prompt Helpers
def generate_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-pro")
    return model.generate_content(prompt).text

def generate_resume_questions(analysis):
    prompt = f"""
    Generate interview questions based on:
    - Projects: {', '.join(analysis.get('Projects', [])) or 'None'}
    - Skills: {', '.join(analysis.get('Skills', [])) or 'None'}
    - Certifications: {', '.join(analysis.get('Certifications', [])) or 'None'}
    - Extracurricular: {', '.join(analysis.get('Extracurricular', [])) or 'None'}
    """
    return generate_gemini_response(prompt)

def generate_answer_approaches(questions):
    return generate_gemini_response(f"Provide structured best approaches to answer:\n{questions}")

def generate_role_based_questions(company, role):
    prompt = f"Generate top interview questions (technical, coding, HR) for {company} - {role}"
    return generate_gemini_response(prompt)

def generate_preparation_resources(company, role):
    prompt = f"""
    Suggest best websites, platforms, and YouTube channels for interview preparation:
    - Company: {company}
    - Role: {role}
    Include resources for coding, system design, aptitude, and HR rounds.
    Provide links where possible.
    """
    return generate_gemini_response(prompt)

def fetch_previous_coding_questions(company, role):
    prompt = f"""
    Provide previous years' coding interview questions with detailed answers for:
    - Company: {company}
    - Role: {role}
    Include difficulty (Easy, Medium, Hard) and step-by-step solutions.
    """
    return generate_gemini_response(prompt)

# ✅ Main SHOW Function
def show():
    st.title("🎯 Smart Interview Guide")
    st.image("https://source.unsplash.com/800x300/?interview,career", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        company = st.selectbox("🏢 Select a Company:", list(companies.keys()))
    with col2:
        job_role = st.selectbox("💼 Select a Job Role:", companies[company])

    uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")

    # Initialize Session State
    for key in ["resume_text", "resume_analysis", "resume_questions", "resume_approaches", "role_questions", "role_approaches", "prep_resources", "prev_coding_qna"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    # Process Uploaded Resume
    if uploaded_file:
        with st.spinner("🔍 Extracting Resume..."):
            with open("resume.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.resume_text = extract_text_from_pdf("resume.pdf")
            st.session_state.resume_analysis = analyze_resume(st.session_state.resume_text)

        st.subheader("📜 Extracted Resume Text")
        st.text_area("Resume Content", st.session_state.resume_text, height=200)

        if st.button("📌 Get Resume-Based Questions"):
            with st.spinner("🚀 Generating Questions..."):
                st.session_state.resume_questions = generate_resume_questions(st.session_state.resume_analysis)

    if st.session_state.resume_questions:
        st.subheader("📝 Resume-Based Interview Questions")
        st.text_area("Generated Questions", st.session_state.resume_questions, height=300)

        if st.button("💡 Generate Best Answer Approaches"):
            with st.spinner("💡 Generating Answer Approaches..."):
                st.session_state.resume_approaches = generate_answer_approaches(st.session_state.resume_questions)

    if st.session_state.resume_approaches:
        st.subheader("💡 Structured Approach to Resume-Based Questions")
        st.text_area("Answer Approach", st.session_state.resume_approaches, height=300)

    if st.button("📌 Get Top Interview Questions (Past Years)"):
        with st.spinner("🔍 Fetching Questions..."):
            st.session_state.role_questions = generate_role_based_questions(company, job_role)

    if st.session_state.role_questions:
        st.subheader("📝 Role-Based Interview Questions")
        st.text_area("Generated Questions", st.session_state.role_questions, height=300)

        if st.button("💡 Generate Best Role-Based Answer Approaches"):
            with st.spinner("💡 Generating Answer Approaches..."):
                st.session_state.role_approaches = generate_answer_approaches(st.session_state.role_questions)

    if st.session_state.role_approaches:
        st.subheader("💡 Structured Approach to Role-Based Questions")
        st.text_area("Answer Approach", st.session_state.role_approaches, height=300)

    if st.button("📌 Get Previous Years' Coding Questions & Answers"):
        with st.spinner("🔍 Fetching Coding Questions..."):
            st.session_state.prev_coding_qna = fetch_previous_coding_questions(company, job_role)

    if st.session_state.prev_coding_qna:
        st.subheader("💻 Previous Coding Questions & Answers")
        st.text_area("Coding Questions", st.session_state.prev_coding_qna, height=400)

    if st.button("🔍 Get Best Interview Preparation Resources"):
        with st.spinner("🔍 Fetching resources..."):
            st.session_state.prep_resources = generate_preparation_resources(company, job_role)

    if st.session_state.prep_resources:
        st.subheader("🔗 Recommended Resources")
        st.markdown(st.session_state.prep_resources, unsafe_allow_html=True)

    st.markdown("Developed with ❤️ for Job Seekers", unsafe_allow_html=True)

# ✅ Run Show Function
if __name__ == "__main__":
    show()

