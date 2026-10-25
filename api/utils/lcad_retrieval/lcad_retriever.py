"""Busca semântica sobre PDFs/TXT ou JSON: embeddings (SBERT ou Ollama) + índice FAISS."""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from faiss import read_index
import time

try:
    from lcad_retrieval.create_faiss_index import create_df_corpus_from_json, create_df_corpus_from_txt, pdf_to_text, create_index
    from lcad_retrieval.ollama_embedding import OllamaEmbedding
except Exception:
    from .create_faiss_index import create_df_corpus_from_json, create_df_corpus_from_txt, pdf_to_text, create_index
    from .ollama_embedding import OllamaEmbedding

CHUNKS_INDEX_NAME = 'chunks.index'
CHUNKS_DF_NAME = 'chunks.csv'

def unique(array):
    uniq, index = np.unique(array, return_index=True)
    return uniq[index.argsort()]

class SentenceRetriever:
    """Codifica e busca fragmentos. Com use_ollama=True, os embeddings são gerados pelo Ollama."""
    def __init__(
        self, 
        use_ollama: bool = False,
        encoder_model_id: str = "intfloat/multilingual-e5-large-instruct", 
        hf_token: str = "", 
    ):
        self.model = ''
        self.df_corpus = ''
        self.paragraphs_per_search = 1
        print("Loading encoder model: " + encoder_model_id)
        if use_ollama:
            self.model = OllamaEmbedding(encoder_model_id)
        else:
            self.model = SentenceTransformer(encoder_model_id, trust_remote_code=True, token=hf_token)

    def init_pdf_retriever(
        self, 
        input_dir: str, 
        data_dir: str = "retriever_data", 
        chunk_size: str = 1000, 
        overlap_chunks: str = 0, 
        force_rebuild_index: bool = False,
    ):
        """Indexa os PDF/TXT de `input_dir` em fragmentos; salva índice e CSV em `data_dir` e os carrega."""
        self._verify_dirs(input_dir=input_dir, data_dir=data_dir)
        # Cada resultado une 3 fragmentos contíguos
        self.paragraphs_per_search = 3

        # Constrói o índice se não existir ou se for forçado
        if not os.path.exists(data_dir+'/'+CHUNKS_INDEX_NAME) or not os.path.exists(data_dir+'/'+CHUNKS_DF_NAME):
            print("Index does not exist. Building index.")
            self._build_index_from_dir(input_dir, data_dir, chunk_size=chunk_size, overlap_chunks=overlap_chunks)
        elif force_rebuild_index:
            print("Index exists. Forced rebuilding of index.")
            self._build_index_from_dir(input_dir, data_dir, chunk_size=chunk_size, overlap_chunks=overlap_chunks)
        else:
            print("Index already exists. Loading index.")

        try:
            self.index_chunks = read_index(self.data_dir+'/'+CHUNKS_INDEX_NAME)
            self.df_corpus = pd.read_csv(self.data_dir+'/'+CHUNKS_DF_NAME)
        except Exception as e:
            raise Exception(f"Could not load chunks index. Verify if folder {input_dir} contains data.") from e
        
    
    def init_json_retriever(
        self,
        json_file_path: str, 
        data_dir: str = "retriever_data", 
        json_key_path: list[str] = ["area_layout", "offices"],
        json_indexing_keys: list[str] = ["name"],
        force_rebuild_index: bool = False,
    ):
        """Indexa as entradas do JSON (caminho `json_key_path`), usando `json_indexing_keys` como texto a codificar."""
        self._verify_dirs(input_dir=json_file_path, data_dir=data_dir)

        # Constrói o índice se não existir ou se for forçado
        if not os.path.exists(data_dir+'/'+CHUNKS_INDEX_NAME) or not os.path.exists(data_dir+'/'+CHUNKS_DF_NAME):
            print("Index does not exist. Building index.")
            self._build_index_from_json(json_file_path, data_dir, json_key_path=json_key_path, json_indexing_keys=json_indexing_keys)
        elif force_rebuild_index:
            print("Index exists. Forced rebuilding of index.")
            self._build_index_from_json(json_file_path, data_dir, json_key_path=json_key_path, json_indexing_keys=json_indexing_keys)
        else:
            print("Index already exists. Loading index.")

        try:
            self.index_chunks = read_index(self.data_dir+'/'+CHUNKS_INDEX_NAME)
            self.df_corpus = pd.read_csv(self.data_dir+'/'+CHUNKS_DF_NAME)
        except Exception as e:
            raise Exception(f"Could not load chunks index. Verify if folder {json_file_path} contains data.") from e
        
        

    def _verify_dirs(self, input_dir: str, data_dir: str):
        """Normaliza os caminhos, cria `data_dir` e valida que `input_dir` exista."""
        if data_dir[-1] == '/':
            data_dir = data_dir[:-1]
        if input_dir[-1] == '/':
            input_dir = input_dir[:-1]
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.input_dir = input_dir

        if not os.path.exists(input_dir):
            raise Exception(f"Input directory {input_dir} does not exist. Initialize the retriever with a valid folder with the data.")
        

    def _build_index_from_json(
        self,
        json_file_path: str, 
        data_dir: str = "retriever_data", 
        json_key_path: list[str] = ["area_layout", "offices"],
        json_indexing_keys: list[str] = ["name"],
    ):
        """Gera CSV e índice a partir de um JSON (codifica-se a coluna `reference`)."""
        df_chunks_json = create_df_corpus_from_json(json_file_path, json_key_path=json_key_path, json_indexing_keys=json_indexing_keys)
        df_chunks_json.to_csv(data_dir+'/'+CHUNKS_DF_NAME, index=False, escapechar="\\")
        create_index(
            df_corpus_path_dir=data_dir,
            df_corpus_name=CHUNKS_DF_NAME,
            encoder_model=self.model,
            index_column = "reference",
            index_dir = data_dir,
            index_name = CHUNKS_INDEX_NAME,
            encoder_model_dimensions=self.model.get_sentence_embedding_dimension(),
            verbose = True
        )

    def _build_index_from_dir(self, input_dir: str, data_dir: str, chunk_size: str = 1000, overlap_chunks: str = 0):
        """Converte os PDFs em TXT, os divide em fragmentos e gera CSV e índice (codifica-se a coluna `text`)."""
        pdf_to_text(input_dir, verbose = True)
        df_chunks_txt = create_df_corpus_from_txt(texts_path_dir=input_dir, paragraph_size=chunk_size, paragraph_overlap=overlap_chunks, verbose = True)
        df_chunks_txt.to_csv(data_dir+'/'+CHUNKS_DF_NAME, index=False, escapechar="\\")
        create_index(
            df_corpus_path_dir=data_dir,
            df_corpus_name=CHUNKS_DF_NAME,
            encoder_model=self.model,
            index_column = "text",
            index_dir = data_dir,
            index_name = CHUNKS_INDEX_NAME,
            encoder_model_dimensions=self.model.get_sentence_embedding_dimension(),
            verbose = True
        )
        

    def _fetch_text(self, dataframe_idx):
        """Devolve o fragmento `dataframe_idx` junto com seus vizinhos, sem repetir a sobreposição."""
        def merge_strings(str1, str2):
            str1 = str(str1)
            str2 = str(str2)
            # Encontra a sobreposição comum
            overlap = find_overlap(str1, str2)
            # Concatena as strings, excluindo a sobreposição comum
            return str1 + str2[len(overlap):]
        def find_overlap(str1, str2):
            max_overlap = min(len(str1), len(str2))
            overlap = ""
            # Percorre as possíveis sobreposições
            for i in range(1, max_overlap + 1):
                if str1.endswith(str2[:i]):
                    overlap = str2[:i]
            return overlap
        if(self.paragraphs_per_search == 1):
            info = self.df_corpus.iloc[dataframe_idx]
            return info.text
        else:
            info = self.df_corpus.iloc[dataframe_idx-(int(self.paragraphs_per_search/2)):dataframe_idx+int(self.paragraphs_per_search/2)+1]
        text = ""
        for info1 in info.text:
            text = merge_strings(text, info1)
        return text
        
    def _search_query(self, query, top_k, previous_context = [], verbose = False):
        """Busca os top_k textos mais próximos: mescla resultados contíguos e descarta os já vistos."""
        t=time.time()
        results = []
        query_vector = self.model.encode([query])

        top_k_results_text = self.index_chunks.search(query_vector, 3*top_k)     
        # Pede 3*top_k para ter margem ao mesclar duplicados
        top_k_ids_text = unique(top_k_results_text[1].tolist()[0])
        # Resultados próximos entre si são mesclados em um
        for i in range(len(top_k_ids_text)):
            for j in range(0, i):
                if abs(top_k_ids_text[i] - top_k_ids_text[j]) <= self.paragraphs_per_search:
                    top_k_ids_text[i] = top_k_ids_text[j]
        # Descarta o que já está em previous_context
        i = 0
        while i < len(top_k_ids_text):
            text = self._fetch_text(top_k_ids_text[i])
            if text in previous_context:
                top_k_ids_text = np.delete(top_k_ids_text, i)
            else:
                i += 1
        top_k_ids_text = unique(top_k_ids_text)[:top_k]
        results_text = [self._fetch_text(idx) for idx in top_k_ids_text]

        results += results_text

        if verbose:
            print('>>>> Results in Total Time: {}'.format(time.time()-t))

        return results


    def get_context(
            self, 
            query: str,
            top_k: int = 3,
            verbose = False):
        """Devolve os top_k fragmentos mais relevantes para `query`."""
        return self._search_query(query, top_k, previous_context = [], verbose = verbose)



# Teste manual (executar a partir da raiz do repositório): consulta os documentos de local_docs/
if __name__ == "__main__":
    retriever = SentenceRetriever()
    retriever.init_pdf_retriever(input_dir="local_docs", data_dir="retriever_data/pdf")
    while(1):
        query = str(input("Query: "))
        #Quais são os principais ingredientes de um alto-forno?
        results = retriever.get_context(query, 2)
        for result in results:
            print("\n\n---------\n\n")
            print(result) 





