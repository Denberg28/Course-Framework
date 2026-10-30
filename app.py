"""Full-width Streamlit authoring: paste the full syllabus, generate, preview below."""
from pathlib import Path
import streamlit as st

from academy_theme import streamlit_css, streamlit_header
from course_core import (CourseError, VERSION, analyze_syllabus, course_allocation, export_bundle,
                         extract_text, load_project, make_project, project_bytes)
from engines import EngineConfig, PROVIDERS
from hosted_keys import gemini_secret
from lesson_format import presentation_parts
from course_workflow import (CUSTOM_MODEL, GEMINI_MODELS, accept_job, advance, can_resume,
                      draft_text, is_complete, new_job)

st.set_page_config(page_title='Course Framework', page_icon='🛩️', layout='wide')
st.html(streamlit_css())
DEFAULTS = {'source': '', 'course_title': '', 'content': '', 'engine_used': 'Local template',
            'model_used': '', 'accepted_source': '', 'pending': None, 'provider': PROVIDERS[1],
            'api_key': '', 'model_choice': GEMINI_MODELS[0], 'custom_model': '',
            'endpoint': 'https://api.openai.com/v1', 'notice': '', 'notice_error': False,
            'online_consent': False, 'replace_course': False,
            'generation_requested': False, 'generation_status': None}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
state = st.session_state


def notify(text, error=False):
    state.notice, state.notice_error = text, error


def clear_generation_status():
    state.generation_status = None


def queue_generation():
    # Callbacks only queue work. Progress is rendered in the authoring controls.
    state.generation_requested = True
    state.notice = ''


def render_generation_status():
    status = state.generation_status
    if not status:
        return
    if status['total']:
        st.progress(status['completed'] / status['total'], text=status['text'])
    if status.get('error'):
        st.error(status['error'])


def endpoint_changed():
    state.online_consent = False
    clear_generation_status()


def provider_changed():
    clear_generation_status()
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
    state.source = (Path(__file__).parent / 'examples' / 'AE416-syllabus.txt').read_text(encoding='utf-8')
    state.course_title = ''
    clear_generation_status()
    notify('AE 416 example loaded. Generate materials from the full syllabus.')


def import_source():
    file = state.get('syllabus_file')
    if file is None:
        return notify('Choose a syllabus file.', True)
    if state.source.strip() and not state.get('replace_source', False):
        return notify('Select Replace syllabus first.', True)
    try:
        state.source = extract_text(file.name, file.getvalue())
        state.course_title = ''
        clear_generation_status()
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
        clear_generation_status()
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
    state.generation_status = {'completed': 0, 'total': 0, 'text': '', 'error': ''}
    try:
        cfg = config()
        if cfg.provider != PROVIDERS[0] and not state.online_consent:
            raise CourseError('Allow sending the syllabus to the selected agent first.')
        project()  # Validate all saved/editor fields before any provider call.
        indices = selected_indices()
        resume = can_resume(state.pending, state.source, state.course_title, cfg, indices)
        job = state.pending if resume else new_job(state.source, state.course_title, cfg, indices)
        status = state.generation_status
        status.update(completed=len(job['completed']), total=len(job['indices']))
        bar = st.progress(status['completed'] / status['total'], text='Preparing modules…')
        while not is_complete(job):
            number = job['indices'][len(job['completed'])] + 1
            status['text'] = f"Generating module {number} · {status['completed']}/{status['total']} complete"
            bar.progress(status['completed'] / status['total'], text=status['text'])
            job = advance(job, cfg)
            state.pending = job  # Commit each successful module before requesting the next.
            status['completed'] = len(job['completed'])
            state.replace_course = False
        status['text'] = f"Draft ready · {status['completed']}/{status['total']} complete"
        bar.progress(1.0, text=status['text'])
    except CourseError as error:
        state.generation_status['error'] = str(error)
    except Exception:
        state.generation_status['error'] = 'The request stopped unexpectedly. Completed modules and your accepted course are preserved.'
    if state.generation_status['error']:
        status = state.generation_status
        status['text'] = f"Stopped · {status['completed']}/{status['total']} complete" if status['total'] else ''


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
        if not part['title']:
            with st.expander('Course overview', expanded=False):
                st.markdown(part['body'], unsafe_allow_html=False)
            continue
        if part['title']:
            st.markdown(part['title'])
        st.markdown(part['body'], unsafe_allow_html=False)
        if part['assessment']:
            with st.expander('Assessment', expanded=False):
                st.markdown(part['assessment'].replace('\n', '  \n'), unsafe_allow_html=False)
        if part['key']:
            with st.expander('Answer key', expanded=False):
                st.markdown(part['key'], unsafe_allow_html=False)
        if part['references']:
            with st.expander('References', expanded=False):
                st.markdown(part['references'], unsafe_allow_html=False)


st.markdown(streamlit_header(), unsafe_allow_html=True)
if state.notice:
    (st.error if state.notice_error else st.success)(state.notice)

