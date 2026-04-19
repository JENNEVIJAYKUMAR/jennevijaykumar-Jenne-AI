import time
import uuid
import requests
import streamlit as st

st.set_page_config(
    page_title="AskJenneAI - AI Search Assistant",
    page_icon="🤖",
    layout="wide",
)

# Hidden SEO text
st.markdown(
    """
    <div style="display:none;">
    AskJenneAI AI chatbot Streamlit AI search assistant Jenne AI Perplexity clone AI web search bot Vijay Kumar Jenne
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Custom CSS
# --------------------------
st.markdown(
    """
    <style>
        .stApp {
            background-color: #343541;
        }

        .main .block-container {
            max-width: 950px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        section[data-testid="stSidebar"] {
            background-color: #202123;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        .sidebar-header {
            font-size: 1.35rem;
            font-weight: 700;
            color: white;
            margin-bottom: 0.25rem;
        }

        .sidebar-subtitle {
            color: #c5c5d2;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }

        .top-header {
            background: #3e3f4b;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 18px;
        }

        .top-title {
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
        }

        .top-subtitle {
            color: #c5c5d2;
            font-size: 0.95rem;
            margin-top: 4px;
        }

        .assistant-box {
            background-color: #444654;
            border-radius: 12px;
            padding: 16px;
            margin-top: 8px;
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .answer-title {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .source-box {
            background-color: #3b3d4a;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .source-title {
            font-size: 0.98rem;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .source-text {
            color: #d1d5db;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .small-note {
            color: #c5c5d2;
            font-size: 0.82rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Secrets
# --------------------------
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

# --------------------------
# Session state
# --------------------------
if "conversations" not in st.session_state:
    first_chat_id = str(uuid.uuid4())
    st.session_state.conversations = {
        first_chat_id: {
            "title": "New Chat",
            "messages": [],
            "created_at": time.time(),
        }
    }
    st.session_state.current_chat = first_chat_id

if "current_chat" not in st.session_state:
    first_chat_id = list(st.session_state.conversations.keys())[0]
    st.session_state.current_chat = first_chat_id

if "active_prompt" not in st.session_state:
    st.session_state.active_prompt = ""

if "typing_speed" not in st.session_state:
    st.session_state.typing_speed = 0.0025

if "last_user_query" not in st.session_state:
    st.session_state.last_user_query = ""

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# --------------------------
# Helpers
# --------------------------
def get_current_messages():
    return st.session_state.conversations[st.session_state.current_chat]["messages"]

def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.conversations[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "created_at": time.time(),
    }
    st.session_state.current_chat = chat_id

def generate_chat_title(query: str) -> str:
    query = query.strip()
    if not query:
        return "New Chat"
    return query[:35] + ("..." if len(query) > 35 else "")

def normalize_query(query: str) -> str:
    q = query.lower().strip()

    if "prime minister of andhra pradesh" in q or "pm of andhra pradesh" in q:
        return query + " Andhra Pradesh is a state in India, so verify whether the correct role is Chief Minister."

    return query

def custom_answer_check(query: str, answer: str) -> str:
    q = query.lower().strip()

    if "prime minister of andhra pradesh" in q or "pm of andhra pradesh" in q:
        return (
            "Andhra Pradesh is an Indian state, so it does not have a Prime Minister. "
            "A state has a Chief Minister. Please ask for the Chief Minister of Andhra Pradesh."
        )

    return answer

def search_web(query: str) -> dict:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 5,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"answer": f"Search error: {e}", "results": []}

    try:
        data = response.json()
    except ValueError:
        return {"answer": f"Search returned invalid response: {response.text}", "results": []}

    results = data.get("results", [])

    if not results:
        return {
            "answer": "Sorry, I could not find useful results for that question.",
            "results": [],
        }

    snippets = []
    for item in results[:3]:
        title = item.get("title", "No title")
        content = item.get("content", "No summary available.")
        snippets.append(f"**{title}**\n{content}")

    final_answer = "Here is a concise summary based on the top search results:\n\n" + "\n\n".join(snippets)

    return {"answer": final_answer, "results": results}

def render_sources(results: list):
    if not results:
        st.info("No sources available yet.")
        return

    st.markdown("### Sources")
    for item in results:
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        content = item.get("content", "No summary available.")

        st.markdown(
            f"""
            <div class="source-box">
                <div class="source-title"><a href="{url}" target="_blank">{title}</a></div>
                <div class="source-text">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def type_text(text: str, speed: float):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(typed)
        time.sleep(speed)
    return placeholder

def run_query(query: str):
    messages = get_current_messages()

    st.session_state.last_user_query = query

    if len(messages) == 0:
        st.session_state.conversations[st.session_state.current_chat]["title"] = generate_chat_title(query)

    messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    clean_query = normalize_query(query)

    with st.chat_message("assistant"):
        thinking = st.empty()
        thinking.info("Thinking...")

        result = search_web(clean_query)
        answer = custom_answer_check(query, result["answer"])
        sources = result["results"]

        st.session_state.last_answer = answer
        st.session_state.last_sources = sources

        thinking.empty()

        st.markdown('<div class="assistant-box">', unsafe_allow_html=True)
        st.markdown('<div class="answer-title">AskJenneAI</div>', unsafe_allow_html=True)
        type_text(answer, st.session_state.typing_speed)
        st.markdown("</div>", unsafe_allow_html=True)

        render_sources(sources)

    messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">🤖 AskJenneAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">AI Search Assistant</div>', unsafe_allow_html=True)

    if st.button("➕ New chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.markdown("---")
    st.markdown("### Chats")
    conversation_items = list(st.session_state.conversations.items())[::-1]

    for chat_id, chat_data in conversation_items:
        title = chat_data["title"]
        button_label = title if len(title) <= 28 else title[:28] + "..."

        if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.markdown("---")
    st.markdown("### Example prompts")

    if st.button("Latest AI news", use_container_width=True):
        st.session_state.active_prompt = "Latest AI news"

    if st.button("Top Python interview questions", use_container_width=True):
        st.session_state.active_prompt = "Top Python interview questions"

    if st.button("Chief Minister of Andhra Pradesh", use_container_width=True):
        st.session_state.active_prompt = "Who is the Chief Minister of Andhra Pradesh?"

    if st.button("Best free ML resources", use_container_width=True):
        st.session_state.active_prompt = "Best free ML learning resources"

    st.markdown("---")
    st.markdown("### Tools")

    nav = st.radio(
        "Navigation",
        ["💬 Chat", "📚 Sources", "📋 Copy Answer", "🔄 Regenerate", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Built by")
    st.markdown("**Vijay Kumar Jenne**")
    st.markdown('<div class="small-note">AskJenneAI project</div>', unsafe_allow_html=True)

# --------------------------
# Header
# --------------------------
st.markdown(
    """
    <div class="top-header">
        <div class="top-title">🤖 AskJenneAI</div>
        <div class="top-subtitle">Smart AI Search Assistant by Vijay Kumar Jenne</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Navigation panels
# --------------------------
if nav == "📚 Sources":
    st.title("📚 Sources")
    render_sources(st.session_state.last_sources)
    st.stop()

if nav == "📋 Copy Answer":
    st.title("📋 Copy Answer")
    if st.session_state.last_answer:
        st.text_area("Latest answer", st.session_state.last_answer, height=260)
        st.download_button(
            "Download answer",
            data=st.session_state.last_answer,
            file_name="askjenneai_answer.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.info("No answer available yet.")
    st.stop()

if nav == "🔄 Regenerate":
    st.title("🔄 Regenerate")
    if st.session_state.last_user_query:
        if st.button("Run last query again", use_container_width=True):
            run_query(st.session_state.last_user_query)
    else:
        st.info("No previous query available.")
    st.stop()

if nav == "⚙️ Settings":
    st.title("⚙️ Settings")
    speed = st.slider("Typing speed", 0.001, 0.02, st.session_state.typing_speed, 0.001)
    st.session_state.typing_speed = speed
    st.info("Lower value = faster typing animation")
    st.stop()

# --------------------------
# Chat display
# --------------------------
messages = get_current_messages()

for msg in messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.markdown('<div class="assistant-box">', unsafe_allow_html=True)
            st.markdown('<div class="answer-title">AskJenneAI</div>', unsafe_allow_html=True)
            st.markdown(msg["content"])
            st.markdown("</div>", unsafe_allow_html=True)

            if msg.get("sources"):
                render_sources(msg["sources"])
        else:
            st.markdown(msg["content"])

# --------------------------
# Example prompt execution
# --------------------------
if st.session_state.active_prompt:
    prompt_to_run = st.session_state.active_prompt
    st.session_state.active_prompt = ""
    run_query(prompt_to_run)

# --------------------------
# Chat input
# --------------------------
query = st.chat_input("Message AskJenneAI...")

if query:
    run_query(query)
