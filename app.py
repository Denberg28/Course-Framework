import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# --- App UI Setup ---
st.set_page_config(page_title="Course Framework", page_icon="🛩️", layout="wide")
st.title("🛩️ Course Framework")
st.write("Generate course materials, create syllabus format, or view existing Markdown files.")

if not api_key:
    st.error("🔑 API Key Missing! Please configure GEMINI_API_KEY in your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- Layout: Tabs ---
tab1, tab2, tab3 = st.tabs([
    "✨ Generate Course",
    "📘 Syllabus Create",
    "📄 View .md File"
])

# =====================================================
# TAB 1: GENERATE COURSE
# =====================================================
with tab1:
    syllabus_input = st.text_area(
        "Type / Paste your syllabus here:",
        height=220,
        placeholder="e.g., Week 1: Introduction to Aircraft Structures..."
    )

    if st.button("Generate Course Material"):
        if not syllabus_input.strip():
            st.warning("Please enter a syllabus first.")
        else:
            with st.spinner("Generating structured course material..."):
                try:
                    prompt = f"""
You are an expert curriculum developer and instructional designer.

Convert the following syllabus into comprehensive, structured course material.

Rules:
1. Output MUST be strictly in Markdown format.
2. Include headers for each module/week.
3. Under each header, include:
   - Brief introduction
   - Detailed lesson points
   - Summary
4. Do not include conversational filler.

Syllabus:
{syllabus_input}
"""

                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=prompt
                    )

                    st.success("Course generated successfully!")

                    st.download_button(
                        label="⬇️ Download Markdown File",
                        data=response.text,
                        file_name="course_material.md",
                        mime="text/markdown"
                    )

                    st.markdown("### Preview")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")


# =====================================================
# TAB 2: SYLLABUS CREATE
# =====================================================
with tab2:
    st.subheader("📘 Syllabus Create")

    course_code = st.text_input("Course Code:")
    course_name = st.text_input("Course Name:")

    course_description = st.text_area(
        "Course Description:",
        height=120
    )

    col1, col2 = st.columns(2)

    with col1:
        units = st.text_input("Number of Units for Lecture & Laboratory:")
        contact_hours = st.text_input("Numbers of Contact Hours per Week:")
        prerequisite = st.text_input("Pre-requisite:")

    with col2:
        lec_total = st.number_input("Total Lecture Hours:", min_value=0, value=54)
        lab_total = st.number_input("Total Laboratory Hours:", min_value=0, value=0)

    course_objectives = st.text_area(
        "Course Objectives:",
        height=150,
        placeholder="1. Understand...\n2. Apply...\n3. Demonstrate..."
    )

    st.markdown("### Course Outline: Lecture")

    outline_rows = st.number_input(
        "Number of outline rows:",
        min_value=1,
        max_value=50,
        value=10
    )

    outline_data = []

    for i in range(outline_rows):
        c1, c2, c3 = st.columns([6, 1, 1])

        with c1:
            topic = st.text_input(f"Topic {i + 1}", key=f"topic_{i}")

        with c2:
            lec_hrs = st.number_input(
                "LEC HRS",
                min_value=0,
                value=0,
                key=f"lec_{i}"
            )

        with c3:
            lab_hrs = st.number_input(
                "LAB HRS",
                min_value=0,
                value=0,
                key=f"lab_{i}"
            )

        outline_data.append((topic, lec_hrs, lab_hrs))

    references = st.text_area(
        "Suggested Textbooks and References:",
        height=120,
        placeholder="1. Book title, Author, Year\n2. Reference material..."
    )

    if st.button("Create Syllabus Markdown"):
        syllabus_md = f"""# Course Syllabus

| Field | Details |
|---|---|
| **Course Code** | {course_code} |
| **Course Name** | {course_name} |
| **Course Description** | {course_description} |
| **Number of Units for Lecture & Laboratory** | {units} |
| **Numbers of Contact Hours per Week** | {contact_hours} |
| **Pre-requisite** | {prerequisite} |

## Course Objectives

{course_objectives}

## Course Outline: Lecture

| Topics | LEC HRS | LAB HRS |
|---|---:|---:|
"""

        for topic, lec_hrs, lab_hrs in outline_data:
            if topic.strip():
                syllabus_md += f"| {topic} | {lec_hrs} | {lab_hrs} |\n"

        syllabus_md += f"""

| **Total** | **{lec_total}** | **{lab_total}** |

## Suggested Textbooks and References

{references}
"""

        st.success("Syllabus created successfully!")

        st.download_button(
            label="⬇️ Download Syllabus Markdown",
            data=syllabus_md,
            file_name="syllabus.md",
            mime="text/markdown"
        )

        st.markdown("### Preview")
        st.markdown(syllabus_md)


# =====================================================
# TAB 3: VIEW .MD FILE
# =====================================================
with tab3:
    st.subheader("Upload Existing Course Material")

    uploaded_file = st.file_uploader(
        "Upload a Markdown (.md) file to preview it",
        type=["md"]
    )

    if uploaded_file is not None:
        markdown_content = uploaded_file.getvalue().decode("utf-8")

        st.markdown("---")
        st.markdown("### Document Preview")
        st.markdown(markdown_content)
