# Furhat RAG Lab

A pair of small Streamlit apps that answer questions using information from documents you upload. The simpler app answers typed questions about one PDF. The voice app accepts several documents and lets you ask by voice or text, then speaks its answer through an animated avatar.

Both apps use OpenAI for embeddings and answers. The voice app also uses OpenAI for speech-to-text and text-to-speech.

## Project files

| File | Description |
|---|---|
| `ask_pdf.py` | Ask typed questions about one PDF and view the answer's sources. |
| `app.py` | Upload multiple documents, ask by voice or text, and hear answers from an animated avatar. |
| `requirements.txt` | Python dependencies for both apps. |
| `docs/constitution.pdf` | Sample PDF for `ask_pdf.py`. |
| `docs/flower_shop.txt` | Sample document for `app.py`. |
| `slides/` | Lab slides and speaker notes. |

## Requirements

- Python 3.10 or later
- An OpenAI API key with API access and billing enabled
- A modern web browser; allow microphone access to use voice input

## Install

Run these commands from the project directory.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell prevents environment activation, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Open `.env` in a text editor and add your API key on one line:

```text
OPENAI_API_KEY=your_openai_api_key
```

Keep the key private. Do not put it in source code or commit `.env`. The repository ignores this file.

## Run an app

Activate `.venv` first whenever you open a new terminal.

Run the single-PDF question-and-answer app:

```bash
python -m streamlit run ask_pdf.py
```

Upload `docs/constitution.pdf`, enter a question, and expand **Sources** to see the passages used to answer it.

Run the voice RAG avatar:

```bash
python -m streamlit run app.py
```

Upload one or more `.txt`, `.md`, or `.pdf` files in the sidebar and click **Ingest**. Then ask a question using the microphone or text input. The app displays the response and its sources, and reads the response aloud. Try `docs/flower_shop.txt` as a sample.

The app is available at <http://localhost:8501>. Stop it with `Ctrl+C` in the terminal.

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'pypdf'` (or another dependency) | Activate `.venv` and run `python -m pip install -r requirements.txt`. Start Streamlit from the same environment. |
| `streamlit` command is not found | Use `python -m streamlit run app.py` or `python -m streamlit run ask_pdf.py`. |
| The app asks for `OPENAI_API_KEY` | Check that `.env` is in the project directory, named exactly `.env`, and contains `OPENAI_API_KEY=...`. Restart the app after editing it. |
| OpenAI authentication or quota error | Check that the key is valid and that the OpenAI account has API billing enabled. |
| Microphone does not work | Allow microphone access in the browser. Microphone input generally requires localhost or HTTPS. |
| No useful text is extracted from a PDF | Use a text-based PDF. Scanned pages are images and need OCR before this app can search their text. |
| Answers do not use a newly uploaded document | In the voice app, click **Ingest** after uploading. The in-memory index is lost when the app restarts or the page session resets. |
| Port 8501 is already in use | Start the app on another port, for example `python -m streamlit run app.py --server.port 8502`. |
