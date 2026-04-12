import os
import re
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import assemblyai as aai
from pypdf import PdfReader
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import cv2
from ultralytics import YOLO
from deepface import DeepFace
import numpy as np
import tempfile

# Set API keys
os.environ['GOOGLE_API_KEY'] = 'AIzaSyD2_oxzOQQtcGDmW_Ul8E7mREi_LYYJO9I'
aai.settings.api_key = '458d04f86c934454bb8148b4f595a171'
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# Load YOLO Model
yolo_model = YOLO("yolov8s.pt")

def is_valid_name(name):
    return bool(re.fullmatch(r"[A-Za-z\s]+", name))

def is_valid_email(email):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

def is_valid_resume(text_list):
    keywords = ["skills", "certification", "certifications", "projects", "experience", "education"]
    combined = " ".join(text_list).lower()
    return any(kw in combined for kw in keywords)

def generate_summary_prompt(comments):
    comments_text = " ".join(map(str, comments))
    return (
        "Ask first question as Introduce about yourself, next Generate 5 Technical questions "
        "based on this resume(projects, skills) for the candidate from the given resume. "
        "Ask 2 questions on SQL. Ask 2 questions on DBMS. Ask total 10 questions. "
        "I DON'T WANT HEADINGS.. GIVE STRAIGHT 1..... QUESTIONS LINE BY LINE:\n\n" + comments_text
    )

def generate_text(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return [page.extract_text() for page in reader.pages]

def transcribe_video(video_path):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(video_path)
    return transcript.text

def generate_pdf(analysis_report):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Interview Analysis Report", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, analysis_report)
    output_path = "Interview_Analysis_Report.pdf"
    pdf.output(output_path)
    return output_path

def send_email(to_email, pdf_path):
    msg = MIMEMultipart()
    msg['From'] = 'ipams2.ohr@gmail.com'
    msg['To'] = to_email
    msg['Subject'] = "Interview Analysis Report"
    msg.attach(MIMEText("Please find the attached Interview Analysis Report.", 'plain'))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name="Interview_Analysis_Report.pdf")
        part['Content-Disposition'] = 'attachment; filename="Interview_Analysis_Report.pdf"'
        msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('ipams2.ohr@gmail.com', 'boyparupktudwtci')
        server.sendmail('ipams2.ohr@gmail.com', to_email, msg.as_string())

def analyze_answers_with_ai(answers):
    prompt = "Analyze the following answers for an interview. Provide feedback on clarity, correctness, and improvement suggestions:\n\n"
    for i, answer in enumerate(answers, 1):
        prompt += f"Answer {i}: {answer}\n\n"
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content(prompt).text

def extract_frames(video_path, interval=10):
    video = cv2.VideoCapture(video_path)
    frames, count = [], 0
    while True:
        ret, frame = video.read()
        if not ret:
            break
        if count % interval == 0:
            frames.append(frame)
        count += 1
    video.release()
    return frames

def detect_mobile_in_frames(frames):
    for frame in frames:
        results = yolo_model(frame)
        for result in results:
            if 'cell phone' in result.names:
                return True
    return False

def extract_face_embedding(image_path):
    result = DeepFace.represent(img_path=image_path, model_name="Facenet")
    return result[0]["embedding"]

def match_faces(image_embedding, frames):
    for frame in frames:
        path = "temp_frame.jpg"
        cv2.imwrite(path, frame)
        try:
            frame_embedding = extract_face_embedding(path)
            similarity = np.dot(image_embedding, frame_embedding) / (
                np.linalg.norm(image_embedding) * np.linalg.norm(frame_embedding))
            if similarity > 0.9:
                return True
        except Exception:
            continue
    return False

def show():
    st.title("SIC Mock Interview Platform")

    if 'step' not in st.session_state:
        st.session_state.step = 0

    if st.session_state.step == 0:
        name = st.text_input("Enter your full name")
        email = st.text_input("Enter your email")
        if st.button("Next"):
            if not is_valid_name(name):
                st.error("Invalid name.")
            elif not is_valid_email(email):
                st.error("Invalid email.")
            else:
                st.session_state.name = name
                st.session_state.email = email
                st.session_state.step = 1

    elif st.session_state.step == 1:
        st.subheader("Malpractice Detection")
        video_file = st.file_uploader("Upload a short test video for detection", type=["mp4"])
        image_file = st.file_uploader("Upload your photo for verification", type=["jpg", "png"])
        if st.button("Verify") and video_file and image_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(video_file.read())
                video_path = temp_video.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image:
                temp_image.write(image_file.read())
                image_path = temp_image.name

            frames = extract_frames(video_path)
            if detect_mobile_in_frames(frames):
                st.warning("Mobile phone detected.")
            else:
                st.success("No mobile phone detected.")

            embedding = extract_face_embedding(image_path)
            if match_faces(embedding, frames):
                st.success("Face matched successfully.")
                st.session_state.step = 2
            else:
                st.warning("Face mismatch.")

    elif st.session_state.step == 2:
        st.subheader("Upload Your Resume")
        pdf_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])
        if pdf_file:
            comments = extract_text_from_pdf(pdf_file)
            if st.session_state.name.lower() not in " ".join(comments).lower():
                st.error("Name not found in resume.")
            elif not is_valid_resume(comments):
                st.error("Resume missing important sections.")
            else:
                prompt = generate_summary_prompt(comments)
                st.session_state.questions = [
                    {"question": q.strip(), "answer": "", "transcribed": False}
                    for q in generate_text(prompt).split('\n') if q.strip()
                ]
                st.session_state.current_question_index = 0
                st.session_state.step = 3

    elif st.session_state.step == 3:
        index = st.session_state.current_question_index
        st.subheader(f"Q{index+1}: {st.session_state.questions[index]['question']}")

        video_file = st.file_uploader("Upload your video answer", type=["mp4"], key=f"video_{index}")
        if video_file and not st.session_state.questions[index]['transcribed']:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(video_file.read())
                video_path = temp_video.name

            frames = extract_frames(video_path)
            transcript = transcribe_video(video_path)
            st.session_state.questions[index]['answer'] = transcript
            st.session_state.questions[index]['transcribed'] = True
            st.info(f"Transcript: {transcript}")

        if st.button("Next Question") and index < len(st.session_state.questions) - 1:
            st.session_state.current_question_index += 1

        if index == len(st.session_state.questions) - 1 and st.button("Submit Answers"):
            answers = [q['answer'] for q in st.session_state.questions]
            analysis_report = analyze_answers_with_ai(answers)
            pdf_path = generate_pdf(analysis_report)
            send_email(st.session_state.email, pdf_path)
            st.success("Interview report emailed successfully.")
