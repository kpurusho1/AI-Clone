import os
import httpx
import urllib.parse
from typing import List, Dict, Any, Optional
from openai import OpenAI
from io import BytesIO
from llama_cloud_services import LlamaParse
from youtube_transcript_api import YouTubeTranscriptApi
from config import OPENAI_API_KEY, LLAMAPARSE_API_KEY
from database import supabase
from llama_index.readers.youtube_transcript import YoutubeTranscriptReader
from llama_index.readers.youtube_transcript.utils import is_youtube_video

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_openai_client():
    """
    Returns an initialized OpenAI client
    
    Returns:
        OpenAI client instance
    """
    return OpenAI(api_key=OPENAI_API_KEY)

# Initialize LlamaParse client
llama_parser = LlamaParse(
    api_key=LLAMAPARSE_API_KEY,  # can also be set in your env as LLAMA_CLOUD_API_KEY
    num_workers=4,       # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en"       # optionally define a language, default=en
)

def get_youtube_transcript(video_url: str):
    if not is_youtube_video(video_url):
        raise ValueError(f"Invalid YouTube URL: {video_url}")
    print(f"Getting transcript for YouTube video: {video_url}")
    
    try:
        # Extract video ID from URL
        video_id = extract_youtube_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract YouTube video ID from URL: {video_url}")
            
        print(f"Fetching transcript for YouTube video ID: {video_id}")
        
        # Get transcript using YouTubeTranscriptApi directly with the fetch method
        transcript_api = YouTubeTranscriptApi()
        fetched_transcript = transcript_api.fetch(video_id, languages=['en'])
        
        # Format transcript into a single text with timestamps
        full_transcript = ""
        for snippet in fetched_transcript.snippets:
            timestamp = snippet.start
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_str = f"[{minutes:02d}:{seconds:02d}] "
            full_transcript += snippet.text + " "
        '''
        # Create a document object similar to what llama_index would return
        from llama_index.core.schema import Document
        document = Document(
            text=full_transcript,
            metadata={
                "source": video_url,
                "video_id": fetched_transcript.video_id,
                "language": fetched_transcript.language,
                "language_code": fetched_transcript.language_code,
                "is_generated": fetched_transcript.is_generated,
                "title": f"YouTube Transcript: {fetched_transcript.video_id}"
            }
        )
        '''
        print(f"Successfully retrieved transcript for YouTube video: {video_url}")
        return full_transcript
        
    except Exception as e:
        print(f"Error getting YouTube transcript: {str(e)}")
        raise Exception(f"Failed to retrieve YouTube transcript: {str(e)}")

