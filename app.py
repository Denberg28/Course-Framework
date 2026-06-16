import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
# --- App UI Setup ---
st.set_page_config(page_title="Course Maker", page_icon="📚", layout="centered")
st.title("📚 Minimalist Course Maker")
st.write("Convert a simple syllabus into structured Markdown course material instantly.")

# --- User Input ---
syllabus_input = st.text_area(
    "Paste your Syllabus here:", 
    height=200, 
    placeholder="e.g., Week 1: Introduction to Python\nWeek 2: Data Structures..."
)
#change test
# --- Generation Trigger ---
if st.button("Generate Course Material"):
    if not syllabus_input.strip():
        st.warning("Please enter a syllabus first.")
    else:
        with st.spinner("Generating structured course material..."):
            try:
                # Prompt enforcing strict instructional design rules
                prompt = f"""
                You are an expert curriculum developer and instructional designer. 
                Convert the following syllabus into comprehensive, structured course material.
                
                Rules:
                1. Output MUST be strictly in Markdown format.
                2. Include headers for each module/week.
                3. Under each header, include a brief introduction, detailed lesson points, and a concluding summary.
                4. Do not include conversational filler; output only the course material.
                
                Syllabus:
                {syllabus_input}
                """
                
                # Call the model (gemini-3.5-flash is best for speed and structured outputs)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                
                st.success("Course generated successfully!")
                
                # --- Export and Preview ---
                st.download_button(
                    label="⬇️ Download Markdown File",
                    data=response.text,
                    file_name="course_material.md",
                    mime="text/markdown"
                )
                
                st.markdown("---")
                st.markdown("### Preview")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
