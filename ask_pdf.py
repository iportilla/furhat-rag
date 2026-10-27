"""
Ask your PDF: the simplest RAG lab (Streamlit + OpenAI)

Upload a PDF, ask a question, get an answer grounded in the document.
Based on the ask-pdf example, rewritten without LangChain or FAISS so every
step is plain Python you can read:

  1. Extract text from the PDF (pypdf).
  2. Split it into overlapping chunks.
  3. Embed each chunk (OpenAI Embeddings API), cached per file.
  4. Find the chunks most similar to the question (cosine similarity, numpy).
  5. Answer from those chunks only (OpenAI Responses API).

Run:  streamlit run ask_pdf.py
"""

import io
import os

import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv(override=True)

CHAT_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000     # characters per chunk
CHUNK_OVERLAP = 200   # characters shared by neighbouring chunks
TOP_K = 4             # chunks sent to the model per question


# ---------- Steps 1-3: PDF -> chunks -> vectors ----------

def extract_text(pdf_bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def split_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    # Overlap keeps a sentence that crosses a chunk boundary readable in both chunks
    chunks = [text[i:i + size] for i in range(0, len(text), size - overlap)]
    return [c for c in chunks if c.strip()]


def embed(texts):
    vecs = []
    for i in range(0, len(texts), 100):  # batch to stay under request limits
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + 100])
        vecs.extend(d.embedding for d in resp.data)
    arr = np.array(vecs, dtype=np.float32)
    return arr / np.linalg.norm(arr, axis=1, keepdims=True)  # normalise for cosine


# Streamlit re-runs this script on every question; caching by the file's bytes
# means each PDF is embedded only once instead of on every question.
@st.cache_data(show_spinner="Reading and embedding the PDF...")
def build_index(pdf_bytes):
    chunks = split_chunks(extract_text(pdf_bytes))
    return chunks, (embed(chunks) if chunks else None)


# ---------- Steps 4-5: question -> best chunks -> answer ----------

def answer(question, chunks, vectors):
    qv = embed([question])[0]
    best = np.argsort(vectors @ qv)[::-1][:TOP_K]
    context = "\n\n".join(f"[{n}] {chunks[i]}" for n, i in enumerate(best, 1))

    resp = client.responses.create(
        model=CHAT_MODEL,
        instructions=(
            "Answer the question using ONLY the context taken from the user's PDF. "
            "If the answer isn't in the context, say you don't know. "
            "Cite the context items you used like [1], [2]."
        ),
        input=f"Context:\n{context}\n\nQuestion: {question}",
        temperature=0,
    )
    return resp.output_text, [chunks[i] for i in best], resp.usage


# ---------- UI ----------

st.set_page_config(page_title="Ask your PDF", page_icon="📄")
st.header("Ask your PDF 💬")

if not os.environ.get("OPENAI_API_KEY"):
    st.error("Set OPENAI_API_KEY in a .env file next to ask_pdf.py (see .env.example).")
    st.stop()
client = OpenAI()

uploaded = st.file_uploader("Upload a PDF", type="pdf")
if uploaded is None:
    st.info("Try docs/constitution.pdf and ask “Who can be a representative?”")
    st.stop()

chunks, vectors = build_index(uploaded.getvalue())
if not chunks:
    st.warning("No text found in this PDF. Scanned PDFs are images and have no text to extract.")
    st.stop()
st.caption(f"{len(chunks)} chunks indexed from {uploaded.name}")

question = st.text_input("Ask a question about your PDF:")
if question:
    with st.spinner("Thinking..."):
        text, sources, usage = answer(question, chunks, vectors)
    st.write(text)
    with st.expander("Sources"):
        for n, chunk in enumerate(sources, 1):
            st.markdown(f"**[{n}]** {chunk}")
    st.caption(f"Tokens: {usage.input_tokens} in, {usage.output_tokens} out")
