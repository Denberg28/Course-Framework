import re
import streamlit as st


def slug_title(line: str, index: int) -> str:
    text = re.sub(r"^\s*(week|module|unit|lesson)\s*\d*\s*[:.\-]?\s*", "", line, flags=re.I).strip()
    return text or f"Module {index}"


def build_course_markdown(syllabus: str) -> str:
    entries = [line.strip(" -\t") for line in syllabus.splitlines() if line.strip()]
    if not entries:
        return ""

    sections = ["# Course Material", "", "Generated locally from the supplied syllabus. No external AI/API service is used.", ""]
    for index, entry in enumerate(entries, 1):
        title = slug_title(entry, index)
        sections.extend([
            f"## Module {index}: {title}",
            "",
            "### Overview",
            f"This module covers **{title}** based on the supplied syllabus item: _{entry}_.",
            "",
            "### Learning Objectives",
            f"- Explain the key concepts associated with {title}.",
            f"- Apply the main principles of {title} in guided activities.",
            f"- Check understanding through a short assessment or reflection.",
            "",
            "### Lesson Focus",
            f"- Core terminology and concepts for {title}",
            f"- Practical examples and applications of {title}",
            f"- Common errors, limitations, or safety considerations where relevant",
            "",
            "### Suggested Activity",
            f"Create one short exercise, example, or discussion task that demonstrates {title}.",
            "",
            "### Assessment",
            f"Use a brief quiz, worksheet, demonstration, or reflection to verify understanding of {title}.",
            "",
            "### Summary",
            f"Review the essential ideas, applications, and takeaways for {title}.",
            "",
        ])
    return "\n".join(sections).strip() + "\n"


st.set_page_config(page_title="Course Framework", page_icon="🛩️", layout="centered")
st.title("🛩️ Course Framework")
st.write("Convert a syllabus into a structured Markdown course framework locally, or preview existing Markdown materials.")

tab1, tab2 = st.tabs(["✨ Generate Course", "📄 View .md File"])

with tab1:
    syllabus_input = st.text_area(
        "Type / paste your syllabus here:",
        height=200,
        placeholder="e.g., Week 1: Introduction to Python\nWeek 2: Data Structures..."
    )

    if st.button("Generate Course Material"):
        if not syllabus_input.strip():
            st.warning("Please enter a syllabus first.")
        else:
            course_markdown = build_course_markdown(syllabus_input)
            st.success("Course framework generated locally.")
            st.download_button(
                label="⬇️ Download Markdown File",
                data=course_markdown,
                file_name="course_material.md",
                mime="text/markdown"
            )
            st.markdown("---")
            st.markdown("### Preview")
            st.markdown(course_markdown)

with tab2:
    st.subheader("Upload Existing Course Material")
    uploaded_file = st.file_uploader("Upload a Markdown (.md) file to preview it", type=["md"])

    if uploaded_file is not None:
        markdown_content = uploaded_file.getvalue().decode("utf-8")
        st.markdown("---")
        st.markdown("### Document Preview")
        st.markdown(markdown_content)
