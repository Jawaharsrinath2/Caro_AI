import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
import json
import qrcode
from io import BytesIO
import docx2txt
import pdfplumber
import re

# -------------------------
# Load Gemini API Key from Streamlit Secrets
# -------------------------
def load_api_key():
    # Streamlit Cloud's recommended way to access secrets
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY missing. Please set it in Streamlit Cloud Secrets (Advanced Settings).")
        st.stop()
    return api_key

# -------------------------
# Resume Parsing
# -------------------------
def parse_resume(file):
    text = ""
    if file.type == "application/pdf":
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e: # Catch a broader exception for parsing failures
            st.warning(f"PDF parsing failed: {e}. Please check the file format or try another PDF.")
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       "application/msword"]:
        try:
            text = docx2txt.process(file)
        except Exception as e:
            st.warning(f"DOCX parsing failed: {e}. Please check the file format or try another DOCX.")
    return text

# -------------------------
# Extract Skills using Gemini
# -------------------------
def extract_skills(model, resume_text):
    prompt = f"""
    Extract all technical and soft skills from the resume below.
    ONLY respond with a JSON array of strings, where each string is a skill. Do NOT include explanations or extra text outside the JSON array.

    Resume Text:
    {resume_text}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up common markdown fences for JSON
        text = re.sub(r"```json|```", "", text).strip()
        skills = json.loads(text)
        # Ensure skills is a list of strings
        if isinstance(skills, list) and all(isinstance(s, str) for s in skills):
            return skills
        else:
            st.warning("AI extracted skills in unexpected format. Falling back to manual input.")
            return []
    except Exception as e:
        st.warning(f"Skill extraction failed: {e}. Ensure the resume has detectable skills. Raw response: {response.text}")
        return []

# -------------------------
# Generate Career Roadmap
# -------------------------
def generate_roadmap(model, name, age, domain, skills, psychometric):
    prompt = f"""
    Act as a personalized AI career advisor. Output a detailed career roadmap and advice.
    User Details:
    Name: {name}
    Age: {age}
    Domain: {domain}
    Skills: {', '.join(skills)}
    Psychometric Profile: {json.dumps(psychometric)}

    Provide a JSON object with two keys:
    1. "career_advice": A comprehensive, well-structured career plan in Markdown format, covering short-term goals, long-term goals, learning paths, and recommended projects.
    2. "roadmap_svg": An SVG diagram (raw SVG string) visualizing the learning roadmap or career progression, if possible. If not, return an empty string for this key.

    Example JSON structure:
    ```json
    {{
      "career_advice": "# Career Path for {name}...\n\n## Short-Term Goals...\n\n",
      "roadmap_svg": "<svg>...</svg>"
    }}
    ```
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip() # Clean markdown fences
        data = json.loads(text)
        return data.get("career_advice", ""), data.get("roadmap_svg", "")
    except Exception as e:
        st.warning(f"Roadmap generation failed: {e}. Gemini response: {response.text if 'response' in locals() else 'No response'}")
        return "", ""

# -------------------------
# Retry Mechanism for Roadmap
# -------------------------
def generate_roadmap_with_retry(model, name, age, domain, skills, psychometric, retries=2):
    for attempt in range(retries + 1):
        career_advice, roadmap_svg = generate_roadmap(model, name, age, domain, skills, psychometric)
        if career_advice: # We prioritize career advice. SVG can be empty.
            return career_advice, roadmap_svg
        st.info(f"Retrying roadmap generation... (Attempt {attempt + 1}/{retries + 1})")
    return "", "" # Fallback if both fail after retries

