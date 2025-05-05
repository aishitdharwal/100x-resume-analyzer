import streamlit as st
import PyPDF2
import io
from groq import Groq
import os

# Set up Groq client
client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def analyze_resume(resume_text, job_description):
    prompt = f"""
    Analyze the following resume against the job description:
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Please provide:
    1. Key strengths and matches with the job requirements
    2. Areas where the candidate's profile may fall short
    3. Specific suggestions for improving the resume to better match this role
    4. Overall assessment of fit for the position
    """
    
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="deepseek-r1-distill-llama-70b",
        temperature=0.5,
    )
    
    return completion.choices[0].message.content

# Streamlit UI
st.title("Resume Analysis Tool")
st.write("Upload your resume and enter the job description to get personalized feedback")

# File upload for resume
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

# Text area for job description
job_description = st.text_area("Enter the job description", height=200)

if st.button("Analyze"):
    if uploaded_file is not None and job_description:
        with st.spinner("Analyzing your resume..."):
            # Extract text from PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            # Get analysis
            analysis = analyze_resume(resume_text, job_description)
            
            # Display results
            st.subheader("Analysis Results")
            st.write(analysis)
    else:
        st.error("Please upload a resume and enter a job description")
