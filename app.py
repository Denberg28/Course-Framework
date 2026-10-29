"""Optional Streamlit interface to the same Windows course authoring core."""
import streamlit as st

from course_core import (CourseError, SAMPLE, VERSION, analyze_syllabus, build_course_markdown,
                         export_bundle, extract_text, load_project, make_project, project_bytes)
from engines import EngineConfig, PROVIDERS, generate_course

st.set_page_config(page_title="Course Framework", page_icon="📘", layout="wide")
for key, default in {"source": "", "course_title": "", "content": "", "engine_used": "Local template",
                     "candidate": "", "candidate_source": "", "candidate_title": "",
                     "candidate_engine": "Local template", "notice": "", "notice_error": False}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def notice(text, error=False):
    st.session_state.notice = text
    st.session_state.notice_error = error


def example():
    st.session_state.source = SAMPLE
    st.session_state.course_title = "Aircraft Structures"
    notice("Example loaded. Review the outline before generating.")


def import_source():
    uploaded = st.session_state.syllabus_file
    if uploaded is None:
        return notice("Choose a syllabus file first.", True)
    if st.session_state.source.strip() and not st.session_state.replace_source:
        return notice("Select Replace syllabus text before importing over existing text.", True)
    try:
        st.session_state.source = extract_text(uploaded.name, uploaded.getvalue())
        notice("Syllabus imported. Review the extracted text and outline.")
    except CourseError as error:
        notice(str(error), True)


def open_project():
    uploaded = st.session_state.project_file
    if uploaded is None:
        return notice("Choose a project file first.", True)
    if (st.session_state.content or st.session_state.source) and not st.session_state.replace_project:
        return notice("Download your project and select Replace current project before opening another.", True)
    try:
        project = load_project(uploaded.getvalue())
        st.session_state.update(source=project["syllabus"], course_title=project["title"], content=project["content"],
                                engine_used=project["engine"], candidate="")
        notice("Project opened.")
    except CourseError as error:
        notice(str(error), True)


def accept_draft():
    if not st.session_state.candidate:
        return
    if (st.session_state.content or st.session_state.source != st.session_state.candidate_source) and not st.session_state.replace_draft:
        return notice("Select Replace accepted course before accepting this generated draft.", True)
    st.session_state.content = st.session_state.candidate
    st.session_state.source = st.session_state.candidate_source
    st.session_state.course_title = st.session_state.candidate_title
    st.session_state.engine_used = st.session_state.candidate_engine
    st.session_state.candidate = ""
    notice("Draft accepted. Edit the course and download a project to keep your work.")


def revise():
    try:
        state = st.session_state
        if not state.content.strip() or not state.revision_instructions.strip():
            raise CourseError("Enter a course draft and revision instructions first.")
        if state.provider != "Local template" and not state.online_consent:
            raise CourseError("Select Send syllabus/draft to the selected engine before online revision.")
        with st.spinner("Revising a copy of your course…"):
            candidate = generate_course(state.source, state.course_title,
                EngineConfig(state.provider, state.api_key, state.model, state.endpoint),
                draft=state.content, instructions=state.revision_instructions)
        state.update(candidate=candidate, candidate_source=state.source,
                     candidate_title=state.course_title, candidate_engine=state.provider)
        notice("Revision ready. Review the generated draft before accepting it.")
    except CourseError as error:
        notice(str(error), True)


st.title("Course Framework")
st.caption(f"Syllabus → course draft → instructor review · {VERSION}")
st.info("Work is kept in this browser session. Download a project to retain it across browser reloads or server restarts.")
if st.session_state.notice:
    (st.error if st.session_state.notice_error else st.success)(st.session_state.notice)

with st.sidebar:
    st.subheader("Engine")
    provider = st.selectbox("Provider", PROVIDERS, key="provider")
    api_key = st.text_input("API key", type="password", key="api_key")
    model = st.text_input("Model ID", value="gemini-2.5-flash-lite", key="model")
    endpoint = st.text_input("API base URL (OpenAI-compatible)", value="https://api.openai.com/v1", key="endpoint")
    st.button("Clear API key", on_click=lambda: st.session_state.update(api_key=""))
    online_consent = st.checkbox("Send syllabus/draft to the selected engine", key="online_consent")
    st.caption("Keys stay in this session and are excluded from project exports. Provider fees/quotas may apply. A compatible provider, endpoint, and model are required.")
    st.divider()
    st.subheader("Open a project")
    st.file_uploader("Course project JSON", type=["json"], key="project_file")
    st.checkbox("Replace current project", key="replace_project")
    st.button("Open project", on_click=open_project)
    st.caption("The Windows edition also supports local OpenAI-compatible servers. This hosted interface accepts public HTTPS endpoints only.")