# -------------------------
# Skill Gap Analysis
# -------------------------
def skill_gap_analysis(model, domain, skills):
    prompt = f"""
    Given the user's current skills: {', '.join(skills)}, and their desired domain: {domain},
    identify key missing skills (top 5 most crucial) and list priority skills (top 3 for immediate focus).
    Provide the output in JSON format with "missing_skills" (array of strings) and "priority_skills" (array of strings).
    Example:
    ```json
    {{
      "missing_skills": ["Cloud Security", "Advanced Machine Learning", "DevOps Practices"],
      "priority_skills": ["Python Proficiency", "Data Structures", "SQL"]
    }}
    ```
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception as e:
        st.warning(f"Skill gap analysis failed: {e}. Gemini response: {response.text if 'response' in locals() else 'No response'}")
        return {}

# -------------------------
# YouTube Course Recommendations + QR
# -------------------------
def recommend_courses(model, domain):
    prompt = f"""
    Recommend 3 high-quality, comprehensive YouTube course links for someone in the {domain} domain looking to upskill.
    Provide ONLY the direct YouTube URLs, one per line. Do not include any other text or formatting.
    """
    try:
        response = model.generate_content(prompt)
        urls = re.findall(r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|playlist\?list=)[\w-]+)', response.text)
        # Filter for actual YouTube links and ensure no duplicates
        return list(set([u for u in urls if "youtube.com" in u or "youtu.be" in u]))
    except Exception as e:
        st.warning(f"Course recommendation failed: {e}. Gemini response: {response.text if 'response' in locals() else 'No response'}")
        return []

def display_courses_with_qr(video_links):
    if not video_links:
        st.info("No courses recommended at this time.")
        return
    st.subheader("📺 Recommended Courses")
    for idx, url in enumerate(video_links, 1):
        st.markdown(f"- [Course {idx}]({url})")
    merged = "\n".join(video_links)
    if merged: # Only generate QR if there are links
        qr = qrcode.make(merged)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="📱 Scan to access courses", width=150)
        st.download_button("⬇️ Download QR Code", buf.getvalue(), "courses_qr.png", "image/png")

# -------------------------
# Main App
# -------------------------
def main():
    st.set_page_config(page_title="CaroAI", page_icon="🧑‍💻", layout="wide")
    st.title("😎 CaroAI - Personalized Career & Skills Advisor")

    api_key = load_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-pro")

    st.sidebar.header("User Information")
    with st.sidebar:
        name = st.text_input("Enter Your Name", key="name_input")
        age = st.number_input("Enter Your Age", min_value=10, max_value=80, value=25, key="age_input")
        domain = st.selectbox("Select Your Desired Domain", ["Web Development", "Data Science", "AI & ML",
                                                               "Mobile Apps", "Cybersecurity", "Cloud Computing",
                                                               "UI/UX Design", "Project Management", "Other"], key="domain_select")
        if domain == "Other":
            domain = st.text_input("Please Specify Your Domain", key="other_domain_input")

        st.markdown("---")
        st.subheader("🧠 Psychometric Profile")
        st.write("Rate yourself from 1 (low) to 10 (high)")
        psychometric = {}
        psychometric["analytical"] = st.slider("Analytical Skills", 1, 10, 5)
        psychometric["creativity"] = st.slider("Creativity", 1, 10, 5)
        psychometric["communication"] = st.slider("Communication", 1, 10, 5)
        psychometric["problem_solving"] = st.slider("Problem Solving", 1, 10, 5)
        psychometric["adaptability"] = st.slider("Adaptability", 1, 10, 5)
        psychometric["leadership"] = st.slider("Leadership", 1, 10, 5)

    st.header("📄 Upload Your Resume")
    uploaded_file = st.file_uploader("Upload PDF or DOCX file to extract your skills automatically.", type=["pdf", "docx"])
    
    resume_text = ""
    skills = []

    if uploaded_file:
        with st.spinner("Parsing resume..."):
            resume_text = parse_resume(uploaded_file)
        if resume_text:
            st.success("Resume parsed successfully!")
            with st.expander("Preview Parsed Resume Text"):
                st.text_area("", resume_text, height=200)

            with st.spinner("⏳ Extracting skills from your resume using AI..."):
                skills = extract_skills(model, resume_text)
            
            if not skills:
                st.warning("AI could not reliably detect skills from your resume. Please enter your key skills manually below.")
                manual_skills_input = st.text_input("Enter your skills, separated by commas (e.g., Python, SQL, AWS, Communication)")
                skills = [s.strip() for s in manual_skills_input.split(',') if s.strip()]
            else:
                st.info(f"✅ Extracted Skills: {', '.join(skills)}")
        else:
            st.error("Could not parse the uploaded file. Please ensure it's a valid PDF or DOCX.")

    st.markdown("---")
    
    # Show Generate Career Roadmap button only after necessary inputs are available
    if st.button("Generate My Personalized Career Plan", type="primary") and name and domain and skills:
        if not skills:
            st.warning("Please provide your skills either by uploading a resume or entering them manually.")
            st.stop()

        with st.spinner("Crafting your personalized career roadmap, skill analysis, and course recommendations... This may take a moment!"):
            career_advice, roadmap_svg = generate_roadmap_with_retry(model, name, age, domain, skills, psychometric)
            gap_analysis_result = skill_gap_analysis(model, domain, skills)
            video_links = recommend_courses(model, domain)

            # Dashboard tabs
            tabs = st.tabs(["🗺️ Career Plan", "🎓 Courses", "📈 Skill Progress", "💼 Internship Opportunities"])
            
            with tabs[0]:
                if career_advice:
                    st.markdown("### Your Personalized Career Advice")
                    st.markdown(career_advice)
                else:
                    st.info("Career advice not available. Please try again or refine your input.")

                if roadmap_svg:
                    st.subheader("📅 Visual Learning Roadmap")
                    # Using components.html for SVG display
                    components.html(f"""
                        <div style="width:100%; overflow-x:auto; border:1px solid #ccc; padding:10px; background-color: white;">
                            {roadmap_svg}
                        </div>
                    """)
                else:
                    st.info("Visual roadmap not available. Gemini might not have generated it or there was an error.")

            with tabs[1]:
                display_courses_with_qr(video_links)

            with tabs[2]:
                st.subheader("🛠 Skill Gap Analysis")
                if gap_analysis_result:
                    st.markdown("#### Missing Key Skills")
                    if gap_analysis_result.get("missing_skills"):
                        for skill in gap_analysis_result["missing_skills"]:
                            st.markdown(f"- {skill}")
                    else:
                        st.info("No specific missing skills identified at this time.")
                    
                    st.markdown("#### Priority Skills for Immediate Focus")
                    if gap_analysis_result.get("priority_skills"):
                        for skill in gap_analysis_result["priority_skills"]:
                            st.markdown(f"- {skill}")
                    else:
                        st.info("No specific priority skills identified at this time.")
                else:
                    st.info("Unable to perform a comprehensive skill gap analysis. Please ensure your domain and skills are clear.")

            with tabs[3]:
                st.subheader("🚀 Internship & Job Opportunities (Demo)")
                st.write("This section would integrate with job boards to find relevant opportunities based on your profile and roadmap.")
                if st.button("Explore Matching Internships"):
                    st.success("🎉 Searching for opportunities... (This is a demo action)")
                    st.info("In a full application, this would link to real job listings.")

    elif uploaded_file and (not name or not domain):
        st.warning("Please fill in your Name, Age, and Domain to generate the career plan.")
    elif not uploaded_file:
        st.info("Upload your resume and fill out your information to get started!")

if __name__ == "__main__":
    main()