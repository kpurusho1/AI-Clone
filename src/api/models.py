from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class PatientCreate(BaseModel):
    org_name: str
    domain_name: str
    expert_name: str
    client_name: str
    org_client_id: int
    client_data_jsonb: str
    consultation_id: str
    created_time: str = Field(..., description="Timestamp with timezone in ISO 8601 format (e.g., '2025-09-07T13:27:42.809634+00:00')")
    org_data_jsonb: Dict[str, Any] = {}
    document_urls: Dict[str, str] = {}
    pdf_documents: Dict[str, str] = {}
    other_doc: Dict[str, Any] = {}

class ClientCreate(BaseModel):
    org_client_id: int
    org_id: UUID
    expert_id: UUID
    client_id: Optional[UUID] = None
    client_name: str
    client_data_jsonb: Dict[str, Any]  # JSON data for the client
    consultation_id: str
    created_time: str = Field(..., description="Timestamp with timezone in ISO 8601 format (e.g., '2025-09-07T13:27:42.809634+00:00')")

class CreateVector(BaseModel):
    memory_type: str = "expert"  # Options: "llm", "organization", "domain", "expert", "client", "myclient"
    org_id: UUID
    expert_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    domain_name: Optional[str] = None
    org_client_id: Optional[int] = None
    
class DeleteVectorRequest(BaseModel):
    memory_type: str = "expert"  # Options: "llm", "organization", "domain", "expert", "client", "myclient"
    domain_name: Optional[str] = None
    org_client_id: Optional[int] = None
    org_name: str
    expert_name: Optional[str] = None
    vector_id: Optional[str] = None
    delete_id: Optional[str] = None

class DomainBatchCreate(BaseModel):
    org_id: UUID
    domains: List[Dict[str, Any]]  # List of domain entries with domain_name, document_urls, pdf_documents, etc.

class DomainCreate(BaseModel):
    org_id: UUID
    domain_name: str

class DomainFilesRequest(BaseModel):
    org_id: UUID
    domain_name: Optional[List[str]] = None

class Expert(BaseModel):
    name: str
    domains: List[str]
    context: str
    org_id: UUID
    expert_id: Optional[UUID] = None

class ExpertUpdate(BaseModel):
    expert_id: UUID
    context: str

class OrgCreate(BaseModel):
    org_name: str
    org_data_jsonb: Dict[str, Any] = {} # JSON data for the client
    
class FilesConfigRequest(BaseModel):
    memory_type: str = "expert"  # Options: "llm", "organization", "domain", "expert", "client", "myclient"
    vector_id: str
    config_file_path: Optional[str] = None  # Path to the config file containing document name and URL pairs
    domain_id: Optional[UUID] = None
    domain_name: Optional[str] = None
    expert_id: Optional[UUID] = None
    org_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    document_urls: Dict[str, str] = {}  # Dict of document_name: document_url
    pdf_documents: Dict[str, str] = {}  # Dict of document_name: document_url
    other_doc: Dict[str, Any] = {}  # Dict of document_name: document_url

class InitializeExpertMemoryRequest(BaseModel):
    org_id: UUID
    expert_name: str
    domain_name: List[str]
    qa_pairs: list  # List of dictionaries with question and answer pairs
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Dict[str, str] = {}  # Dictionary of document name to file_path
    other_doc: Dict[str, Any] = {}  # Dictionary of document name to file_path

class InitializeMyClientMemoryRequest(ClientCreate):
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Dict[str, str] = {}  # Dictionary of document name to file_path
    other_doc: Dict[str, Any] = {}  # Dictionary of document name to file_path

class InitializeOrgMemoryRequest(OrgCreate):
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Dict[str, str] = {}  # Dictionary of document name to file_path
    other_doc: Dict[str, Any] = {}  # Dictionary of document name to file_path

class JsonStringRequest(BaseModel):
    json_string: str

class PersonaGenerationRequest(BaseModel):
    qa_pairs: list  # List of dictionaries with question and answer pairs

class QueryRequest(BaseModel):
    query: str
    memory_type: str = "myclient"  # Options: "llm", "organization", "domain", "expert", "client", "myclient"
    org_name: str
    domain_name: Optional[str] = None
    expert_id: Optional[UUID] = None
    org_client_id: Optional[int] = None
    thread_id: Optional[str] = None
    expert_name: Optional[str] = None

class UpdateExpertPersonaRequest(BaseModel):
    expert_id: UUID
    qa_pairs: list  # List of dictionaries with question and answer pairs

class UpdateRequest(BaseModel):
    memory_type: str = "myclient"  # Options: "llm", "organization", "domain", "expert", "client", "myclient"
    org_name: str
    domain_name: Optional[str] = None
    expert_name: str
    org_client_id: Optional[int] = None
    qa_pairs: Optional[list] = []  # List of dictionaries with question and answer pairs (optional)
    document_urls: Dict[str, str] = {}  # Dictionary of document name to URL mappings
    pdf_documents: Optional[Dict[str, str]] = None  # Dictionary of document name to file_path
    other_doc: Optional[Dict[str, Any]] = None  # Dictionary of document name to file_path

class UpdateVectorStoreRequest(CreateVector):
    document_urls: Dict[str, str] = {}  # Dict of document_name: document_url
    pdf_documents: Optional[Dict[str, str]] = None  # Dictionary of document name to file_path
    other_doc: Optional[Dict[str, Any]] = None  # Dictionary of document name to file_path  

