"""Aero Academy visual tokens and desktop styles; no course or network state."""
PAPER = '#ffffff'
INK = '#102640'
MUTED = '#536174'
LINE = '#e4e9f0'
FIELD = '#fafbfd'
GOLD = '#e6b844'
WARM = '#fff7df'


def apply_desktop_theme(root):
    from tkinter import ttk
    root.configure(background=PAPER)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=PAPER, foreground=INK)
    style.configure('Title.TLabel', font=('Segoe UI', 18))
    style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'))
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Rail.TFrame', background=FIELD)
    style.configure('Rail.TLabel', background=FIELD, foreground=MUTED)
    style.configure('Brand.TLabel', background=FIELD, font=('Segoe UI', 11, 'bold'))
    style.configure('TSeparator', background=LINE)
    style.configure('TButton', padding=(10, 6), background=PAPER, borderwidth=1,
                    bordercolor=LINE, lightcolor=PAPER, darkcolor=PAPER, relief='flat')
    style.map('TButton', background=[('disabled', FIELD), ('active', FIELD)],
              foreground=[('disabled', MUTED)])
    style.configure('Accent.TButton', background=INK, foreground=PAPER,
                    bordercolor=INK, lightcolor=INK, darkcolor=INK)
    style.map('Accent.TButton', background=[('disabled', LINE), ('active', '#203d65')],
              foreground=[('disabled', MUTED), ('!disabled', PAPER)])
    style.configure('Nav.TRadiobutton', padding=(12, 10), background=FIELD,
                    foreground=INK, font=('Segoe UI', 10), relief='flat')
    style.layout('Nav.TRadiobutton', [('Radiobutton.padding', {'sticky': 'nswe', 'children': [
        ('Radiobutton.focus', {'sticky': 'nswe', 'children': [
            ('Radiobutton.label', {'sticky': 'nswe'})]})]})])
    style.map('Nav.TRadiobutton', background=[('selected', GOLD), ('active', WARM)],
              foreground=[('selected', INK)])
    style.configure('TEntry', padding=7, fieldbackground=FIELD, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, insertcolor=INK)
    style.map('TEntry', bordercolor=[('focus', INK)])
    style.configure('TCombobox', padding=7, fieldbackground=FIELD, background=PAPER,
                    bordercolor=LINE, arrowcolor=INK)
    style.map('TCombobox', fieldbackground=[('readonly', FIELD)],
              foreground=[('readonly', INK)], selectbackground=[('readonly', FIELD)],
              selectforeground=[('readonly', INK)])
    root.option_add('*TCombobox*Listbox.background', PAPER)
    root.option_add('*TCombobox*Listbox.foreground', INK)
    root.option_add('*TCombobox*Listbox.selectBackground', WARM)
    root.option_add('*TCombobox*Listbox.selectForeground', INK)
    style.configure('Workspace.TNotebook', background=PAPER, borderwidth=0, tabmargins=0,
                    bordercolor=PAPER, lightcolor=PAPER, darkcolor=PAPER)
    style.layout('Workspace.TNotebook.Tab', [])
    style.configure('TPanedwindow', background=LINE)
    style.configure('Vertical.TScrollbar', background=LINE, troughcolor=FIELD,
                    borderwidth=0, arrowsize=12)
    return style


