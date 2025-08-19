from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
import os
from database import supabase
from models import (
    ExpertCreate, ExpertResponse, ExpertUpdate,
    QueryRequest, 
    DeleteVectorRequest,
    DomainCreate,
    DomainFilesConfigRequest, PersonaGenerationRequest,
    ExpertVectorCreate,
    AddFilesToExpertVectorCreate, 
    UpdateVectorStoreRequest,
    UpdateExpertPersonaRequest,InitializeExpertMemoryRequest,
    UpdateExpertRequest
)

from utils import (
    create_vector_store, 
    add_documents_to_vector_store,
    delete_vector_index,
    edit_vector_store, client,
    generate_persona_from_qa,
    query_expert_with_assistant
)

router = APIRouter()

# 1. Initialize expert memory
@router.post("/memory/expert/initialize", response_model=dict)
async def initialize_expert_memory(request: InitializeExpertMemoryRequest):
    """
    Initialize an expert's memory by:
    1. Creating domain if it doesn't exist
    2. Adding files to domain vector from config file
    3. Generating persona from QA data
    4. Creating expert with generated persona
    5. Adding files to expert vector
    """
    try:
        print(f"Initializing memory for expert: {request.expert_name} in domain: {request.domain_name}")
        results = {}
        
        # Step 1: Create domain or get existing domain
        print("Step 1: Creating or getting domain")
        domain_request = DomainCreate(domain_name=request.domain_name)
        domain_result = await create_domain(domain_request)
        results["domain"] = domain_result
        print(f"Domain result: {domain_result}")
        
        # Step 2: Add files to domain vector from config file
        print("Step 2: Adding files to domain vector from config file")
        
        # Look for config file in both current directory and project root directory
        config_file_name = f"{request.domain_name}_config.json"
        config_file_path = config_file_name
        root_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_file_name)
        
        print(f"Looking for config file at: {config_file_path} or {root_config_path}")
        
        # Check if config file exists in either location
        if os.path.exists(config_file_path):
            print(f"Found config file in current directory: {config_file_path}")
        elif os.path.exists(root_config_path):
            config_file_path = root_config_path
            print(f"Found config file in project root: {config_file_path}")
        
        if os.path.exists(config_file_path):
            config_request = DomainFilesConfigRequest(domain_name=request.domain_name, config_file_path=config_file_path)
            domain_files_result = await add_files_to_domain_vector_from_config(config_request)
            results["domain_files"] = domain_files_result
            print(f"Domain files result: {domain_files_result}")
        else:
            print(f"Warning: Config file {config_file_path} not found, skipping domain files addition")
            results["domain_files"] = {"status": "skipped", "message": f"Config file {config_file_path} not found"}
        
        # Step 3: Generate persona from QA data
        print("Step 3: Generating persona from QA data")
        persona_request = PersonaGenerationRequest(qa_pairs=request.qa_pairs)
        persona_result = await generate_persona_from_qa_data(persona_request)
        results["persona"] = persona_result
        print(f"Persona result: {persona_result}")
        
        # Step 4: Create expert with generated persona
        print("Step 4: Creating expert with generated persona")
        expert_request = ExpertCreate(
            name=request.expert_name,
            domain=request.domain_name,
            context=persona_result["persona"],  # Use the generated persona as context
            use_default_domain_knowledge=False
        )
        expert_result = await create_expert(expert_request)
        results["expert"] = expert_result
        print(f"Expert result: {expert_result}")
        
        # Step 5: Add files to expert vector
        print("Step 5: Adding files to expert vector")
        # Convert document_urls dict to the format expected by AddFilesToExpertVectorCreate
        expert_files_request = AddFilesToExpertVectorCreate(
            expert_name=request.expert_name,
            document_urls=request.document_urls,
            pdf_documents=request.pdf_documents,
            client_name=None
        )
        expert_files_result = await add_files_to_expert_vector(expert_files_request)
        results["expert_files"] = expert_files_result
        print(f"Expert files result: {expert_files_result}")
        
        return {
            "expert_name": request.expert_name,
            "domain_name": request.domain_name,
            "status": "success",
            "message": f"Successfully initialized memory for expert {request.expert_name} in domain {request.domain_name}",
            "results": results
        }
    except Exception as e:
        print(f"Error initializing expert memory: {str(e)}")
        # Return partial success with details about what succeeded and what failed
        return {
            "expert_name": request.expert_name,
            "domain_name": request.domain_name,
            "status": "partial_success",
            "message": f"Partially initialized memory for expert {request.expert_name}. Some steps may have failed: {str(e)}",
            "results": results
        }

