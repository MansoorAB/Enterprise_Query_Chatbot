# Enterprise_Query_Chatbot
An AI assistant that answers questions about enterprise policies and documents.

## Features
- RAG-based question answering on policy documents
- Support for text and tables in PDFs
- Interactive Streamlit UI
- Document upload and processing
- Chat history

## Version Control Process
When updating policy documents:
1. Backup current master:
   ```bash
   # Create dated backup of current master
   cp -r ./data/startup/master ./data/startup/YYYYMMDD
   ```

2. Update documents:
   - Place modified policy documents in './data/startup/master/'
   - This ensures master always contains the latest version

3. Process documents:
   ```bash
   python process_documents.py --docs-dir ./data/startup/master --db-dir ./data/startup_chroma_db
   ```

This approach:
- Maintains version history with dated backups
- Keeps master as single source of truth
- Allows tracking of document changes over time

### Command-line Flexibility
Process documents with custom directories using command-line arguments:
```bash
# Default usage
python process_documents.py

# Custom directories
python process_documents.py --docs-dir ./my_pdfs --db-dir ./my_database

# Get help
python process_documents.py --help
```

### Smart Update System
The document processor includes intelligent updating capabilities:
- Only processes changed portions of documents
- Maintains document version history
- Efficiently updates embeddings for modified sections
- Preserves embeddings for unchanged content
- Tracks changes with detailed statistics:
  * New documents processed
  * Documents updated
  * Documents unchanged
  * Chunks added/removed

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

3. Process your documents:
```bash
python process_documents.py
```

4. Run the Streamlit app:
```bash
streamlit run app.py
```

## Usage
1. Place your PDF documents in the documents directory
2. Process documents using process_documents.py
3. Ask questions through the Streamlit interface
4. View answers in a chat-like interface
5. Clear chat history as needed

## Document Processing
The system maintains a smart document processing pipeline:
1. Chunks documents into manageable sections
2. Generates and stores embeddings
3. Tracks document changes using hashes
4. Updates only modified content
5. Provides detailed processing statistics

## Limitations and Considerations

### Document Chunking Trade-offs
1. **Document Processing**:
    - Uses smaller chunks (400 chars with 50 overlap)
    - Pros:
      * More granular updates
      * Efficient storage
      * Better for partial document changes
    - Cons:
      * May split related content (like tables)
      * Requires careful chunk size tuning
      * Might lose some document structure

2. **Current Solution**:
    - Using UnstructuredPDFLoader with optimized settings:
      ```python
      loader = UnstructuredPDFLoader(file_path, mode="elements", strategy="fast")
      splitter = RecursiveCharacterTextSplitter(
          chunk_size=400,
          chunk_overlap=50,
          separators=["\n\n", "\n", ".", "•", "|", " ", ""]
      )
      ```
    - Balances granularity with content coherence
    - Compromise between update efficiency and content preservation

3. **Future Considerations**:
   - For very large documents (100+ pages), PyPDFLoader might be worth exploring:
     * Handles large files more efficiently
     * Better memory management
     * Faster processing of big documents
   - Trade-off would be:
     * Less granular updates
     * Higher storage overhead
     * Need to reprocess entire pages on small changes
   - Current implementation prioritizes precise updates for smaller policy documents

## Open Issues

### RAG Response Accuracy
1. **Table Data Correlation**:
   - Current Issue:
     ```
     Q: "What is the current annual leaves per year and how many of them can be carried forward?"
     A: "Employees are entitled to 20 days of annual leave per year. However, the information 
         provided does not specify how many of those days can be carried forward."
     ```
   - Problem:
     * System finds annual leave days (20)
     * Misses carry forward info ("Up to 5 days") from same table
     * Fails to correlate related table cells
   - Potential Solutions:
     * Improve table chunking strategy
     * Add table structure metadata
     * Enhance prompt to look for related information

2. **Number Formatting in Tables**:
   - Current Issue:
     ```
     Q: "What is mid level employee base salary range and bonus range?"
     A: "The mid-level employee base salary range is 60,000−90,000, and the bonus range is 
         90,000−130,000."
     ```
   - Problem:
     * Incorrect parsing of salary ranges
     * System confuses different rows in compensation table
     * Poor formatting of numerical ranges
   - Potential Solutions:
     * Add number formatting preprocessing
     * Improve table row association
     * Add validation for numerical responses
     * Enhance table structure recognition

## Appendix: System Components

### Core Files
1. **generate_sample_policies.py**
   - Creates sample PDF policy documents
   - Configurable content and formatting
   - Used for testing and demonstration

2. **process_documents.py**
   - Handles document processing and updates
   - Chunks documents into sections
   - Generates embeddings
   - Manages version control

3. **rag_system.py**
   - Core RAG (Retrieval Augmented Generation) implementation
   - Manages connection to OpenAI
   - Handles document querying and response generation

4. **app.py**
   - Streamlit web interface
   - Chat-like interaction
   - Question input and response display

### Database Files
1. **document_metadata.json**
   - Located in: `data/startup_chroma_db/`
   - Purpose:
     * Tracks document processing history
     * Stores chunk hashes for change detection
     * Helps determine what needs updating
     * Acts as version control system

2. **chroma.sqlite3**
   - Located in: `data/startup_chroma_db/`
   - Purpose:
     * Stores vector embeddings
     * Manages relationships between:
       - Collections
       - Embeddings (high-dimensional vectors)
       - Documents (text chunks)
       - Metadata (source info, chunk hashes)
     * Powers similarity search for queries
   - Key tables:
     * `embeddings`: Numerical vectors from OpenAI
     * `documents`: Actual text chunks
     * `metadata`: Source tracking information

### Query Flow
1. User asks question
2. Question converted to embedding
3. Chroma searches similar vectors in SQLite
4. Retrieves relevant text chunks
5. GPT generates final answer

This architecture enables:
- Efficient document updates
- Fast similarity search
- Accurate response generation
- Version tracking
