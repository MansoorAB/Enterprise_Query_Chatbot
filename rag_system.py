import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA


class EnterpriseAssistant:
    def __init__(self, db_dir: str = "./data/chroma_db"):
        load_dotenv()
        
        # Initialize OpenAI components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
        )
        
        # Load existing vector store
        self.vector_store = Chroma(
            persist_directory=db_dir,
            embedding_function=self.embeddings
        )
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            chain_type="stuff",
            return_source_documents=True
        )


    def query(self, question):
        """Query the RAG system"""
        try:
            result = self.qa_chain.invoke({"query": question})
            
            return result['result'].strip()
            
        except Exception as e:
            return f"Error: {str(e)}" 