# 2. Query expert using OpenAI Assistant API
@router.post("/query_expert_with_assistant")
async def query_expert_with_assistant_endpoint(request: QueryRequest):
    """
    Query an expert using the OpenAI Assistant API
    """
    try:
        thread_id = request.thread_id if hasattr(request, 'thread_id') else None
        
        result = await query_expert_with_assistant(
            expert_name=request.expert_name,
            query=request.query,
            memory_type=request.memory_type,
            thread_id=thread_id
        )
        
        return result
    except Exception as e:
        print(f"[ERROR] query_expert_with_assistant_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. Update expert memory and context
@router.post("/expert/update", response_model=dict)
async def update_expert(request: UpdateExpertRequest):
    """
    Update an expert's memory by:
    1. Adding files to domain vector from config file
    2. Generating persona from QA data
    3. Updating expert with generated persona
    4. Adding files to expert vector
    """
    try:        
        results = {}
        
        # Step 1: Create domain or get existing domain
        print("Step 1: Creating or getting domain")
        domain_request = DomainCreate(domain_name=request.domain_name)
        domain_result = await create_domain(domain_request)
        results["domain"] = domain_result
        print(f"Domain result: {domain_result}")
        
        # Step 2: Update expert with new context
        if request.qa_pairs:
            print("Step 2: Updating expert with generated persona")
            expert_request = UpdateExpertPersonaRequest(
                expert_name=request.expert_name,
                qa_pairs=request.qa_pairs
            )
            await update_expert_persona(expert_request)
        

        # Step 3: Add files to domain vector from config file
        print("Step 2: Adding files to domain vector from config file")
        # Look for config file in both current directory and project root directory
        config_file_name = f"{request.domain_name}_config.json"
        config_file_path = config_file_name
        root_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_file_name)
        print(f"Looking for config file at: {config_file_path} or {root_config_path}")
        # Check if config file exists in either location
        if os.path.exists(config_file_path):
            print(f"Found config file in current directory: {config_file_path}")
        elif os.path.exists(root_config_path):
            config_file_path = root_config_path
            print(f"Found config file in project root: {config_file_path}")
        document_urls = {}
        if os.path.exists(config_file_path):
            document_urls = await parse_config_file(config_file_path)
            if not document_urls:
                print(f"Warning: Config file {config_file_path} is empty, skipping domain files addition")
            else:
                domain_files_request = UpdateVectorStoreRequest(
                    domain_name=request.domain_name,
                    document_urls=document_urls
                )
                await update_vector_store(domain_files_request)
                print(f"Domain files added successfully")
        else:
            print(f"Warning: Config file {config_file_path} not found, skipping domain files addition")
        
        # Step 4: Add files to expert vector
        print("Step 4: Adding files to expert vector")
        if request.document_urls or request.pdf_documents:
            expert_files_request = UpdateVectorStoreRequest(
                expert_name=request.expert_name,
                domain_name=request.domain_name,
                document_urls=request.document_urls,
                pdf_documents=request.pdf_documents
            )
            await update_vector_store(expert_files_request)
            print(f"Expert files added successfully")
        
        return {
            "expert_name": request.expert_name,
            "domain_name": request.domain_name,
            "status": "success",
            "message": f"Successfully initialized memory for expert {request.expert_name} in domain {request.domain_name}",
            "results": results
        }
    except Exception as e:
        print(f"Error initializing expert memory: {str(e)}")
        # Return partial success with details about what succeeded and what failed
        return {
            "expert_name": request.expert_name,
            "domain_name": request.domain_name,
            "status": "partial_success",
            "message": f"Partially initialized memory for expert {request.expert_name}. Some steps may have failed: {str(e)}",
            "results": results
        }


#________Helper functions (potential APIs)________

