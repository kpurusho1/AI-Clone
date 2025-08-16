from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
import os
from database import supabase
from models import (
    ExpertCreate, ExpertResponse, ExpertUpdate,
    QueryRequest, QueryResponse, QueryResponseContent,
    DeleteVectorRequest, ExpertVectorUpdate,
    DomainCreate, AddFilesToDomainVectorCreate, VectorStoreQuery,
    DomainFilesConfigRequest, PersonaGenerationRequest,
    ExpertVectorCreate, ExpertClientVectorCreate,
    AddFilesToExpertVectorCreate, 
    UpdateVectorStoreRequest, UpdateFilesToDomainVectorCreate,
    CreateAssistantRequest, CreateAssistantResponse,
    CreateThreadRequest, CreateThreadResponse,
    AddMessageRequest, AddMessageResponse,
    RunThreadRequest, RunThreadResponse,
    GetRunStatusRequest, GetRunStatusResponse,UpdateFilesToExpertVectorCreate,
    GetThreadMessagesRequest, GetThreadMessagesResponse,
    UpdateExpertPersonaRequest,InitializeExpertMemoryRequest, UpdateDomainFilesConfigRequest,
    YouTubeTranscriptRequest
)

from utils import (
    create_vector_store, 
    add_documents_to_vector_store,
    query_vector_index, delete_vector_index,
    edit_vector_store, client, delete_files_in_vector_store,
    # OpenAI Assistant API functions
    create_assistant, get_or_create_assistant, create_thread,
    add_message_to_thread, run_thread, get_run_status,
    get_thread_messages, query_expert_with_assistant,
    generate_persona_from_qa,
    # YouTube transcript function
    get_youtube_transcript
)

router = APIRouter()

# 1. Create domain - will create default vector store for domain
@router.post("/domains", response_model=dict)
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

# 2. Get all domains and returns complete domain object
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

# 2.1 Get domain name for an expert
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

# 3 Get vector ID based on domain, expert, and client parameters
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

# 4. Create expert
@router.post("/experts", response_model=ExpertResponse)
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

# 5 Get all experts - will return expert objects
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

