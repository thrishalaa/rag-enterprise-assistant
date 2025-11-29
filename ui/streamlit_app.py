import streamlit as st
import requests
import html
import re

# ---------------------------
# CONFIG
# ---------------------------
API_BASE = "http://127.0.0.1:8000"
LOGIN_ENDPOINT = f"{API_BASE}/login"
CHAT_ENDPOINT = f"{API_BASE}/chat"
INGEST_ENDPOINT = f"{API_BASE}/ingest"

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# SESSION STATE
# ---------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"

# ---------------------------
# FLOATING SIDEBAR TOGGLE
# ---------------------------
toggle_html = """
<style>
#float-toggle {
    position: fixed;
    top: 20px;
    left: 20px;
    height: 42px;
    width: 42px;
    background: #2a2a2a;
    color: white;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    border: 1px solid #444;
    z-index: 999999;
    user-select: none;
    transition: .15s;
}
#float-toggle:hover {
    background: #444;
    transform: scale(1.05);
}
</style>

<div id="float-toggle">☰</div>

<script>
document.getElementById("float-toggle").onclick = function() {
    const ctrl = window.parent.document.querySelector('button[data-testid="collapsedControl"]');
    if (ctrl) ctrl.click();
};
</script>
"""

st.markdown(toggle_html, unsafe_allow_html=True)

# ---------------------------
# DARK MODE CSS
# ---------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.user-message {
    background-color: #2a2a2a;
    color: white;
    padding: 1rem;
    border-radius: 1rem;
    margin-bottom: 1rem;
}

.assistant-message {
    background-color: #1e1e1e;
    color: #e6e6e6;
    padding: 1rem;
    border-radius: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
}

.source-pill {
    background-color: #333;
    color: #eee;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    margin-right: 0.5rem;
}

.sources-container {
    background-color: #111;
    border: 1px solid #333;
    padding: 0.75rem;
    color: #bbb;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
}

section[data-testid="stSidebar"] {
    background-color: #1a1a1a !important;
}

section[data-testid="stSidebar"] * {
    color: #f0f0f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HELPER
# ---------------------------
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


# ---------------------------
# LOGIN
# ---------------------------
if st.session_state.token is None:

    st.markdown("""
        <div style="
            max-width:400px;
            margin:6rem auto;
            padding:2rem;
            background:#1e1e1e;
            border-radius:1rem;
            text-align:center;
            color:#eee;">
            <h1>🤖 Knowledge Assistant</h1>
            <p style="color:#bbb;">Sign in to continue</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            try:
                resp = requests.post(LOGIN_ENDPOINT, json={"username": username, "password": password})
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except:
                st.error("Unable to connect to server")
    st.stop()

# ---------------------------
# SIDEBAR MENU
# ---------------------------
with st.sidebar:
    st.header("Menu")

    if st.button("💬 Chat", use_container_width=True):
        st.session_state.current_page = "chat"
        st.rerun()

    if st.button("📤 Upload Documents", use_container_width=True):
        st.session_state.current_page = "upload"
        st.rerun()

    st.markdown("---")

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.token = None
        st.rerun()

# ---------------------------
# HEADER
# ---------------------------
st.header("💬 Enterprise Knowledge Assistant")

# ---------------------------
# CHAT PAGE
# ---------------------------
if st.session_state.current_page == "chat":

    for msg in st.session_state.messages:

        st.markdown(
            f'<div class="user-message"><b>You</b><br>{sanitize_text(msg["question"])}</div>',
            unsafe_allow_html=True
        )

        ans = sanitize_text(msg["answer"]).replace("\n", "<br>")
        st.markdown(
            f'<div class="assistant-message"><b>Assistant</b><br>{ans}</div>',
            unsafe_allow_html=True
        )

        if msg.get("sources"):
            pills = "".join(
                f'<span class="source-pill">📄 {html.escape(src.split("/")[-1])}</span>'
                for src in msg["sources"]
            )
            st.markdown(
                f'<div class="sources-container"><b>SOURCES</b><br>{pills}</div>',
                unsafe_allow_html=True
            )

    with st.form("chat_form", clear_on_submit=True):
        query = st.text_input("Ask something...")
        if st.form_submit_button("Send") and query.strip():
            with st.spinner("Thinking..."):
                try:
                    resp = requests.get(
                        CHAT_ENDPOINT,
                        params={"q": query},
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.messages.append({
                            "question": query,
                            "answer": sanitize_text(data["answer"]),
                            "sources": data.get("sources", [])
                        })
                        st.rerun()
                    else:
                        st.error("Server error")
                except Exception as e:
                    st.error(str(e))

# ---------------------------
# UPLOAD PAGE
# ---------------------------
elif st.session_state.current_page == "upload":

    st.subheader("📤 Upload Documents")

    files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True
    )

    if st.button("Upload & Ingest"):
        if not files:
            st.warning("Please upload files")
        else:
            with st.spinner("Processing..."):
                try:
                    payload = [("files", (f.name, f.getvalue(), f.type)) for f in files]
                    resp = requests.post(
                        INGEST_ENDPOINT,
                        files=payload,
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if resp.status_code == 200:
                        st.success("Documents ingested successfully!")
                        st.json(resp.json())
                    else:
                        st.error("Failed to ingest documents")
                except Exception as e:
                    st.error(str(e))
