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
    .block-container {{ max-width: 1100px; padding-top: 1.5rem; padding-bottom: 2rem; }}
    h1 {{ font-size: 1.65rem !important; font-weight: 500 !important; }}
    h2,h3 {{ font-weight: 500 !important; }}
    [data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
    button[data-baseweb="tab"] {{ padding: .55rem 1rem; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background: {WARM}; color: {INK}; }}
    [data-baseweb="tab-highlight"] {{ background: {GOLD}; }}
    </style>'''
