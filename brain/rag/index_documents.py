from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.settings import Settings

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11500"
)

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from .config import DOCS_DIR, INDEX_DIR

def build_rag_index():
    print(f"Indexando documentos de {DOCS_DIR} ...")
    documents = SimpleDirectoryReader(DOCS_DIR).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=INDEX_DIR)
    print(f"Indexação concluída! Índice salvo em {INDEX_DIR}")

if __name__ == "__main__":
    build_rag_index()
