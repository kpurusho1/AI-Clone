import os
import httpx
import tempfile
import urllib.parse
from typing import List, Optional
from openai import OpenAI
from io import BytesIO
import requests
from llama_cloud_services import LlamaParse
from config import OPENAI_API_KEY, LLAMAPARSE_API_KEY
from database import supabase

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
        
        # Download the document if it's a web URL
        if document_url.startswith(('http://', 'https://')):
            # Extract file extension from URL
            url_path = urllib.parse.urlparse(document_url).path
            file_extension = os.path.splitext(url_path)[1]
            print(f"Detected file extension from URL: {file_extension}")
            
            if not file_extension:
                # If no extension found, default to .pdf
                file_extension = '.pdf'
                print(f"No extension detected, defaulting to: {file_extension}")
            
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
                # Save to a temporary file with the correct extension
                #temp_file_handle, temp_path = tempfile.mkstemp(suffix=file_extension)
                #with os.fdopen(temp_file_handle, 'wb') as temp_file:
                    #temp_file.write(response.content)
                #print(f"Saved to temporary file: {temp_path}")
        else:
            # It's a local file path
            #temp_path = document_url
            # Handle local file path
            with open(document_url, "rb") as file_content:
                result = client.files.create(
                    file=file_content,
                    purpose="assistants"
                )
        
        # Parse the document using LlamaParse
        # Use the async version of the parser
        #print(f"Parsing document with LlamaParse: {temp_path}")
        #result = await llama_parser.aparse(file_content)
        #from urllib.request import Request, urlopen
        #from io import BytesIO
        #path = "https://my-bucket.amazonaws.com/path-to-file.pdf"
        #remoteFile = urlopen(Request(path)).read()
        #memoryFile = BytesIO(remoteFile)
        #documents = parser.load_data(memoryFile, extra_info={"file_name": "sample-file.pdf"}) # file name is required to be passed
        #print(documents)
        #print(f"Parsing successful, result type: {type(result)}")
        #print(f"Result attributes: {dir(result)}")
        
        # Extract the content from the result
        # The JobResult object might have different attributes depending on the version
        # Common attributes are: text, content, markdown, or document
        """
        if hasattr(result, 'text'):
            content = result.text
            print(f"Found 'text' attribute, length: {len(content)}")
        elif hasattr(result, 'content'):
            content = result.content
            print(f"Found 'content' attribute, length: {len(content)}")
        elif hasattr(result, 'document'):
            content = result.document
            print(f"Found 'document' attribute, length: {len(content)}")
        elif hasattr(result, 'markdown'):
            content = result.markdown
            print(f"Found 'markdown' attribute, length: {len(content)}")
        else:
            # If none of the expected attributes are found, convert the entire result to string
            content = str(result)
            print(f"No standard content attribute found, using string representation, length: {len(content)}")
        
        # Clean up temporary file if we created one
        if temp_path and document_url.startswith(('http://', 'https://')):
            print(f"Cleaning up temporary file: {temp_path}")
            os.unlink(temp_path)
        """
        # Store document information in the documents table if domain is provided
        if domain_name:
            try:
                # Get count of existing documents for this domain to generate name
                # Use provided document name or generate one if not provided
                if document_name:
                    doc_name = document_name
                else:
                    doc_count_result = supabase.table("documents").select("id").eq("domain", domain_name).execute()
                    doc_count = len(doc_count_result.data) + 1
                    doc_name = f"Document {doc_count}"
                if expert_name:
                    created_by = expert_name
                else:
                    created_by = "default"
                if client_name:
                    client_name = client_name
                else:
                    client_name = None
                # Insert document record
                doc_insert = supabase.table("documents").insert({
                    "name": doc_name,
                    "document_link": document_url,
                    "domain": domain_name,
                    "created_by": created_by,
                    "client_name": client_name,
                    "openai_file_id": result.id  # Store OpenAI file ID
                }).execute()
                
                print(f"Stored document in database: {doc_name}, OpenAI file ID: {result.id}")
            except Exception as e:
                print(f"Error storing document in database: {str(e)}")
                # Continue anyway as we still want to return the file ID
        
        # Return the extracted result id
        return result.id
    except Exception as e:
        print(f"Error in create_file_for_vector_store: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Clean up temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                print(f"Cleaned up temporary file after error: {temp_path}")
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {str(cleanup_error)}")
        
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
    try:
        print(f"Processing batch of {len(document_urls)} documents")
        file_ids = []
        
        # Process each document URL and collect file IDs
        for doc_name, document_url in document_urls.items():
            file_id = await create_file_for_vector_store(client, document_url, document_name=doc_name, domain_name=domain_name, expert_name=expert_name, client_name=client_name)
            file_ids.append(file_id)
            print(f"Created file with ID: {file_id} for document: {doc_name}")
        
        return file_ids
    except Exception as e:
        print(f"Error in create_files_for_vector_store: {str(e)}")
        raise Exception(f"Error creating files: {str(e)}")

async def add_to_vector_store(client, vector_store_id: str, document_id: str):
    """
    Add a single document to a vector store
    """
    try:
        result = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=document_id
        )
        return result
    except Exception as e:
        print(f"Error adding document to vector store: {str(e)}")
        raise Exception(f"Error adding document to vector store: {str(e)}")

