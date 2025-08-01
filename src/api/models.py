from typing import Dict, List, Optional
from pydantic import BaseModel, UUID4

class Expert(BaseModel):
    name: str
    domain: str
    context: str
    default_vector_id: Optional[str] = None
    preferred_vector_id: Optional[str] = None

class ExpertCreate(Expert):
    use_default_domain_knowledge: bool = True

class ExpertResponse(Expert):
    id: UUID4

class ExpertUpdate(BaseModel):
    name: str
    context: str

class QueryRequest(BaseModel):
    query: str
    expert_name: str
    memory_type: str = "expert"  # Options: "llm", "domain", "expert", "client"
    client_name: Optional[str] = None

class Citation(BaseModel):
    quote: str
    source: str

class QueryResponseContent(BaseModel):
    text: str
    citations: Optional[List[Citation]] = None


class QueryResponse(BaseModel):
    response: QueryResponseContent

class DeleteVectorIdRequest(BaseModel):
    expert_name: str
    vector_id: str
    
class DeleteVectorRequest(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    client_name: Optional[str] = None

class DomainCreate(BaseModel):
    domain_name: str

class ExpertVectorCreate(BaseModel):
    expert_name: str
    use_default_domain_vector: bool = False
    
class ExpertClientVectorCreate(BaseModel):
    expert_name: str
    client_name: str
    
class AddFilesToExpertVectorCreate(BaseModel):
    expert_name: str
    use_for_specific_client: bool = False
    client_name: Optional[str] = None
    document_urls: Dict[str, str]  # Dict of document_name: document_url
    
class AddFilesToDomainVectorCreate(BaseModel):
    domain_name: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url

class UpdateVectorStoreRequest(BaseModel):
    vector_id: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url

class VectorStoreQuery(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    client_name: Optional[str] = None
    owner: Optional[str] = None  # 'domain', 'expert', or 'client'

