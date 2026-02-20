# app.py
import streamlit as st
import uuid
import speech_recognition as sr
import ollama
import PyPDF2
import pandas as pd
from PIL import Image
import pytesseract
import io
import base64
import time
import traceback

# ------------------------------- #
# CONFIG & SETUP
# ------------------------------- #
st.set_page_config(page_title="CodeGene", layout="wide")

# Path to tesseract - adjust if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ------------------------------- #
# HELPER: LOAD CSS
# ------------------------------- #
def load_css(file_name: str = "styles.css"):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# ------------------------------- #
# UTILITY FUNCTIONS
# ------------------------------- #
def new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "New Chat", "messages": []}
    st.session_state.current_chat = chat_id

def process_file(uploaded_file):
    """Process non-image files immediately (text/pdf/csv)."""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"File processing error: {e}"
    return "Unsupported file type"

def perform_ocr(image_file):
    """Extract text from an uploaded image file using pytesseract."""
    try:
        image_file.seek(0)
        image = Image.open(image_file).convert("RGB")
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"OCR failed: {e}"

def image_to_base64(image_file):
    image_file.seek(0)
    image = Image.open(image_file).convert("RGB")
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_ollama_message(response_obj):
    """
    Extract assistant content from an Ollama response object (safe).
    Returns string content or str(response_obj) fallback.
    """
    try:
        # If it's an object with message attribute:
        if hasattr(response_obj, "message") and response_obj.message is not None:
            # Some SDKs have .message.content
            msg = response_obj.message
            if hasattr(msg, "content"):
                return msg.content or ""
            # maybe msg itself is dict-like
            try:
                return str(msg)
            except Exception:
                pass
        # If it's a dict-like response
        if isinstance(response_obj, dict):
            m = response_obj.get("message", {})
            if isinstance(m, dict):
                return m.get("content", "") or ""
            # sometimes nested
            return str(response_obj)
        # fallback to string
        return str(response_obj)
    except Exception:
        return str(response_obj)

def call_ollama_once(system_prompt, user_prompt, model_name="llama2:latest"):
    """
    Calls Ollama without streaming (single response) to avoid streaming-event logs.
    Returns assistant text (string) or raises exception.
    """
    try:
        resp = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # do NOT pass stream=True to avoid event objects
        )
        content = extract_ollama_message(resp)
        return content
    except Exception as e:
        # Re-raise so callers can catch and display errors
        raise


# ------------------------------- #
# SESSION INITIALIZATION
# ------------------------------- #
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "account_open" not in st.session_state:
    st.session_state.account_open = False
if "page" not in st.session_state:
    st.session_state.page = "Chat"
if "last_file" not in st.session_state:
    st.session_state.last_file = None

# image handling flags
if "pending_image" not in st.session_state:
    st.session_state.pending_image = None          # holds uploaded image file (temp)
if "last_uploaded_name" not in st.session_state:
    st.session_state.last_uploaded_name = None     # avoid re-setting same upload on rerun
if "processing" not in st.session_state:
    st.session_state.processing = False

# create first chat if none
if not st.session_state.current_chat:
    new_chat()

# ------------------------------- #
# SIDEBAR
# ------------------------------- #
with st.sidebar:
    with st.container():
        if st.button("✏️ New Chat"):
            new_chat()

        search_query = st.text_input("🔍 Search...")

        st.markdown("### GENIEs")
        if st.button("Tools"):
            st.session_state.page = "Tools"

        st.markdown("### Recents")
        for chat_id, chat in reversed(list(st.session_state.chats.items())):
            if search_query.strip() == "" or search_query.lower() in chat["title"].lower():
                if st.button(chat["title"], key=chat_id):
                    st.session_state.current_chat = chat_id
                    st.session_state.page = "Chat"

    with st.container():
        st.markdown('<div class="account-footer">', unsafe_allow_html=True)
        if st.button("👤 Account"):
            st.session_state.account_open = not st.session_state.account_open
        if st.session_state.account_open:
            st.info("**User:** demo_user@example.com")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------- #