# 5.1 Get client names for a specific expert and optional domain
@router.get("/experts/{expert_name}/clients", response_model=List[str])
async def get_client_names(expert_name: str, domain: str = None):
    """
    Get unique client names for a specific expert and optional domain
    """
    try:
        print(f"Getting client names for expert: {expert_name}, domain: {domain if domain else 'any'}")
        
        # Build the query based on parameters
        query = supabase.table("documents").select("client_name").eq("created_by", expert_name)
        
        # Add domain filter if provided
        if domain:
            query = query.eq("domain", domain)
            
        # Execute the query
        result = query.execute()
        print(f"Query result: {result.data}")
        
        # Extract unique client names
        client_names = set()
        for doc in result.data:
            if doc.get("client_name"):
                client_names.add(doc.get("client_name"))
        
        print(f"Found {len(client_names)} unique clients")
        return list(client_names)
    except Exception as e:
        print(f"Error getting client names: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 5.2 Get an expert's context
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

# 5.3 Update context
@router.put("/experts/context", response_model=ExpertResponse)
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

# 6. Create vector store for expert and domain - will use default for preferred if bool is true
@router.post("/vectors/expert-domain", response_model=dict)
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

# 7. Update expert domain vector store - update preferred vector store id
@router.post("/vectors/expert-domain/update", response_model=dict)
async def update_expert_domain_vector(vector_create: ExpertVectorUpdate):
    """
    Get or create a vector store for an expert given expert name
    """
    try:
        print(f"Getting or creating vector store for expert: {vector_create.expert_name}")
        
        domain_name = vector_create.domain_name
        vector_id_result = await get_vector_id(domain_name)
        default_vector_id = vector_id_result.get("vector_id") if vector_id_result else None
        
        expert_vector_store = await get_vector_id(domain_name, vector_create.expert_name)
        expert_vector_id = expert_vector_store.get("vector_id")
        id = expert_vector_store.get("id")

        print(f"Domain name from expert record: {domain_name}")
        
        # If the expert already has a preferred vector ID, return it
        if expert_vector_id and expert_vector_id != default_vector_id and not vector_create.replace_vector:
            print(f"Using existing preferred vector ID: {expert_vector_id}")
            return {
                "expert_name": vector_create.expert_name,
                "domain_name": domain_name,
                "vector_id": expert_vector_id,
                "vector_name": f"{vector_create.expert_name}_{domain_name}",
                "message": f"Using existing vector store for expert {vector_create.expert_name} and domain {domain_name}"
            }
        
        delete_vector_memory(vector_id=expert_vector_id, delete_id=id)
        
        # Create vector store with name 'expert_name_domain_name'
        vector_name = f"{vector_create.expert_name}_{domain_name}"
        print(f"Creating vector store with name: {vector_name}")
        
        try:
            vector_store = await create_vector_store(client, vector_name)
            print(f"Vector store created: {vector_store}")
            vector_id = vector_store.id if hasattr(vector_store, 'id') else None
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating vector store: {str(e)}")
        
        if vector_id:
            try:
                # Also add an entry to the vector_stores table
                vector_store_data = {
                    "vector_id": vector_id,
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
            except Exception as e:
                print(f"Error updating expert or creating vector_stores entry: {str(e)}")
                # Continue anyway, the vector store was created successfully
        
        return {
            "expert_name": vector_create.expert_name,
            "domain_name": domain_name,
            "vector_id": vector_id,
            "vector_name": vector_name,
            "message": f"Vector store created successfully for expert {vector_create.expert_name} and domain {domain_name}"
        }
    except Exception as e:
        print(f"Error updating expert domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 8. Create client-specific expert vector store
@router.post("/vectors/expert-client", response_model=dict)
async def create_expert_client_vector(vector_create: ExpertClientVectorCreate):
    """
    Create a vector store for an expert with a specific client name
    """
    try:
        print(f"Creating client-specific vector store for expert: {vector_create.expert_name}, client: {vector_create.client_name}")
        
        # Check if expert exists and get domain
        expert_domain_result = await get_expert_domain(vector_create.expert_name)
        domain_name = expert_domain_result.get("domain_name") if expert_domain_result else None
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {vector_create.expert_name} does not have an associated domain")
        print(f"Domain name from expert record: {domain_name}")
        
        # Create vector store with name 'expert_name_client_name_domain_name'
        vector_name = f"{vector_create.expert_name}_{vector_create.client_name}_{domain_name}"
        print(f"Checking if vector store with name {vector_name} already exists")
        
        # Check if a vector store with this name already exists in the vector_stores table
        existing_vector = await get_vector_id(domain_name, vector_create.expert_name, vector_create.client_name)
        if existing_vector.get("vector_id"):
            # Vector store already exists, use the existing one
            vector_id = existing_vector.get("vector_id")
            print(f"Vector store already exists. Using existing vector store with ID: {vector_id}")
        else:
            # Create a new vector store
            print(f"Creating new vector store with name: {vector_name}")
            try:
                vector_store = await create_vector_store(client, vector_name)
                print(f"Vector store created: {vector_store}")
                vector_id = vector_store.get("vector_id")
            except Exception as e:
                print(f"Error creating vector store: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating vector store: {str(e)}")
        
        # Add an entry to the vector_stores table for this client-specific vector
        if vector_id and not existing_vector.get("vector_id"):
            try:
                vector_store_data = {
                    "vector_id": vector_id,
                    "domain_name": domain_name,
                    "expert_name": vector_create.expert_name,
                    "client_name": vector_create.client_name,
                    "owner": "client",  # Mark as owned by client
                    "file_ids": [],  # Start with empty file IDs
                    "batch_ids": []   # Start with empty batch IDs
                }
                
                print(f"Vector store data to insert: {vector_store_data}")
                
                # Insert into vector_stores table
                vector_result = supabase.table("vector_stores").insert(vector_store_data).execute()
                print(f"Vector store insert result: {vector_result}")
            except Exception as e:
                print(f"Error creating vector_stores entry: {str(e)}")
                # Continue anyway, the vector store was created successfully
        
        return {
            "expert_name": vector_create.expert_name,
            "client_name": vector_create.client_name,
            "domain_name": domain_name,
            "vector_id": vector_id,
            "vector_name": vector_name,
            "message": f"Client-specific vector store created successfully for expert {vector_create.expert_name}, client {vector_create.client_name}, and domain {domain_name}"
        }
    except Exception as e:
        print(f"Error creating expert client vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 9. Add files to domain vector
@router.post("/vectors/domain/files", response_model=dict)
async def add_files_to_domain_vector(files_create: AddFilesToDomainVectorCreate):
    """
    Add files to a domain's default vector store
    """
    try:
        print(f"Adding files to domain vector for domain: {files_create.domain_name}")
        print(f"Document URLs: {files_create.document_urls}")
        
        domain_vector = await get_vector_id(files_create.domain_name)
        default_vector_id = domain_vector.get("vector_id")
        id = domain_vector.get("id")
        
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {files_create.domain_name} does not have a default vector ID")

        print(f"Default vector ID from domain record: {default_vector_id}")
        
        # Add the documents to the vector store
        result = await add_documents_to_vector_store(client, default_vector_id, files_create.document_urls, files_create.domain_name, None, None)
        print(f"Added documents to vector store: {result}")
        
        # Update vector_stores table with the new file information
        file_ids = result.get("file_ids", [])
        batch_id = result.get("batch_id")
        
        try:
            update_data = {
                "file_ids": file_ids,
                "batch_ids": [batch_id] if batch_id else [],
                "latest_batch_id": batch_id,
            }
            update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
            print(f"Updated existing vector_stores entry with replacement: {update_result}")
            
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        return {
            "domain_name": files_create.domain_name,
            "vector_id": default_vector_id,
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "message": f"Added {len(files_create.document_urls)} documents to default vector store for domain {files_create.domain_name}"
        }
    except Exception as e:
        print(f"Error adding files to domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 10. Add files to domain vector
@router.post("/vectors/domain/files/update", response_model=dict)
async def update_files_to_domain_vector(files_update: UpdateFilesToDomainVectorCreate):
    """
    Add files to a domain's default vector store
    """
    try:
        print(f"Adding files to domain vector for domain: {files_update.domain_name}")
        print(f"Document URLs: {files_update.document_urls}")
        
        domain_vector = await get_vector_id(files_update.domain_name)
        default_vector_id = domain_vector.get("vector_id")
        id = domain_vector.get("id")
        
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {files_create.domain_name} does not have a default vector ID")

        print(f"Default vector ID from domain record: {default_vector_id}")
        print(f"Default vector ID from domain record: {default_vector_id}")
        existing_entry = supabase.table("vector_stores").select("*").eq("id", id).execute()
        if not files_update.append_files:
            # Get file_ids from vector store
            files_to_delete = existing_entry.data[0].get("file_ids")
            if files_to_delete and isinstance(files_to_delete, list) and len(files_to_delete) > 0:
                # Use the utility function to delete files
                delete_result = await delete_files_in_vector_store(client, default_vector_id, files_to_delete)
                if delete_result.get("failed_files") > 0:
                    raise HTTPException(status_code=400, detail=f"Failed to delete {delete_result.get('failed_files')} files from vector store.")
                else:
                    # Delete vector store file_ids
                    delete_result = supabase.table("vector_stores").update({"file_ids": [], "batch_ids": [], "latest_batch_id": None}).eq("id", id).execute()
                    print(f"Deleted {delete_result.get('deleted_files')} files from vector store. {delete_result.get('failed_files')} files failed to delete.")
            else:
                print("No files to delete in vector store.")
            
            
        # Initialize result variables
        file_ids = []
        batch_id = None
        result = {"file_ids": [], "batch_id": None, "status": "skipped"}
        
        # Only add documents to vector store if we have valid document URLs
        if files_update.document_urls:
            result = await add_documents_to_vector_store(client, default_vector_id, files_update.document_urls, files_update.domain_name, None, None)
            print(f"Added documents to vector store: {result}")
            
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
        else:
            print("Skipping document addition to vector store - no valid documents found")
        
        try:    
            if files_update.append_files:
                existing_file_ids = existing_entry.data[0].get("file_ids", [])
                existing_batch_ids = existing_entry.data[0].get("batch_ids", [])
                
                # Combine existing and new file_ids without duplicates
                updated_file_ids = list(set(existing_file_ids + file_ids))
                    
                # Add new batch_id if it exists
                updated_batch_ids = existing_batch_ids
                if batch_id and batch_id not in updated_batch_ids:
                    updated_batch_ids.append(batch_id)
                    
                update_data = {
                    "file_ids": updated_file_ids,
                    "batch_ids": updated_batch_ids,
                    "latest_batch_id": batch_id or existing_entry.data[0].get("latest_batch_id")
                    }
                    
                print(f"Appending files: {len(file_ids)} new files to {len(existing_file_ids)} existing files")
            else:
                update_data = {
                    "file_ids": file_ids,  # Replace with new file_ids
                    "batch_ids": [batch_id] if batch_id else [],  # Replace with new batch_id
                    "latest_batch_id": batch_id
                    }
                
            update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
            print(f"Updated existing vector_stores entry with replacement: {update_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        return {
            "domain_name": files_update.domain_name,
            "vector_id": default_vector_id,
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "message": f"Added {len(files_update.document_urls)} documents to default vector store for domain {files_update.domain_name}"
        }
    except Exception as e:
        print(f"Error adding files to domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 11. Add files to domain vector from config file
@router.post("/vectors/domain/files/config", response_model=dict)
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
            # Read and parse the config file
            try:
                with open(config_request.config_file_path, 'r') as file:
                    file_content = file.read().strip()
                    if not file_content:  # Check if file is empty
                        print(f"Warning: Config file {config_request.config_file_path} is empty")
                        file_empty = True
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
            result = await add_documents_to_vector_store(client, default_vector_id, document_urls, config_request.domain_name, None, None)
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

# 11.1 Add files to domain vector from config file
@router.post("/vectors/domain/files/config/update", response_model=dict)
async def update_files_to_domain_vector_from_config(config_request: UpdateDomainFilesConfigRequest):
    """
    Update files to a domain's default vector store from a configuration file
    
    The config file should be in JSON format with the following structure:
    {
        "files": [
            {"name": "Document 1", "url": "https://example.com/doc1.pdf"},
            {"name": "Document 2", "url": "https://example.com/doc2.pdf"}
        ]
    }
    """
    try:
        print(f"Updating files to domain vector for domain: {config_request.domain_name} from config file: {config_request.config_file_path}")
        
        # Initialize variables
        document_urls = {}
        file_exists = os.path.exists(config_request.config_file_path)
        file_empty = False
        
        if file_exists:
            # Read and parse the config file
            try:
                with open(config_request.config_file_path, 'r') as file:
                    file_content = file.read().strip()
                    if not file_content:  # Check if file is empty
                        print(f"Warning: Config file {config_request.config_file_path} is empty")
                        file_empty = True
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
        else:
            print(f"Warning: Config file {config_request.config_file_path} does not exist")
        
        vector_store = await get_vector_id(config_request.domain_name)
        default_vector_id = vector_store.get("vector_id")
        id = vector_store.get("id")
        
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {config_request.domain_name} does not have a default vector ID")
        
        print(f"Default vector ID from domain record: {default_vector_id}")
        existing_entry = supabase.table("vector_stores").select("*").eq("id", id).execute()
        if not config_request.append_files:
            # Get file_ids from vector store
            files_to_delete = existing_entry.data[0].get("file_ids")
            if files_to_delete and isinstance(files_to_delete, list) and len(files_to_delete) > 0:
                # Use the utility function to delete files
                delete_result = await delete_files_in_vector_store(client, default_vector_id, files_to_delete)
                if delete_result.get("failed_files") > 0:
                    raise HTTPException(status_code=400, detail=f"Failed to delete {delete_result.get('failed_files')} files from vector store.")
                else:
                    # Delete vector store file_ids
                    delete_result = supabase.table("vector_stores").update({"file_ids": [], "batch_ids": [], "latest_batch_id": None}).eq("id", id).execute()
                    print(f"Deleted {delete_result.get('deleted_files')} files from vector store. {delete_result.get('failed_files')} files failed to delete.")
            else:
                print("No files to delete in vector store.")
            
            
        # Initialize result variables
        file_ids = []
        batch_id = None
        result = {"file_ids": [], "batch_id": None, "status": "skipped"}
        
        # Only add documents to vector store if we have valid document URLs
        if document_urls:
            result = await add_documents_to_vector_store(client, default_vector_id, document_urls, config_request.domain_name, None, None)
            print(f"Added documents to vector store: {result}")
            file_ids = result.get("file_ids", [])
            batch_id = result.get("batch_id")
        else:
            print("Skipping document addition to vector store - no valid documents found")
        
        try:    
            if config_request.append_files:
                existing_file_ids = existing_entry.data[0].get("file_ids", [])
                existing_batch_ids = existing_entry.data[0].get("batch_ids", [])
                
                # Combine existing and new file_ids without duplicates
                updated_file_ids = list(set(existing_file_ids + file_ids))
                    
                # Add new batch_id if it exists
                updated_batch_ids = existing_batch_ids
                if batch_id and batch_id not in updated_batch_ids:
                    updated_batch_ids.append(batch_id)
                    
                update_data = {
                    "file_ids": updated_file_ids,
                    "batch_ids": updated_batch_ids,
                    "latest_batch_id": batch_id or existing_entry.data[0].get("latest_batch_id")
                    }
                    
                print(f"Appending files: {len(file_ids)} new files to {len(existing_file_ids)} existing files")
            else:
                update_data = {
                    "file_ids": file_ids,  # Replace with new file_ids
                    "batch_ids": [batch_id] if batch_id else [],  # Replace with new batch_id
                    "latest_batch_id": batch_id
                    }
                
            update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
            print(f"Updated existing vector_stores entry with replacement: {update_result}")
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

# 12. Generate persona from QA data
@router.post("/persona/generate", response_model=dict)
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

# 12.1 Update expert persona
@router.api_route("/experts/persona/update", methods=["POST", "PUT"], response_model=dict)
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

# 13. Update vector store
@router.post("/vectors/update", response_model=dict)
async def update_vector_store(update_request: UpdateVectorStoreRequest):
    """
    Update an existing vector store by adding new documents
    
    Args:
        update_request: Request containing vector_id and document_urls
        
    Returns:
        Updated vector store information
    """
    try:
        print(f"Updating vector store {update_request.expert_name} with {len(update_request.document_urls)} new documents")
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
            client_name
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

# 14. Add files to expert vector
@router.post("/vectors/expert/files", response_model=dict)
async def add_files_to_expert_vector(files_create: AddFilesToExpertVectorCreate):
    """
    Add files to an expert vector store, either the default one or a client-specific one
    """
    try:
        print(f"Adding files to expert vector for expert: {files_create.expert_name}")
        print(f"Use for specific client: {files_create.use_for_specific_client}")
        print(f"Document URLs: {files_create.document_urls}")
        
        # Check if document_urls is empty
        if not files_create.document_urls:
            print("No document URLs provided, returning early")
            return {
                "expert_name": files_create.expert_name,
                "client_name": files_create.client_name if files_create.use_for_specific_client else None,
                "vector_id": None,
                "file_ids": [],
                "batch_id": None,
                "status": "skipped",
                "message": "No documents provided to add to vector store"
            }
        
        vector_id = None
        expert_domain_result = await get_expert_domain(files_create.expert_name)
        domain_name = expert_domain_result.get("domain_name") if expert_domain_result else None
        client_name = files_create.client_name if files_create.use_for_specific_client else None
        create_entry_vector_stores_table = False

        # Get the appropriate vector ID based on the use_for_specific_client flag
        if files_create.use_for_specific_client:
            # Validate client name is provided when use_for_specific_client is True
            if not files_create.client_name:
                raise HTTPException(status_code=400, detail="Client name is required when use_for_specific_client is True")
                
            # Create a client-specific vector store and get its ID
            client_vector_result = await create_expert_client_vector(
                ExpertClientVectorCreate(
                    expert_name=files_create.expert_name,
                    client_name=files_create.client_name
                )
            )
            vector_id = client_vector_result.get("vector_id")
            create_entry_vector_stores_table = True
            print(f"Using client-specific vector ID: {vector_id}")
        else:
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
  
        # Add the documents to the vector store
        result = await add_documents_to_vector_store(client, vector_id, files_create.document_urls, domain_name, files_create.expert_name, client_name)
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
        
        return {
            "expert_name": files_create.expert_name,
            "client_name": files_create.client_name if files_create.use_for_specific_client else None,
            "vector_id": vector_id,
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "message": f"Added {len(files_create.document_urls)} documents to vector store for expert {files_create.expert_name}"
        }
    except Exception as e:
        print(f"Error adding files to expert vector: {str(e)}")
        # Return partial success instead of raising an exception
        return {
            "expert_name": files_create.expert_name,
            "client_name": files_create.client_name if files_create.use_for_specific_client else None,
            "vector_id": None,
            "file_ids": [],
            "batch_id": None,
            "status": "error",
            "message": f"Error adding files to expert vector: {str(e)}"
        }

# 14.1 Update files to expert vector
@router.put("/vectors/expert/files", response_model=dict)
async def update_files_to_expert_vector(files_update: UpdateFilesToExpertVectorCreate):
    """
    Update files in an expert vector store by appending new files to existing ones.
    This endpoint first finds the appropriate vector ID based on expert name, client name, and domain,
    then adds the new documents and updates the vector_stores table by appending the new file IDs and batch IDs.
    """
    try:
        print(f"Updating files in expert vector for expert: {files_update.expert_name}")
        print(f"Use for specific client: {files_update.use_for_specific_client}")
        print(f"Document URLs: {files_update.document_urls}")
        print(f"Append files: {files_update.append_files}")
        
        # Check if document_urls is empty
        if not files_update.document_urls:
            print("No document URLs provided, returning early")
            return {
                "expert_name": files_update.expert_name,
                "client_name": files_update.client_name if files_update.use_for_specific_client else None,
                "vector_id": None,
                "file_ids": [],
                "batch_id": None,
                "status": "skipped",
                "message": "No documents provided to update vector store"
            }
        
        # Check if expert exists and get domain
        expert_result = await get_expert_domain(files_update.expert_name)
        domain_name = expert_result.get("domain_name")
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {files_update.expert_name} does not have an associated domain")
        print(f"Domain name from expert record: {domain_name}")
        
        client_name = files_update.client_name if files_update.use_for_specific_client else None
        vector_st = await get_vector_id(domain_name, files_update.expert_name, client_name)
        vector_id = vector_st.get("vector_id")
        id = vector_st.get("id")

        if not vector_id:
            # If no vector store found, create one using the add_files_to_expert_vector endpoint
            print("No existing vector store found, creating a new one")
            raise HTTPException(status_code=400, detail=f"No existing vector store found for expert {files_update.expert_name}")
        
        # Use the found vector ID
        print(f"Found existing vector ID: {vector_id}")
        existing_entry = supabase.table("vector_stores").select("*").eq("id", id).execute()
        if not files_update.append_files:
            # Get file_ids from vector store
            files_to_delete = existing_entry.data[0].get("file_ids")
            if files_to_delete and isinstance(files_to_delete, list) and len(files_to_delete) > 0:
                # Use the utility function to delete files
                print(f"Deleting files from vector store: {files_to_delete}")
                delete_result = await delete_files_in_vector_store(client, vector_id, files_to_delete)
                if delete_result.get("failed_files") > 0:
                    raise HTTPException(status_code=400, detail=f"Failed to delete {delete_result.get('failed_files')} files from vector store.")
                else:
                    # Delete vector store file_ids
                    delete_result = supabase.table("vector_stores").update({"file_ids": [], "batch_ids": [], "latest_batch_id": None}).eq("id", id).execute()
                    print(f"Deleted {delete_result.get('deleted_files')} files from vector store. {delete_result.get('failed_files')} files failed to delete.")
            else:
                print("No files to delete in vector store.")
            
        
        # Add the documents to the vector store
        result = await add_documents_to_vector_store(client, vector_id, files_update.document_urls, domain_name, files_update.expert_name, client_name)
        print(f"Added documents to vector store: {result}")
        
        # Update vector_stores table with the new file information
        file_ids = result.get("file_ids", [])
        batch_id = result.get("batch_id")
        
        try:
            # If append_files is True, combine with existing file_ids and batch_ids
            if files_update.append_files:
                existing_file_ids = existing_entry.data[0].get("file_ids", [])
                existing_batch_ids = existing_entry.data[0].get("batch_ids", [])
                    
                # Combine existing and new file_ids without duplicates
                updated_file_ids = list(set(existing_file_ids + file_ids))
                    
                # Add new batch_id if it exists
                updated_batch_ids = existing_batch_ids
                if batch_id and batch_id not in updated_batch_ids:
                    updated_batch_ids.append(batch_id)
                    
                update_data = {
                    "file_ids": updated_file_ids,
                    "batch_ids": updated_batch_ids,
                    "latest_batch_id": batch_id or existing_entry.data[0].get("latest_batch_id")
                }
                    
                print(f"Appending files: {len(file_ids)} new files to {len(existing_file_ids)} existing files")
            else:
                # Replace existing file_ids and batch_ids
                update_data = {
                    "file_ids": file_ids,
                    "batch_ids": [batch_id] if batch_id else [],
                    "latest_batch_id": batch_id
                }
                print(f"Replacing files: {len(file_ids)} new files")
                
            update_result = supabase.table("vector_stores").update(update_data).eq("id", id).execute()
            print(f"Updated vector_stores entry: {update_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        return {
            "expert_name": files_update.expert_name,
            "client_name": client_name,
            "vector_id": vector_id,
            "file_ids": file_ids,
            "all_file_ids": update_data["file_ids"] if "update_data" in locals() else file_ids,
            "batch_id": batch_id,
            "status": "success",
            "append_mode": files_update.append_files,
            "message": f"{'Appended' if files_update.append_files else 'Replaced'} {len(files_update.document_urls)} documents in vector store for expert {files_update.expert_name}"
        }
    except Exception as e:
        print(f"Error updating files in expert vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 15. Delete vector memory
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

# 16. Get documents by domain, expert, and client
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

# 17. Respond to query
@router.post("/query", response_model=QueryResponse)
async def query_expert(query_request: QueryRequest):
    """
    Query an expert using their vector index based on the specified memory type.
    Memory types:
    - llm: Use LLM memory (no vector search)
    - domain: Use domain memory 
    - expert: Use expert memory 
    - client: Use client memory 
    """
    try:
        print(f"[DEBUG] query_expert: Received query for expert: {query_request.expert_name}")
        print(f"[DEBUG] query_expert: Query text: {query_request.query}")
        print(f"[DEBUG] query_expert: Memory type: {query_request.memory_type}")
        # Get expert data
        try:
            expert_domain_result = await get_expert_domain(query_request.expert_name)
            domain_name = expert_domain_result.get("domain_name") if expert_domain_result else None
            if query_request.client_name:
                print(f"[DEBUG] query_expert: Client name: {query_request.client_name}")
                vector_st = await get_vector_id(domain_name, query_request.expert_name, query_request.client_name)
            else:
                vector_st = await get_vector_id(domain_name, query_request.expert_name)
            vector_id = vector_st.get("vector_id")
            id = vector_st.get("id")
            print(f"[DEBUG] query_expert: Vector store fetch result: {vector_st}")
        except Exception as e:
            print(f"[ERROR] query_expert: Failed to fetch expert data: {str(e)}")
            raise
        
        # Determine which vector ID to use based on memory type
        vector_store_ids = None
        
        if query_request.memory_type != "llm":
            # Use LLM memory (no vector search)
            print(f"[DEBUG] query_expert: Using LLM memory (no vector search)")
            vector_store_ids = vector_id
        '''    
        elif query_request.memory_type == "domain":
            # Use domain memory
            domain_name = expert_data.get("domain")
            if not domain_name:
                print(f"[ERROR] query_expert: No domain found for expert {query_request.expert_name}")
                raise HTTPException(status_code=404, detail=f"No domain found for expert {query_request.expert_name}")
                
            # Get domain data
            domain = supabase.table("domains").select("*").eq("domain_name", domain_name).execute()
            if not domain.data:
                print(f"[ERROR] query_expert: Domain {domain_name} not found")
                raise HTTPException(status_code=404, detail=f"Domain {domain_name} not found")
                
            domain_data = domain.data[0]
            vector_id = domain_data.get("default_vector_id")
            if not vector_id:
                print(f"[ERROR] query_expert: No vector index found for domain {domain_name}")
                raise HTTPException(status_code=404, detail=f"No vector index found for domain {domain_name}")
                
            print(f"[DEBUG] query_expert: Using domain memory with vector ID: {vector_id}")
            vector_store_ids = [vector_id]
        elif query_request.memory_type == "expert":
            # Use expert memory
            vector_id = expert_data.get("preferred_vector_id")
            if not vector_id:
                print(f"[ERROR] query_expert: No vector index found for expert {query_request.expert_name}")
                raise HTTPException(status_code=404, detail=f"No vector index found for expert {query_request.expert_name}")
                
            print(f"[DEBUG] query_expert: Using expert memory with vector ID: {vector_id}")
            vector_store_ids = [vector_id]
        elif query_request.memory_type == "client":
            # Use client memory
            if not query_request.client_name:
                print(f"[ERROR] query_expert: Client name is required for client memory")
                raise HTTPException(status_code=400, detail="Client name is required for client memory")
                
            # Get vector ID for expert-client combination
            try:
                vector_stores = supabase.table("vector_stores")\
                    .select("*")\
                    .eq("expert_name", query_request.expert_name)\
                    .eq("client_name", query_request.client_name).execute()
                    
                if not vector_stores.data:
                    print(f"[ERROR] query_expert: No vector store found for expert {query_request.expert_name} and client {query_request.client_name}")
                    raise HTTPException(
                        status_code=404, 
                        detail=f"No vector store found for expert {query_request.expert_name} and client {query_request.client_name}"
                    )
                    
                vector_id = vector_stores.data[0].get("vector_id")
                if not vector_id:
                    print(f"[ERROR] query_expert: Vector ID not found in vector store")
                    raise HTTPException(status_code=404, detail="Vector ID not found in vector store")
                    
                print(f"[DEBUG] query_expert: Using client memory with vector ID: {vector_id}")
                vector_store_ids = [vector_id]
                
            except Exception as e:
                print(f"[ERROR] query_expert: Failed to get vector ID for expert-client combination: {str(e)}")
                raise
        else:
            print(f"[ERROR] query_expert: Invalid memory type: {query_request.memory_type}")
            raise HTTPException(status_code=400, detail=f"Invalid memory type: {query_request.memory_type}")
        '''
        # Query the vector index or LLM
        try:
            print(f"[DEBUG] query_expert: Querying with vector_store_ids: {vector_store_ids}")
            context = supabase.table("experts").select("context").eq("name", query_request.expert_name).execute().data[0].get("context", "")
            response = await query_vector_index(query_request.query, vector_store_ids, context)
            print(f"[DEBUG] query_expert: Query response type: {type(response)}")
            
            # Ensure response is properly formatted
            if isinstance(response, dict):
                # Convert any non-string text to string
                if 'text' in response and not isinstance(response['text'], str):
                    response['text'] = str(response['text'])
                print(f"[DEBUG] query_expert: Response text: {response.get('text', '')[:100]}...")
            else:
                print(f"[DEBUG] query_expert: Response is not a dict, converting to proper format")
                response = {"text": str(response), "citations": None}
                
            # Final validation to ensure we have valid text
            if 'text' not in response or not response['text']:
                print(f"[DEBUG] query_expert: No text in response, using default message")
                response['text'] = "I couldn't find a specific answer to your question."
                
            # Handle optional citations field
            if 'citations' not in response:
                print(f"[DEBUG] query_expert: No citations in response, setting to None")
                response['citations'] = None
            elif not isinstance(response['citations'], list):
                print(f"[DEBUG] query_expert: Invalid citations format, setting to None")
                response['citations'] = None
        except Exception as e:
            print(f"[ERROR] query_expert: Failed to query: {str(e)}")
            raise
        
        print(f"[DEBUG] query_expert: Returning response")
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 18. Initialize expert memory
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
            use_for_specific_client=False,
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

# OpenAI Assistant API endpoints
@router.post("/create_assistant", response_model=CreateAssistantResponse)
async def create_assistant_endpoint(request: CreateAssistantRequest):
    """
    Create an OpenAI Assistant for a specific expert and memory type
    """
    try:
        assistant = await get_or_create_assistant(
            expert_name=request.expert_name,
            memory_type=request.memory_type,
            client_name=request.client_name,
            model=request.model
        )
        
        return CreateAssistantResponse(
            assistant_id=assistant.id,
            expert_name=request.expert_name,
            memory_type=request.memory_type,
            client_name=request.client_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_thread", response_model=CreateThreadResponse)
async def create_thread_endpoint(request: CreateThreadRequest):
    """
    Create a new thread for conversation
    """
    try:
        thread = await create_thread()
        
        return CreateThreadResponse(
            thread_id=thread.id,
            expert_name=request.expert_name,
            memory_type=request.memory_type,
            client_name=request.client_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add_message", response_model=AddMessageResponse)
async def add_message_endpoint(request: AddMessageRequest):
    """
    Add a message to a thread
    """
    try:
        message = await add_message_to_thread(
            thread_id=request.thread_id,
            content=request.content,
            role=request.role
        )
        
        return AddMessageResponse(
            message_id=message.id,
            thread_id=request.thread_id,
            content=request.content,
            role=request.role
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run_thread", response_model=RunThreadResponse)
async def run_thread_endpoint(request: RunThreadRequest):
    """
    Run a thread with an assistant
    """
    try:
        run = await run_thread(
            thread_id=request.thread_id,
            assistant_id=request.assistant_id
        )
        
        return RunThreadResponse(
            run_id=run.id,
            thread_id=request.thread_id,
            assistant_id=request.assistant_id,
            status=run.status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get_run_status", response_model=GetRunStatusResponse)
async def get_run_status_endpoint(request: GetRunStatusRequest):
    """
    Get the status of a run
    """
    try:
        run = await get_run_status(
            thread_id=request.thread_id,
            run_id=request.run_id
        )
        
        response = None
        if run.status == "completed":
            response = await get_assistant_response(request.thread_id, request.run_id)
        
        return GetRunStatusResponse(
            run_id=run.id,
            thread_id=request.thread_id,
            status=run.status,
            response=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get_thread_messages", response_model=GetThreadMessagesResponse)
async def get_thread_messages_endpoint(request: GetThreadMessagesRequest):
    """
    Get messages from a thread
    """
    try:
        messages_result = await get_thread_messages(
            thread_id=request.thread_id,
            limit=request.limit
        )
        
        # Convert OpenAI message objects to our model format
        messages = []
        for msg in messages_result.data:
            content_items = []
            for content in msg.content:
                if content.type == "text":
                    content_items.append(MessageContent(
                        type=content.type,
                        text=content.text.value
                    ))
            
            messages.append(ThreadMessage(
                id=msg.id,
                role=msg.role,
                content=content_items
            ))
        
        return GetThreadMessagesResponse(messages=messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            client_name=request.client_name,
            thread_id=thread_id
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/youtube/transcript")
async def youtube_transcript_endpoint(request: YouTubeTranscriptRequest):
    """
    Get transcript from a YouTube video URL
    
    Args:
        request: YouTubeTranscriptRequest with video_url
        
    Returns:
        List of documents containing transcript text and metadata
    """
    try:
        print(f"Getting transcript for YouTube video: {request.video_url}")
        
        # Get transcript using the utility function
        transcript = get_youtube_transcript(request.video_url)
        
        return transcript
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error getting YouTube transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