def extract_youtube_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various YouTube URL formats
    
    Args:
        url: YouTube URL in any format
        
    Returns:
        YouTube video ID or None if not a valid YouTube URL
    """
    import re
    # Regular expressions for different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)',  # Standard and shortened URLs
        r'youtube\.com\/embed\/([\w-]+)',                      # Embed URLs
        r'youtube\.com\/v\/([\w-]+)',                          # Old embed URLs
        r'youtube\.com\/user\/[\w-]+\/\?v=([\w-]+)',         # User URLs
        r'youtube\.com\/attribution_link\?.*v%3D([\w-]+)',    # Attribution links
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

async def create_vector_store(client, vector_name: str):
    try:
        # Create a vector store for the document
        vector_store = client.vector_stores.create(
            name = vector_name
        )
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        raise Exception(f"Error creating vector store: {str(e)}")

async def create_file_for_vector_store(client, document_url: str, document_name: str = None, domain_name: str = None, expert_name: str = None, client_name: str = None) -> str:
    """
    Create a file from a document URL and return the file ID
    
    Args:
        client: OpenAI client
        document_url: URL or local path to the document
        document_name: Optional name for the document (will be generated if not provided)
        domain_name: Optional domain name to associate the document with
        expert_name: Optional expert name to associate the document with
        client_name: Optional client name to associate the document with
        
    Returns:
        File ID created in OpenAI
    """
    try:
        print(f"Processing document from URL: {document_url}")
        temp_path = None
        
        if document_url.__contains__("youtube"):
            # get_youtube_transcript
            transcript = get_youtube_transcript(document_url)
            # Convert string to bytes before using BytesIO
            file_content = BytesIO(transcript.encode('utf-8'))
            # Create a more descriptive filename with .txt extension
            video_id = extract_youtube_id(document_url) or "video"
            file_name = f"youtube_transcript_{video_id}.txt"
            file_tuple = (file_name, file_content)
            result = client.files.create(
                file=file_tuple,
                purpose="assistants"
            )
        # Download the document if it's a web URL
        elif document_url.startswith(('http://', 'https://')):
            # Extract file extension from URL
            url_path = urllib.parse.urlparse(document_url).path
            file_extension = os.path.splitext(url_path)[1]
            print(f"Detected file extension from URL: {file_extension}")
            
            # Special handling for arxiv URLs
            
            if not file_extension or file_extension not in [
                '.c', '.cpp', '.css', '.csv', '.doc', '.docx', '.gif', '.go', '.html', 
                '.java', '.jpeg', '.jpg', '.js', '.json', '.md', '.pdf', '.php', '.pkl', 
                '.png', '.pptx', '.py', '.rb', '.tar', '.tex', '.ts', '.txt', '.webp', 
                '.xlsx', '.xml', '.zip'
            ]:
                # If no extension found or invalid extension, default to PDF
                file_extension = '.pdf'
                print(f"No valid extension detected, defaulting to: {file_extension}")
            
            async with httpx.AsyncClient(timeout=60.0) as httpclient:
                response = await httpclient.get(document_url)
                response.raise_for_status()
                # using OpenAI document to create BytesIO object
                file_content = BytesIO(response.content)
                file_name = document_url.split("/")[-1]
                file_tuple = (file_name, file_content)
                result = client.files.create(
                    file=file_tuple,
                    purpose="assistants"
                )

        else:
            # It's a local file path
            # Try different path resolutions to find the file
            file_path = document_url
            found = False
            
            # List of possible base directories to try
            base_dirs = [
                os.getcwd(),  # Current working directory
                os.path.dirname(os.path.abspath(__file__)),  # Directory of this script
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),  # Project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Docs"),  # Docs folder
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"),  # data folder
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "documents")  # documents folder
            ]
            
            # First try the path as is
            if os.path.exists(file_path) and os.path.isfile(file_path):
                found = True
                print(f"Found file at original path: {file_path}")
            else:
                # Try resolving against different base directories
                for base_dir in base_dirs:
                    resolved_path = os.path.join(base_dir, document_url)
                    print(f"Trying path: {resolved_path}")
                    if os.path.exists(resolved_path) and os.path.isfile(resolved_path):
                        file_path = resolved_path
                        found = True
                        print(f"Found file at: {file_path}")
                        break
            
            if not found:
                raise FileNotFoundError(f"Could not find file at {document_url} or any resolved paths")
                
            with open(file_path, "rb") as file_content:
                result = client.files.create(
                    file=file_content,
                    purpose="assistants"
                )

        # Store document information in the documents table if domain is provided
        if domain_name:
            # Get count of existing documents for this domain to generate name
            # Use provided document name or generate one if not provided
            if document_name:
                doc_name = document_name
            else:
                doc_count_result = supabase.table("documents").select("id").eq("domain", domain_name).execute()
                doc_count = len(doc_count_result.data) + 1
                doc_name = f"Document {doc_count}"
                
            # Initialize variables with default values
            created_by = None
            
            if expert_name:
                created_by = expert_name
                
            # No need to reassign client_name to itself
            # if client_name:
            #    client_name = client_name
                
            # Check if document with same name already exists
            existing_doc = supabase.table("documents").select("*").eq("name", doc_name).execute()
            
            if existing_doc.data and len(existing_doc.data) > 0:
                # Document with this name already exists
                print(f"Document with name '{doc_name}' already exists. Checking URL...")
                
                # If it's the same URL, just return the existing OpenAI file ID
                if existing_doc.data[0].get("document_link") == document_url:
                    print(f"Same URL found. Reusing existing OpenAI file ID: {existing_doc.data[0].get('openai_file_id')}")
                    return existing_doc.data[0].get("openai_file_id")
                
                # If it's a different URL, make the name unique by adding a timestamp
                import time
                timestamp = int(time.time())
                doc_name = f"{doc_name}_{timestamp}"
                print(f"Different URL. Using unique name: {doc_name}")
            
            # Insert document record
            doc_record = {
                "name": doc_name,
                "document_link": document_url,
                "domain": domain_name,
            }
            
            # Only add these fields if they have values
            if created_by:
                doc_record["created_by"] = created_by
            if client_name:
                doc_record["client_name"] = client_name
                
            # Add the OpenAI file ID to the record
            doc_record["openai_file_id"] = result.id
            
            # Insert the complete record
            supabase.table("documents").insert(doc_record).execute()
            
            print(f"Stored document in database: {doc_name}, OpenAI file ID: {result.id}")
        # Return the extracted result id
        return result.id
    except Exception as e:
        print(f"Error in create_file_for_vector_store: {str(e)}")
        print(f"Error type: {type(e)}")
        raise Exception(f"Error creating file: {str(e)}")

async def create_files_for_vector_store(client, document_urls: dict, domain_name: str = None, expert_name: str = None, client_name: str = None) -> list:
    """
    Create multiple files from document URLs and return the file IDs
    
    Args:
        client: OpenAI client
        document_urls: Dictionary of document names to URLs or local paths
        domain_name: Optional domain name to associate the documents with
        expert_name: Optional expert name to associate the documents with
        client_name: Optional client name to associate the documents with
        
    Returns:
        List of file IDs created in OpenAI
    """
    print(f"Processing batch of {len(document_urls)} documents")
    file_ids = []
    failed_docs = []
    
    # Process each document URL and collect file IDs
    for doc_name, document_url in document_urls.items():
        try:
            file_id = await create_file_for_vector_store(client, document_url, document_name=doc_name, domain_name=domain_name, expert_name=expert_name, client_name=client_name)
            file_ids.append(file_id)
            print(f"Created file with ID: {file_id} for document: {doc_name}")
        except Exception as e:
            print(f"Failed to process document '{doc_name}' with URL '{document_url}': {str(e)}")
            failed_docs.append(doc_name)
            continue  # Skip this document and continue with the next one
    
    # Report on any failed documents
    if failed_docs:
        print(f"Warning: {len(failed_docs)} documents failed to process: {', '.join(failed_docs)}")
    
    return file_ids

async def add_documents_to_vector_store(client, vector_store_id: str, document_urls: dict, domain_name: str, expert_name: str, client_name: str = None):
    """
    Process multiple documents and add them to a vector store using batch API
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        document_urls: Dictionary of document names to URLs or local paths
        domain_name: Optional domain name to associate the documents with
        expert_name: Name of the expert to associate the documents with
        
    Returns:
        Dictionary with file_ids, batch_id, vector_store_id, and status
    """
    # First create files from the documents
    file_ids = await create_files_for_vector_store(client, document_urls, domain_name, expert_name, client_name)
    print(f"Created {len(file_ids)} files with IDs: {file_ids}")
    
    # If no files were successfully created, return early with a warning
    if not file_ids:
        print("Warning: No files were successfully created. Cannot add to vector store.")
        return {
            "file_ids": [],
            "batch_id": None,
            "vector_store_id": vector_store_id,
            "status": "failed",
            "message": "No files were successfully created"
        }
    
    try:
        # Then add the files to the vector store as a batch
        batch_result = await add_batch_to_vector_store(client, vector_store_id, file_ids)
        print(f"Added files to vector store as batch: {batch_result['id']}")
        
        return {
            "file_ids": file_ids,
            "batch_id": batch_result['id'],
            "vector_store_id": vector_store_id,
            "status": batch_result['status'],
            "message": f"Successfully added {len(file_ids)} files to vector store"
        }
    except Exception as e:
        print(f"Error adding documents to vector store: {str(e)}")
        # Return partial success if we at least created some files
        return {
            "file_ids": file_ids,
            "batch_id": None,
            "vector_store_id": vector_store_id,
            "status": "partial_failure",
            "message": f"Created {len(file_ids)} files but failed to add them to vector store: {str(e)}"
        }

async def add_batch_to_vector_store(client, vector_store_id: str, document_ids: list):
    """
    Add multiple documents to a vector store using batch API
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        document_ids: List of document IDs to add to the vector store
        
    Returns:
        Batch creation result
    """
    try:
        print(f"Adding batch of {len(document_ids)} documents to vector store {vector_store_id}")
        result = client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=document_ids
        )
        print(f"Batch creation initiated with ID: {result.id}")
        
        # Return a consistent dictionary format instead of the raw APIResponse
        return {
            "id": result.id,
            "status": result.status,
            "vector_store_id": vector_store_id,
            "file_ids": document_ids
        }
    except Exception as e:
        print(f"Error adding batch to vector store: {str(e)}")
        raise Exception(f"Error adding batch to vector store: {str(e)}")
        
async def edit_vector_store(client, vector_store_id: str, file_ids: list, document_urls: dict, domain_name: str, expert_name: str = None, client_name: str = None):
    """
    Edit an existing vector store by adding new documents and/or removing deselected documents
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store to edit
        file_ids: Existing file IDs in the vector store
        document_urls: Dictionary mapping document names to URLs to keep or add to the vector store
        domain_name: Domain name to associate the documents with
        expert_name: Optional expert name to associate the documents with
        client_name: Optional client name to associate the documents with
        
    Returns:
        Dictionary with status, message, file_ids, and batch_id
    """
    try:
        print(f"Editing vector store {vector_store_id} with {len(document_urls)} documents")
        
        # Get existing document URLs from the documents table that match the file_ids
        query = supabase.table("documents").select("id, document_link, openai_file_id").in_("openai_file_id", file_ids)
        existing_docs_query = query.execute()
        existing_docs = existing_docs_query.data
        
        # Create a mapping of document URLs to their file IDs
        existing_url_to_file_id = {doc["document_link"]: doc["openai_file_id"] for doc in existing_docs if "document_link" in doc and "openai_file_id" in doc}
        
        # Identify which URLs are new and need to be added
        existing_urls = list(existing_url_to_file_id.keys())
        document_urls_values = list(document_urls.values())
        new_urls_dict = {name: url for name, url in document_urls.items() if url not in existing_urls}
        
        # Create files for each new document URL
        new_file_ids = []
        for doc_name, document_url in new_urls_dict.items():
            try:
                file_id = await create_file_for_vector_store(client, document_url, document_name=doc_name, domain_name=domain_name, expert_name=expert_name, client_name=client_name)
                new_file_ids.append(file_id)
                print(f"Created file with ID {file_id} for document {doc_name}: {document_url}")
            except Exception as e:
                print(f"Error creating file for document {doc_name}: {document_url}: {str(e)}")
                # Continue with other documents even if one fails
                continue
        
        # Get file IDs for URLs that should be kept
        kept_file_ids = [existing_url_to_file_id[url] for url in document_urls.values() if url in existing_urls]
        
        # Keep track of all file IDs for database records
        all_file_ids = kept_file_ids + new_file_ids
        print(f"Combined file IDs: {all_file_ids}")
        
        # Only add new files to the vector store batch
        batch_id = None
        if new_file_ids:
            print(f"Adding only new files to vector store: {new_file_ids}")
            batch_result = await add_batch_to_vector_store(client, vector_store_id, new_file_ids)
            batch_id = batch_result['id']  # Using dictionary access since we updated the function
            print(f"Added batch with ID {batch_id} to vector store {vector_store_id}")
        else:
            print("No new files to add to vector store")
            
        # Delete files that are not part of kept_file_ids from documents table
        files_to_delete = [file_id for file_id in file_ids if file_id not in kept_file_ids and file_id not in new_file_ids]
        if files_to_delete:
            print(f"Deleting {len(files_to_delete)} files that are no longer needed: {files_to_delete}")
            try:
                # Delete from documents table where openai_file_id is in files_to_delete
                delete_result = supabase.table("documents").delete().in_("openai_file_id", files_to_delete).execute()
                
                print(f"Deleted {len(delete_result.data)} documents from the database")
                
                # Delete files from the vector store in OpenAI
                for file_id in files_to_delete:
                    try:
                        # First delete from vector store
                        client.vector_stores.files.delete(
                            vector_store_id=vector_store_id,
                            file_id=file_id
                        )
                        print(f"Deleted file {file_id} from vector store {vector_store_id}")
                        
                        # Then delete the file from OpenAI
                        client.files.delete(file_id)
                        print(f"Deleted file {file_id} from OpenAI")
                    except Exception as e:
                        print(f"Error deleting file {file_id} from OpenAI: {str(e)}")
                        # Continue with other files even if one fails
            except Exception as e:
                print(f"Error deleting documents: {str(e)}")
                # Continue anyway as this is not critical
        
        return {
            "status": "success",
            "message": f"Updated vector store {vector_store_id} with {len(new_file_ids)} new documents",
            "file_ids": new_file_ids,
            "all_file_ids": all_file_ids,
            "batch_id": batch_id,
            "vector_store_id": vector_store_id
        }
    except Exception as e:
        print(f"Error editing vector store: {str(e)}")
        raise Exception(f"Error editing vector store: {str(e)}")

#check for status as 'completed'
async def check_vector_store_status(client, vector_store_id: str):
    try:
        result = client.vector_stores.files.list(
            vector_store_id=vector_store_id
        )
        return result
    except Exception as e:
        print(f"Error checking vector store status: {str(e)}")
        raise Exception(f"Error checking vector store status: {str(e)}")

async def check_batch_status(client, vector_store_id: str, batch_id: str):
    """
    Check the status of a file batch operation
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        batch_id: ID of the batch operation to check
        
    Returns:
        Batch status information
    """
    try:
        result = client.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            file_batch_id=batch_id
        )
        print(f"Batch status: {result.status}")
        return result
    except Exception as e:
        print(f"Error checking batch status: {str(e)}")
        raise Exception(f"Error checking batch status: {str(e)}")
        raise Exception(f"Error checking vector store status: {str(e)}")

async def upload_to_supabase_storage(file_content: str, file_name: str) -> str:
    """
    Upload a file to Supabase storage and return the URL
    """
    try:
        # Upload the file to Supabase storage
        response = supabase.storage.from_("documents").upload(
            file_name, 
            file_content.encode('utf-8'),
            file_options={"content-type": "text/markdown"}
        )
        
        # Get the public URL
        file_url = supabase.storage.from_("documents").get_public_url(file_name)
        return file_url
    except Exception as e:
        raise Exception(f"Error uploading to Supabase storage: {str(e)}")

async def create_vector_index(documents: List[str], namespace: str) -> str:
    """
    Create a vector index using OpenAI's vectorStores API
    """
    try:
        print(f"[DEBUG] create_vector_index: Starting with {len(documents)} documents for namespace '{namespace}'")
        
        # Prepare the documents for vector store creation
        vector_docs = []
        for i, doc in enumerate(documents):
            try:
                vector_docs.append({
                    "id": f"doc_{i}",
                    "text": doc,
                    "metadata": {"source": namespace}
                })
                if i % 10 == 0 and i > 0:
                    print(f"[DEBUG] create_vector_index: Processed {i}/{len(documents)} documents")
            except Exception as e:
                print(f"[ERROR] create_vector_index: Error processing document {i}: {str(e)}")
                print(f"[ERROR] Document content type: {type(doc)}")
                if isinstance(doc, str):
                    print(f"[ERROR] Document length: {len(doc)}")
                    print(f"[ERROR] Document preview: {doc[:100]}...")
                raise
        
        print(f"[DEBUG] create_vector_index: Creating vector store with name 'Vector Store - {namespace}'")
        try:
            # Create a vector store using the client.vector_stores.create method
            vector_store = client.vector_stores.create(
                name=f"Vector Store - {namespace}",
                type="text",
                vector_dimensions=1536,  # Default for text-embedding-ada-002
                model="text-embedding-ada-002",
                content_type="application/json"
            )
            print(f"[DEBUG] create_vector_index: Vector store created with ID: {vector_store.id}")
        except Exception as e:
            print(f"[ERROR] create_vector_index: Failed to create vector store: {str(e)}")
            raise
        
        # Add documents to the vector store
        batch_size = 100  # Process in batches to avoid API limits
        print(f"[DEBUG] create_vector_index: Adding documents in batches of {batch_size}")
        for i in range(0, len(vector_docs), batch_size):
            batch = vector_docs[i:i+batch_size]
            batch_end = min(i+batch_size, len(vector_docs))
            print(f"[DEBUG] create_vector_index: Processing batch {i}-{batch_end} of {len(vector_docs)}")
            try:
                client.vector_stores.add_vectors(
                    vector_store_id=vector_store.id,
                    vectors=batch
                )
                print(f"[DEBUG] create_vector_index: Successfully added batch {i}-{batch_end}")
            except Exception as e:
                print(f"[ERROR] create_vector_index: Failed to add vectors batch {i}-{batch_end}: {str(e)}")
                raise
        
        print(f"[DEBUG] create_vector_index: Successfully created vector store with ID: {vector_store.id}")
        return vector_store.id
    except Exception as e:
        print(f"[ERROR] create_vector_index: {str(e)}")
        raise Exception(f"Error creating vector index: {str(e)}")

async def query_vector_index(query: str, vector_store_ids: list = None, context: str = "") -> dict:
    """
    Query a vector index using OpenAI's vectorStores API with file_search tool
    If vector_store_ids is None, use LLM memory (no vector search)
    """
    try:
        print(f"[DEBUG] query_vector_index: Starting query '{query}' with vector_store_ids '{vector_store_ids}'")

        try:
            # Use LLM directly if no vector_store_ids provided
            if not vector_store_ids:
                print(f"[DEBUG] query_vector_index: No vector_store_ids provided, using LLM directly")
                response = client.responses.create(
                    model="gpt-4o",
                    input=[
                            {"role": "system", "content": context},
                            {"role": "user", "content": query}
                        ],
                    temperature=0
                )
            else:
                # Use vector search
                print(f"[DEBUG] query_vector_index: Creating OpenAI response with file_search tool")
                response = client.responses.create(
                    model="gpt-4o",
                    input=[
                            {"role": "system", "content": context},
                            {"role": "user", "content": query}
                        ],
                    tools=[
                        {
                            "type": "file_search",
                            "vector_store_ids": vector_store_ids,
                            "max_num_results": 2
                        }
                    ],
                    include=["file_search_call.results"],
                    temperature=0
                )
            print(f"[DEBUG] query_vector_index: Response type: {type(response)}")
        except Exception as e:
            print(f"[ERROR] query_vector_index: Failed to create OpenAI response: {str(e)}")
            raise

        # Process the response
        print(f"[DEBUG] query_vector_index: Processing response")
        
        # Extract the text from the response using our helper function
        actual_text = extract_text_from_response(response)
        print(f"[DEBUG] query_vector_index: Extracted text: {actual_text[:50]}...")
        
        # Ensure we have a string
        if not isinstance(actual_text, str):
            print(f"[DEBUG] query_vector_index: Converting non-string text to string")
            actual_text = str(actual_text)
        return {"text": actual_text, "citations": None}
    except Exception as e:
        print(f"[ERROR] query_vector_index: {str(e)}")
        raise Exception(f"Error querying vector index: {str(e)}")

def extract_text_from_response(response):
    """
    Extract text content from various OpenAI response formats.
    Handles different response structures including ResponseOutputMessage objects.
    
    Based on OpenAI's standard response structure:
    response.output: List[ResponseOutputMessage]
    
    Where each ResponseOutputMessage has:
    - id: str
    - role: str (usually 'assistant')
    - content: List[ResponseOutputText]
    - type: str (usually 'message')
    
    And each ResponseOutputText has:
    - text: str (the actual content we want)
    - type: str (usually 'output_text')
    """
    try:
        print(f"[DEBUG] extract_text_from_response: Response type: {type(response)}")
        
        # Standard way based on OpenAI's response structure
        if hasattr(response, 'output'):
            
            # Handle the standard case where output is a list of ResponseOutputMessage objects
            if isinstance(response.output, list):
                print(f"[DEBUG] extract_text_from_response: Output is a list with {len(response.output)} items")
                
                # Extract text using the pattern shown in the example
                for msg in response.output:
                    if hasattr(msg, 'role') and msg.role == "assistant" and hasattr(msg, 'content'):
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                print(f"[DEBUG] extract_text_from_response: Found text in assistant message")
                                return content.text
                
                # If we didn't find an assistant message, try any message
                for msg in response.output:
                    if hasattr(msg, 'content') and isinstance(msg.content, list):
                        for content in msg.content:
                            print(f"[DEBUG] extract_text_from_response: Found content in message content")
                            if hasattr(content, 'text'):
                                print(f"[DEBUG] extract_text_from_response: Found text in message content")
                                return content.text
        
        # Handle ResponseOutputMessage string representation
        if hasattr(response, 'text'):
            text_value = response.text
            if isinstance(text_value, str):
                # Check if it's a ResponseOutputMessage string representation
                print(f"[DEBUG] extract_text_from_response: Found text in message content")
                if 'ResponseOutputMessage' in text_value and 'text=' in text_value:
                    # Extract using regex
                    import re
                    print(f"[DEBUG] extract_text_from_response: Attempting to extract text with regex")
                    match = re.search(r"text='([^']*)'(?:, type='output_text')", text_value)
                    if match:
                        extracted_text = match.group(1)
                        # Unescape any escaped quotes
                        extracted_text = extracted_text.replace("\'", "'")
                        print(f"[DEBUG] extract_text_from_response: Extracted text from ResponseOutputMessage using regex")
                        return extracted_text
                    else:
                        # Try a more general pattern
                        match = re.search(r"text='(.*?)'", text_value)
                        if match:
                            extracted_text = match.group(1)
                            extracted_text = extracted_text.replace("\'", "'")
                            print(f"[DEBUG] extract_text_from_response: Extracted text using general regex")
                            return extracted_text
                # Just a regular string
                return text_value
            # It's an object with potential text attribute
            elif hasattr(text_value, 'text'):
                print(f"[DEBUG] extract_text_from_response: Found text in message content")
                return text_value.text
        
        # Fallback to other possible structures
        
        # Check for content attribute
        if hasattr(response, 'content') and isinstance(response.content, list):
            for item in response.content:
                print(f"[DEBUG] extract_text_from_response: Found content in message content")
                if hasattr(item, 'text'):
                    print(f"[DEBUG] extract_text_from_response: Found text in message content")
                    return item.text
        
        # If we got here, return the string representation as a last resort
        print(f"[DEBUG] extract_text_from_response: No structured text found, using string representation")
        return str(response)
    except Exception as e:
        print(f"[ERROR] extract_text_from_response: {str(e)}")
        return str(response)

async def delete_vector_index(vector_id: str) -> bool:
    """
    Delete a vector index using OpenAI's vectorStores API
    """
    try:
        print(f"[DEBUG] delete_vector_index: Attempting to delete vector store with ID: {vector_id}")
        try:
            # Delete the vector store using the client
            client.vector_stores.delete(vector_id)
            print(f"[DEBUG] delete_vector_index: Successfully deleted vector store with ID: {vector_id}")
            return True
        except Exception as e:
            print(f"[ERROR] delete_vector_index: Failed to delete vector store: {str(e)}")
            raise
    except Exception as e:
        print(f"[ERROR] delete_vector_index: {str(e)}")
        raise Exception(f"Error deleting vector index: {str(e)}")

async def generate_persona_from_qa(client, qa_data):
    """
    Generate a persona summary from question-answer data
    
    Args:
        client: OpenAI client
        qa_data: List of dictionaries with 'question' and 'answer' keys
        
    Returns:
        Generated persona summary as a string
    """
    try:
        print(f"[DEBUG] generate_persona_from_qa: Generating persona from {len(qa_data)} QA pairs")
        
        # Format QA data as a string
        qa_formatted = ""
        for i, qa in enumerate(qa_data):
            qa_formatted += f"Question {i+1}: {qa.get('question', '')}\n"
            qa_formatted += f"Answer {i+1}: {qa.get('answer', '')}\n\n"
        
        # Create system prompt
        system_prompt = """Use the question and answers to understand the experience and expertise of the individual. 
        Summarize them into a five to six line summary describing the individual's persona. 
        This summary should capture their expertise, experience, and communication style 
        so that it can be passed as a system prompt to any LLM call."""
        
        # Create user prompt
        user_prompt = f"Here are the question-answer pairs:\n\n{qa_formatted}\n\nBased on these, create a concise persona summary."
        
        # Call OpenAI API
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        # Extract the generated persona
        persona_summary = extract_text_from_response(response)
        print(f"[DEBUG] generate_persona_from_qa: Generated persona summary")
        
        return persona_summary
    except Exception as e:
        print(f"[ERROR] generate_persona_from_qa: {str(e)}")
        raise Exception(f"Error generating persona from QA data: {str(e)}")

# OpenAI Assistant API functions
async def create_assistant(expert_name: str, memory_type: str = "expert", client_name: str = None, model: str = "gpt-4o"):
    """
    Create an OpenAI Assistant for a specific expert and memory type
    
    Args:
        expert_name: Name of the expert
        memory_type: Type of memory to use (llm, domain, expert, client)
        client_name: Optional client name for client-specific memory
        model: OpenAI model to use
        
    Returns:
        Assistant object with ID
    """
    try:
        print(f"[DEBUG] create_assistant: Creating assistant for expert '{expert_name}' with memory type '{memory_type}'")
        
        # Get expert context
        expert_data = None
        try:
            # Get expert data from database
            expert_result = supabase.table("experts").select("*").eq("name", expert_name).execute()
            if expert_result.data and len(expert_result.data) > 0:
                expert_data = expert_result.data[0]
        except Exception as e:
            print(f"[ERROR] create_assistant: Error getting expert data: {str(e)}")
            raise Exception(f"Error getting expert data: {str(e)}")
        
        if not expert_data:
            raise Exception(f"Expert '{expert_name}' not found")
        
        # Get vector store ID based on memory type
        vector_id = None
        
        try:
            # Get vector store IDs directly from vector_stores table
            query = supabase.table("vector_stores").select("vector_id")
            
            # Apply filters based on available information
            domain_name = expert_data.get("domain")
            if domain_name:
                query = query.eq("domain_name", domain_name)
            
            if expert_name:
                query = query.eq("expert_name", expert_name)
            else:
                query = query.is_("expert_name", "null")
            
            if client_name:
                if not expert_name:
                    raise HTTPException(status_code=400, 
                                      detail="Cannot specify client name without expert name")
                query = query.eq("client_name", client_name)
            else:
                query = query.is_("client_name", "null")
            
            # Execute the query
            vector_store_result = query.execute()
            
            # Process results
            if vector_store_result.data and len(vector_store_result.data) > 0:
                vector_id = vector_store_result.data[0].get("vector_id")
            if not vector_id:
                raise HTTPException(status_code=404, detail="Vector store not found")
                
            print(f"[DEBUG] create_assistant: Found {vector_id} vector store ID")
            
        except Exception as e:
            print(f"[ERROR] create_assistant: Error getting vector IDs: {str(e)}")
            # Continue execution even if there's an error retrieving vector IDs
        
        # Create assistant instructions based on expert context and memory type
        instructions = f"You are an AI assistant named {expert_name}."
        
        if expert_data.get("context"):
            instructions += f"\n\nYou have the following experience and expertise: {expert_data.get('context')}."
        
        if memory_type == "domain":
            instructions += f"\n\nYou have access to domain knowledge about {expert_data.get('domain')}."
        elif memory_type == "expert":
            instructions += f"\n\nYou have access to expert-specific knowledge."
        elif memory_type == "client" and client_name:
            instructions += f"\n\nYou have access to client-specific knowledge for {client_name}."
        
        # Create the assistant
        tools = []
        tool_resources = {}
        if vector_id and memory_type != "llm":
            # Use file_search instead of retrieval as per the latest OpenAI API
            tools.append({"type": "file_search"})
            tool_resources = {
                "file_search": {
                    "vector_store_ids": [vector_id]
                }
            }
        
        assistant = client.beta.assistants.create(
            name=f"{expert_name}_{memory_type}" + (f"_{client_name}" if client_name else ""),
            instructions=instructions,
            model=model,
            tools=tools,
            tool_resources=tool_resources
        )
        
        # Store assistant ID in database
        try:
            # Create a table entry for the assistant
            assistant_data = {
                "assistant_id": assistant.id,
                "expert_name": expert_name,
                "memory_type": memory_type,
                "client_name": client_name,
                "vector_ids": [vector_id]
            }
            
            supabase.table("assistants").insert(assistant_data).execute()
            print(f"[DEBUG] create_assistant: Assistant created with ID: {assistant.id}")
        except Exception as e:
            print(f"[ERROR] create_assistant: Error storing assistant data: {str(e)}")
            # Try to delete the assistant if we couldn't store it
            try:
                client.beta.assistants.delete(assistant.id)
            except:
                pass
            raise Exception(f"Error storing assistant data: {str(e)}")
        
        return assistant
    except Exception as e:
        print(f"[ERROR] create_assistant: {str(e)}")
        raise Exception(f"Error creating assistant: {str(e)}")

async def get_or_create_assistant(expert_name: str, memory_type: str = "expert", client_name: str = None, model: str = "gpt-4o"):
    """
    Get an existing assistant or create a new one
    
    Args:
        expert_name: Name of the expert
        memory_type: Type of memory to use (llm, domain, expert, client)
        client_name: Optional client name for client-specific memory
        model: OpenAI model to use
        
    Returns:
        Assistant object with ID
    """
    try:
        print(f"[DEBUG] get_or_create_assistant: Looking for assistant for expert '{expert_name}' with memory type '{memory_type}'")
        
        # Check if assistant already exists
        query = supabase.table("assistants").select("*").eq("expert_name", expert_name).eq("memory_type", memory_type)
        
        if memory_type == "client" and client_name:
            query = query.eq("client_name", client_name)
        elif memory_type != "client":
            query = query.is_("client_name", "null")
        
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            assistant_id = result.data[0].get("assistant_id")
            print(f"[DEBUG] get_or_create_assistant: Found existing assistant with ID: {assistant_id}")
            
            # Get the assistant from OpenAI
            try:
                assistant = client.beta.assistants.retrieve(assistant_id)
                return assistant
            except Exception as e:
                print(f"[ERROR] get_or_create_assistant: Error retrieving assistant: {str(e)}")
                # If the assistant doesn't exist in OpenAI, create a new one
                print(f"[DEBUG] get_or_create_assistant: Creating new assistant since retrieval failed")
                return await create_assistant(expert_name, memory_type, client_name, model)
        else:
            # Create a new assistant
            print(f"[DEBUG] get_or_create_assistant: No existing assistant found, creating new one")
            return await create_assistant(expert_name, memory_type, client_name, model)
    except Exception as e:
        print(f"[ERROR] get_or_create_assistant: {str(e)}")
        raise Exception(f"Error getting or creating assistant: {str(e)}")

async def create_thread():
    """
    Create a new thread for conversation
    
    Returns:
        Thread object with ID
    """
    try:
        print(f"[DEBUG] create_thread: Creating new thread")
        thread = client.beta.threads.create()
        return thread
    except Exception as e:
        print(f"[ERROR] create_thread: {str(e)}")
        raise Exception(f"Error creating thread: {str(e)}")

async def add_message_to_thread(thread_id: str, content: str, role: str = "user"):
    """
    Add a message to a thread
    
    Args:
        thread_id: ID of the thread
        content: Message content
        role: Message role (user or assistant)
        
    Returns:
        Message object
    """
    try:
        print(f"[DEBUG] add_message_to_thread: Adding message to thread {thread_id}")
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
        return message
    except Exception as e:
        print(f"[ERROR] add_message_to_thread: {str(e)}")
        raise Exception(f"Error adding message to thread: {str(e)}")

async def run_thread(thread_id: str, assistant_id: str):
    """
    Run a thread with an assistant
    
    Args:
        thread_id: ID of the thread
        assistant_id: ID of the assistant
        
    Returns:
        Run object
    """
    try:
        print(f"[DEBUG] run_thread: Running thread {thread_id} with assistant {assistant_id}")
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        return run
    except Exception as e:
        print(f"[ERROR] run_thread: {str(e)}")
        raise Exception(f"Error running thread: {str(e)}")

async def get_run_status(thread_id: str, run_id: str):
    """
    Get the status of a run
    
    Args:
        thread_id: ID of the thread
        run_id: ID of the run
        
    Returns:
        Run object
    """
    try:
        print(f"[DEBUG] get_run_status: Getting status of run {run_id} in thread {thread_id}")
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        return run
    except Exception as e:
        print(f"[ERROR] get_run_status: {str(e)}")
        raise Exception(f"Error getting run status: {str(e)}")

async def get_thread_messages(thread_id: str, limit: int = 10):
    """
    Get messages from a thread
    
    Args:
        thread_id: ID of the thread
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of messages
    """
    try:
        print(f"[DEBUG] get_thread_messages: Getting messages from thread {thread_id}")
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=limit
        )
        return messages
    except Exception as e:
        print(f"[ERROR] get_thread_messages: {str(e)}")
        raise Exception(f"Error getting thread messages: {str(e)}")

async def wait_for_run_completion(thread_id: str, run_id: str, max_wait_seconds: int = 60):
    """
    Wait for a run to complete
    
    Args:
        thread_id: ID of the thread
        run_id: ID of the run
        max_wait_seconds: Maximum time to wait in seconds
        
    Returns:
        Run object when complete
    """
    import time
    import asyncio
    
    try:
        print(f"[DEBUG] wait_for_run_completion: Waiting for run {run_id} to complete")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            run = await get_run_status(thread_id, run_id)
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
            
            # Wait a bit before checking again
            await asyncio.sleep(1)
        
        # If we get here, we timed out
        print(f"[WARNING] wait_for_run_completion: Timed out waiting for run {run_id} to complete")
        return await get_run_status(thread_id, run_id)
    except Exception as e:
        print(f"[ERROR] wait_for_run_completion: {str(e)}")
        raise Exception(f"Error waiting for run completion: {str(e)}")

async def get_assistant_response(thread_id: str, run_id: str):
    """
    Get the assistant's response from a completed run
    
    Args:
        thread_id: ID of the thread
        run_id: ID of the run
        
    Returns:
        Assistant's response text
    """
    try:
        print(f"[DEBUG] get_assistant_response: Getting response from run {run_id}")
        
        # Get the messages from the thread
        messages = await get_thread_messages(thread_id, limit=1)
        
        if not messages.data:
            return "No response from assistant."
        
        # Get the latest message (should be from the assistant)
        latest_message = messages.data[0]
        
        if latest_message.role != "assistant":
            return "No response from assistant."
        
        # Extract the text from the message content
        response_text = ""
        for content_item in latest_message.content:
            if content_item.type == "text":
                response_text += content_item.text.value
        
        return response_text
    except Exception as e:
        print(f"[ERROR] get_assistant_response: {str(e)}")
        raise Exception(f"Error getting assistant response: {str(e)}")

async def delete_files_in_vector_store(client, vector_store_id: str, file_ids: list):
    """
    Delete files from a vector store and from OpenAI
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        file_ids: List of file IDs to delete
        
    Returns:
        Dictionary with status and deleted_files count
    """
    try:
        deleted_count = 0
        failed_count = 0
        failed_files = []
        
        for file_id in file_ids:
            try:
                # First delete from vector store
                client.vector_stores.files.delete(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
                print(f"Deleted file {file_id} from vector store {vector_store_id}")
                
                # Then delete the file from OpenAI
                client.files.delete(file_id)
                print(f"Deleted file {file_id} from OpenAI")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {file_id} from OpenAI: {str(e)}")
                failed_count += 1
                failed_files.append(file_id)
                # Continue with other files even if one fails
        
        return {
            "status": "completed",
            "deleted_files": deleted_count,
            "failed_files": failed_count,
            "failed_file_ids": failed_files
        }
    except Exception as e:
        print(f"Error in delete_files_in_vector_store: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "deleted_files": 0
        }

async def query_expert_with_assistant(expert_name: str, query: str, memory_type: str = "expert", client_name: str = None, thread_id: str = None):
    """
    Query an expert using the OpenAI Assistant API
    
    Args:
        expert_name: Name of the expert
        query: User query
        memory_type: Type of memory to use (llm, domain, expert, client)
        client_name: Optional client name for client-specific memory
        thread_id: Optional thread ID for continuing a conversation
        
    Returns:
        Dictionary with response, thread_id, and run_id
    """
    try:
        print(f"[DEBUG] query_expert_with_assistant: Querying expert '{expert_name}' with memory type '{memory_type}'")
        
        # Get or create the assistant
        assistant = await get_or_create_assistant(expert_name, memory_type, client_name)
        
        # Create a thread if one wasn't provided
        if not thread_id:
            thread = await create_thread()
            thread_id = thread.id
        
        # Add the user message to the thread
        await add_message_to_thread(thread_id, query)
        
        # Run the thread with the assistant
        run = await run_thread(thread_id, assistant.id)
        
        # Wait for the run to complete
        run = await wait_for_run_completion(thread_id, run.id)
        
        # Get the assistant's response
        response = await get_assistant_response(thread_id, run.id)
        
        return {
            "response": {"text": response},
            "thread_id": thread_id,
            "run_id": run.id,
            "status": run.status
        }
    except Exception as e:
        print(f"[ERROR] query_expert_with_assistant: {str(e)}")
        raise Exception(f"Error querying expert with assistant: {str(e)}")

