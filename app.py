
import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# --- App UI Setup ---
st.set_page_config(page_title="Course Framework", page_icon="🛩️", layout="centered")
st.title("🛩️ Course Framework")
st.write("Convert a simple syllabus into structured Markdown course material instantly, or view existing materials.")

# --- Layout: Tabs ---
tab1, tab2 = st.tabs(["✨ Generate Course", "📄 View .md File"])

with tab1:
    # --- User Input ---
    syllabus_input = st.text_area(
        "Type/ Paste your Syllabus here:", 
        height=200, 
        placeholder="e.g., Week 1: Introduction to Python\nWeek 2: Data Structures..."
    )
    
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
                    
                    # Call the model
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
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

with tab2:
    # --- File Upload and Viewer ---
    st.subheader("Upload Existing Course Material")
    uploaded_file = st.file_uploader("Upload a Markdown (.md) file to preview it", type=["md"])
    
    if uploaded_file is not None:
        # Read and decode the file content
        markdown_content = uploaded_file.getvalue().decode("utf-8")
        
        st.markdown("---")
        st.markdown("### Document Preview")
        # Render the markdown directly in Streamlit
        st.markdown(markdown_content)
