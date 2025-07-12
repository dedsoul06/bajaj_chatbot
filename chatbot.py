import os
import re
import pdfplumber
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class LocalBajajChatbot:
    def __init__(self):
        # Initialize local models
        print("Loading local embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight local model
        self.embeddings = []
        self.text_chunks = []
        self.financial_data = None
        
        # Configuration
        self.config = {
            "top_k": 3,
            "chunk_size": 500,
            "overlap": 100
        }
        print("System ready!")

    def load_data(self, pdf_folder: str, csv_path: str = None):
        """Load all quarterly PDFs and optional CSV"""
        print(f"Loading data from {pdf_folder}...")
        
        # Process PDFs
        for filename in sorted(os.listdir(pdf_folder)):
            if filename.endswith(".pdf"):
                quarter = filename.split("_")[0]  # Extract Q1, Q2 etc.
                print(f"Processing {filename}...")
                self._process_pdf(os.path.join(pdf_folder, filename), quarter)
        
        # Process CSV if provided
        if csv_path and os.path.exists(csv_path):
            print(f"Loading CSV data from {csv_path}...")
            self._process_csv(csv_path)
        
        if self.text_chunks:
            print("Generating embeddings...")
            self._generate_embeddings()
        print("Data loading complete!")

    def _process_pdf(self, file_path: str, quarter: str):
        """Extract and tag PDF content with quarter info"""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Add quarter metadata to each chunk
                        cleaned = f"[Quarter: {quarter}] " + re.sub(r'\s+', ' ', text).strip()
                        self._chunk_text(cleaned)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def _process_csv(self, file_path: str):
        """Load and analyze CSV data"""
        try:
            self.financial_data = pd.read_csv(file_path)
            
            # Generate descriptive chunks from CSV
            stats = self.financial_data.describe().to_string()
            self.text_chunks.append(f"[CSV SUMMARY]\n{stats}")
            
            # Add recent records as context
            recent = self.financial_data.tail(5).to_string()
            self.text_chunks.append(f"[RECENT RECORDS]\n{recent}")
            
        except Exception as e:
            print(f"CSV processing error: {e}")

    def _chunk_text(self, text: str):
        """Split text into manageable chunks"""
        words = text.split()
        for i in range(0, len(words), self.config["chunk_size"] - self.config["overlap"]):
            chunk = ' '.join(words[i:i + self.config["chunk_size"]])
            # Preserve quarter tags in chunks
            if "[Quarter:" in text and "[Quarter:" not in chunk:
                chunk = text.split("[Quarter:")[0] + chunk
            self.text_chunks.append(chunk)

    def _generate_embeddings(self):
        """Create embeddings for all text chunks"""
        # Process in batches to avoid memory issues
        batch_size = 32
        for i in range(0, len(self.text_chunks), batch_size):
            batch = self.text_chunks[i:i + batch_size]
            self.embeddings.extend(self.embedding_model.encode(batch))

    def _semantic_search(self, query: str) -> list:
        """Find most relevant text chunks"""
        if not self.embeddings:
            return []

        query_embedding = self.embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[-self.config["top_k"]:][::-1]
        return [self.text_chunks[i] for i in top_indices]

    def answer_question(self, query: str) -> str:
        """Generate answers using semantic search"""
        # First try to find exact matches in CSV data
        if self.financial_data is not None and any(keyword in query.lower() for keyword in ["number", "value", "amount", "percentage"]):
            try:
                # Simple numeric lookup - you can enhance this
                if "revenue" in query.lower():
                    return f"Latest revenue: {self.financial_data['revenue'].iloc[-1]:,.2f}"
                elif "profit" in query.lower():
                    return f"Latest profit: {self.financial_data['profit'].iloc[-1]:,.2f}"
            except:
                pass
        
        # Fall back to semantic search
        context_chunks = self._semantic_search(query)
        context = "\n\n".join(context_chunks)[:3000]  # Limit context length
        
        # Simple rule-based response - replace this with a local LLM if needed
        if not context:
            return "I couldn't find relevant information to answer that question."
        
        # Extract most relevant sentence
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', context)
        query_words = set(query.lower().split())
        best_score = 0
        best_sentence = ""
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            score = len(query_words.intersection(sentence_words))
            if score > best_score:
                best_score = score
                best_sentence = sentence
                
        return f"Based on our documents: {best_sentence.strip()}"

# Usage Example
if __name__ == "__main__":
    bot = LocalBajajChatbot()
    
    # Load all quarterly reports and financial data
    bot.load_data(
        pdf_folder="data/quarterly_reports",
        csv_path="data/financials.csv"
    )
    
    print("\nBajaj Finserv Local Chatbot ready!")
    print("Type 'exit' to quit\n")
    
    while True:
        query = input("Your question: ")
        if query.lower() in ['exit', 'quit']:
            break
            
        response = bot.answer_question(query)
        print(f"\nResponse: {response}\n")