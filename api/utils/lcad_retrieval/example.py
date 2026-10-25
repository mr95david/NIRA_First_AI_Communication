"""Exemplo de uso do SentenceRetriever com o mapa de local_docs/. Requer HF_TOKEN; executar de dentro desta pasta."""

from lcad_retriever import SentenceRetriever
import os
import tempfile

hf_token = os.environ["HF_TOKEN"]
MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "local_docs", "map_description.json")

if __name__ == "__main__":
    retriever = SentenceRetriever(hf_token=hf_token)
    # O índice é gravado em uma pasta temporária para não alterar retriever_data/
    retriever.init_json_retriever(
        json_file_path=MAP_PATH,
        data_dir=tempfile.mkdtemp(),
        json_key_path=["area_layout", "offices"],
        json_indexing_keys=["name"],
        force_rebuild_index=True
    )

    for query in ["I would like to go somewhere to eat", "Where is the HCS?"]:
        print("\n\n>>Query: ", query)
        for result in retriever.get_context(query, top_k=2):
            print(result)
            print()
