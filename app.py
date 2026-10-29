"""One-page Streamlit authoring: paste, choose an agent, generate, review, save."""
import streamlit as st

from academy_theme import streamlit_css
from course_core import (CourseError, SAMPLE, VERSION, analyze_syllabus, export_bundle,
                         extract_text, load_project, make_project, project_bytes)
from engines import EngineConfig, PROVIDERS
from hosted_keys import gemini_secret
from lesson_format import presentation_parts
from course_workflow import (CUSTOM_MODEL, GEMINI_MODELS, accept_job, advance, can_resume,
                      draft_text, is_complete, new_job)

st.set_page_config(page_title='Course Framework', page_icon='📘', layout='wide')
st.markdown(streamlit_css(), unsafe_allow_html=True)
DEFAULTS = {'source': '', 'course_title': '', 'content': '', 'engine_used': 'Local template',
            'model_used': '', 'accepted_source': '', 'pending': None, 'provider': PROVIDERS[1],
            'api_key': '', 'model_choice': GEMINI_MODELS[0], 'custom_model': '',
            'endpoint': 'https://api.openai.com/v1', 'notice': '', 'notice_error': False,
            'online_consent': False, 'replace_course': False}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
state = st.session_state


def notify(text, error=False):
    state.notice, state.notice_error = text, error


def provider_changed():
    state.api_key, state.online_consent = '', False
    state.model_choice = (GEMINI_MODELS[0] if state.provider == PROVIDERS[1] else
                          'Offline template' if state.provider == PROVIDERS[0] else CUSTOM_MODEL)


def config():
    model = state.custom_model.strip() if state.model_choice == CUSTOM_MODEL else state.model_choice
    key = state.get('api_key', '')
    if state.provider == PROVIDERS[1]:
        key = gemini_secret(st.secrets) or key
    return EngineConfig(state.provider, key, model, state.get('endpoint', 'https://api.openai.com/v1'))


def project():
    title = state.course_title.strip()
    if not title and state.source.strip():
        title = analyze_syllabus(state.source)['metadata'].get('title', '')
    return make_project(state.source, title, state.content, state.engine_used,
                        model=state.model_used, pending=state.pending, accepted_syllabus=state.accepted_source or state.source)


def selected_indices():
    return None if state.get('module_scope', -1) == -1 else [state.module_scope]


def example():
    if state.source.strip() and not state.get('replace_source', False):
        return notify('Select Replace syllabus before loading over existing text.', True)
    state.source, state.course_title = SAMPLE, ''
    notify('Example loaded.')


def import_source():
    file = state.get('syllabus_file')
    if file is None:
        return notify('Choose a syllabus file.', True)
    if state.source.strip() and not state.get('replace_source', False):
        return notify('Select Replace syllabus first.', True)
    try:
        state.source = extract_text(file.name, file.getvalue())
        state.course_title = ''
        notify('Syllabus imported.')
    except CourseError as error:
        notify(str(error), True)


def open_project():
    file = state.get('project_file')
    if file is None:
        return notify('Choose a project file.', True)
    if (state.source or state.content or state.pending) and not state.get('replace_project', False):
        return notify('Save your current project and select Replace project first.', True)
    try:
        saved = load_project(file.getvalue())
        state.update(source=saved['syllabus'], course_title=saved['title'], content=saved['content'],
                     engine_used=saved['engine'], model_used=saved['model'], accepted_source=saved['accepted_syllabus'], pending=saved['pending'],
                     replace_course=False)
        if saved['pending']:
            job = saved['pending']
            if job['provider'] in PROVIDERS:
                if state.provider != job['provider']:
                    state.api_key, state.online_consent = '', False
                state.provider = job['provider']
                state.model_choice = (job['model'] if job['model'] in GEMINI_MODELS else
                                      'Offline template' if state.provider == PROVIDERS[0] else CUSTOM_MODEL)
                state.custom_model = job['model']
        notify('Project opened. Set the original agent/endpoint and session key to resume.')
    except CourseError as error:
        notify(str(error), True)


def generate():
    try:
        cfg = config()
        if cfg.provider != PROVIDERS[0] and not state.online_consent:
            raise CourseError('Allow sending the syllabus to the selected agent first.')
        project()  # Validate all saved/editor fields before any provider call.
        indices = selected_indices()
        resume = can_resume(state.pending, state.source, state.course_title, cfg, indices)
        job = state.pending if resume else new_job(state.source, state.course_title, cfg, indices)
        bar = st.progress(len(job['completed']) / len(job['indices']), text='Generating modules…')
        while not is_complete(job):
            number = job['indices'][len(job['completed'])] + 1
            bar.progress(len(job['completed']) / len(job['indices']), text=f'Generating module {number}…')
            job = advance(job, cfg)
            state.pending = job  # Commit each successful module before requesting the next.
            state.replace_course = False
        bar.progress(1.0, text='Draft ready')
        notify('Draft ready. Review it and select Use draft.')
    except CourseError as error:
        notify(str(error), True)
    except Exception:
        notify('The request stopped unexpectedly. Completed modules and your accepted course are preserved.', True)


def use_draft():
    try:
        if (state.content or (state.pending and state.source != state.pending['syllabus'])) and not state.replace_course:
            raise CourseError('Select Replace current course before using this draft.')
        saved = accept_job(project(), state.pending)
        state.update(source=saved['syllabus'], course_title=saved['title'], content=saved['content'],
                     engine_used=saved['engine'], model_used=saved['model'], accepted_source=saved['accepted_syllabus'], pending=None,
                     replace_course=False)
        notify('Course ready. Edit if needed and save your project.')
    except CourseError as error:
        notify(str(error), True)


