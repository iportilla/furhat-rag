# Lab slides: Voice RAG Avatar

- [voice-rag-avatar-lab.pdf](voice-rag-avatar-lab.pdf): the deck as a PDF, 15 slides at 1920×1080.
- [slides.html](slides.html): the same slides as one web page. Download it and open it in a browser (it loads its fonts from Google Fonts).

## Speaker notes

### 1. Voice RAG Avatar

Welcome. In this lab we build a small web app that lets you upload documents and then ask questions about them out loud. An animated avatar answers by voice, using only what is in your documents. Everything is in one Python file, so you can read all of it in a single sitting.

### 2. What you’ll build in 45 minutes

Three things happen in this app: you feed it documents, you ask a question with your voice, and an avatar answers out loud. Along the way you will touch five ideas that show up in almost every voice assistant: retrieval-augmented generation, embeddings, speech-to-text, text-to-speech, and how Streamlit keeps state.

### 3. Why retrieval matters

A language model only knows what it saw in training. Ask it about your flower shop and it will happily invent plausible hours. Retrieval-augmented generation fixes that: before asking the model, we search our own documents for the most relevant passages and paste them into the prompt with an instruction to answer only from them, and to say “I don’t know” otherwise.

### 4. The big picture

The app has two pipelines. Ingest runs once when you click the Ingest button: read the files, split them into chunks of about 300 words, turn each chunk into an embedding vector, and keep them in memory as the index. The ask pipeline runs on every question: record, transcribe, retrieve from the index, answer, turn the answer into speech, and play it through the avatar. The dark boxes show where the two pipelines meet.

### 5. How the app finds the right chunks

Embeddings map text into a space where meaning becomes geometry. We use OpenAI’s text-embedding-3-small. Because the app normalises every vector to length 1, cosine similarity is just a dot product, so scoring every chunk is a single matrix multiplication: vectors @ question. The table shows illustrative scores; with k = 4 the four best chunks are used even when some are only loosely related, which is why the prompt also says to answer only from relevant context.

### 6. One question, step by step

Walk through one round trip. Four of the six steps are OpenAI API calls: transcribe, embed the question, chat completion, and text-to-speech. Step 4 also sends the last few turns of the conversation, which is why a follow-up like “and on Mondays?” works. The avatar is a small SVG face; a bit of JavaScript reads the audio volume with the Web Audio API and stretches the mouth.

### 7. Four OpenAI models, four jobs

Each step uses a small, cheap model, which keeps a class session to a few cents per student. The constants CHAT_MODEL, EMBED_MODEL, STT_MODEL and TTS_MODEL are defined at the top of app.py. One caveat: if you change the embedding model you must ingest again, because vectors from different models can’t be compared.

### 8. Streamlit re-runs your whole script

This is the one Streamlit idea that surprises everyone. There is no event loop to write: every interaction re-executes the script from line one. Normal variables are recreated each time, so anything that must persist — the index, the chat history, the last reply’s audio — lives in st.session_state. After a new answer the app calls st.rerun() so the avatar redraws with the new audio.

### 9. A tour of app.py, top to bottom

Open app.py next to this slide. The file is deliberately flat: plain functions, no classes, in the same order as the diagram. If you only have five minutes, read answer() — that is where the system prompt lives and where retrieval meets the language model.

### 10. Setup in six commands

The virtual environment keeps this project’s packages separate from everything else on your machine; your prompt shows (.venv) when it is active. On Windows, if activation says scripts are disabled, run Set-ExecutionPolicy -Scope CurrentUser RemoteSigned once. In the old Command Prompt, activate with .venv\Scripts\activate.bat instead. Before running the app you must put your key in .env — that is the next slide.

### 11. Your key lives in .env, not in code

Secrets never go in source code, because source code ends up on GitHub. The app calls load_dotenv() at startup, which reads .env and sets OPENAI_API_KEY for the OpenAI library. The repo’s .gitignore already lists .env, but always glance at git status before committing. Quick check from the terminal: python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('OPENAI_API_KEY')))" should print True. If a key leaks, delete it on the OpenAI keys page straight away.

### 12. Your turn: run the lab

Give students about 15 minutes here. The orange question is the most important one: orchids are not in the document, so a well-grounded assistant should say it does not know rather than invent a price. If it does invent one, that is a great discussion about prompt wording. Then have students upload their own document — a syllabus or a product manual works well.

### 13. Stretch challenges

For fast finishers. Tuning retrieval is the most instructive: tiny chunks lose context, huge chunks dilute the match. Latency connects to the KPIs from the earlier labs: transcribe, answer and speech each add time. The last card ties back to the robot: RAG answers can be spoken by Furhat through the Realtime API, using request_speak_text from the async bridge in the earlier labs, with the avatar replaced by the robot’s own face.

### 14. When something breaks

These six cover almost every problem seen in class. The index lives in memory, so reloading the page empties it; students often forget to click Ingest again. Scanned PDFs are pictures of text, so pypdf extracts nothing from them. The full troubleshooting table, with Windows specifics, is in the README.

### 15. Retrieve. Answer. Speak.

Recap: retrieval keeps the model honest, embeddings make retrieval possible, and speech in and out turns a chatbot into a conversation partner. The same three steps are what you will plug into the Furhat robot. Everything — code, README, setup for Mac and Windows — is in the repo.