def streamlit_css():
    """Small visual overrides; native Streamlit controls retain their semantics."""
    return f'''<style>
    .stApp {{ background: {PAPER}; color: {INK}; }}
    [data-testid="stSidebar"] {{ background: {FIELD}; border-right: 1px solid {LINE}; }}
    .block-container {{ max-width: 1100px; padding-top: .5rem; padding-bottom: 2rem; }}
    h1 {{ font-size: 1.65rem !important; font-weight: 500 !important; }}
    h2,h3 {{ font-weight: 500 !important; }}
    [data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
    button[data-baseweb="tab"] {{ padding: .55rem 1rem; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background: {WARM}; color: {INK}; }}
    [data-baseweb="tab-highlight"] {{ background: {GOLD}; }}
    [data-testid="stMain"] {{
        margin-top: 3.75rem; height: calc(100dvh - 3.75rem);
        max-height: calc(100dvh - 3.75rem); min-height: 0;
        overflow-y: scroll; scrollbar-gutter: stable; scroll-behavior: smooth;
        scrollbar-width: auto; scrollbar-color: {MUTED} {FIELD};
    }}
    @supports selector(::-webkit-scrollbar) {{
        [data-testid="stMain"] {{ scrollbar-color: auto; scrollbar-width: auto; }}
    }}
    [data-testid="stMain"]::-webkit-scrollbar {{ width: 16px; }}
    [data-testid="stMain"]::-webkit-scrollbar-track {{ background: {LINE}; border-left: 1px solid {LINE}; }}
    [data-testid="stMain"]::-webkit-scrollbar-thumb {{
        background: {MUTED}; border: 3px solid {LINE}; border-radius: 8px; min-height: 56px;
    }}
    [data-testid="stMain"]::-webkit-scrollbar-thumb:hover {{ background: {INK}; }}
    .cf-masthead {{ display: flex; align-items: center; justify-content: space-between;
        gap: 1rem; padding: .45rem 0 .65rem; }}
    .cf-brand {{ display: flex; align-items: center; gap: .9rem; min-width: 0; }}
    .cf-logo {{ display: grid; place-items: center; width: 52px; height: 52px;
        flex-shrink: 0; font-size: 1.9rem; background: {FIELD}; border: 1px solid {LINE};
        border-bottom: 3px solid {GOLD}; border-radius: 14px; }}
    .cf-brand h1 {{ margin: 0; padding: 0; line-height: 1.25; color: {INK}; }}
    .cf-brand p {{ margin: .3rem 0 0; font-size: .88rem; color: {MUTED}; }}
    .cf-art {{ width: 128px; height: 70px; flex-shrink: 0; }}
    .cf-nav {{ display: flex; gap: 1.3rem; padding: .2rem 0 .7rem;
        border-bottom: 1px solid {LINE}; font-size: .84rem; }}
    .cf-nav a, .cf-return {{ color: {MUTED}; text-decoration: none;
        transition: color .15s ease; }}
    .cf-nav a:hover, .cf-return:hover {{ color: {INK}; text-decoration: underline; }}
    .cf-nav a:focus-visible, .cf-return:focus-visible {{ outline: 2px solid {INK}; outline-offset: 4px; }}
    .cf-return {{ font-size: .86rem; }}
    .cf-section-anchor, #course-material {{ scroll-margin-top: 1rem; }}
    .st-key-generation_status [data-testid="stProgress"] {{ margin-bottom: .25rem; }}
    @media (max-width: 640px) {{
        .cf-art {{ display: none; }}
        .cf-logo {{ width: 42px; height: 42px; font-size: 1.55rem; }}
        .cf-brand h1 {{ font-size: 1.4rem !important; }}
        .cf-brand p {{ font-size: .8rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        [data-testid="stMain"] {{ scroll-behavior: auto; }}
        .cf-nav a, .cf-return {{ transition: none; }}
    }}
    </style>'''


def streamlit_header():
    """Static original-airplane branding and a small, decorative lesson illustration.

    No user/provider text is interpolated into this HTML.
    """
    return '''<header class="cf-masthead">
    <div class="cf-brand"><span class="cf-logo" aria-hidden="true">🛩️</span>
    <div><h1>Course Framework</h1><p>Paste the full syllabus → generate course material.</p></div></div>
    <svg class="cf-art" viewBox="0 0 160 90" fill="none" aria-hidden="true" focusable="false">
    <rect x="27" y="15" width="65" height="62" rx="7" fill="#fafbfd" stroke="#e4e9f0" transform="rotate(-9 27 15)"/>
    <rect x="48" y="9" width="65" height="70" rx="7" fill="#ffffff" stroke="#e4e9f0"/>
    <path d="M61 25H91M61 34H99M61 43H93M61 52H86" stroke="#bac5d2" stroke-width="3" stroke-linecap="round"/>
    <path d="M61 64H78" stroke="#e6b844" stroke-width="4" stroke-linecap="round"/>
    <circle cx="117" cy="57" r="18" fill="#fff7df" stroke="#e6b844"/>
    <path d="M109 57L115 63L125 51" stroke="#102640" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M131 19H143M137 13V25" stroke="#e4e9f0" stroke-width="2" stroke-linecap="round"/>
    </svg></header>
    <nav class="cf-nav" aria-label="Workspace navigation">
    <a href="#syllabus">Syllabus</a><a href="#course-material">Course material ↓</a>
    </nav>'''
