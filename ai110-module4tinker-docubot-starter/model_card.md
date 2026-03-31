# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs
2. Retrieval only
3. RAG (retrieval plus LLM)

---

## 1. System Overview

**What is DocuBot trying to do?**

> DocuBot is a documentation assistant that answers developer questions about a codebase by searching through project documentation files. Its goal is to provide accurate, evidence-based answers grounded in what the docs actually say, rather than what a language model might guess.

**What inputs does DocuBot take?**

> A natural language question from the developer, a folder of markdown documentation files (docs/), and optionally a Gemini API key to enable LLM-powered modes.

**What outputs does DocuBot produce?**

> In retrieval-only mode: raw documentation snippets with source labels (e.g., "AUTH.md > Token Generation"). In RAG mode: a natural language answer synthesized from retrieved snippets, with source citations. In both cases, the system refuses to answer with "I do not know based on these docs" when evidence is insufficient.

---

## 2. Retrieval Design

**How does your retrieval system work?**

> - **Chunking**: Each markdown file is split into sections based on `## ` headings. The 4 documents become 29 focused chunks, each labeled with the file and section name (e.g., "DATABASE.md > Tables").
> - **Indexing**: An inverted index maps every lowercase word (with punctuation stripped) to the chunk labels where it appears. This enables fast lookup of which chunks contain a given term.
> - **Scoring**: For each query, every chunk is scored by counting how many times meaningful (non-stop-word) query terms appear in the chunk text. Stop words like "the", "is", "how" are filtered out to prevent long chunks from dominating.
> - **Threshold + ranking**: Chunks scoring below 2 (the minimum relevance threshold) are discarded. Remaining chunks are sorted by score descending, and the top k (default 3) are returned.

**What tradeoffs did you make?**

> - **Section-level chunking vs paragraph-level**: I chose `## ` headings as the split boundary because markdown docs are already structured around headings. This gives sections of roughly 5-20 lines each — focused enough to be useful, but large enough to preserve context. Paragraph-level would be more precise but risks losing context needed to understand the answer.
> - **Word counting vs TF-IDF**: Simple word counting is fast and transparent but treats all non-stop words equally. A term like "token" that appears in every file gets the same per-occurrence weight as "refresh" which is more specific. TF-IDF would fix this but adds complexity.
> - **Threshold of 2**: Low enough to catch queries with uncommon terms (like `/api/projects/<project_id>` where meaningful words are sparse after punctuation stripping), high enough to refuse truly unrelated questions.

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**

> - **Naive LLM mode (Mode 1)**: Sends the developer's question directly to Gemini with no document context at all. The model answers from its general training knowledge. The `all_text` parameter is accepted but ignored in the current implementation — this is intentional to demonstrate how an ungrounded model behaves.
> - **Retrieval only mode (Mode 2)**: No LLM is called. The system returns raw chunk text with source labels. The developer reads the documentation snippets themselves.
> - **RAG mode (Mode 3)**: Retrieval runs first. If relevant chunks are found, they are passed to Gemini inside a carefully structured prompt that instructs the model to answer using only the provided snippets, cite which files it relied on, and refuse with "I do not know" if the snippets are insufficient.

**What instructions do you give the LLM to keep it grounded?**

> The RAG prompt in `llm_client.py` includes these rules:
> - "Use only the information in the snippets. Do not invent new functions, endpoints, or configuration values."
> - "If the snippets are not enough to answer confidently, reply exactly: 'I do not know based on the docs I have.'"
> - "When you do answer, briefly mention which files you relied on."
>
> These constraints create two layers of guardrails: the retrieval threshold prevents irrelevant snippets from reaching the LLM, and the prompt rules prevent the LLM from going beyond what the snippets say.

---

## 4. Experiments and Comparisons

