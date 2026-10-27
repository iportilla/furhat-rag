"""
E) Voice-driven RAG assistant with an avatar (Streamlit + OpenAI)

- Upload .txt / .md / .pdf files in the sidebar and click "Ingest".
- Talk to the avatar with the microphone (or type as a fallback).
- Speech -> text (OpenAI transcription) -> retrieve chunks -> answer (gpt-4o-mini)
  -> text -> speech (OpenAI TTS), with the avatar's mouth moving to the audio.

Run:  streamlit run app.py
"""

import base64
import hashlib
import io
import os

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv(override=True)

CHAT_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
STT_MODEL = "gpt-4o-mini-transcribe"
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICES = ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]


# ---------- RAG: ingest ----------

def read_file(uploaded) -> str:
    if uploaded.name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(uploaded.getvalue()))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return uploaded.getvalue().decode("utf-8", errors="ignore")


def split_chunks(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += max(1, chunk_size - overlap)
    return chunks


def embed(client, texts):
    vecs = []
    for i in range(0, len(texts), 100):  # batch to stay under request limits
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + 100])
        vecs.extend(d.embedding for d in resp.data)
    arr = np.array(vecs, dtype=np.float32)
    return arr / np.linalg.norm(arr, axis=1, keepdims=True)  # normalise for cosine


def ingest(client, files):
    chunks = []
    for f in files:
        for c in split_chunks(read_file(f)):
            chunks.append({"doc": f.name, "text": c})
    if not chunks:
        return [], None
    return chunks, embed(client, [c["text"] for c in chunks])


# ---------- RAG: retrieve + answer ----------

def top_k(client, query, k=4):
    if st.session_state.vectors is None:
        return []
    qv = embed(client, [query])[0]
    scores = st.session_state.vectors @ qv
    best = np.argsort(scores)[::-1][:k]
    return [st.session_state.chunks[i] for i in best]


def answer(client, question):
    contexts = top_k(client, question)
    context_text = "\n\n".join(f"[{i+1}] ({c['doc']}) {c['text']}" for i, c in enumerate(contexts))
    system = (
        "You are a friendly talking avatar. Your answers are spoken aloud, so keep them "
        "short (2-4 sentences) and conversational, no markdown or bullet lists. "
        "Answer using ONLY the context below. If the answer isn't in the context, say you don't know. "
        "Mention sources naturally, e.g. 'according to <doc name>'.\n\n"
        f"Context:\n{context_text or '(no documents ingested yet)'}"
    )
    # Keep the last few turns so follow-up questions work
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": question}]
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=messages)
    return resp.choices[0].message.content, contexts


# ---------- Voice ----------

def transcribe(client, audio_bytes) -> str:
    resp = client.audio.transcriptions.create(model=STT_MODEL, file=("speech.wav", audio_bytes))
    return resp.text.strip()


def speak(client, text, voice) -> bytes:
    resp = client.audio.speech.create(model=TTS_MODEL, voice=voice, input=text, response_format="mp3")
    return resp.content


# ---------- Avatar ----------

def avatar(audio_bytes=None):
    """SVG face; when audio is given it autoplays and the mouth follows the loudness."""
    audio_tag = ""
    if audio_bytes:
        b64 = base64.b64encode(audio_bytes).decode()
        audio_tag = f'<audio id="voice" autoplay controls src="data:audio/mp3;base64,{b64}"></audio>'
    components.html(f"""
    <div style="display:flex;flex-direction:column;align-items:center;font-family:sans-serif">
      <svg style="width:100%;max-width:220px;height:auto" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="90" fill="#ffd8b1" stroke="#c98b5a" stroke-width="3"/>
        <path d="M20 85 Q100 -10 180 85 Q150 40 100 45 Q50 40 20 85Z" fill="#6b3e26"/>
        <g id="eyes">
          <circle cx="70" cy="95" r="9" fill="#333"/><circle cx="130" cy="95" r="9" fill="#333"/>
        </g>
        <ellipse id="mouth" cx="100" cy="145" rx="26" ry="3" fill="#a33"/>
      </svg>
      {audio_tag}
    </div>
    <script>
      const mouth = document.getElementById("mouth");
      const eyes = document.getElementById("eyes");
      // Blink every few seconds
      setInterval(() => {{
        eyes.setAttribute("transform", "translate(0,95) scale(1,0.1) translate(0,-95)");
        setTimeout(() => eyes.removeAttribute("transform"), 150);
      }}, 3500);

      const audio = document.getElementById("voice");
      if (audio) {{
        const ctx = new AudioContext();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        ctx.createMediaElementSource(audio).connect(analyser);
        analyser.connect(ctx.destination);
        const data = new Uint8Array(analyser.frequencyBinCount);
        audio.addEventListener("play", () => ctx.resume());
        (function animate() {{
          analyser.getByteFrequencyData(data);
          const level = data.reduce((a, b) => a + b, 0) / data.length;  // 0..255
          mouth.setAttribute("ry", audio.paused ? 3 : 3 + level / 4);
          requestAnimationFrame(animate);
        }})();
      }}
    </script>
    """, height=300)


# ---------- UI ----------

st.set_page_config(page_title="RAG Voice Avatar", page_icon="🗣️", layout="wide")

if not os.environ.get("OPENAI_API_KEY"):
    st.error("Set OPENAI_API_KEY in a .env file next to app.py (see .env.example).")
    st.stop()
client = OpenAI()

for key, default in {"chunks": [], "vectors": None, "messages": [], "last_audio": None,
                     "reply_audio": None}.items():
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("📚 Documents")
    files = st.file_uploader("Upload .txt, .md or .pdf", type=["txt", "md", "pdf"],
                             accept_multiple_files=True)
    if st.button("Ingest", disabled=not files, use_container_width=True):
        with st.spinner("Chunking and embedding..."):
            st.session_state.chunks, st.session_state.vectors = ingest(client, files)
        st.success(f"Indexed {len(st.session_state.chunks)} chunks from {len(files)} file(s).")
    st.caption(f"Index: {len(st.session_state.chunks)} chunks")

    st.header("⚙️ Settings")
    voice = st.selectbox("Voice", TTS_VOICES, index=0)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.reply_audio = None

st.title("🗣️ RAG Voice Avatar")
left, right = st.columns([1, 2])

with left:
    avatar(st.session_state.reply_audio)
    recording = st.audio_input("Press the mic and ask a question")
    typed = st.chat_input("...or type your question")

# Work out the question: a new recording, or typed text
question = None
if recording is not None:
    audio_bytes = recording.getvalue()
    digest = hashlib.md5(audio_bytes).hexdigest()
    if digest != st.session_state.last_audio:  # don't re-process the same clip on rerun
        st.session_state.last_audio = digest
        with st.spinner("Transcribing..."):
            question = transcribe(client, audio_bytes)
if typed:
    question = typed

if question:
    with st.spinner("Thinking..."):
        reply, sources = answer(client, question)
    with st.spinner("Speaking..."):
        st.session_state.reply_audio = speak(client, reply, voice)
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "assistant", "content": reply, "sources": sources})
    st.rerun()  # redraw so the avatar picks up the new audio

with right:
    if not st.session_state.messages:
        st.info("Ingest some documents, then ask a question with your voice.")
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
            st.write(m["content"])
            if m.get("sources"):
                with st.expander("Sources"):
                    for i, c in enumerate(m["sources"], 1):
                        st.markdown(f"**[{i}] {c['doc']}** — {c['text'][:300]}...")