# Keep the original reading order: full-width input, compact controls, output below.
run_generation = False
with st.container(key='syllabus_input'):
    st.markdown('<div id="syllabus" class="cf-section-anchor" tabindex="-1"></div>', unsafe_allow_html=True)
    st.text_area('Syllabus', key='source', height=240, max_chars=180000,
                 on_change=clear_generation_status,
                 placeholder='Paste the full course syllabus: course details, outcomes, topic/hour table, and references.')
    plan, count = None, 0
    try:
        if state.source.strip():
            plan = analyze_syllabus(state.source)
            count = len(plan['topics'])
            st.caption(f"{plan['metadata'].get('code', '')} · {plan['metadata'].get('title', 'Course')} · {count} modules · {len(plan['outcomes'])} outcomes")
            metadata = plan['metadata']
            if 'lecture_hours' in metadata and 'lab_hours' in metadata:
                st.caption(f"{metadata['lecture_hours']:g} lecture h · {metadata['lab_hours']:g} lab h · {metadata.get('hours', '—')} total h")
    except CourseError as error:
        st.error(str(error))
    scope_options = [-1, *range(count)]
    if state.get('module_scope', -1) not in scope_options:
        state.module_scope = -1
    agent, key = st.columns(2)
    options = ([*GEMINI_MODELS, CUSTOM_MODEL] if state.provider == PROVIDERS[1] else
               ['Offline template'] if state.provider == PROVIDERS[0] else [CUSTOM_MODEL])
    if state.model_choice not in options:
        state.model_choice = options[0]
    agent.selectbox('Agent model', options, key='model_choice',
                    on_change=clear_generation_status,
                    help='3.5 Flash-Lite is the default. Choose 3.8 Flash for demanding work. Availability and quotas depend on your provider account.')
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
        st.text_input('Model ID', key='custom_model', placeholder='Provider model ID', on_change=clear_generation_status)
    if state.provider != PROVIDERS[0]:
        st.checkbox('Send syllabus to this agent (fees/quota may apply)', key='online_consent')
    try:
        resumable = bool(count) and can_resume(state.pending, state.source, state.course_title, config(), selected_indices())
        with st.container(key='generation_controls'):
            progress_panel = st.container(key='generation_status')
            with progress_panel:
                if not state.generation_requested:
                    render_generation_status()
            st.button('Generating…' if state.generation_requested else 'Resume' if resumable else 'Generate',
                      key='generate_button', type='primary', on_click=queue_generation,
                      disabled=not count or state.generation_requested, width='stretch')
            run_generation = state.generation_requested
    except CourseError as error:
        st.error(str(error))
    with st.expander('Settings & files'):
        st.selectbox('Provider', PROVIDERS, key='provider', on_change=provider_changed)
        if state.provider == PROVIDERS[2]:
            st.text_input('API base URL', key='endpoint', on_change=endpoint_changed)
        st.text_input('Title (optional)', key='course_title', on_change=clear_generation_status)
        if count:
            st.selectbox('Modules', scope_options, key='module_scope',
                         on_change=clear_generation_status,
                         format_func=lambda i: f'All modules ({count})' if i == -1 else f"{i + 1}. {plan['topics'][i]['title']}")
        if not hosted_key:
            st.button('Clear key', on_click=lambda: state.update(api_key=''))
        st.file_uploader('Import syllabus', type=['txt', 'md', 'docx', 'pdf'], key='syllabus_file')
        st.checkbox('Replace syllabus', key='replace_source')
        a, b = st.columns(2)
        a.button('Import', on_click=import_source)
        b.button('Example', on_click=example, help='Load the complete AE 416 syllabus.')
        st.file_uploader('Open project', type=['json'], key='project_file')
        st.checkbox('Replace project', key='replace_project')
        st.button('Open', on_click=open_project)
        st.caption('Save project keeps accepted material and unfinished modules. Credentials are excluded.')
    if plan:
        with st.expander('Outline'):
            st.markdown(course_allocation(plan))
            for outcome in plan['outcomes']:
                st.caption(outcome)
            for warning in plan['warnings']:
                st.caption(warning)

st.divider()
with st.container(key='course_output'):
    st.subheader('Course material', anchor='course-material')
    job = state.pending
    if state.source or state.content or job:
        try:
            saved = project()
            a, b, c = st.columns(3)
            a.download_button('Save project', project_bytes(saved), 'course-project.json', 'application/json', width='stretch')
            markdown = draft_text(job) if job else state.content
            b.download_button('Download Markdown', markdown, 'course-material-draft.md' if job else 'course-material.md',
                              'text/markdown', disabled=not markdown, width='stretch')
            c.download_button('Export course', export_bundle({**saved, 'pending': None}), 'course-package.zip',
                              'application/zip', disabled=not state.content, width='stretch')
        except CourseError as error:
            st.error(str(error))
    if job:
        st.caption(f"Draft · {len(job['completed'])}/{len(job['indices'])} modules · {job['model'] or 'Offline template'}")
        if is_complete(job):
            if state.content or state.source != job['syllabus']:
                st.checkbox('Replace current course', key='replace_course')
            st.button('Use draft', on_click=use_draft, type='primary', disabled=state.generation_requested)
        render_course(draft_text(job))
    elif state.content:
        render_course(state.content)
    else:
        st.caption('Paste a full syllabus and select Generate. Discussion, activity and assessment appear here.')
    if state.content:
        with st.expander('Edit course' if not job else 'Accepted course'):
            st.text_area('Course Markdown', key='content', height=360, max_chars=400000)
    if job or state.content:
        st.caption('Review facts, references and answer keys before teaching. Save project keeps unfinished drafts.')
        st.markdown('<a class="cf-return" href="#syllabus">↑ Back to syllabus</a>', unsafe_allow_html=True)

# Register every settings/editor widget before rerunning, so its state survives.
if run_generation:
    state.generation_requested = False  # Consume once; reruns never repeat a request.
    with progress_panel:
        generate()
    st.rerun()
