from typing import Dict, Optional
from pydantic import BaseModel, UUID4

class AddFilesToExpertVectorCreate(BaseModel):
    expert_name: str
    document_urls: Dict[str, str] = {}  # Dict of document_name: document_url
    pdf_documents: Dict[str, bytes] = {}  # Dict of document_name: document_content_bytes
    client_name: Optional[str] = None

class DeleteVectorRequest(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    client_name: Optional[str] = None
    vector_id: Optional[str] = None
    delete_id: Optional[str] = None

class DomainCreate(BaseModel):
    domain_name: str

class DomainFilesConfigRequest(BaseModel):
    domain_name: str
    config_file_path: str  # Path to the config file containing document name and URL pairs

class Expert(BaseModel):
    name: str
    domain: str
    context: str

class ExpertCreate(Expert):
    use_default_domain_knowledge: bool = True

class ExpertResponse(Expert):
    id: UUID4

class ExpertUpdate(BaseModel):
    name: str
    context: str

class ExpertVectorCreate(BaseModel):
    expert_name: str
    domain_name: str
    use_default_domain_vector: bool = False

class InitializeExpertMemoryRequest(BaseModel):
    expert_name: str
    domain_name: str
    qa_pairs: list  # List of dictionaries with question and answer pairs
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Dict[str, bytes] = {}  # Dictionary of document name to PDF content bytes

class PersonaGenerationRequest(BaseModel):
    qa_pairs: list  # List of dictionaries with question and answer pairs

class QueryRequest(BaseModel):
    query: str
    expert_name: str
    memory_type: str = "expert"  # Options: "llm", "domain", "expert", "client"
    client_name: Optional[str] = None
    thread_id: Optional[str] = None

class UpdateExpertPersonaRequest(BaseModel):
    expert_name: str
    qa_pairs: list  # List of dictionaries with question and answer pairs

class UpdateExpertRequest(BaseModel):
    expert_name: str
    domain_name: str
    qa_pairs: Optional[list] = []  # List of dictionaries with question and answer pairs (optional)
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Dict[str, bytes] = {}  # Dictionary of document name to PDF content bytes

class UpdateVectorStoreRequest(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    document_urls: Dict[str, str] = {}  # Dict of document_name: document_url
    pdf_documents: Dict[str, bytes] = {}  # Dictionary of document name to PDF content bytes
