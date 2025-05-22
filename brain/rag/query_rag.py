from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.settings import Settings

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11500"
)
Settings.llm = None

from llama_index.core import StorageContext, load_index_from_storage
from .config import INDEX_DIR, MODEL_NAME

def query_rag(user_prompt, top_k=4, model=MODEL_NAME):
    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine(similarity_top_k=top_k, llm=None)

    docs_context = query_engine.query(user_prompt)
    context_text = str(docs_context)

    return context_text.strip()
