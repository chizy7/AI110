# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls

---

## TF Reflection

[**Full Model Card**](model_card.md)

The biggest moment for me in this project came from running the naive LLM mode and seeing how confidently wrong it can be. I asked “Which fields are stored in the users table?” and it came back with over 20 columns like `remember_token`, `phone_number`, and `is_admin`. In reality, the table only has 4 fields. The response looked clean and well structured, but it was completely made up. That gap between how convincing something sounds and how accurate it actually is stuck with me. Just because it reads well does not mean it is true.

What really surprised me was how much a simple retrieval layer changes everything. The scoring function is very basic. It just counts word matches and filters out stop words. No machine learning, no embeddings, nothing complex. But forcing the model to reference actual documentation before answering made a huge difference. When I asked “How do I connect to the database?” the naive version gave a broad answer covering PostgreSQL, MySQL, MongoDB, and CLI tools. The retrieval version said “set DATABASE_URL, defaults to SQLite app.db” and pointed to DATABASE.md. Same model, same question, but completely different level of reliability.

Building the retrieval system also showed me that search is more of a design problem than a coding problem. My first version returned full documents, which meant answers were buried in a lot of irrelevant text. Switching to section-based chunks using markdown headings made the results much more precise. Then I had to figure out the right relevance threshold. If it was too high, valid queries got rejected. If it was too low, unrelated queries slipped through with bad answers. That tradeoff between recall and precision is not something you can fully automate. You have to decide what matters more.

AI tools helped with the repetitive parts, like generating a stop word list, suggesting how to handle punctuation, and formatting the model card. But the important decisions were still on me. Things like choosing section-based chunking over paragraph-level, setting the threshold to 2 instead of 3, and defining what counts as a guardrail all required thinking through the tradeoffs. The AI could give options, but it could not choose for me.

If I kept going with this, I would focus on three upgrades. First, adding BM25 scoring so rare terms like “refresh” carry more weight than common ones like “token.” Second, introducing semantic embeddings so queries like “log in” can match “authenticate.” Third, adding chunk overlap so splitting by headings does not lose important context from nearby sections. Those changes would fix the biggest gaps without needing to rebuild the system from scratch.

