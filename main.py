import streamlit as st
import PyPDF2
import io
from groq import Groq
import os
import boto3
import uuid


# Set up Groq client

try:
    client = Groq(
        api_key=os.environ["GROQ_API_KEY"]
    )
except:
    pass

try:
    aws_access_key = os.environ["AWS_ACCESS_KEY_ID"]
    aws_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
except:
    try:
        with open('rootkey.csv', 'r') as f:
            # Skip header row
            next(f)
            # Read first line containing credentials
            line = f.readline().strip()
            aws_access_key, aws_secret_key = line.split(',')
            print(aws_access_key)
    except:
        st.error("AWS credentials not found in environment variables or rootkey.csv")

def put_item_in_dynamodb(table_name, item):
    """
    Put an item in DynamoDB table using boto3
    
    Args:
        table_name (str): Name of the DynamoDB table
        item (dict): Dictionary containing the item data to be inserted
    
    Returns:
        dict: Response from DynamoDB
    """
    try:
        dynamodb = boto3.resource('dynamodb',
                                aws_access_key_id=aws_access_key,
                                aws_secret_access_key=aws_secret_key,
                                region_name = 'ap-south-1')
        
        table = dynamodb.Table(table_name)
        response = table.put_item(Item=item)
        return response
    except Exception as e:
        st.error(f"Error putting item in DynamoDB: {str(e)}")
        return None




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

# User information input
st.subheader("Personal Information")
col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    current_role = st.text_input("Current Job Role")

with col2:
    city = st.text_input("City")
    years_experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=0)
    target_role = st.text_input("Target Job Role")



# Add a divider for visual separation
st.divider()

# File upload for resume
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")


# Text area for job description
job_description = st.text_area("Enter the job description", height=200)

if st.button("Analyze"):
    if uploaded_file is not None and job_description:
        with st.spinner("Analyzing your resume..."):
            # Extract text from PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            # Upload to S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            bucket_name = 'aishit'
            file_name = f"resumes/{uploaded_file.name}"
            
            # Upload file to S3
            s3_client.upload_fileobj(
                uploaded_file,
                bucket_name,
                file_name
            )
            # Get analysis
            analysis = analyze_resume(resume_text, job_description)
            
            # Display results
            st.subheader("Analysis Results")
            st.write(analysis)


            # Create dictionary for DynamoDB
            user_data = {
                'id': str(uuid.uuid4()),
                'name': name,
                'age': age,
                'current_role': current_role,
                'city': city,
                'years_experience': years_experience,
                'target_role': target_role,
                'job_description': job_description,
                'resume_text': resume_text,
                'analysis': analysis
            }

            put_item_in_dynamodb('100x-resume-analyzer-app', user_data)
    else:
        st.error("Please upload a resume and enter a job description")