async def add_document_to_vector_store(client, vector_store_id: str, document_url: str, document_name: str = None, domain_name: str = None):
    """
    Process a single document and add it to a vector store
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        document_url: URL or local path to the document
        document_name: Optional name for the document
        domain_name: Optional domain name to associate the document with
        
    Returns:
        Dictionary with file_id, vector_store_id, and status
    """
    try:
        # First create a file from the document
        file_id = await create_file_for_vector_store(client, document_url, document_name=document_name, domain_name=domain_name, expert_name=None, client_name=None)
        print(f"Created file with ID: {file_id} for document: {document_name or document_url}")
        
        # Then add the file to the vector store
        result = await add_to_vector_store(client, vector_store_id, file_id)
        print(f"Added file to vector store: {result}")
        
        return {
            "file_id": file_id,
            "vector_store_id": vector_store_id,
            "status": "success"
        }
    except Exception as e:
        print(f"Error adding document to vector store: {str(e)}")
        raise Exception(f"Error adding document to vector store: {str(e)}")

async def add_documents_to_domain_vector_store(client, vector_store_id: str, document_urls: dict, domain_name: str = None):
    """
    Process multiple documents and add them to a vector store using batch API
    
    Args:
        client: OpenAI client
        vector_store_id: ID of the vector store
        document_urls: Dictionary of document names to URLs or local paths
        domain_name: Optional domain name to associate the documents with
        
    Returns:
        Dictionary with file_ids, batch_id, vector_store_id, and status
    """
    try:
        # First create files from the documents
        file_ids = await create_files_for_vector_store(client, document_urls, domain_name, None, None)
        print(f"Created {len(file_ids)} files with IDs: {file_ids}")
        
        # Then add the files to the vector store as a batch
        batch_result = await add_batch_to_vector_store(client, vector_store_id, file_ids)
        print(f"Added files to vector store as batch: {batch_result.id}")
        
        return {
            "file_ids": file_ids,
            "batch_id": batch_result.id,
            "vector_store_id": vector_store_id,
            "status": batch_result.status
        }
    except Exception as e:
        print(f"Error adding documents to vector store: {str(e)}")
        raise Exception(f"Error adding documents to vector store: {str(e)}")

async def add_documents_to_expert_vector_store(client, vector_store_id: str, document_urls: dict, domain_name: str, expert_name: str, client_name: str = None):
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
    try:
        # First create files from the documents
        file_ids = await create_files_for_vector_store(client, document_urls, domain_name, expert_name, client_name)
        print(f"Created {len(file_ids)} files with IDs: {file_ids}")
        
        # Then add the files to the vector store as a batch
        batch_result = await add_batch_to_vector_store(client, vector_store_id, file_ids)
        print(f"Added files to vector store as batch: {batch_result.id}")
        
        return {
            "file_ids": file_ids,
            "batch_id": batch_result.id,
            "vector_store_id": vector_store_id,
            "status": batch_result.status
        }
    except Exception as e:
        print(f"Error adding documents to vector store: {str(e)}")
        raise Exception(f"Error adding documents to vector store: {str(e)}")

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
        return result
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
        
        # Combine kept file IDs and new file IDs
        all_file_ids = kept_file_ids + new_file_ids
        print(f"Combined file IDs: {all_file_ids}")
        batch_result = await add_batch_to_vector_store(client, vector_store_id, all_file_ids)
        batch_id = batch_result.id
        # Add the batch to the vector store if there are new files
        if new_file_ids:
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
