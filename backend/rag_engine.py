# rag_engine.py
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "local_faiss_index"


class RAGService:
    def __init__(self):
        self.vector_store = None
        self._load_db()

    def _load_db(self):
        """Ładuje gotową bazę wektorową z dysku."""
        if not os.path.exists(DB_PATH):
            print(f"--- ⚠️ OSTRZEŻENIE: Nie znaleziono bazy '{DB_PATH}'! ---")
            print("Uruchom najpierw plik 'build_db.py', aby stworzyć bazę.")
            return

        print(f"--- 📂 Ładowanie bazy wiedzy z '{DB_PATH}'... ---")
        embeddings = OpenAIEmbeddings()

        # allow_dangerous_deserialization=True jest wymagane dla lokalnych plików FAISS
        # Jest to bezpieczne, o ile sam wygenerowałeś te pliki.
        self.vector_store = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("--- ✅ Baza wiedzy załadowana i gotowa do użycia. ---")

    def search(self, query: str) -> str:
        if not self.vector_store:
            return "Błąd: Baza wiedzy nie jest dostępna (nie została zbudowana)."

        # Wyszukaj 2 najlepsze fragmenty
        results = self.vector_store.similarity_search(query, k=2)

        # Złącz wyniki w jeden tekst
        context = "\n\n".join([doc.page_content for doc in results])
        print(context)
        return context


# Tworzymy instancję gotową do importu
RAG_ENGINE = RAGService()