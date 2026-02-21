import os
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pydantic import BaseModel

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

class RAGService:
    def __init__(self, db_path: str = "vector_db", policy_doc: str = "data/KYC_Policy_Rulebook_Dummy.txt"):
        self.db_path = db_path
        self.policy_doc = policy_doc
        # Initialize small local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = None
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Initialize or load the database
        self._initialize_db()

    def _initialize_db(self):
        """Loads or creates the vector database from the policy PDF."""
        if os.path.exists(self.db_path) and len(os.listdir(self.db_path)) > 0:
            print("Loading existing vector database...")
            self.vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        else:
            if os.path.exists(self.policy_doc):
                print(f"Ingesting policy document: {self.policy_doc}")
                self.ingest_document(self.policy_doc)
            else:
                print(f"Warning: Policy document not found at {self.policy_doc}. RAG will be limited to base knowledge.")
                # Create empty DB
                self.vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)

    def ingest_document(self, file_path: str):
        """Chunks and embeds a PDF or TXT document."""
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path)
            
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        self.vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        self.vector_db.persist()

    def query(self, user_query: str) -> ChatResponse:
        """Retrieves relevant chunks and generates an answer."""
        if not self.vector_db:
            return ChatResponse(answer="I'm sorry, my knowledge base is not initialized.", sources=[])

        # Similarity Search
        docs = self.vector_db.similarity_search(user_query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [f"Page {doc.metadata.get('page', 'Unknown')}" for doc in docs]
        
        # LLM Logic (Simulated for Local Demo - Replace with OpenAI/LLM call as needed)
        # In a real scenario, you'd pass `context` and `user_query` to an LLM chain.
        simulated_answer = self._generate_simulated_answer(user_query, context)
        
        return ChatResponse(
            answer=simulated_answer,
            sources=list(set(sources))
        )

    def _generate_simulated_answer(self, query: str, context: str) -> str:
        """A simple heuristic answer generator for demonstration purposes."""
        query_low = query.lower()
        if "address" in query_low:
            return f"Based on the KYC Policy, address verification requires proof of residence such as a utility bill or bank statement issued within the last 3 months. Reference Context: {context[:200]}..."
        elif "id" in query_low or "identity" in query_low:
            return f"The policy states that identity verification (KYC) must be performed using a government-issued photo ID (Passport, Driving License, or National ID). Reference Context: {context[:200]}..."
        elif "forgery" in query_low or "tampering" in query_low:
            return f"In case of suspected document tampering, the protocol requires immediate escalation to the Fraud Investigation Team. ELA and Deep Learning heatmaps must be saved for the report. Reference Context: {context[:200]}..."
        else:
            return f"I found some relevant information in the policy regarding '{query}'. Here is a summary of the matched sections: {context[:300]}..."

# Singleton Instance
rag_service = RAGService()
