
# E) Voice RAG Avatar — Streamlit + OpenAI

A simple web app where you upload documents and then **talk** to an animated avatar that answers questions from them.

- **RAG** (Retrieval-Augmented Generation): instead of answering from general knowledge, the model is given the most relevant pieces of *your* documents and told to answer only from those.
- **Voice**: you speak into the mic; the avatar answers out loud.
- **Streamlit**: turns a plain Python script into a web page, with no HTML or JavaScript needed (except for the small avatar).

### Two apps, two labs

| App | Run | What it shows | Start here if… |
|---|---|---|---|
| **Ask your PDF** (`ask_pdf.py`) | `streamlit run ask_pdf.py` | Upload one PDF, type a question, read the answer. ~100 lines. | You’re new to RAG. Do this one first. |
| **Voice RAG Avatar** (`app.py`) | `streamlit run app.py` | Several documents, voice in, spoken answer from an animated avatar, chat memory. | You finished the PDF lab. |

Both use the same setup, `.env` file and packages. See [Lab 1: Ask your PDF](#lab-1-ask-your-pdf) for the simpler app; the rest of this README describes the avatar app.

---

## How the Voice RAG Avatar works

### The big picture

```mermaid
flowchart LR
    subgraph Ingest["1. Ingest (once per upload)"]
        D[📄 Your files<br/>.txt .md .pdf] --> T[Extract text]
        T --> C[Split into ~300-word chunks]
        C --> E[OpenAI embeddings<br/>text-embedding-3-small]
        E --> I[(In-memory index<br/>chunks + vectors)]
    end

    subgraph Ask["2. Ask (every question)"]
        M[🎤 Microphone] --> S[Speech → text<br/>gpt-4o-mini-transcribe]
        K[⌨️ Typed question] --> Q
        S --> Q[Question]
        Q --> R[Find 4 most similar chunks]
        I --> R
        R --> L[Answer from chunks<br/>gpt-4o-mini]
        L --> V[Text → speech<br/>gpt-4o-mini-tts]
        V --> A[🙂 Avatar speaks<br/>mouth follows audio]
        L --> H[💬 Chat history + sources]
    end
```

### One question, step by step

```mermaid
sequenceDiagram
    actor You
    participant UI as Streamlit app
    participant OAI as OpenAI API
    participant Av as Avatar (browser)

    You->>UI: Record question with mic
    UI->>OAI: Audio (transcribe)
    OAI-->>UI: "When are you open on weekends?"
    UI->>OAI: Embed the question
    OAI-->>UI: Question vector
    UI->>UI: Compare with chunk vectors, keep top 4
    UI->>OAI: System prompt + top 4 chunks + recent chat + question
    OAI-->>UI: "We're open 10am to 4pm on weekends..."
    UI->>OAI: Answer text (text-to-speech)
    OAI-->>UI: MP3 audio
    UI->>Av: Play audio
    Av-->>You: Speaks, mouth moves with the volume
```

### How "find the most similar chunks" works

An **embedding** is a list of numbers (a vector) that represents the meaning of a piece of text. Texts with similar meaning get vectors that point in similar directions. The app:

1. Stores one vector per chunk when you click **Ingest**.
2. Turns your question into a vector the same way.
3. Scores every chunk with **cosine similarity** (how closely the two vectors point the same way) and keeps the best 4.

```mermaid
flowchart LR
    Q["Question vector"] --> X{"Cosine similarity<br/>with every chunk"}
    X --> S1["0.82 flower_shop.txt #1 ✅"]
    X --> S2["0.41 manual.pdf #7 ✅"]
    X --> S3["0.12 manual.pdf #3 ❌"]
```

---

## What you need

- **Python 3.10 or newer**. Check with `python --version` (macOS/Linux may need `python3`; Windows may use `py`).
- An **OpenAI API key** from <https://platform.openai.com/api-keys>. Using the API costs a little money per request; a class session normally costs cents.
- A **microphone** and a recent Chrome, Edge or Firefox.
- **Git**, to download the code. Check with `git --version`. On Windows, install it from <https://git-scm.com/download/win>. On macOS, running `git` the first time offers to install it. (No Git? On the [GitHub page](https://github.com/iportilla/furhat-rag) click **Code → Download ZIP** and unzip it.)

## Project layout

```text
furhat-rag/
├── ask_pdf.py          # Lab 1: simple Ask your PDF app
├── app.py              # Lab 2: Voice RAG Avatar app
├── requirements.txt    # Python packages to install (shared by both)
├── .env.example        # template for your secrets file
├── .env                # YOUR secrets file (you create it; never committed)
├── .gitignore          # tells git to ignore .env, .venv, caches
├── docs/
│   ├── constitution.pdf # sample PDF for Lab 1
│   └── flower_shop.txt  # sample document for Lab 2
└── README.md
```

---

## Setup on macOS / Linux

```bash
# 1) Download the code and go into the project folder
git clone https://github.com/iportilla/furhat-rag.git
cd furhat-rag

# 2) Create a virtual environment (an isolated set of packages just for this project)
python3 -m venv .venv

# 3) Activate it. Your prompt should now start with (.venv)
source .venv/bin/activate

# 4) Install the packages listed in requirements.txt
pip install -r requirements.txt

# 5) Create your secrets file from the template, then put your key in it
#    (details in "Create your .env file" below)
cp .env.example .env
open -e .env          # macOS: opens in TextEdit. Linux: nano .env

# 6) Start the app; it opens http://localhost:8501 in your browser
streamlit run app.py
```

## Setup on Windows

Use **PowerShell** (Start menu → type "PowerShell"). If Python isn't installed, get it from <https://www.python.org/downloads/> and tick **"Add python.exe to PATH"** in the installer.

```powershell
# 1) Download the code and go into the project folder
cd $HOME\Documents
git clone https://github.com/iportilla/furhat-rag.git
cd furhat-rag

# 2) Create a virtual environment
py -m venv .venv

# 3) Activate it. Your prompt should now start with (.venv)
.venv\Scripts\Activate.ps1

# 4) Install the packages
pip install -r requirements.txt

# 5) Create your secrets file from the template, then put your key in it
#    (details in "Create your .env file" below)
copy .env.example .env
notepad .env

# 6) Start the app
streamlit run app.py
```

**Windows tips**

- If activation fails with *"running scripts is disabled on this system"*, run this once, then try step 3 again:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- Using the old **Command Prompt** (cmd) instead? Activate with `.venv\Scripts\activate.bat`.
- If `py` isn't found, try `python`. If that opens the Microsoft Store, Python isn't installed properly; reinstall it from python.org with "Add to PATH" ticked.
- Notepad may save the file as `.env.txt`. See [Create your `.env` file](#create-your-env-file) for how to spot and fix it.
- When Windows Firewall asks about Python, allowing **private networks** is enough.

---

## Create your `.env` file

The app needs your OpenAI API key. Instead of typing it into the code (where it could end up on GitHub), you keep it in a small text file called **`.env`** in the project folder. When the app starts, `load_dotenv()` reads that file and makes the key available to the OpenAI library.

```mermaid
flowchart LR
    T[".env.example<br/>(template, in git)"] -- copy --> E[".env<br/>(your key, NOT in git)"]
    E -- "load_dotenv()" --> A["app.py"]
    A -- "OPENAI_API_KEY" --> O["OpenAI API"]
    G[".gitignore"] -. "keeps .env out of git" .-> E
```

### Step 1: Get an API key

1. Sign in at <https://platform.openai.com>.
2. Go to **API keys** (<https://platform.openai.com/api-keys>) and click **Create new secret key**.
3. Give it a name like `furhat-rag` and click **Create**.
4. **Copy the key now.** It starts with `sk-` and is shown only once. If you lose it, delete it and create a new one.
5. Make sure the account has credit under **Settings → Billing**, otherwise every request fails with a quota error.

### Step 2: Create the file

The file must be named exactly **`.env`**: a dot, then `env`, with no name in front and no `.txt` at the end. It must be in the same folder as `app.py`.

**macOS / Linux**

```bash
cp .env.example .env
open -e .env        # macOS (TextEdit). On Linux use: nano .env
```

**Windows (PowerShell)**

```powershell
copy .env.example .env
notepad .env
```

Prefer not to copy? You can create it in one line instead. Replace `sk-your-key-here` with your real key:

```bash
# macOS / Linux
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

```powershell
# Windows PowerShell (ASCII avoids an invisible character that can break the file)
"OPENAI_API_KEY=sk-your-key-here" | Out-File -Encoding ascii .env
```

### Step 3: Put your key in it

The finished file is a single line:

```text
OPENAI_API_KEY=sk-proj-AbCdEf123...
```

Rules that trip people up:

| ✅ Do | ❌ Don't |
|---|---|
| `OPENAI_API_KEY=sk-proj-abc...` | `OPENAI_API_KEY = sk-proj-abc...` (spaces around `=`) |
| Paste the whole key on one line | Break it over two lines or leave part of it off |
| Name the file `.env` | `.env.txt`, `env`, `env.env` or `.env.example` |
| Keep it next to `app.py` | Put it in a parent or `docs/` folder |
| Save the file before running the app | Edit it while the app runs and expect a change: restart with `Ctrl+C`, then `streamlit run app.py` |

Quotes are optional (`OPENAI_API_KEY="sk-..."` also works).

### Step 4: Check it

Make sure the file exists and has the right name. These commands show hidden files:

```bash
ls -a                 # macOS / Linux: you should see .env
```

```powershell
Get-ChildItem -Force  # Windows: you should see .env, not .env.txt
```

Check that Python can read the key (prints only the first characters, so your key is not shown in full):

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); k=os.getenv('OPENAI_API_KEY'); print(k[:7]+'...' if k else 'NOT FOUND')"
```

You should see something like `sk-proj...`. If you see `NOT FOUND`, check the name and folder again.

**Seeing hidden files in the file browser.** Files starting with a dot are hidden by default.

- macOS Finder: press `Cmd + Shift + .`
- Windows File Explorer: **View → Show → Hidden items**, and also tick **File name extensions** so you can spot a sneaky `.env.txt`.

### Keep the key safe

- `.gitignore` already lists `.env`, so `git add` won't pick it up. Run `git status` before committing; `.env` should **not** appear.
- Never paste the key into code, screenshots, chats or the README.
- If a key leaks, delete it on the API keys page right away and create a new one.
- **Sharing the app with a class?** Each student should use their own key, or the instructor can share one through a private channel, never in the repo.

---

### Every time you come back

You only do the setup once. Next time, just activate the environment and run:

| | macOS / Linux | Windows (PowerShell) |
|---|---|---|
| Activate | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| Run | `streamlit run app.py` | `streamlit run app.py` |
| Stop | `Ctrl+C` in the terminal | `Ctrl+C` in the terminal |
| Leave the venv | `deactivate` | `deactivate` |

---

## Lab 1: Ask your PDF

The simplest possible RAG app: one PDF, one question box, one answer. Every step is a short, plain Python function, with no LangChain or vector database to learn first.

```bash
streamlit run ask_pdf.py
```

1. Upload `docs/constitution.pdf` (or any PDF with real text in it).
2. Ask *“Who can be a representative?”* and read the answer and its `[1]`, `[2]` citations.
3. Open **Sources** to see the exact chunks the model was given.
4. Ask something that isn’t in the document, e.g. *“What is the capital of France?”*. It should say it doesn’t know.

```mermaid
flowchart LR
    P[📄 PDF] --> X[extract_text<br/>pypdf]
    X --> S[split_chunks<br/>1000 chars, 200 overlap]
    S --> E[embed<br/>Embeddings API]
    E --> I[(vectors<br/>cached per file)]
    Q[❓ Question] --> QE[embed]
    QE --> R[top 4 by<br/>cosine similarity]
    I --> R
    R --> A[answer<br/>Responses API]
    A --> O[💬 Answer + sources<br/>+ token count]
```

| Function | What it does |
|---|---|
| `extract_text` | Reads the text of every page with `pypdf` |
| `split_chunks` | Cuts the text into 1000-character pieces that overlap by 200, so a sentence on a boundary appears whole in at least one chunk |
| `embed` | Turns texts into vectors with `client.embeddings.create` |
| `build_index` | Runs the three steps above once per file. `@st.cache_data` remembers the result, so asking a second question doesn’t re-embed the PDF |
| `answer` | Embeds the question, picks the 4 closest chunks and asks the model with `client.responses.create` |

**Things to try:** change `CHUNK_SIZE`, `CHUNK_OVERLAP` or `TOP_K` at the top of the file and see how answers change; edit the `instructions` to change the tone; watch the token count grow as `TOP_K` goes up.

<details>
<summary>How this differs from the original ask-pdf example</summary>

`ask_pdf.py` is a rewrite of the [ask-pdf](https://github.com/iportilla/ask-pdf) demo, updated to the current OpenAI Python SDK and simplified for a lab:

| Original | Here | Why |
|---|---|---|
| LangChain `load_qa_chain` (“stuff” chain) | `client.responses.create(...)` | `load_qa_chain` is deprecated and gone in LangChain 1.0. The Responses API is OpenAI’s current API for generating text. |
| `ChatOpenAI` / `OpenAIEmbeddings` wrappers | `openai` SDK directly | One less library between you and the API |
| FAISS vector store | numpy dot product | For one PDF, a matrix multiply is instant and needs no extra install (FAISS can be awkward on Windows) |
| `PyPDF2` | `pypdf` | PyPDF2 is deprecated; `pypdf` is its maintained successor |
| `get_openai_callback()` for token usage | `resp.usage` | The Responses API returns usage directly |
| Re-embedded the PDF on every question | `@st.cache_data` | Faster and cheaper |
| OpenAI, Azure and Ollama providers; `.xlsx` support | OpenAI only, PDF only | Kept small for a first lab |

</details>

---

## Lab 2: Using the Voice RAG Avatar

1. In the sidebar, upload `.txt`, `.md` or `.pdf` files (try `docs/flower_shop.txt`) and click **Ingest**.
2. Click the 🎤 mic, ask e.g. *"When are you open on weekends?"*, then click stop.
3. The avatar answers out loud. Open **Sources** under a reply to see which chunks it used.
4. Ask a follow-up like *"And on Mondays?"*; the last few turns are remembered.

You can also type in the box instead of speaking. Pick a different voice in the sidebar, or use **Clear conversation** to start over.

---

## A tour of `app.py`

The file reads top to bottom in the same order as the diagrams.

| Section | Functions | What it does |
|---|---|---|
| Settings | `CHAT_MODEL`, `EMBED_MODEL`, ... | Model names at the top, easy to change |
| RAG: ingest | `read_file`, `split_chunks`, `embed`, `ingest` | Text from files → chunks → normalised vectors |
| RAG: retrieve + answer | `top_k`, `answer` | Finds the best chunks and builds the prompt |
| Voice | `transcribe`, `speak` | Speech-to-text and text-to-speech |
| Avatar | `avatar` | SVG face plus a little JavaScript that reads the audio volume and moves the mouth |
| UI | bottom of the file | Sidebar, columns, mic, chat history |

### How Streamlit runs your code

This is the part that surprises most new Streamlit developers: **the whole script re-runs from top to bottom on every click or input.** Anything you want to keep between runs has to go in `st.session_state`.

```mermaid
flowchart TD
    A[User clicks, types or records] --> B[Streamlit re-runs app.py from the top]
    B --> C{"Is it in<br/>st.session_state?"}
    C -- yes --> D[Value survives:<br/>chunks, vectors, messages, reply_audio]
    C -- no --> E[Recomputed from scratch]
    D --> F[Page is redrawn]
    E --> F
```

That is why the app:

- Keeps the index, chat history and last reply audio in `st.session_state`.
- Stores a hash of the last recording in `last_audio`, so the same clip isn't transcribed again on every re-run.
- Calls `st.rerun()` after a new answer, so the avatar redraws with the new audio.

---

## Ideas to try

- **Change the personality**: edit the `system` prompt in `answer()`.
- **Retrieve more or fewer chunks**: change `k=4` in `top_k()`, or `chunk_size` / `overlap` in `split_chunks()`.
- **Use a stronger model**: change `CHAT_MODEL`.
- **Keep the index between restarts**: save `chunks` and `vectors` to a file (for example `np.save("vectors.npy", vectors)` plus a JSON file for `chunks`), and load them at startup.
- **Go fully offline**: swap the OpenAI calls for a local [Ollama](https://ollama.com) server: `/api/chat` for answers and `/api/embed` with `nomic-embed-text` for embeddings.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Set OPENAI_API_KEY..." on the page | `.env` is missing, misnamed (`.env.txt`), or not in the same folder as `app.py`. Run the check in [Step 4](#step-4-check-it). |
| `ModuleNotFoundError: No module named 'streamlit'` | The virtual environment isn't active. Activate it, then run `pip install -r requirements.txt` again. |
| `streamlit: command not found` / `not recognized` | Same as above, or run `python -m streamlit run app.py`. |
| Mic button does nothing | Allow microphone access in the browser (padlock icon in the address bar). The mic only works on `localhost` or HTTPS. |
| Avatar doesn't speak | The browser may block autoplay. Press ▶ on the player under the face. |
| `AuthenticationError` / 401 | The API key is wrong or was revoked. |
| `RateLimitError` / 429 / insufficient quota | Add billing credit to your OpenAI account, or wait a moment. |
| "I don't know" for something that is in the file | Click **Ingest** again after uploading (the index is lost on page reload). Scanned PDFs are images with no text, so nothing is extracted. |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |

> **Keep your key secret.** Never commit `.env` to git or paste the key into shared files or chats.