| Query | Naive LLM | Retrieval Only | RAG | Notes |
|-------|-----------|----------------|-----|-------|
| Where is the auth token generated? | Harmful — generic essay about OAuth, Auth0, JWTs. Never mentions `auth_utils.py` | Helpful — returns AUTH.md > Token Generation with the exact function name | Helpful — concise: "`generate_access_token` in `auth_utils.py`", cites AUTH.md | RAG best: precise answer, no noise |
| How do I connect to the database? | Harmful — massive tutorial covering PostgreSQL, MySQL, MongoDB CLI tools. Never mentions `DATABASE_URL` | Helpful — returns the Connection Configuration section with `DATABASE_URL` examples | Helpful — clean summary: "set `DATABASE_URL`, defaults to SQLite `app.db`", cites DATABASE.md | RAG best: synthesizes two chunks into a readable answer |
| Which endpoint lists all users? | Risky — guesses `GET /users` (close but wrong prefix, misses admin restriction) | Helpful — returns relevant chunks but the exact endpoint is buried in the text | Helpful — direct answer: "`GET /api/users`", cites API_REFERENCE.md | RAG best: extracts the key fact |
| How does a client refresh an access token? | Harmful — generic OAuth2 refresh flow essay, mentions `/oauth/token` which does not exist in this app | Helpful — returns AUTH.md > Client Workflow and API_REFERENCE.md > Authentication Endpoints | Helpful — concise: "`POST /api/refresh` with Bearer header", cites both files | RAG best: combines evidence from two files |
| Is there any payment processing? | Acceptable — says "I need to review the actual documentation" | Helpful — refuses: "I do not know based on these docs" | Helpful — refuses: "I do not know based on these docs" | Both retrieval and RAG correctly refuse |
| Which fields are in the users table? | Harmful — invents 20+ fields like `remember_token`, `phone_number`, `is_admin` | Helpful — returns DATABASE.md > Tables with the exact 4-column schema | Helpful — lists exactly: `user_id`, `email`, `password_hash`, `joined_at`, cites DATABASE.md | RAG best: clean list vs raw markdown table |

**What patterns did you notice?**

> - **Naive LLM looks impressive but is untrustworthy**: Every naive answer is fluent, detailed, and confident. But none reference the actual codebase. The user table answer invents 20+ fields when only 4 exist. The auth token answer describes OAuth providers when the real answer is one function in one file. Fluency is not accuracy.
> - **Retrieval only is accurate but hard to interpret**: The correct information is always present in the returned chunks, but the developer has to read through raw markdown to find the answer. For simple questions this is fine, but for questions spanning multiple files (like token refresh, which involves AUTH.md and API_REFERENCE.md), the developer must mentally combine two chunks.
> - **RAG is clearly better than both for synthesis**: RAG takes the evidence from retrieval and produces a focused, readable answer with citations. It combines information from multiple chunks when needed (database connection = overview + configuration), extracts the key fact from noisy context (endpoint = `GET /api/users` from a long API reference), and refuses cleanly when retrieval returns nothing.
> - **RAG still depends entirely on retrieval quality**: If retrieval misses the right chunk, RAG cannot compensate. The model only sees what retrieval gives it.

---

## 5. Failure Cases and Guardrails

**Failure case 1: Naive LLM hallucinates database schema**

> - Question: "Which fields are stored in the users table?"
> - What happened: The naive LLM invented 20+ fields including `remember_token`, `phone_number`, `is_admin`, `first_name`, `last_name`, `profile_picture_url` — none of which exist in this application's schema.
> - What should have happened: The system should return only the 4 actual fields (`user_id`, `email`, `password_hash`, `joined_at`) or refuse to answer.
> - Why it matters: A developer acting on this answer would write code referencing columns that do not exist, leading to runtime errors that could take significant time to debug.

**Failure case 2: Retrieval returns wrong top result for project endpoint query**