source_tab, course_tab, preview_tab = st.tabs(["1 · Syllabus", "2 · Course editor", "3 · Preview & export"])

with source_tab:
    left, right = st.columns([3, 2])
    with left:
        st.button("Load example", on_click=example)
        with st.expander("Import syllabus"):
            st.file_uploader("TXT, Markdown, DOCX, or text-based PDF · up to 8 MB", type=["txt", "md", "docx", "pdf"], key="syllabus_file")
            st.checkbox("Replace syllabus text", key="replace_source")
            st.button("Import text", on_click=import_source)
        st.text_area("Syllabus", key="source", height=360, max_chars=180000,
                     placeholder="Course Name: ...\nLearning Outcomes:\n1. ...\nTopics:\nWeek 1: ...")
        st.text_input("Course title", key="course_title", max_chars=300)
    with right:
        st.subheader("Detected outline")
        if st.session_state.source.strip():
            try:
                plan = analyze_syllabus(st.session_state.source)
                st.caption(f"{len(plan['topics'])} modules · {len(plan['outcomes'])} course outcomes")
                for warning in plan["warnings"]:
                    st.warning(warning)
                st.dataframe([{"Module": i, "Week(s)": t["schedule"] or "Unassigned", "Topic": t["title"]}
                              for i, t in enumerate(plan["topics"], 1)], hide_index=True, width="stretch")
                with st.expander("Outcomes and references"):
                    st.write(plan["outcomes"])
                    st.write(plan["references"])
            except CourseError as error:
                st.error(str(error))
        else:
            st.caption("Paste a syllabus or load the example. Edit the source to correct the detected structure.")
    if st.button("Generate course", type="primary"):
        try:
            if provider != "Local template" and not online_consent:
                raise CourseError("Select Send syllabus/draft to the selected engine before online generation.")
            title = st.session_state.course_title.strip() or analyze_syllabus(st.session_state.source)["metadata"].get("title", "Untitled Course")
            with st.spinner("Generating a review draft…"):
                candidate = generate_course(st.session_state.source, title, EngineConfig(provider, api_key, model, endpoint))
            st.session_state.update(candidate=candidate, candidate_source=st.session_state.source,
                                    candidate_title=title, candidate_engine=provider)
            st.success("Draft ready in Course editor. Your accepted course is preserved until you use it.")
        except CourseError as error:
            st.error(str(error))

with course_tab:
    if st.session_state.candidate:
        st.subheader("Generated draft · review before accepting")
        st.caption("This pending draft is kept only in the current session. Accept it before saving a course project.")
        st.text_area("Generated Markdown", key="candidate", height=300, max_chars=400000)
        st.checkbox("Replace accepted course", key="replace_draft")
        st.button("Use this draft", on_click=accept_draft)
    st.subheader("Accepted course")
    st.text_area("Course material (Markdown)", key="content", height=440, max_chars=400000)
    st.text_input("Revision instructions", key="revision_instructions", max_chars=5000,
                  placeholder="Add worked examples to module 2 and preserve the remaining modules.")
    st.button("Revise with engine", on_click=revise)

with preview_tab:
    try:
        project = make_project(st.session_state.source, st.session_state.course_title,
                               st.session_state.content, st.session_state.engine_used)
        a, b, c = st.columns(3)
        a.download_button("Save project JSON", project_bytes(project), "course-project.json", "application/json", width="stretch")
        b.download_button("Course Markdown", project["content"], "course.md", "text/markdown", disabled=not project["content"], width="stretch")
        c.download_button("Complete course ZIP", export_bundle(project), "course-package.zip", "application/zip", disabled=not project["content"], width="stretch")
        st.caption("Review facts, answers, coverage, grading, and references before sharing. Local mode creates a framework with explicit content placeholders.")
        if project["content"]:
            st.markdown(project["content"], unsafe_allow_html=False)
        else:
            st.caption("Generate and accept a draft, or write material in the course editor.")
    except CourseError as error:
        st.error(str(error))
