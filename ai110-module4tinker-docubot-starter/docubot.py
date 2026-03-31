"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Chunking documents into sections for precise retrieval
- Building a simple retrieval index
- Retrieving relevant snippets with guardrails
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob

# Common words that appear everywhere and hurt retrieval precision
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "about", "up", "down", "if", "or", "and", "but", "not", "no", "nor",
    "so", "yet", "both", "either", "neither", "each", "every", "all",
    "any", "few", "more", "most", "other", "some", "such", "than",
    "too", "very", "just", "also", "how", "what", "which", "who",
    "when", "where", "why", "this", "that", "these", "those", "there",
    "here", "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "its", "our", "their",
}

# Minimum score a snippet must reach to be considered relevant.
# Below this threshold, DocuBot refuses to answer.
MIN_RELEVANCE_SCORE = 2


class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Break documents into smaller sections for precise retrieval
        self.chunks = self.chunk_documents(self.documents)

        # Build a retrieval index over chunks
        self.index = self.build_index(self.chunks)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Chunking: split documents into heading-based sections
    # -----------------------------------------------------------

    def chunk_documents(self, documents):
        """
        Splits each document into sections based on markdown ## headings.
        Returns a list of (source_label, section_text) tuples.

        Each source_label looks like "AUTH.md > Token Generation" so the
        user knows both the file and the section a snippet came from.
        """
        chunks = []
        for filename, text in documents:
            sections = self._split_by_headings(text)
            for heading, body in sections:
                if not body.strip():
                    continue
                label = f"{filename} > {heading}" if heading else filename
                chunks.append((label, body.strip()))
        return chunks

    def _split_by_headings(self, text):
        """
        Splits markdown text on lines starting with '## '.
        Returns a list of (heading_text, section_body) pairs.
        Content before the first ## heading gets heading="Overview".
        """
        lines = text.split("\n")
        sections = []
        current_heading = "Overview"
        current_lines = []

        for line in lines:
            if line.startswith("## "):
                # Save the previous section
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines)))
                current_heading = line.lstrip("# ").strip()
                current_lines = []
            else:
                current_lines.append(line)

        # Save the last section
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines)))

        return sections

    # -----------------------------------------------------------
    # Index Construction
    # -----------------------------------------------------------

    def build_index(self, chunks):
        """
        Build a tiny inverted index mapping lowercase words to the chunk
        labels they appear in.
        """
        index = {}
        for label, text in chunks:
            words = set()
            for raw_word in text.lower().split():
                cleaned = raw_word.strip(".,;:!?()[]{}\"'`#*-_>/\\")
                if cleaned:
                    words.add(cleaned)
            for word in words:
                if word not in index:
                    index[word] = []
                if label not in index[word]:
                    index[word].append(label)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        Return a relevance score for how well the text matches the query.
        Counts occurrences of meaningful (non-stop) query words in the text.
        """
        text_lower = text.lower()
        query_words = query.lower().split()
        score = 0
        for word in query_words:
            cleaned = word.strip(".,;:!?()[]{}\"'`#*-_>/\\")
            if cleaned and cleaned not in STOP_WORDS and cleaned in text_lower:
                score += text_lower.count(cleaned)
        return score

    def retrieve(self, query, top_k=3):
        """
        Score every chunk, apply the minimum relevance threshold,
        and return the top_k most relevant (label, text) pairs.
        """
        scored = []
        for label, text in self.chunks:
            score = self.score_document(query, text)
            if score >= MIN_RELEVANCE_SCORE:
                scored.append((score, label, text))

        scored.sort(key=lambda item: item[0], reverse=True)

        # Return as (label, text) to match the expected interface
        return [(label, text) for _, label, text in scored[:top_k]]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Retrieval only mode.
        Returns focused snippets with source labels, or a clear refusal.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for label, text in snippets:
            formatted.append(f"[{label}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        RAG mode.
        Uses retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
