😎 CaroAI - Personalized Career & Skills Advisor  

CaroAI is a personalized AI-powered career advisor built with Google Cloud Gemini + Streamlit, designed to guide students in India towards the right career paths, skill development, and internships.  

It helps students discover their strengths, bridge skill gaps, and prepare for the rapidly evolving job market.  

---

🚀 Features  

- 🧑‍💼 Smart Resume Parsing – Upload your resume (PDF/DOCX), automatically extract technical & soft skills.  
- 🧠 Psychometric Test – Rate yourself on Analytical, Creativity, Problem Solving, Adaptability, Leadership & more.  
- 📅 Personalized AI Career Roadmap – Gemini generates a 12-month structured roadmap (skills, projects, certifications).  
- 🛠 Skill Gap Analysis – AI highlights missing & priority skills for your chosen domain.  
- 📺 YouTube Course Recommendations – Get curated video courses + auto-generated QR code for easy access.  
- 🚀 Internship Apply (Demo) – One-click internship application simulation.  
- 📊 Dashboard Tabs – Organized into Career Plan, Courses, Skill Progress, and Internship Apply.  

---

🏗️ Architecture  

Frontend: Streamlit  
AI Engine: Google Gemini API (Gemini 2.5 Pro)  
Resume Parsing: pdfplumber, docx2txt  
Skill Extraction & Gap Analysis: Gemini LLM + Regex  
Visualization: SVG Roadmap rendered in-app  
Deployment: Hugging Face Spaces  

---

🔄 Process Flow  

1. Student registers & uploads resume  
2. Resume parsed → Skills extracted (Gemini)  
3. Student completes psychometric self-assessment  
4. Gemini generates career advice + skill roadmap (SVG + markdown)  
5. Skill gap analysis identifies missing skills  
6. Recommended YouTube courses + QR code generated  
7. Student views everything in Dashboard tabs  
8. Optional: Internship apply (demo for hackathon)  

---

🖼️ Demo Screens  

- Resume Upload + Skills Extraction  
- Career Roadmap (AI generated)  
- Skill Gap Analysis Dashboard  
- YouTube Recommendations + QR Code  

---

🔑 Setup Instructions  

1. Clone the repo  
```bash
git clone https://github.com/Jawaharsrinath2/Caro_AI.git
cd Caro_AI

2. Install dependencies
pip install -r requirements.txt

3. Add your Gemini API Key

Get your Gemini API key from Google AI Studio.

Create a .env file or set it as an environment variable:

export GEMINI_API_KEY="your_api_key_here"

4. Run locally
streamlit run app.py
---

👨‍💻 Author

Jawahar Srinath M N
📍 Salem, India
📧 jawaharnatarajan2003@gmail.com
🔗 https://www.linkedin.com/in/jawahar-srinath/
