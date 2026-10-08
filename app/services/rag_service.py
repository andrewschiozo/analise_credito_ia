import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class RAGService:
    def __init__(self):
        self.persist_directory = "./chroma_db"
        self.pdf_path = "./app/data/rag_politica_credito.pdf"
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.vector_store = self._inicializar_banco_vetorial()

    def _inicializar_banco_vetorial(self) -> Chroma:
        """Carrega o PDF e alimenta o ChromaDB se ele ainda não existir."""

        vector_store = Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embeddings
        )
        
        if len(vector_store.get()['ids']) == 0:
            print("Banco vetorial vazio. Carregando PDF e gerando embeddings...")
            loader = PyPDFLoader(self.pdf_path)
            documentos = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = text_splitter.split_documents(documentos)

            vector_store.add_documents(chunks)
            print(f"{len(chunks)} chunks salvos no ChromaDB com sucesso.")

        return vector_store

    def recuperar_contexto(self, finalidade: str) -> str:
        """Busca as regras mais relevantes baseadas no que o cliente pediu."""

        query = f"Regras de empréstimo e taxas para: {finalidade}"

        docs_relevantes = self.vector_store.similarity_search(query, k=2)
                
        if not docs_relevantes:
            return "Nenhuma regra encontrada."
            
        return "\n\n".join([doc.page_content for doc in docs_relevantes])
       