# Create domain - will create default vector store for domain
async def create_domain(domain_create: DomainCreate):
    """
    Create a new domain with custom domain name or with domain from the enum DomainName
    """
    try:
        print(f"Creating domain with name: {domain_create.domain_name}")
        print(f"Domain name type: {type(domain_create.domain_name)}")
        
        # Extract the domain name value (handle both string and enum)
        if hasattr(domain_create.domain_name, 'value'):
            domain_name = domain_create.domain_name.value
        else:
            domain_name = str(domain_create.domain_name)
        
        print(f"Domain name after extraction: {domain_name}")
        
        # Check if domain already exists
        domain_exists = supabase.table("domains").select("*").eq("domain_name", domain_name).execute()
        print(f"Domain exists check result: {domain_exists.data}")
        
        if domain_exists.data:
            print(f"Domain {domain_name} already exists, returning existing domain")
            existing_domain = domain_exists.data[0]
            # Get vector ID for the existing domain
            vector_id_result = await get_vector_id(domain_name)
            vector_id = vector_id_result.get("vector_id") if vector_id_result else None
            
            return {
                "domain_name": existing_domain.get("domain_name"),
                "vector_id": vector_id,
                "message": f"Domain {domain_name} already exists"
            }
        
        # Create vector store with name 'Default_<domain_name>'
        vector_name = f"Default_{domain_name}"
        print(f"Creating vector store with name: {vector_name}")
        
        try:
            vector_store = await create_vector_store(client, vector_name)
            print(f"Vector store created: {vector_store}")
            vector_id = vector_store.id if hasattr(vector_store, 'id') else None
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            vector_id = None
        
        # Create domain entry in database
        domain_data = {
            "domain_name": domain_name,
            "expert_names": []
        }
        
        print(f"Domain data to insert: {domain_data}")
        
        # Insert domain into database
        result = supabase.table("domains").insert(domain_data).execute()
        print(f"Insert result: {result}")
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create domain")
            
        # Also add an entry to the vector_stores table if we have a vector_id
        if vector_id:
            try:
                vector_store_data = {
                    "vector_id": vector_id,
                    "domain_name": domain_name,
                    "expert_name": None,  # Default domain vector has no expert
                    "client_name": None,  # Default domain vector has no client
                    "owner": "domain",  # Mark as owned by domain
                    "file_ids": [],  # Start with empty file IDs
                    "batch_ids": []   # Start with empty batch IDs
                }
                
                print(f"Vector store data to insert: {vector_store_data}")
                
                # Insert into vector_stores table
                vector_result = supabase.table("vector_stores").insert(vector_store_data).execute()
                print(f"Vector store insert result: {vector_result}")
            except Exception as e:
                print(f"Warning: Failed to create vector_stores entry: {str(e)}")
                # Continue anyway, the domain was created successfully
        
        return {
            "domain_name": domain_name,
            "vector_id": vector_id,
            "message": f"Domain {domain_name} created successfully"
        }
    except Exception as e:
        print(f"Error creating domain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Create expert
async def create_expert(expert: ExpertCreate):
    """
    Create a new expert with domain and context
    """
    try:
        print(f"Creating expert with name: {expert.name}, domain: {expert.domain}")
        print(f"Domain type: {type(expert.domain)}")
        print(f"Domain representation: {repr(expert.domain)}")
        
        # Extract the actual value from the enum
        domain_value = expert.domain.value if hasattr(expert.domain, 'value') else str(expert.domain)
        print(f"Domain value after extraction: {domain_value}")
        
        # Check if domain exists
        domain_exists = supabase.table("domains").select("domain_name").eq("domain_name", domain_value).execute()
        print(f"Domain exists check result: {domain_exists.data}")
        
        if not domain_exists.data:
            raise HTTPException(status_code=404, detail=f"Domain {domain_value} not found")
        
        # Create expert data
        expert_data = {
            "name": expert.name,
            "domain": domain_value,
            "context": expert.context
        }
        
        # Insert expert into database
        result = supabase.table("experts").insert(expert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create expert")
        
        # Update domain's expert_names array
        try:
            # First get the current expert_names array
            domain_info = supabase.table("domains").select("expert_names").eq("domain_name", domain_value).execute()
            
            # Extract the current expert_names or initialize an empty list
            current_experts = domain_info.data[0].get("expert_names", []) if domain_info.data else []
            if current_experts is None:
                current_experts = []
            
            # Append the new expert name
            if expert.name not in current_experts:
                current_experts.append(expert.name)
            
            # Update the domain with the new list
            supabase.table("domains").update({"expert_names": current_experts}).eq("domain_name", domain_value).execute()
        except Exception as domain_update_error:
            print(f"Error updating domain expert_names: {str(domain_update_error)}")
            # Continue anyway, the expert was created successfully
        
        # Create expert domain vector
        try:
            vector_create = ExpertVectorCreate(
                expert_name=expert.name,
                domain_name=domain_value,
                use_default_domain_vector=expert.use_default_domain_knowledge
            )
            vector_result = await create_expert_domain_vector(vector_create)
            print(f"Expert domain vector created: {vector_result}")
        except Exception as vector_error:
            print(f"Error creating expert domain vector: {str(vector_error)}")
            # Continue anyway, the expert was created successfully
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add files to domain vector from config file
async def add_files_to_domain_vector_from_config(config_request: DomainFilesConfigRequest):
    """
    Add files to a domain's default vector store from a configuration file
    
    The config file should be in JSON format with the following structure:
    {
        "files": [
            {"name": "Document 1", "url": "https://example.com/doc1.pdf"},
            {"name": "Document 2", "url": "https://example.com/doc2.pdf"}
        ]
    }
    """
    try:
        print(f"Adding files to domain vector for domain: {config_request.domain_name} from config file: {config_request.config_file_path}")
        
        # Initialize variables
        document_urls = {}
        file_exists = os.path.exists(config_request.config_file_path)
        file_empty = False
        
        if file_exists:
            document_urls = await parse_config_file(config_request.config_file_path)
            # if document_urls is empty, set file_empty to True
            if not document_urls:
                file_empty = True
        else:
            print(f"Warning: Config file {config_request.config_file_path} does not exist")
        
        vector_store = await get_vector_id(config_request.domain_name)
        default_vector_id = vector_store.get("vector_id")
        id = vector_store.get("id")
        
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {config_request.domain_name} does not have a default vector ID")
        
        print(f"Default vector ID from domain record: {default_vector_id}")
        
        # Initialize result variables
        file_ids = []
        batch_id = None
        result = {"file_ids": [], "batch_id": None, "status": "skipped"}
        
        # Only add documents to vector store if we have valid document URLs
        if document_urls:
            result = await add_documents_to_vector_store(client, default_vector_id, document_urls, config_request.domain_name, None, None, None)
            print(f"Added documents to vector store: {result}")
            file_ids = result.get("file_ids", [])
            batch_id = result.get("batch_id")
        else:
            print("Skipping document addition to vector store - no valid documents found")
        
        try:
            # Check if entry exists for this vector_id
            existing_entry = supabase.table("vector_stores").select("*").eq("id", id).execute()
            print(f"Existing vector store entry check: {existing_entry.data}")
            
            if existing_entry.data:
                # Replace existing entry with new data
                update_data = {
                    "file_ids": file_ids,  # Replace with new file_ids
                    "batch_ids": [batch_id] if batch_id else [],  # Replace with new batch_id
                    "latest_batch_id": batch_id
                }
                
                update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
                print(f"Updated existing vector_stores entry with replacement: {update_result}")
            else:
                # Create new entry
                insert_data = {
                    "vector_id": default_vector_id,
                    "domain_name": config_request.domain_name,
                    "expert_name": None,  # Domain vector has no expert
                    "client_name": None,   # Domain vector has no client
                    "file_ids": file_ids,
                    "batch_ids": [batch_id] if batch_id else [],
                    "latest_batch_id": batch_id,
                    "owner": "domain"  # Domain vector owner is 'domain'
                }
                insert_result = supabase.table("vector_stores").insert(insert_data).execute()
                print(f"Created new vector_stores entry: {insert_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        # Prepare appropriate message based on whether documents were added
        if document_urls:
            message = f"Added {len(document_urls)} documents from config file to default vector store for domain {config_request.domain_name}"
        else:
            if not file_exists:
                message = f"Config file {config_request.config_file_path} does not exist. Created/updated vector store entry without adding documents."
            elif file_empty:
                message = f"Config file {config_request.config_file_path} is empty. Created/updated vector store entry without adding documents."
            else:
                message = f"No valid document entries found in config file. Created/updated vector store entry without adding documents."
        
        return {
            "domain_name": config_request.domain_name,
            "vector_id": default_vector_id,
            "vector_name": f"Default_{config_request.domain_name}",  # Following naming convention
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "config_file": config_request.config_file_path,
            "document_count": len(document_urls),
            "message": message
        }
    except Exception as e:
        print(f"Error adding files to domain vector from config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Parse file to get it into the formal of document name and url
async def parse_config_file(config_file_path):
    # Read and parse the config file
    document_urls = {}
    try:
        with open(config_file_path, 'r') as file:
            file_content = file.read().strip()
            if not file_content:  # Check if file is empty
                print(f"Warning: Config file {config_file_path} is empty")
            else:
                config_data = json.loads(file_content)
                
                if not isinstance(config_data, dict) or 'files' not in config_data or not isinstance(config_data['files'], list):
                    raise HTTPException(status_code=400, detail="Invalid config file format. Expected JSON with 'files' array")
                    
                # Convert to document_urls format expected by add_documents_to_vector_store
                for file_entry in config_data['files']:
                    if 'name' in file_entry and 'url' in file_entry:
                        document_urls[file_entry['name']] = file_entry['url']
                    else:
                        print(f"Warning: Skipping invalid file entry: {file_entry}")
                        
                if not document_urls:
                    print(f"Warning: No valid file entries found in config file")
                    
                print(f"Parsed {len(document_urls)} document URLs from config file")         
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in config file: {str(e)}")
    return document_urls

# Create vector store for expert and domain - will use default for preferred if bool is true
async def create_expert_domain_vector(vector_create: ExpertVectorCreate):
    """
    Create or update vector IDs for an expert based on domain
    """
    try:
        print(f"Creating/updating vector IDs for expert: {vector_create.expert_name}")
        print(f"Use default domain vector: {vector_create.use_default_domain_vector}")
        
        domain_name = vector_create.domain_name
        
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {vector_create.expert_name} does not have an associated domain")
        
        print(f"Domain name from expert record: {domain_name}")
        
        # Get default vector ID for the domain using the existing function
        vector_id_result = await get_vector_id(domain_name)
        default_vector_id = vector_id_result.get("vector_id") if vector_id_result else None
            
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {domain_name} does not have a default vector ID")
        
        # Update expert's vector IDs based on the use_default_domain_vector flag
        if vector_create.use_default_domain_vector:
            # Use domain's default vector ID for both default and preferred
            expert_vector_id = default_vector_id
        else:
            vector_name = f"{vector_create.expert_name}_{domain_name}"
            print(f"Creating vector store with name: {vector_name}")
            vector_store = await create_vector_store(client, vector_name)
            print(f"Vector store created: {vector_store}")
            expert_vector_id = vector_store.id if hasattr(vector_store, 'id') else None
            
        # Update expert's preferred vector ID
        #if expert_vector_id:
           
        if not expert_vector_id:
            raise HTTPException(status_code=400, detail="Error creating vector store")
            
        # Also add an entry to the vector_stores table
        vector_store_data = {
            "vector_id": expert_vector_id,
            "domain_name": domain_name,
            "expert_name": vector_create.expert_name,
            "client_name": None,  # Expert vector has no client
            "owner": "expert",  # Mark as owned by expert
            "file_ids": [],  # Start with empty file IDs
            "batch_ids": []   # Start with empty batch IDs
        }
                
        print(f"Vector store data to insert: {vector_store_data}")
                
        # Insert into vector_stores table
        vector_result = supabase.table("vector_stores").insert(vector_store_data).execute()
        print(f"Vector store insert result: {vector_result}")
        
        return {
            "expert_name": vector_create.expert_name,
            "domain_name": domain_name,
            "vector_id": expert_vector_id,
            "message": f"Expert {vector_create.expert_name} updated with domain's default vector ID"
        }
    except Exception as e:
        print(f"Error creating expert domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add files to expert vector
async def add_files_to_expert_vector(files_create: AddFilesToExpertVectorCreate):
    """
    Add files to an expert vector store from URLs and/or PDF document bytes
    """
    try:
        print(f"Adding files to expert vector for expert: {files_create.expert_name}")
        print(f"Document URLs: {len(files_create.document_urls) if files_create.document_urls else 0}")
        print(f"PDF Documents: {len(files_create.pdf_documents) if files_create.pdf_documents else 0}")
        
        # Check if both document_urls and pdf_documents are empty
        if not files_create.document_urls and not files_create.pdf_documents:
            print("No documents provided, returning early")
            return {
                "expert_name": files_create.expert_name,
                "client_name": files_create.client_name,
                "vector_id": None,
                "file_ids": [],
                "batch_id": None,
                "status": "skipped",
                "message": "No documents provided to add to vector store"
            }
        
        vector_id = None
        expert_domain_result = await get_expert_domain(files_create.expert_name)
        domain_name = expert_domain_result.get("domain_name") if expert_domain_result else None
        create_entry_vector_stores_table = False
        client_name = None
        # Get the expert's preferred vector store and get its ID
        expert_domain_vector = await get_vector_id(domain_name)
        expert_domain_vector_id = expert_domain_vector.get("vector_id")
        expert_vector_result = await get_vector_id(domain_name, files_create.expert_name)
        vector_id = expert_vector_result.get("vector_id")
        id = expert_vector_result.get("id")
        print(f"Using expert's vector ID: {vector_id}")
        # if adding files to expert vector, then it cannot be the domain vector
        if expert_domain_vector_id == vector_id:
            # Create a proper ExpertVectorCreate object to pass to the function
            vector_create = ExpertVectorCreate(
                expert_name=files_create.expert_name,
                domain_name=domain_name,
                use_default_domain_vector=False
            )
            vector_result = await create_expert_domain_vector(vector_create)
            vector_id = vector_result.get("vector_id")
            create_entry_vector_stores_table = True
        # Add the documents to the vector store
        if not vector_id:
            raise HTTPException(status_code=500, detail="Failed to get or create vector store")
  
        # Add the documents to the vector store (both URLs and PDF documents)
        result = await add_documents_to_vector_store(client, vector_id, files_create.document_urls, domain_name, files_create.expert_name, client_name, files_create.pdf_documents)
        print(f"Added documents to vector store: {result}")
        
        # Update vector_stores table with the new file information
        # Handle result properly whether it's a dictionary or an APIResponse object
        if hasattr(result, 'get'):
            # It's a dictionary
            file_ids = result.get("file_ids", [])
            batch_id = result.get("batch_id")
        else:
            # It's an APIResponse object or something else
            print(f"Result type: {type(result)}")
            # Try to access attributes directly
            try:
                file_ids = result.file_ids if hasattr(result, 'file_ids') else []
                batch_id = result.batch_id if hasattr(result, 'batch_id') else None
            except Exception as e:
                print(f"Error accessing result attributes: {str(e)}")
                # Fallback to empty values
                file_ids = []
                batch_id = None
        
        try:
            # Check if entry exists for this vector_id
            if not create_entry_vector_stores_table:
                # Replace existing entry with new file_ids and batch_id
                update_data = {
                    "file_ids": file_ids,  # Replace with new file_ids instead of appending
                    "batch_ids": [batch_id] if batch_id else [],  # Replace with new batch_id
                    "latest_batch_id": batch_id  # Always update latest_batch_id
                }
                
                update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
                print(f"Updated existing vector_stores entry with replacement: {update_result}")
            else:
                # Create new entry
                # Determine owner based on client_name and expert_name
                owner = "client" if client_name else "expert"
                
                insert_data = {
                    "vector_id": vector_id,
                    "domain_name": domain_name,
                    "expert_name": files_create.expert_name,
                    "client_name": client_name,
                    "file_ids": file_ids,
                    "batch_ids": [batch_id] if batch_id else [],
                    "latest_batch_id": batch_id,
                    "owner": owner
                }
                insert_result = supabase.table("vector_stores").insert(insert_data).execute()
                print(f"Created new vector_stores entry: {insert_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        # Calculate total documents processed
        url_count = len(files_create.document_urls) if files_create.document_urls else 0
        pdf_count = len(files_create.pdf_documents) if files_create.pdf_documents else 0
        total_docs = url_count + pdf_count
        
        return {
            "expert_name": files_create.expert_name,
            "client_name": files_create.client_name,
            "vector_id": vector_id,
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "url_count": url_count,
            "pdf_count": pdf_count,
            "message": f"Added {total_docs} documents ({url_count} URLs, {pdf_count} PDFs) to vector store for expert {files_create.expert_name}"
        }
    except Exception as e:
        print(f"Error adding files to expert vector: {str(e)}")
        # Return partial success instead of raising an exception
        return {
            "expert_name": files_create.expert_name,
            "client_name": files_create.client_name,
            "vector_id": None,
            "file_ids": [],
            "batch_id": None,
            "status": "error",
            "url_count": 0,
            "pdf_count": 0,
            "message": f"Error adding files to expert vector: {str(e)}"
        }

# Generate persona from QA data
async def generate_persona_from_qa_data(persona_request: PersonaGenerationRequest):
    """
    Generate a persona summary from QA data provided directly in the request
    
    The request body should have the following structure:
    {
        "qa_pairs": [
            {"question": "What is your area of expertise?", "answer": "I specialize in pediatric cardiology..."},
            {"question": "How do you approach difficult cases?", "answer": "I believe in a collaborative approach..."}
        ]
    }
    """
    try:
        print(f"Generating persona from {len(persona_request.qa_pairs)} QA pairs")
        
        # Validate QA pairs
        if not persona_request.qa_pairs:
            raise HTTPException(status_code=400, detail="No QA pairs provided in request")
        
        valid_qa_pairs = []
        for qa in persona_request.qa_pairs:
            if isinstance(qa, dict) and 'question' in qa and 'answer' in qa:
                valid_qa_pairs.append(qa)
            else:
                print(f"Warning: Skipping invalid QA pair: {qa}")
        
        if not valid_qa_pairs:
            raise HTTPException(status_code=400, detail="No valid QA pairs found in request")
            
        print(f"Validated {len(valid_qa_pairs)} QA pairs from request")
        
        # Generate persona using OpenAI
        persona_summary = await generate_persona_from_qa(client, valid_qa_pairs)
        
        return {
            "qa_pairs_count": len(valid_qa_pairs),
            "persona": persona_summary,
            "message": "Successfully generated persona from QA pairs"
        }
    except Exception as e:
        print(f"Error generating persona from config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update expert persona
async def update_expert_persona(request: UpdateExpertPersonaRequest):
    """
    Generate a persona from QA data and update the expert's context with it
    
    This endpoint combines the persona generation and context update steps:
    1. Generate a persona from the provided QA pairs
    2. Update the expert's context with the generated persona
    """
    try:
        print(f"Updating persona for expert: {request.expert_name} with {len(request.qa_pairs)} QA pairs")
        
        # Step 1: Generate persona from QA data
        persona_request = PersonaGenerationRequest(qa_pairs=request.qa_pairs)
        persona_result = await generate_persona_from_qa_data(persona_request)
        persona_summary = persona_result["persona"]
        print(f"Generated persona: {persona_summary}")
        
        # Step 2: Update expert's context with the generated persona
        expert_update = ExpertUpdate(name=request.expert_name, context=persona_summary)
        update_result = await update_context(expert_update)
        
        return {
            "expert_name": request.expert_name,
            "qa_pairs_count": len(request.qa_pairs),
            "persona": persona_summary,
            "update_result": update_result,
            "status": "success",
            "message": f"Successfully updated persona for expert {request.expert_name}"
        }
    except Exception as e:
        print(f"Error updating expert persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update context
async def update_context(expert_update: ExpertUpdate):
    """
    Update an expert's context
    """
    try:
        # Find expert by name
        expert = supabase.table("experts").select("*").eq("name", expert_update.name).execute()
        
        if not expert.data:
            raise HTTPException(status_code=404, detail=f"Expert {expert_update.name} not found")
        
        # Update expert's context
        result = supabase.table("experts").update({"context": expert_update.context}).eq("name", expert_update.name).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update expert context")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update vector store
async def update_vector_store(update_request: UpdateVectorStoreRequest):
    """
    Update an existing vector store by adding new documents
    
    Args:
        update_request: Request containing vector_id, document_urls, and pdf_documents
        
    Returns:
        Updated vector store information
    """
    try:
        url_count = len(update_request.document_urls) if update_request.document_urls else 0
        pdf_count = len(update_request.pdf_documents) if update_request.pdf_documents else 0
        total_docs = url_count + pdf_count
        print(f"Updating vector store {update_request.expert_name} with {total_docs} new documents ({url_count} URLs, {pdf_count} PDFs)")
        expert_name = None
        domain_name = None
        if update_request.expert_name:
            expert_name = update_request.expert_name
            expert_domain_result = await get_expert_domain(expert_name)
        if update_request.domain_name:
            domain_name = update_request.domain_name
        else:
            domain_name = expert_domain_result.get("domain_name") if expert_domain_result else None
        vector_st = await get_vector_id(domain_name, expert_name)
        vector_id = vector_st.get("vector_id")
        id = vector_st.get("id")
        # Query by vector_id directly from the vector_stores table
        vector_store_result = supabase.table("vector_stores").select("*").eq("id", id).execute()
        print(f"Vector store query result: {vector_store_result.data}")
        
        if not vector_store_result.data:
            raise HTTPException(status_code=404, detail=f"Vector store with ID {vector_id} not found")
        
        vector_store = vector_store_result.data[0]
        client_name = vector_store["client_name"]
        file_ids = vector_store["file_ids"]
        
        result = await edit_vector_store(
            client, 
            vector_id, 
            file_ids, 
            update_request.document_urls, 
            domain_name, 
            expert_name, 
            client_name,
            update_request.pdf_documents
        )
        
        # Update vector_stores table with the new file information
        new_file_ids = result.get("file_ids", [])
        all_file_ids = result.get("all_file_ids", [])
        batch_id = result.get("batch_id")
        
        try:
            # Update the vector_stores entry
            # Get existing batch_ids from the vector store
            existing_batch_ids = vector_store.get("batch_ids", [])
            
            # If batch_id is not None, add it to the existing batch_ids
            if batch_id:
                if existing_batch_ids:
                    # If existing_batch_ids is already an array, append the new batch_id
                    if not batch_id in existing_batch_ids:
                        batch_ids = existing_batch_ids + [batch_id]
                    else:
                        batch_ids = existing_batch_ids
                else:
                    # If there are no existing batch_ids, create a new array with just this batch_id
                    batch_ids = [batch_id]
            else:
                # If no new batch was created, keep the existing batch_ids
                batch_ids = existing_batch_ids
                
            update_data = {
                "file_ids": all_file_ids,
                "batch_ids": batch_ids,
                "latest_batch_id": batch_id if batch_id else vector_store.get("latest_batch_id"),
                "updated_at": "now()"
            }
            update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
            print(f"Updated vector_stores entry: {update_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        return {
            "status": "success",
            "message": f"Added {len(new_file_ids)} documents to vector store {vector_id}",
            "vector_id": vector_id,
            "domain_name": domain_name,
            "expert_name": expert_name,
            "client_name": client_name,
            "new_file_ids": new_file_ids,
            "all_file_ids": all_file_ids,
            "batch_id": batch_id
        }
    except Exception as e:
        print(f"Error updating vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get details from database if required and Delete vector memory if required
@router.get("/documents")
async def get_documents(
    domain: Optional[str] = None, 
    created_by: Optional[str] = None, 
    client_name: Optional[str] = None
):
    """
    Get documents filtered by domain, expert (created_by), and client_name
    
    Priority rules:
    1. If client_name is provided, return documents matching client_name (and domain/expert if provided)
    2. If created_by is provided but no client_name, return documents with created_by and null client_name
    3. If neither expert nor client is provided, return domain documents with 'default' created_by and null client_name
    """
    try:
        print(f"Getting documents with filters - domain: {domain}, expert: {created_by}, client: {client_name}")
        
        # Start building the query
        query = supabase.table("documents").select("*")
        
        # Handle domain enum value extraction if needed
        if domain and hasattr(domain, 'value'):
            domain_value = domain.value
        else:
            domain_value = domain
        if not domain_value and not created_by and not client_name:
            raise HTTPException(status_code=400, detail="At least one filter must be provided")
            
        # Apply filters based on the specified priority rules
        if domain_value:
            query = query.eq("domain", domain_value)
        else:
            query = query.is_("domain", "null")
        
        if created_by:
            query = query.eq("created_by", created_by)
        else:
            query = query.is_("created_by", "null")
        
        # Add client filter based on whether it's provided
        if client_name:
            if not created_by:
                raise HTTPException(status_code=400, 
                                  detail="Cannot specify client_name without created_by")
            query = query.eq("client_name", client_name)
        else:
            query = query.is_("client_name", "null")
        
        # Execute the query
        result = query.execute()
        print(f"Found {len(result.data)} documents")
        return result.data
    except Exception as e:
        print(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains", response_model=List[dict])
async def get_domains():
    """
    Get all domains
    """
    try:
        print("Getting all domains")
        result = supabase.table("domains").select("*").execute()
        print(f"Found {len(result.data)} domains")
        return result.data
    except Exception as e:
        print(f"Error getting domains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get domain name for an expert
@router.get("/experts/{expert_name}/domain", response_model=dict)
async def get_expert_domain(expert_name: str):
    """
    Get domain name for a given expert name
    """
    try:
        print(f"Getting domain for expert: {expert_name}")
        
        # Query the expert by name
        result = supabase.table("experts").select("name, domain").eq("name", expert_name).execute()
        print(f"Expert query result: {result.data}")
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Expert {expert_name} not found")
        
        expert_data = result.data[0]
        domain_name = expert_data.get("domain")
        
        if not domain_name:
            return {
                "expert_name": expert_name,
                "domain_name": None,
                "message": f"No domain associated with expert {expert_name}"
            }
        
        return {
            "expert_name": expert_name,
            "domain_name": domain_name
        }
    except Exception as e:
        print(f"Error getting expert domain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get vector ID based on domain, expert, and client parameters
@router.get("/vectors/id", response_model=dict)
async def get_vector_id(domain_name: str, expert_name: Optional[str] = None, client_name: Optional[str] = None):
    """
    Get vector ID from the vector_stores table based on provided parameters.
    - domain_name is mandatory
    - expert_name is optional (if not provided, gets domain-level vector store)
    - client_name is optional (if provided with expert_name, gets client-level vector store)
    """
    try:
        print(f"Getting vector ID for domain: {domain_name}, expert: {expert_name}, client: {client_name}")
        
        # Build query to find the vector store
        query = supabase.table("vector_stores").select("*")\
            .eq("domain_name", domain_name)
        
        # Add expert filter based on whether it's provided
        if expert_name:
            query = query.eq("expert_name", expert_name)
        else:
            query = query.is_("expert_name", "null")
        
        # Add client filter based on whether it's provided
        if client_name:
            if not expert_name:
                raise HTTPException(status_code=400, 
                                  detail="Cannot specify client_name without expert_name")
            query = query.eq("client_name", client_name)
        else:
            query = query.is_("client_name", "null")
        
        result = query.execute()
        print(f"Vector store query result: {result.data}")
        
        if not result.data:
            # Construct appropriate message based on provided parameters
            if expert_name and client_name:
                message = f"No vector store found for client {client_name} with expert {expert_name} in domain {domain_name}"
            elif expert_name:
                message = f"No vector store found for expert {expert_name} in domain {domain_name}"
            else:
                message = f"No vector store found for domain {domain_name}"
            
            return {
                "domain_name": domain_name,
                "expert_name": expert_name,
                "client_name": client_name,
                "vector_id": None,
                "id": None,
                "message": message
            }
        
        # Vector store found, return its ID
        vector_store = result.data[0]
        vector_id = vector_store.get("vector_id")
        id = vector_store.get("id")
        
        return {
            "domain_name": domain_name,
            "expert_name": expert_name,
            "client_name": client_name,
            "vector_id": vector_id,
            "id": id,
            "message": "Vector store found"
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error getting vector ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all experts - will return expert objects
@router.get("/experts", response_model=List[ExpertResponse])
async def get_experts():
    """
    Get all experts
    """
    try:
        print("Getting all experts")
        result = supabase.table("experts").select("*").execute()
        print(f"Found {len(result.data)} experts")
        return result.data
    except Exception as e:
        print(f"Error getting experts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get an expert's context
@router.get("/experts/{expert_name}/context", response_model=dict)
async def get_expert_context(expert_name: str):
    """
    Get an expert's context
    
    Args:
        expert_name: Name of the expert
        
    Returns:
        Expert context
    """
    try:
        print(f"Getting context for expert: {expert_name}")
        result = supabase.table("experts").select("context").eq("name", expert_name).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Expert {expert_name} not found")
        
        return {"context": result.data[0]["context"]}
    except Exception as e:
        print(f"Error getting expert context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete vector memory
@router.delete("/vectors/memory", response_model=dict)
async def delete_vector_memory(delete_request: DeleteVectorRequest):
    """
    Delete a vector memory based on domain, expert, and/or client name.
    This endpoint handles deletion of domain, expert, or client-specific vector stores.
    """
    try:
        print(f"[DEBUG] delete_vector_memory: Request received with domain_name={delete_request.domain_name}, "
              f"expert_name={delete_request.expert_name}, client_name={delete_request.client_name}")
        
        vector_id = delete_request.vector_id if delete_request.vector_id else None
        vector_id_to_delete = delete_request.delete_id if delete_request.delete_id else None
        if not vector_id_to_delete:
            # Build the query to find the vector store
            query = supabase.table("vector_stores").select("*")
            
            if delete_request.domain_name:
                query = query.eq("domain_name", delete_request.domain_name)
            
            if delete_request.expert_name:
                query = query.eq("expert_name", delete_request.expert_name)
            else:
                query = query.is_("expert_name", "null")

            if delete_request.client_name:
                if not delete_request.expert_name:
                    raise HTTPException(status_code=400, 
                                      detail="Cannot specify client name without expert name")
                query = query.eq("client_name", delete_request.client_name)
            else:
                query = query.is_("client_name", "null")
            
            if vector_id:
                query = query.eq("vector_id", vector_id)
                    
            result = query.execute()
            if not result.data:
                raise HTTPException(status_code=404, detail="Vector store not found")
            vector_id_to_delete = result.data[0].get("id")
            vector_id = result.data[0].get("vector_id") if not vector_id else vector_id
        
        # Delete the vector index
        await delete_vector_index(vector_id)
        
        # Delete the vector store record
        supabase.table("vector_stores").delete().eq("id", vector_id_to_delete).execute()
        
        return {"message": f"Vector memory deleted for domain: {delete_request.domain_name}, "
                           f"expert: {delete_request.expert_name}, client: {delete_request.client_name}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))