def render_course(text):
    for part in presentation_parts(text):
        if part['title']:
            st.markdown(part['title'])
        st.markdown(part['body'], unsafe_allow_html=False)
        if part['assessment']:
            with st.expander('Assessment · 5 questions', expanded=False):
                st.markdown(part['assessment'], unsafe_allow_html=False)
        if part['key']:
            with st.expander('Answer key', expanded=False):
                st.markdown(part['key'], unsafe_allow_html=False)
        if part['references']:
            with st.expander('References', expanded=False):
                st.markdown(part['references'], unsafe_allow_html=False)


st.title('Course Framework')
st.caption('Syllabus → discussion, activity, assessment.')
if state.notice:
    (st.error if state.notice_error else st.success)(state.notice)

left, right = st.columns([2, 3], gap='large')
with left:
    st.text_area('Syllabus', key='source', height=280, max_chars=180000,
                 placeholder='Paste your syllabus here…\n\nWeek 1: Topic\nWeek 2: Topic')
    agent, key = st.columns([1, 1])
    options = ([*GEMINI_MODELS, CUSTOM_MODEL] if state.provider == PROVIDERS[1] else
               ['Offline template'] if state.provider == PROVIDERS[0] else [CUSTOM_MODEL])
    if state.model_choice not in options:
        state.model_choice = options[0]
    agent.selectbox('Agent model', options, key='model_choice', help='Presets are shortcuts; availability depends on your provider account.')
    hosted_key = ''
    if state.provider == PROVIDERS[1]:
        try:
            hosted_key = gemini_secret(st.secrets)
        except CourseError as error:
            st.error(str(error))
    if hosted_key:
        key.caption('Gemini key configured in Secrets')
    elif state.provider != PROVIDERS[0]:
        key.text_input('API key', type='password', key='api_key')
    if state.model_choice == CUSTOM_MODEL:
        st.text_input('Model ID', key='custom_model', placeholder='Provider model ID')
    with st.expander('Settings & files'):
        st.selectbox('Provider', PROVIDERS, key='provider', on_change=provider_changed)
        if state.provider == PROVIDERS[2]:
            st.text_input('API base URL', key='endpoint', on_change=lambda: state.update(online_consent=False))
        st.text_input('Title (optional)', key='course_title')
        if not hosted_key:
            st.button('Clear key', on_click=lambda: state.update(api_key=''))
        st.file_uploader('Import syllabus', type=['txt', 'md', 'docx', 'pdf'], key='syllabus_file')
        st.checkbox('Replace syllabus', key='replace_source')
        a, b = st.columns(2)
        a.button('Import', on_click=import_source)
        b.button('Example', on_click=example)
        st.file_uploader('Open project', type=['json'], key='project_file')
        st.checkbox('Replace project', key='replace_project')
        st.button('Open', on_click=open_project)
        st.caption('Credentials are excluded from projects. Save a project to keep your course and unfinished modules.')
    count = 0
    try:
        if state.source.strip():
            plan = analyze_syllabus(state.source)
            count = len(plan['topics'])
            st.caption(f"{count} modules · {len(plan['outcomes'])} outcomes")
            with st.expander('Outline'):
                for i, topic in enumerate(plan['topics'], 1):
                    st.write(f"{i}. {topic['title']} · {topic['schedule'] or 'Week unassigned'}")
                for warning in plan['warnings']:
                    st.caption(warning)
        scope_options = [-1, *range(count)]
        if state.get('module_scope', -1) not in scope_options:
            state.module_scope = -1
        if count:
            st.selectbox('Modules', scope_options, key='module_scope',
                         format_func=lambda i: f'All modules ({count})' if i == -1 else f"{i + 1}. {plan['topics'][i]['title']}")
        if state.provider != PROVIDERS[0]:
            st.checkbox('Send syllabus to this agent (fees/quota may apply)', key='online_consent')
        resumable = bool(count) and can_resume(state.pending, state.source, state.course_title, config(), selected_indices())
        requests = count if state.get('module_scope', -1) == -1 else 1
        if resumable:
            requests -= len(state.pending['completed'])
        st.button('Resume' if resumable else 'Generate', type='primary', on_click=generate, disabled=not count, width='stretch')
        if count and state.provider != PROVIDERS[0]:
            st.caption(f'{requests} module request(s) · completed modules are kept if a request fails.')
    except CourseError as error:
        st.error(str(error))

with right:
    st.subheader('Course')
    job = state.pending
    if job:
        st.caption(f"Draft · {len(job['completed'])}/{len(job['indices'])} modules · {job['model'] or 'Offline template'}")
        if is_complete(job):
            if state.content or state.source != job['syllabus']:
                st.checkbox('Replace current course', key='replace_course')
            st.button('Use draft', on_click=use_draft, type='primary')
        render_course(draft_text(job))
    elif state.content:
        render_course(state.content)
    else:
        st.caption('Paste a syllabus and generate your first draft.')
    if state.content:
        with st.expander('Edit course' if not job else 'Accepted course'):
            st.text_area('Course Markdown', key='content', height=360, max_chars=400000)
    if state.source or state.content or job:
        st.divider()
        try:
            saved = project()
            a, b = st.columns(2)
            a.download_button('Save project', project_bytes(saved), 'course-project.json', 'application/json', width='stretch')
            b.download_button('Export course', export_bundle({**saved, 'pending': None}), 'course-package.zip',
                              'application/zip', disabled=not state.content, width='stretch')
            st.caption('Review facts, official references, and answer keys before teaching. Save project also keeps unfinished drafts.')
        except CourseError as error:
            st.error(str(error))
