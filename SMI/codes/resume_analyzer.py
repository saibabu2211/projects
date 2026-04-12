import os
import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai
from fpdf import FPDF
import re

# ✅ Configure Google Gemini AI API Key
GEMINI_API_KEY = "AIzaSyA1r-fmE3Q2LiDzFdiabESKCEObCgsoeEc"  # Replace with your actual API Key
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Custom Styling
st.markdown("""
    <style>
        .stFileUploader { border: 2px dashed #4CAF50 !important; padding: 10px; border-radius: 10px; }
        .stTextArea textarea { font-size: 16px; font-family: Arial, sans-serif; }
        .score-box { font-size: 24px; font-weight: bold; color: #4CAF50; text-align: center; padding: 10px; border: 2px solid #4CAF50; border-radius: 10px; width: 200px; margin: auto; }
    </style>
""", unsafe_allow_html=True)

# ✅ Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        if text.strip():
            return text.strip()
    except Exception as e:
        st.warning("⚠ Using OCR for image-based PDF...")
        try:
            images = convert_from_path(pdf_path)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
        except Exception as e:
            st.error(f"OCR failed: {e}")
            return ""
    return text.strip()

# ✅ Function to analyze resume
def analyze_resume(resume_text, job_description=""):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    Analyze the resume and compare it to the job description.
    
    Provide:
    - Strengths
    - Weaknesses
    - Existing Skills
    - Skills to Improve
    - Recommended Online Courses
    - Best Job Roles
    - Suggested Keywords
    - Summary
    - Resume Score (out of 10)

    Resume:
    {resume_text}

    Job Description:
    {job_description if job_description else "No job description provided"}
    """

    response = model.generate_content(prompt)
    return response.text.strip() if response and response.text else "⚠ No AI response received."

# ✅ Function to generate enhanced resume (ATS Optimized)
def generate_enhanced_resume(resume_text, job_description=""):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    Improve the resume by making it ATS-friendly and optimized based on the provided job description.

    Resume:
    {resume_text}

    Job Description:
    {job_description if job_description else "No job description provided"}
    """

    response = model.generate_content(prompt)
    return response.text.strip() if response and response.text else "⚠ No AI response received."

# ✅ Function to clean text (remove unsupported characters)
def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters

# ✅ Function to generate ATS-friendly resume PDF and save to "Downloads" folder
def create_pdf(enhanced_resume_text, file_name="Enhanced_Resume.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    enhanced_resume_text = clean_text(enhanced_resume_text)

    for line in enhanced_resume_text.split("\n"):
        pdf.cell(200, 7, txt=line, ln=True)

    # ✅ Get the user's Downloads folder
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    pdf_path = os.path.join(downloads_folder, file_name)

    # ✅ Save the PDF to the Downloads folder
    pdf.output(pdf_path)

    return pdf_path

# ✅ Show Function with Sidebar and Resume Analyzer Integration
def show():
    # Sidebar UI elements
    st.sidebar.header("📂 Upload Your Resume")
    uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

    st.sidebar.header("🔎 Compare with a Job Description (Optional)")
    job_description = st.sidebar.text_area("Paste job description here", height=200)

    # File Processing & AI Analysis
    if uploaded_file:
        with st.spinner("📄 Extracting resume text..."):
            with open("temp_resume.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            resume_text = extract_text_from_pdf("temp_resume.pdf")

        if resume_text:
            with st.expander("📜 **Extracted Resume Text**", expanded=False):
                st.text_area("Extracted Text", resume_text, height=200)

            if st.button("🔍 Analyze Resume"):
                with st.spinner("🤖 Analyzing with AI..."):
                    analysis_result = analyze_resume(resume_text, job_description)

                st.subheader("📊 AI Analysis Result")
                st.text_area("AI Analysis", analysis_result, height=300)

            if job_description:
                if st.button("📄 Generate Enhanced Resume"):
                    with st.spinner("🔍 Optimizing Resume..."):
                        enhanced_resume = generate_enhanced_resume(resume_text, job_description)

                    st.subheader("📄 Enhanced Resume")
                    st.text_area("Optimized Resume", enhanced_resume, height=300)

                    # ✅ Save and Download PDF
                    pdf_path = create_pdf(enhanced_resume)
                    st.success(f"✅ Enhanced resume saved in: {pdf_path}")

                    with open(pdf_path, "rb") as f:
                        st.download_button(label="📥 Download Enhanced Resume (PDF)", 
                                           data=f, 
                                           file_name="Enhanced_Resume.pdf", 
                                           mime="application/pdf")
