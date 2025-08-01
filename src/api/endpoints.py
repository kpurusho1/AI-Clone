from fastapi import APIRouter, HTTPException
from typing import List, Optional

from database import supabase
from models import (
    ExpertCreate, ExpertResponse, ExpertUpdate,
    QueryRequest, QueryResponse,
    DeleteVectorIdRequest, DomainCreate, ExpertVectorCreate, ExpertClientVectorCreate,
    AddFilesToExpertVectorCreate, AddFilesToDomainVectorCreate, VectorStoreQuery,
    UpdateVectorStoreRequest, DeleteVectorRequest
)
from utils import (
    create_vector_store, 
    add_documents_to_domain_vector_store,
    add_documents_to_expert_vector_store,
    query_vector_index, delete_vector_index,
    edit_vector_store, client
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
        domain_exists = supabase.table("domains").select("domain_name").eq("domain_name", domain_name).execute()
        print(f"Domain exists check result: {domain_exists.data}")
        
        if domain_exists.data:
            raise HTTPException(status_code=400, detail=f"Domain {domain_name} already exists")
        
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
            "default_vector_id": vector_id,
            "expert_names": []
        }
        
        print(f"Domain data to insert: {domain_data}")
        
        # Insert domain into database
        result = supabase.table("domains").insert(domain_data).execute()
        print(f"Insert result: {result}")
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create domain")
        
        return {
            "domain_name": domain_name,
            "default_vector_id": vector_id,
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

# 3. Get default vector ID for a domain - will return default vector store id for a given domain
@router.get("/domains/{domain_name}/vector_id", response_model=dict)
async def get_domain_vector_id(domain_name: str):
    """
    Get default vector ID for a given domain name
    """
    try:
        print(f"Getting default vector ID for domain: {domain_name}")
        
        # Query the domain by name
        result = supabase.table("domains").select("domain_name, default_vector_id").eq("domain_name", domain_name).execute()
        print(f"Domain query result: {result.data}")
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Domain {domain_name} not found")
        
        domain_data = result.data[0]
        default_vector_id = domain_data.get("default_vector_id")
        
        if not default_vector_id:
            return {
                "domain_name": domain_name,
                "default_vector_id": None,
                "message": f"No default vector ID found for domain {domain_name}"
            }
        
        return {
            "domain_name": domain_name,
            "default_vector_id": default_vector_id
        }
    except Exception as e:
        print(f"Error getting domain vector ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 3.1 Get preferred vector ID for an expert
@router.get("/experts/{expert_name}/vector_id", response_model=dict)
async def get_expert_vector_id(expert_name: str):
    """
    Get preferred vector ID for a given expert name
    """
    try:
        print(f"Getting preferred vector ID for expert: {expert_name}")
        
        # Query the expert by name
        result = supabase.table("experts").select("name, preferred_vector_id").eq("name", expert_name).execute()
        print(f"Expert query result: {result.data}")
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Expert {expert_name} not found")
        
        expert_data = result.data[0]
        preferred_vector_id = expert_data.get("preferred_vector_id")
        
        if not preferred_vector_id:
            return {
                "expert_name": expert_name,
                "preferred_vector_id": None,
                "message": f"No preferred vector ID found for expert {expert_name}"
            }
        
        return {
            "expert_name": expert_name,
            "preferred_vector_id": preferred_vector_id
        }
    except Exception as e:
        print(f"Error getting expert vector ID: {str(e)}")
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
        
        # Get domain data
        domain_data = domain_exists.data[0]
        
        # Create expert data
        expert_data = {
            "name": expert.name,
            "domain": domain_value,  # Use the string value instead of the enum
            "context": expert.context
            # default_vector_id will be set by create_expert_domain_vector
        }
        print(f"Expert data to insert: {expert_data}")
        
        # Insert expert into database
        result = supabase.table("experts").insert(expert_data).execute()
        print(f"Insert result: {result}")
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create expert")
        
        # Update domain's expert_names array
        try:
            # First get the current expert_names array
            domain_info = supabase.table("domains").select("expert_names").eq("domain_name", domain_value).execute()
            print(f"Current domain info: {domain_info.data}")
            
            # Extract the current expert_names or initialize an empty list
            current_experts = domain_info.data[0].get("expert_names", []) if domain_info.data else []
            if current_experts is None:
                current_experts = []
            print(f"Current experts: {current_experts}")
            
            # Append the new expert name
            if expert.name not in current_experts:
                current_experts.append(expert.name)
            
            # Update the domain with the new list
            update_result = supabase.table("domains").update({"expert_names": current_experts}).eq("domain_name", domain_value).execute()
            print(f"Domain update result: {update_result}")
        except Exception as domain_update_error:
            print(f"Error updating domain expert_names: {str(domain_update_error)}")
            # Continue anyway, the expert was created successfully
        
        # Create expert domain vector using the create_expert_domain_vector function
        try:
            print(f"Creating expert domain vector for {expert.name}")
            print(f"Use default domain knowledge: {expert.use_default_domain_knowledge}")
            vector_create = ExpertVectorCreate(
                expert_name=expert.name,
                use_default_domain_vector=expert.use_default_domain_knowledge
            )
            vector_result = await create_expert_domain_vector(vector_create)
            print(f"Expert domain vector created: {vector_result}")
            # No need to update expert with preferred_vector_id as create_expert_domain_vector already does this
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

# 6. Get vector ID for an expert and client combination
@router.get("/vectors/expert/{expert_name}/client/{client_name}", response_model=dict)
async def get_expert_client_vector_id(expert_name: str, client_name: str):
    """
    Get vector ID for a specific expert and client combination
    """
    try:
        print(f"Getting vector ID for expert: {expert_name} and client: {client_name}")
        
        # Query the vector_stores table for the expert-client combination
        result = supabase.table("vector_stores") \
            .select("vector_id, expert_name, client_name") \
            .eq("expert_name", expert_name) \
            .eq("client_name", client_name) \
            .execute()
        print(f"Vector store query result: {result.data}")
        
        if not result.data:
            return {
                "expert_name": expert_name,
                "client_name": client_name,
                "vector_id": None,
                "message": f"No vector store found for expert {expert_name} and client {client_name}"
            }
        
        vector_store = result.data[0]
        vector_id = vector_store.get("vector_id")
        
        return {
            "expert_name": expert_name,
            "client_name": client_name,
            "vector_id": vector_id
        }
    except Exception as e:
        print(f"Error getting expert-client vector ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 7. Create vector store for expert and domain - will use default for preferred if bool is true
@router.post("/vectors/expert-domain", response_model=dict)
async def create_expert_domain_vector(vector_create: ExpertVectorCreate):
    """
    Create or update vector IDs for an expert based on domain
    """
    try:
        print(f"Creating/updating vector IDs for expert: {vector_create.expert_name}")
        print(f"Use default domain vector: {vector_create.use_default_domain_vector}")
        
        # Check if expert exists and get domain
        expert_result = supabase.table("experts").select("*").eq("name", vector_create.expert_name).execute()
        print(f"Expert query result: {expert_result.data}")
        
        if not expert_result.data:
            raise HTTPException(status_code=404, detail=f"Expert {vector_create.expert_name} not found")
        
        expert_data = expert_result.data[0]
        domain_name = expert_data.get("domain")
        
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {vector_create.expert_name} does not have an associated domain")
        
        print(f"Domain name from expert record: {domain_name}")
        
        # Get default vector ID for the domain using the existing function
        try:
            domain_vector_result = await get_domain_vector_id(domain_name)
            print(f"Domain vector result: {domain_vector_result}")
            default_vector_id = domain_vector_result.get("default_vector_id")
            
            if not default_vector_id:
                raise HTTPException(status_code=400, detail=f"Domain {domain_name} does not have a default vector ID")
                
        except HTTPException as e:
            # Re-raise any HTTP exceptions from get_domain_vector_id
            raise e
        
        # Update expert's vector IDs based on the use_default_domain_vector flag
        update_data = {"default_vector_id": default_vector_id}
        
        if vector_create.use_default_domain_vector:
            # Use domain's default vector ID for both default and preferred
            update_data["preferred_vector_id"] = default_vector_id
            
            try:
                update_result = supabase.table("experts").update(update_data).eq("name", vector_create.expert_name).execute()
                print(f"Expert update result: {update_result}")
                
                return {
                    "expert_name": vector_create.expert_name,
                    "domain_name": domain_name,
                    "default_vector_id": default_vector_id,
                    "preferred_vector_id": default_vector_id,
                    "message": f"Expert {vector_create.expert_name} updated with domain's default vector ID"
                }
            except Exception as e:
                print(f"Error updating expert: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error updating expert: {str(e)}")
        else:
            # Update default vector ID and create a new vector store for preferred
            try:
                # First update the default vector ID
                update_result = supabase.table("experts").update(update_data).eq("name", vector_create.expert_name).execute()
                print(f"Expert default vector ID update result: {update_result}")
                
                # Then call update_expert_domain_vector to create a new vector store
                # and update the preferred vector ID
                return await update_expert_domain_vector(ExpertVectorCreate(expert_name=vector_create.expert_name))
            except Exception as e:
                print(f"Error updating expert: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error updating expert: {str(e)}")
    except Exception as e:
        print(f"Error creating expert domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 8. Update expert domain vector store - update preferred vector store id
@router.post("/vectors/expert-domain/update", response_model=dict)
async def update_expert_domain_vector(vector_create: ExpertVectorCreate):
    """
    Get or create a vector store for an expert given expert name
    """
    try:
        print(f"Getting or creating vector store for expert: {vector_create.expert_name}")
        
        # Check if expert exists and get domain
        expert_result = supabase.table("experts").select("*").eq("name", vector_create.expert_name).execute()
        print(f"Expert query result: {expert_result.data}")
        
        if not expert_result.data:
            raise HTTPException(status_code=404, detail=f"Expert {vector_create.expert_name} not found")
        
        expert_data = expert_result.data[0]
        domain_name = expert_data.get("domain")
        preferred_vector_id = expert_data.get("preferred_vector_id")
        default_vector_id = expert_data.get("default_vector_id")


        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {vector_create.expert_name} does not have an associated domain")
        
        print(f"Domain name from expert record: {domain_name}")
        print(f"Preferred vector ID from expert record: {preferred_vector_id}")
        
        # If the expert already has a preferred vector ID, return it
        if preferred_vector_id and preferred_vector_id != default_vector_id:
            print(f"Using existing preferred vector ID: {preferred_vector_id}")
            return {
                "expert_name": vector_create.expert_name,
                "domain_name": domain_name,
                "vector_id": preferred_vector_id,
                "vector_name": f"{vector_create.expert_name}_{domain_name}",
                "message": f"Using existing vector store for expert {vector_create.expert_name} and domain {domain_name}"
            }
        
        # Check if domain exists
        domain_exists = supabase.table("domains").select("*").eq("domain_name", domain_name).execute()
        print(f"Domain exists check result: {domain_exists.data}")
        
        if not domain_exists.data:
            raise HTTPException(status_code=404, detail=f"Domain {domain_name} not found")
        
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
        
        # Update expert's preferred vector ID
        if vector_id:
            try:
                update_result = supabase.table("experts").update({"preferred_vector_id": vector_id}).eq("name", vector_create.expert_name).execute()
                print(f"Expert update result: {update_result}")
            except Exception as e:
                print(f"Error updating expert: {str(e)}")
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

# 9. Create client-specific expert vector store
@router.post("/vectors/expert-client", response_model=dict)
async def create_expert_client_vector(vector_create: ExpertClientVectorCreate):
    """
    Create a vector store for an expert with a specific client name
    """
    try:
        print(f"Creating client-specific vector store for expert: {vector_create.expert_name}, client: {vector_create.client_name}")
        
        # Check if expert exists and get domain
        expert_result = supabase.table("experts").select("*").eq("name", vector_create.expert_name).execute()
        print(f"Expert query result: {expert_result.data}")
        
        if not expert_result.data:
            raise HTTPException(status_code=404, detail=f"Expert {vector_create.expert_name} not found")
        
        expert_data = expert_result.data[0]
        domain_name = expert_data.get("domain")
        
        if not domain_name:
            raise HTTPException(status_code=400, detail=f"Expert {vector_create.expert_name} does not have an associated domain")
        
        print(f"Domain name from expert record: {domain_name}")
        
        # Check if domain exists
        domain_exists = supabase.table("domains").select("*").eq("domain_name", domain_name).execute()
        print(f"Domain exists check result: {domain_exists.data}")
        
        if not domain_exists.data:
            raise HTTPException(status_code=404, detail=f"Domain {domain_name} not found")
        
        # Create vector store with name 'expert_name_client_name_domain_name'
        vector_name = f"{vector_create.expert_name}_{vector_create.client_name}_{domain_name}"
        print(f"Checking if vector store with name {vector_name} already exists")
        
        # Check if a vector store with this name already exists in the vector_stores table
        existing_vector = supabase.table("vector_stores").select("*").eq("expert_name", vector_create.expert_name)\
            .eq("client_name", vector_create.client_name).eq("domain_name", domain_name).execute()
        
        if existing_vector.data:
            # Vector store already exists, use the existing one
            print(f"Vector store already exists: {existing_vector.data[0]}")
            vector_id = existing_vector.data[0].get("vector_id")
            print(f"Using existing vector store with ID: {vector_id}")
        else:
            # Create a new vector store
            print(f"Creating new vector store with name: {vector_name}")
            try:
                vector_store = await create_vector_store(client, vector_name)
                print(f"Vector store created: {vector_store}")
                vector_id = vector_store.id if hasattr(vector_store, 'id') else None
            except Exception as e:
                print(f"Error creating vector store: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating vector store: {str(e)}")
        
        # Store the client-specific vector ID in a new table or add to experts table
        # For now, we'll just return the vector ID without updating any tables
        # This could be extended to store client-specific vector IDs in a separate table
        
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

# 10. Add files to domain vector
@router.post("/vectors/domain/files", response_model=dict)
async def add_files_to_domain_vector(files_create: AddFilesToDomainVectorCreate):
    """
    Add files to a domain's default vector store
    """
    try:
        print(f"Adding files to domain vector for domain: {files_create.domain_name}")
        print(f"Document URLs: {files_create.document_urls}")
        
        # Check if domain exists and get default vector ID
        domain_result = supabase.table("domains").select("*").eq("domain_name", files_create.domain_name).execute()
        print(f"Domain query result: {domain_result.data}")
        
        if not domain_result.data:
            raise HTTPException(status_code=404, detail=f"Domain {files_create.domain_name} not found")
        
        domain_data = domain_result.data[0]
        default_vector_id = domain_data.get("default_vector_id")
        
        if not default_vector_id:
            raise HTTPException(status_code=400, detail=f"Domain {files_create.domain_name} does not have a default vector ID")
        
        print(f"Default vector ID from domain record: {default_vector_id}")
        
        # Add the documents to the vector store
        result = await add_documents_to_domain_vector_store(client, default_vector_id, files_create.document_urls, files_create.domain_name)
        print(f"Added documents to vector store: {result}")
        
        # Update vector_stores table with the new file information
        file_ids = result.get("file_ids", [])
        batch_id = result.get("batch_id")
        
        try:
            # Check if entry exists for this vector_id
            existing_entry = supabase.table("vector_stores").select("*").eq("vector_id", default_vector_id).execute()
            print(f"Existing vector store entry check: {existing_entry.data}")
            
            if existing_entry.data:
                raise HTTPException(status_code=404, detail=f"Vector store with ID {default_vector_id} already exists")
            else:
                # Create new entry
                insert_data = {
                    "vector_id": default_vector_id,
                    "domain_name": files_create.domain_name,
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
        
        return {
            "domain_name": files_create.domain_name,
            "vector_id": default_vector_id,
            "vector_name": f"Default_{files_create.domain_name}",  # Following naming convention
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "message": f"Added {len(files_create.document_urls)} documents to default vector store for domain {files_create.domain_name}"
        }
    except Exception as e:
        print(f"Error adding files to domain vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 11. Get vector stores
@router.post("/vectors/stores", response_model=dict)
async def get_vector_stores(query: VectorStoreQuery):
    """
    Get vector stores based on domain, expert, client, and owner information
    
    Args:
        query: Query parameters including domain_name, expert_name, client_name, and owner
        
    Returns:
        List of vector stores matching the query parameters
    """
    try:
        print(f"Getting vector stores with query: {query}")
        
        # Start building the query
        db_query = supabase.table("vector_stores").select("*")
        
        # Determine owner based on provided parameters if not explicitly specified
        computed_owner = None
        if query.client_name:
            computed_owner = "client"
        elif query.expert_name:
            computed_owner = "expert"
        elif query.domain_name:
            computed_owner = "domain"
        else:
            # Return the results
            return {
                "status": "failure",
                "message": "specify domain, expert or client"
            }
            
        # Apply filters based on provided parameters
        if query.domain_name:
            db_query = db_query.eq("domain_name", query.domain_name)
            
        if query.expert_name:
            db_query = db_query.eq("expert_name", query.expert_name)
            
        if query.client_name:
            db_query = db_query.eq("client_name", query.client_name)
            
        if computed_owner:
            db_query = db_query.eq("owner", computed_owner)
        
        # Execute the query
        result = db_query.execute()
        print(f"Vector stores query result: {result.data}")
        if len(result.data) > 1:
            return {
                "status": "failure",
                "message": "Multiple vector stores found. Narrow your search"
            }
        # Return the results
        return {
            "status": "success",
            "vector_store_id": result.data[0]["vector_id"],
            "count": len(result.data)
        }
    except Exception as e:
        print(f"Error getting vector stores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 12. Update vector store
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
        print(f"Updating vector store {update_request.vector_id} with {len(update_request.document_urls)} new documents")
        
        # Query by vector_id directly from the vector_stores table
        vector_store_result = supabase.table("vector_stores").select("*").eq("vector_id", update_request.vector_id).execute()
        print(f"Vector store query result: {vector_store_result.data}")
        
        if not vector_store_result.data:
            raise HTTPException(status_code=404, detail=f"Vector store with ID {update_request.vector_id} not found")
        
        vector_store = vector_store_result.data[0]
        domain_name = vector_store["domain_name"]
        expert_name = vector_store["expert_name"]
        client_name = vector_store["client_name"]
        file_ids = vector_store["file_ids"]
        
        # Call edit_vector_store function to update the vector store
        result = await edit_vector_store(
            client, 
            update_request.vector_id, 
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
            update_result = supabase.table("vector_stores").update(update_data).eq("vector_id", update_request.vector_id).execute()
            print(f"Updated vector_stores entry: {update_result}")
        except Exception as e:
            print(f"Error updating vector_stores table: {str(e)}")
            # Continue anyway, the vector store was updated successfully
        
        return {
            "status": "success",
            "message": f"Added {len(new_file_ids)} documents to vector store {update_request.vector_id}",
            "vector_id": update_request.vector_id,
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

# 13. Add files to expert vector
@router.post("/vectors/expert/files", response_model=dict)
async def add_files_to_expert_vector(files_create: AddFilesToExpertVectorCreate):
    """
    Add files to an expert vector store, either the default one or a client-specific one
    """
    try:
        print(f"Adding files to expert vector for expert: {files_create.expert_name}")
        print(f"Use for specific client: {files_create.use_for_specific_client}")
        print(f"Document URLs: {files_create.document_urls}")
        
        vector_id = None
        vector_name = None
        
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
            vector_name = client_vector_result.get("vector_name")
            print(f"Using client-specific vector ID: {vector_id}")
        else:
            # Get or create the expert's preferred vector store and get its ID
            expert_vector_result = await update_expert_domain_vector(
                ExpertVectorCreate(
                    expert_name=files_create.expert_name
                )
            )
            vector_id = expert_vector_result.get("vector_id")
            vector_name = expert_vector_result.get("vector_name")
            print(f"Using expert's preferred vector ID: {vector_id}")
        
        # Add the documents to the vector store
        if not vector_id:
            raise HTTPException(status_code=500, detail="Failed to get or create vector store")
            
        # Check if expert exists and get domain
        expert_result = supabase.table("experts").select("*").eq("name", files_create.expert_name).execute()
        print(f"Expert query result: {expert_result.data}")
        
        if not expert_result.data:
            raise HTTPException(status_code=404, detail=f"Expert {files_create.expert_name} not found")
        
        expert_data = expert_result.data[0]
        domain_name = expert_data.get("domain")
        client_name = files_create.client_name if files_create.use_for_specific_client else None
        
        # Add the documents to the vector store
        result = await add_documents_to_expert_vector_store(client, vector_id, files_create.document_urls, domain_name, files_create.expert_name, client_name)
        print(f"Added documents to vector store: {result}")
        
        # Update vector_stores table with the new file information
        file_ids = result.get("file_ids", [])
        batch_id = result.get("batch_id")
        
        try:
            # Check if entry exists for this vector_id
            existing_entry = supabase.table("vector_stores").select("*").eq("vector_id", vector_id).execute()
            print(f"Existing vector store entry check: {existing_entry.data}")
            
            if existing_entry.data:
                raise HTTPException(status_code=404, detail=f"Vector store with ID {vector_id} already exists")
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
            "vector_name": vector_name,
            "file_ids": result.get("file_ids"),
            "batch_id": result.get("batch_id"),
            "status": result.get("status"),
            "message": f"Added {len(files_create.document_urls)} documents to vector store for expert {files_create.expert_name}"
        }
    except Exception as e:
        print(f"Error adding files to expert vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 14. Delete vector ID
@router.delete("/vectors/expert", response_model=dict)
async def delete_vector_id(delete_request: DeleteVectorIdRequest):
    """
    Delete an expert's preferred vector ID
    """
    try:
        # Find expert
        expert = supabase.table("experts").select("*").eq("name", delete_request.expert_name).execute()
        
        if not expert.data:
            raise HTTPException(status_code=404, detail=f"Expert {delete_request.expert_name} not found")
        
        expert_data = expert.data[0]
        
        # Check if the vector ID matches the expert's preferred vector ID
        if expert_data.get("preferred_vector_id") != delete_request.vector_id:
            raise HTTPException(status_code=400, detail="Vector ID does not match expert's preferred vector ID")
        
        # Delete the vector index
        await delete_vector_index(delete_request.vector_id)
        
        # Update expert's preferred vector ID to None
        supabase.table("experts").update({"preferred_vector_id": None}).eq("name", delete_request.expert_name).execute()
        
        return {"message": f"Vector ID {delete_request.vector_id} deleted for expert {delete_request.expert_name}"}
    except Exception as e:
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
        
        # Determine the owner based on the provided parameters
        owner = None
        if delete_request.domain_name and not delete_request.expert_name and not delete_request.client_name:
            owner = "domain"
        elif delete_request.expert_name and not delete_request.client_name:
            owner = "expert"
        elif delete_request.expert_name and delete_request.client_name:
            owner = "client"
        else:
            raise HTTPException(status_code=400, detail="Invalid combination of parameters. "
                                                     "Must provide either domain_name only, "
                                                     "expert_name only, or both expert_name and client_name.")
        
        print(f"[DEBUG] delete_vector_memory: Determined owner as '{owner}'")
        
        # Build the query to find the vector store
        query = supabase.table("vector_stores").select("*")
        
        if owner == "domain":
            query = query.eq("domain_name", delete_request.domain_name).eq("owner", "domain")
        elif owner == "expert":
            query = query.eq("expert_name", delete_request.expert_name).eq("owner", "expert")
        elif owner == "client":
            query = query.eq("expert_name", delete_request.expert_name)\
                        .eq("client_name", delete_request.client_name)\
                        .eq("owner", "client")
        
        # Execute the query
        result = query.execute()
        print(f"[DEBUG] delete_vector_memory: Query result: {result.data}")
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No vector store found for the given parameters")
        
        vector_store = result.data[0]
        vector_id = vector_store.get("vector_id")
        
        if not vector_id:
            raise HTTPException(status_code=404, detail="Vector ID not found in the record")
        
        # Perform additional checks based on owner
        if owner == "domain":
            # Check if there are experts associated with this domain
            experts_check = supabase.table("experts").select("name")\
                                  .eq("domain", delete_request.domain_name).execute()
            
            if experts_check.data and len(experts_check.data) > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete domain memory for '{delete_request.domain_name}' "
                           f"as there are {len(experts_check.data)} experts associated with it. "
                           f"Remove the experts first."
                )
        
        elif owner == "expert":
            # Check if there are clients associated with this expert
            clients_check = supabase.table("vector_stores").select("client_name")\
                                  .eq("expert_name", delete_request.expert_name)\
                                  .neq("client_name", None).execute()
            
            if clients_check.data and len(clients_check.data) > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot delete expert memory for '{delete_request.expert_name}' "
                           f"as there are {len(clients_check.data)} clients associated with it. "
                           f"Remove the client memories first."
                )
        
        # Delete the vector index
        print(f"[DEBUG] delete_vector_memory: Deleting vector store with ID: {vector_id}")
        await delete_vector_index(vector_id)
        
        # Update the appropriate tables based on owner
        if owner == "domain":
            # Update domains table to remove vector_id
            supabase.table("domains").update({"default_vector_id": None})\
                    .eq("domain_name", delete_request.domain_name).execute()
            print(f"[DEBUG] delete_vector_memory: Updated domains table for '{delete_request.domain_name}'")
            
        elif owner == "expert":
            # Update experts table to remove preferred_vector_id
            supabase.table("experts").update({"preferred_vector_id": None})\
                    .eq("name", delete_request.expert_name).execute()
            print(f"[DEBUG] delete_vector_memory: Updated experts table for '{delete_request.expert_name}'")
        
        # Delete the entry from vector_stores table
        supabase.table("vector_stores").delete().eq("vector_id", vector_id).execute()
        print(f"[DEBUG] delete_vector_memory: Deleted entry from vector_stores table")
        
        return {
            "message": f"Vector memory deleted successfully",
            "vector_id": vector_id,
            "owner": owner,
            "domain_name": delete_request.domain_name if owner == "domain" else vector_store.get("domain_name"),
            "expert_name": delete_request.expert_name if owner in ["expert", "client"] else None,
            "client_name": delete_request.client_name if owner == "client" else None
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[ERROR] delete_vector_memory: {str(e)}")
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
        
        # Apply filters based on the specified priority rules
        if client_name:
            # Case 1: Filter by client_name (and domain/expert if provided)
            print(f"Filtering documents by client_name: {client_name}")
            query = query.eq("client_name", client_name)
            
            if domain_value:
                query = query.eq("domain", domain_value)
                
            if created_by:
                query = query.eq("created_by", created_by)
                
        elif created_by:
            # Case 2: Filter by created_by with null client_name
            print(f"Filtering documents by created_by: {created_by} with null client_name")
            query = query.eq("created_by", created_by).is_("client_name", "null")
            
            if domain_value:
                query = query.eq("domain", domain_value)
                
        elif domain_value:
            # Case 3: Filter by domain with 'default' created_by and null client_name
            print(f"Filtering documents by domain: {domain_value} with default created_by and null client_name")
            query = query.eq("domain", domain_value).eq("created_by", "default").is_("client_name", "null")
            
        else:
            # If no filters provided, get all documents
            print("No filters provided. Not fetching any documents")
            # return null documents
            return []
        
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
    - domain: Use domain memory (domain's default_vector_id)
    - expert: Use expert memory (expert's preferred_vector_id)
    - client: Use client memory (client-specific vector store)
    """
    try:
        print(f"[DEBUG] query_expert: Received query for expert: {query_request.expert_name}")
        print(f"[DEBUG] query_expert: Query text: {query_request.query}")
        print(f"[DEBUG] query_expert: Memory type: {query_request.memory_type}")
        if query_request.client_name:
            print(f"[DEBUG] query_expert: Client name: {query_request.client_name}")
        
        # Get expert data
        try:
            expert = supabase.table("experts").select("*").eq("name", query_request.expert_name).execute()
            print(f"[DEBUG] query_expert: Expert data fetch result: {expert}")
        except Exception as e:
            print(f"[ERROR] query_expert: Failed to fetch expert data: {str(e)}")
            raise
        
        if not expert.data:
            print(f"[ERROR] query_expert: Expert {query_request.expert_name} not found")
            raise HTTPException(status_code=404, detail=f"Expert {query_request.expert_name} not found")
        
        expert_data = expert.data[0]
        print(f"[DEBUG] query_expert: Expert data: {expert_data}")
        
        # Determine which vector ID to use based on memory type
        vector_store_ids = None
        
        if query_request.memory_type == "llm":
            # Use LLM memory (no vector search)
            print(f"[DEBUG] query_expert: Using LLM memory (no vector search)")
            vector_store_ids = None
            
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
        
        # Query the vector index or LLM
        try:
            print(f"[DEBUG] query_expert: Querying with vector_store_ids: {vector_store_ids}")
            response = await query_vector_index(query_request.query, vector_store_ids, expert_data.get("context", ""))
            print(f"[DEBUG] query_expert: Query response type: {type(response)}")
            
            # Ensure response is properly formatted
            if isinstance(response, dict):
                # Convert any non-string text to string
                if 'text' in response and not isinstance(response['text'], str):
                    response['text'] = str(response['text'])
                citations = response.get('citations')
                citation_count = len(citations) if citations is not None and isinstance(citations, list) else 0
                print(f"[DEBUG] query_expert: Response contains {citation_count} citations")
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

