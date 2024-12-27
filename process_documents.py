import os
from pathlib import Path
import hashlib
from typing import Dict, List
import json
from datetime import datetime
import argparse
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from dotenv import load_dotenv

import warnings
warnings.filterwarnings("ignore")


class DocumentProcessor:
    def __init__(self, docs_dir: str, db_dir: str):
        load_dotenv()
        self.docs_dir = Path(docs_dir)
        self.db_dir = Path(db_dir)
        self.metadata_file = self.db_dir / "document_metadata.json"
        self.embeddings = OpenAIEmbeddings()
        
        # Create directories if they don't exist
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize vector store
        self.vector_store = Chroma(
            persist_directory=str(self.db_dir),
            embedding_function=self.embeddings
        )
        
        # Load or initialize metadata
        self.metadata = self._load_metadata()


    def _load_metadata(self) -> Dict:
        """Load document metadata from JSON file"""
        if self.metadata_file.exists():
            print(f"Loading existing metadata from {self.metadata_file}")
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        print("No existing metadata found. Starting fresh.")
        return {}


    def _save_metadata(self):
        """Save document metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        print(f"Metadata saved to {self.metadata_file}")


    def _calculate_chunk_hash(self, chunk) -> str:
        """Calculate hash based on semantic structure"""
        page_num = chunk.metadata.get('page_number', 0)
        section = chunk.metadata.get('section', '')  # e.g., "leave_table"
        row_id = chunk.metadata.get('row_id', '')    # e.g., "personal_leave"
        
        hash_content = f"page:{page_num}|section:{section}|row:{row_id}|{chunk.page_content}"
        hash_value = hashlib.md5(hash_content.encode()).hexdigest()
        # print(f'{hash_content=}')
        # print(f'{hash_value=}')
        return hash_value


    def _parse_document_structure(self, chunk) -> tuple:
        """Parse document content to identify sections and row IDs"""
        content = chunk.page_content.strip()
        
        # Identify sections
        if "Human Resources Policy" in content:
            return "header", "title"
        elif "Code of Conduct" in content:
            return "conduct", "main"
        # Handle leave table content more precisely
        elif "Leave Type" in content or "Days per Year" in content:
            return "leave_table", "header"
        elif content in ["Annual", "Sick", "Personal"]:
            return "leave_table", f"{content.lower()}_leave"
        elif content.isdigit() and len(content) <= 2:  # Days numbers
            prev_chunk = chunk.metadata.get('prev_chunk', '')
            if "Annual" in prev_chunk:
                return "leave_table", "annual_days"
            elif "Sick" in prev_chunk:
                return "leave_table", "sick_days"
            elif "Personal" in prev_chunk:
                return "leave_table", "personal_days"
        elif content.strip().lower().startswith('up to') or content == "None":  # Carry forward
            prev_chunk2 = chunk.metadata.get('prev_chunk2', '')
            if "Annual" in prev_chunk2:
                return "leave_table", "annual_carry"
            elif "Sick" in prev_chunk2:
                return "leave_table", "sick_carry"
            elif "Personal" in prev_chunk2:
                return "leave_table", "personal_carry"
        elif "Leave Policy" in content:
            if "Leave Type" in content:
                return "leave_table", "header"
            elif any(leave in content for leave in ["Annual", "Sick", "Personal"]):
                leave_type = next(lt for lt in ["Annual", "Sick", "Personal"] if lt in content)
                return "leave_table", f"{leave_type.lower()}_row"
            else:
                return "leave_policy", "main"
        
        # Default for unidentified content
        return "general", "content"


    def _get_document_chunks(self, file_path: Path) -> List[dict]:
        """Get chunks from a document with their hashes"""
        loader = UnstructuredPDFLoader(str(file_path), mode="elements", strategy="fast")
        documents = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "•", "|", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        
        # First pass: store original content
        for i, chunk in enumerate(chunks):
            chunk.metadata['prev_chunk'] = chunks[i-1].page_content if i > 0 else ""
            chunk.metadata['prev_chunk2'] = chunks[i-2].page_content if i > 1 else ""
        
        # Debug print to see chunks
        for chunk in chunks:
            section, row_id = self._parse_document_structure(chunk)
            chunk.metadata['section'] = section
            chunk.metadata['row_id'] = row_id
            # print(f"""
            #     CHUNK [{section}:{row_id}]
            #     prev: {chunk.metadata['prev_chunk'][:50]}...
            #     prev2: {chunk.metadata['prev_chunk2'][:50]}...
            #     content: {chunk.page_content[:200]}
            #     """)        
        return [{
            'content': chunk.page_content,
            'hash': self._calculate_chunk_hash(chunk),
            'metadata': {
                'source': str(file_path),
                'chunk_hash': self._calculate_chunk_hash(chunk),
                'page_number': chunk.metadata.get('page_number', 0),
                'section': chunk.metadata.get('section', ''),
                'row_id': chunk.metadata.get('row_id', '')
            }
        } for chunk in chunks]


    def process_documents(self):
        """Process all PDF documents in the docs directory"""

        print(f"\nProcessing documents from: {self.docs_dir}")
        print(f"Using database directory: {self.db_dir}")
        
        # Track statistics
        stats = {
            'processed': 0,
            'updated': 0,
            'unchanged': 0,
            'chunks_added': 0,
            'chunks_removed': 0
        }
        
        # Process each PDF in the directory
        for pdf_file in self.docs_dir.glob("*.pdf"):
            pdf_path = str(pdf_file)
            print(f"\nProcessing {pdf_file.name}...")
            
            # Get new chunks
            new_chunks = self._get_document_chunks(pdf_file)
            # print(f'{new_chunks=}')
            
            # print(f'{self.metadata=}')
            # Check if file was previously processed    
            if pdf_path in self.metadata:
                old_chunks = self.metadata[pdf_path].get('chunks', [])
                old_hashes = {chunk['hash'] for chunk in old_chunks}
                new_hashes = {chunk['hash'] for chunk in new_chunks}

                # print(f'{old_chunks=}')
                # print(f'{old_hashes=}')
                # print(f'{new_hashes=}')

                # Identify changes
                chunks_to_remove = old_hashes - new_hashes
                chunks_to_add = new_hashes - old_hashes

                print(f'{chunks_to_remove=}')
                print(f'{chunks_to_add=}')
                
                if chunks_to_remove or chunks_to_add:
                    print(f"Found changes in {pdf_file.name}")
                    stats['updated'] += 1
                    
                    # Remove old chunks
                    if chunks_to_remove:
                        chunk_hashes_to_remove = [
                            chunk['metadata']['chunk_hash'] 
                            for chunk in old_chunks 
                            if chunk['hash'] in chunks_to_remove
                        ]
                        self.vector_store._collection.delete(
                            where={"chunk_hash": {"$in": chunk_hashes_to_remove}}
                        )
                        stats['chunks_removed'] += len(chunks_to_remove)
                    
                    # Add new chunks
                    chunks_to_add_docs = [
                        chunk for chunk in new_chunks 
                        if chunk['hash'] in chunks_to_add
                    ]
                    if chunks_to_add_docs:
                        self.vector_store.add_texts(
                            texts=[chunk['content'] for chunk in chunks_to_add_docs],
                            metadatas=[{
                                'source': chunk['metadata']['source'],
                                'chunk_hash': chunk['metadata']['chunk_hash'],
                                'page_number': chunk['metadata']['page_number'],
                                'section': chunk['metadata']['section'],
                                'row_id': chunk['metadata']['row_id']
                            } for chunk in chunks_to_add_docs]
                        )
                        stats['chunks_added'] += len(chunks_to_add_docs)
                else:
                    print(f"No changes detected in {pdf_file.name}")
                    stats['unchanged'] += 1
            else:
                # New file, add all chunks
                print(f"New file detected: {pdf_file.name}")
                stats['processed'] += 1
                self.vector_store.add_texts(
                    texts=[chunk['content'] for chunk in new_chunks],
                    metadatas=[{
                        'source': chunk['metadata']['source'],
                        'chunk_hash': chunk['metadata']['chunk_hash'],
                        'page_number': chunk['metadata']['page_number'],
                        'section': chunk['metadata']['section'],
                        'row_id': chunk['metadata']['row_id']
                    } for chunk in new_chunks]
                )
                stats['chunks_added'] += len(new_chunks)
            
            # Update metadata
            self.metadata[pdf_path] = {
                'last_processed': datetime.now().isoformat(),
                'chunks': new_chunks
            }
        
        # Save metadata
        self._save_metadata()
        self.vector_store.persist()
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"New documents processed: {stats['processed']}")
        print(f"Documents updated: {stats['updated']}")
        print(f"Documents unchanged: {stats['unchanged']}")
        print(f"Total chunks added: {stats['chunks_added']}")
        print(f"Total chunks removed: {stats['chunks_removed']}")
        print("\nDocument processing completed!")


def main():
    parser = argparse.ArgumentParser(
        description="Process PDF documents and create/update embeddings database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--docs-dir",
        default="./data/documents",
        help="Directory containing PDF documents to process"
    )
    
    parser.add_argument(
        "--db-dir",
        default="./data/chroma_db",
        help="Directory for the Chroma database"
    )
    
    args = parser.parse_args()
    
    processor = DocumentProcessor(docs_dir=args.docs_dir, db_dir=args.db_dir)
    processor.process_documents()


if __name__ == "__main__":
    main() 