# MAIN PAGE: CHAT
# ------------------------------- #
if st.session_state.page == "Chat":
    current_chat = st.session_state.chats[st.session_state.current_chat]

    st.markdown("### 💬 CodeGene")

    # Messages container
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    for msg in current_chat["messages"]:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role == "user":
            html = f'<div class="chat-row user"><div class="chat-bubble user-msg">{content}</div></div>'
        else:
            html = f'<div class="chat-row bot"><div class="chat-bubble bot-msg">{content}</div></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input container (fixed)
    st.markdown('<div class="stChatInputContainer">', unsafe_allow_html=True)
    col_input, col_voice, col_file = st.columns([10, 1, 1])

    # chat_input returns None normally; when user submits, returns string (possibly empty)
    with col_input:
        prompt = st.chat_input("Type your message...")

    with col_voice:
        voice_input = st.button("🎤", help="Voice input (speech-to-text)")

    # file_uploader in the input area (small browse button)
    with col_file:
        uploaded_file = st.file_uploader(
            "Upload file",
            type=["txt", "pdf", "csv", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
            key="chat_file_uploader"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # handle voice recognition (only when pressed)
    if voice_input:
        try:
            st.info("🎙️ Listening... Speak now")
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            try:
                recognized = recognizer.recognize_google(audio)
                # set prompt so the rest of the flow handles it (chat_input won't have a value)
                prompt = recognized
                st.success(f"Recognized: {recognized}")
            except sr.UnknownValueError:
                st.error("Could not understand audio")
            except sr.RequestError:
                st.error("Speech recognition service unavailable")
        except Exception as e:
            st.error(f"Microphone error: {e}")

    # -------------------------------
    # FILE UPLOAD HANDLING (images wait; others processed immediately)
    # -------------------------------
    if uploaded_file is not None:
        # If new upload (different name), save into session_state.pending_image and track name
        if uploaded_file.name != st.session_state.get("last_uploaded_name"):
            st.session_state.last_uploaded_name = uploaded_file.name
            if uploaded_file.type.startswith("image/"):
                # keep the uploaded file object in pending_image (it stays across reruns)
                st.session_state.pending_image = uploaded_file
                st.info(f"📸 Image '{uploaded_file.name}' is ready. Type a question or press Enter to send.")
            else:
                # Non-image: process immediately and append to chat
                file_content = process_file(uploaded_file)
                current_chat["messages"].append({
                    "role": "user",
                    "content": f"📄 Uploaded file: {uploaded_file.name}\n\n{file_content[:1500]}"
                })
                # we processed a file so clear sentinel to avoid processing again
                st.session_state.last_uploaded_name = None

    # show a small preview next to input (like ChatGPT): display only when pending_image exists
    # Only show preview if not processing any request
    if prompt is not None:
        if st.session_state.processing:
            st.warning("Already processing a previous request. Please wait.")
        else:
            st.session_state.processing = True
            try:
                user_text = prompt.strip()
                has_image = st.session_state.pending_image is not None

                # Case 1: Image + Text
                if has_image:
                    image_file = st.session_state.pending_image
                    img_name = image_file.name

                    # --- OCR step ---
                    with st.spinner("🔍 Extracting text from image..."):
                        ocr_text = perform_ocr(image_file)

                    # --- Construct AI prompt including OCR text ---
                    full_prompt = f"""
    You are CodeGene AI, a helpful assistant.
    The user uploaded an image named '{img_name}'.

    Extracted text from the image:
    {ocr_text}

    Now answer the user's question based on the image and text:
    {user_text}
    """

                    # --- Add to chat visually ---
                    img_b64 = image_to_base64(image_file)
                    st.session_state.chats[st.session_state.current_chat]["messages"].append({
                        "role": "user",
                        "content": f"<img src='data:image/png;base64,{img_b64}' "
                                f"style='max-width:200px;border-radius:10px;margin-bottom:8px; display:block;'/>{user_text}"
                    })

                    # --- Clear the pending image immediately ---
                    st.session_state.pending_image = None

                    # --- Get AI response ---
                    with st.spinner("🤖 Generating answer..."):
                        answer = call_ollama_once(
                            system_prompt="You are CodeGene AI, a helpful assistant.",
                            user_prompt=full_prompt,
                            model_name="llama2:latest"
                        )

                    st.session_state.chats[st.session_state.current_chat]["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })

                # Case 2: Text-only message
                else:
                    st.session_state.chats[st.session_state.current_chat]["messages"].append({
                        "role": "user",
                        "content": user_text
                    })
                    with st.spinner("🤖 Generating answer..."):
                        answer = call_ollama_once(
                            system_prompt="You are CodeGene AI, a helpful assistant.",
                            user_prompt=user_text,
                            model_name="llama2:latest"
                        )
                    st.session_state.chats[st.session_state.current_chat]["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })

                st.session_state.processing = False
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error while processing image or question:\n{e}")
                st.session_state.processing = False


# ------------------------------- #
# TOOLS SECTION
# ------------------------------- #
elif st.session_state.page == "Tools":
    st.title("🛠️ Tools")
    tool = st.radio("Select a tool", ["Image Generator", "Deep Research"])
    if st.button("Open Tool"):
        if tool == "Image Generator":
            st.session_state.page = "ImageGen"
        elif tool == "Deep Research":
            st.session_state.page = "Research"

elif st.session_state.page == "ImageGen":
    st.title("🖼️ Image Generator")
    img_prompt = st.text_input("Enter prompt for image generation")
    if st.button("Generate Image"):
        st.info(f"Image generated for: {img_prompt} (placeholder)")

elif st.session_state.page == "Research":
    st.title("🔎 Deep Research")
    query = st.text_area("Enter your research query", height=150)
    model_choice = st.radio("Select model", ["llama2:latest"], index=0)
    if st.button("Run Research"):
        if not query.strip():
            st.warning("⚠️ Please enter a query first.")
        else:
            try:
                assistant_text = call_ollama_once(
                    system_prompt="You are a deep research assistant. Provide a detailed, factual, structured answer.",
                    user_prompt=query,
                    model_name=model_choice
                )
                st.markdown("**Assistant:**")
                st.markdown(assistant_text)
            except Exception as e:
                st.error(f"Error calling Ollama: {e}\n{traceback.format_exc()}")





