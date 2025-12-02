# build_db.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Ładowanie klucza API (OpenAI)
load_dotenv()

DB_PATH = "local_faiss_index"
KNOWLEDGE_DIR = "knowledge"


def build_vector_db():
    print("--- 🏗️  ROZPOCZYNAM BUDOWANIE BAZY WEKTOROWEJ ---")

    # 1. Sprawdź czy folder z wiedzą istnieje
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"❌ Błąd: Nie znaleziono folderu '{KNOWLEDGE_DIR}'")
        return

    # 2. Wczytaj dokumenty
    print(f"1. Wczytywanie plików z folderu {KNOWLEDGE_DIR}...")
    loader = DirectoryLoader(
        KNOWLEDGE_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}  # <--- To naprawia problem polskich znaków na Windows
    )
    documents = loader.load()

    if not documents:
        print("❌ Błąd: Folder jest pusty. Dodaj pliki .txt")
        return
    print(f"   Znaleziono {len(documents)} dokumentów.")

    # 3. Podziel tekst na kawałki (Chunks)
    print("2. Dzielenie tekstu na fragmenty...")
    text_splitter = CharacterTextSplitter(chunk_size=600, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"   Utworzono {len(chunks)} fragmentów tekstu.")

    # 4. Tworzenie wektorów i bazy FAISS
    print("3. Generowanie embeddingów (to może chwilę potrwać)...")
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)

    # 5. Zapisywanie na dysk
    print(f"4. Zapisywanie bazy do folderu '{DB_PATH}'...")
    vector_store.save_local(DB_PATH)

    print("\n--- ✅ SUKCES! Baza została zbudowana i zapisana. ---")
    print("Teraz możesz uruchomić Agenta.")


if __name__ == "__main__":
    build_vector_db()