> - Question: "What does the /api/projects/<project_id> route return?"
> - What happened: With the original MIN_RELEVANCE_SCORE of 3, the correct chunk (API_REFERENCE.md > Project Data Endpoints) scored only 2 and was filtered out, while DATABASE.md > Query Helpers scored 4 because it mentions "project" and "project_id" multiple times in a different context.
> - What should have happened: The API reference chunk should rank highest since it contains the actual endpoint definition.
> - Root cause: Our word-count scoring treats all occurrences equally. The database helpers chunk mentions "project" more times than the API reference chunk, even though the API reference is the authoritative source for endpoint behavior.

**When should DocuBot say "I do not know based on the docs I have"?**

> 1. When the query topic is completely absent from the documentation (e.g., payment processing, Kubernetes deployment, machine learning).
> 2. When the query uses terms that exist in the docs but in irrelevant contexts, and no chunk scores above the relevance threshold (e.g., "How do I process batch jobs?" — the word "process" might appear, but no chunk discusses batch processing).

**What guardrails did you implement?**

> 1. **Minimum relevance threshold (MIN_RELEVANCE_SCORE = 2)**: Chunks scoring below this are discarded before ranking. If no chunks pass, the system refuses.
> 2. **Stop word filtering**: Common English words are excluded from scoring so that long documents don't dominate every query.
> 3. **RAG prompt constraints**: The Gemini prompt explicitly forbids inventing functions, endpoints, or config values, requires citation of source files, and mandates an "I do not know" refusal when snippets are insufficient.
> 4. **Two-layer defense**: Retrieval filters first (threshold), then the LLM prompt filters second (refusal instruction). Even if a marginally relevant chunk slips through retrieval, the LLM is instructed not to extrapolate beyond it.

---

## 6. Limitations and Future Improvements

**Current limitations**

1. **Word-count scoring has no concept of term importance**: The word "token" appears in AUTH.md, API_REFERENCE.md, and SETUP.md. Our scoring counts every occurrence equally, so a file mentioning "token" 10 times in passing can outscore a file with 3 highly relevant mentions. TF-IDF or BM25 would weight rare, specific terms higher.
2. **Exact string matching only**: Searching for "credentials" will not match chunks containing only "username and password." There is no synonym awareness or semantic similarity. A developer asking "How do I log in?" gets different results than one asking "How do I authenticate?" even though they mean the same thing.
3. **Section-level chunking can split related context**: If an answer spans two adjacent sections (e.g., the database overview explains what `db.py` does, and the next section lists the tables), retrieval might return only one section, missing the full picture.
4. **No conversation memory**: Each question is independent. A follow-up like "What about the projects table?" after asking about the users table has no context from the previous answer.

**Future improvements**

1. **Semantic embeddings for retrieval**: Replace word-count scoring with vector similarity using sentence embeddings. This would handle synonyms, paraphrasing, and conceptual similarity (e.g., "log in" matching "authenticate").
2. **BM25 scoring**: A simpler improvement than embeddings — weight terms by how rare they are across the corpus. "token" appearing in every file would get a low weight, while "refresh" appearing only in AUTH.md would get a high weight.
3. **Chunk overlap**: When splitting on headings, include 1-2 sentences from the previous section as context so that no chunk starts mid-explanation.

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**

> If developers trust DocuBot's answers without verifying against the actual documentation, they could write code based on hallucinated endpoints, wrong environment variable names, or invented database columns. In naive LLM mode, the system confidently presents fabricated information that looks authoritative. Even in RAG mode, if retrieval selects the wrong chunk, the LLM can produce a plausible-sounding but incorrect answer grounded in irrelevant context.

**What instructions would you give real developers who want to use DocuBot safely?**

> - Always verify critical answers (endpoint paths, environment variable names, schema definitions) against the source documentation before writing code.
> - Prefer RAG mode over naive LLM mode. If RAG says "I do not know," trust the refusal — do not switch to naive mode hoping for a better answer.
> - Check the cited source files. If the RAG answer cites a file that seems unrelated to your question, the retrieval may have selected the wrong chunk.
> - Treat DocuBot as a search assistant that helps you find the right section of the docs faster, not as an authoritative source of truth.

---
