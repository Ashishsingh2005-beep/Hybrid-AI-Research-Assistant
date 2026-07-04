import re
import math
from collections import Counter

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """
    Splits text into chunks of `chunk_size` characters with an overlap of `overlap` characters.
    """
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        # If we reached the end, stop
        if end == text_len:
            break
        start += chunk_size - overlap
    return chunks

def preprocess(text: str) -> list[str]:
    """
    Tokenizes text by splitting into alphanumeric words and lowercasing them.
    """
    return re.findall(r'\w+', text.lower())

class SimpleRetriever:
    """
    A pure-Python TF-IDF retriever for document searching.
    No heavy dependencies like ChromaDB or FAISS, making it highly robust and fast.
    """
    def __init__(self, documents: list[str]):
        self.documents = documents
        self.doc_tokens = [preprocess(doc) for doc in documents]
        self.num_docs = len(documents)
        
        # Calculate Document Frequency (DF) for IDF calculation
        self.doc_freqs = Counter()
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
                
        # Precompute Inverse Document Frequency (IDF)
        self.idf = {}
        for token, df in self.doc_freqs.items():
            # Standard smooth IDF formula
            self.idf[token] = math.log((self.num_docs + 1) / (df + 0.5)) + 1.0
            
    def retrieve(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        """
        Retrieves the top `top_k` documents matching the query based on TF-IDF similarity.
        """
        if not self.documents:
            return []
            
        query_tokens = preprocess(query)
        if not query_tokens:
            # Return first top_k documents if query is empty/unparseable
            return [(doc, 0.0) for doc in self.documents[:top_k]]
            
        scores = []
        for i, tokens in enumerate(self.doc_tokens):
            if not tokens:
                scores.append((self.documents[i], 0.0))
                continue
                
            tf = Counter(tokens)
            doc_len = len(tokens)
            
            score = 0.0
            for token in query_tokens:
                if token in tf:
                    # Term frequency normalization
                    tf_norm = tf[token] / doc_len
                    score += tf_norm * self.idf.get(token, 0.0)
            scores.append((self.documents[i], score))
            
        # Sort documents by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
