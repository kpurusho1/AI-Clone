from typing import Dict, List, Optional, Any
from pydantic import BaseModel, UUID4, Field

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

class DeleteVectorRequest(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    client_name: Optional[str] = None
    vector_id: Optional[str] = None
    delete_id: Optional[str] = None

class DomainCreate(BaseModel):
    domain_name: str

class ExpertVectorCreate(BaseModel):
    expert_name: str
    domain_name: str
    use_default_domain_vector: bool = False
    
class ExpertVectorUpdate(BaseModel):
    expert_name: str
    domain_name: str
    replace_vector: bool = False
    
class ExpertClientVectorCreate(BaseModel):
    expert_name: str
    client_name: str
    
class AddFilesToExpertVectorCreate(BaseModel):
    expert_name: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url
    use_for_specific_client: bool = False
    client_name: Optional[str] = None
    
class UpdateFilesToExpertVectorCreate(BaseModel):
    expert_name: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url
    use_for_specific_client: bool = False
    client_name: Optional[str] = None
    append_files: bool = True  # Whether to append files or replace them

class AddFilesToDomainVectorCreate(BaseModel):
    domain_name: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url

class UpdateFilesToDomainVectorCreate(BaseModel):
    domain_name: str
    document_urls: Dict[str, str]  # Dict of document_name: document_url
    append_files: bool = True  # Whether to append files or replace them

class UpdateVectorStoreRequest(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    document_urls: Dict[str, str]  # Dict of document_name: document_url

class VectorStoreQuery(BaseModel):
    domain_name: Optional[str] = None
    expert_name: Optional[str] = None
    client_name: Optional[str] = None
    owner: Optional[str] = None  # 'domain', 'expert', or 'client'

class DomainFilesConfigRequest(BaseModel):
    domain_name: str
    config_file_path: str  # Path to the config file containing document name and URL pairs

class UpdateDomainFilesConfigRequest(BaseModel):
    domain_name: str
    config_file_path: str  # Path to the config file containing document name and URL pairs
    append_files: bool = True  # Whether to append files or replace them

class PersonaGenerationRequest(BaseModel):
    qa_pairs: list  # List of dictionaries with question and answer pairs

class InitializeExpertMemoryRequest(BaseModel):
    expert_name: str
    domain_name: str
    qa_pairs: list  # List of dictionaries with question and answer pairs
    document_urls: dict  # Dictionary of document name to URL mappings

class UpdateExpertPersonaRequest(BaseModel):
    expert_name: str
    qa_pairs: list  # List of dictionaries with question and answer pairs

# Models for OpenAI Assistant API integration
class CreateAssistantRequest(BaseModel):
    expert_name: str
    memory_type: str = "expert"  # Options: "llm", "domain", "expert", "client"
    client_name: Optional[str] = None
    model: str = "gpt-4o"

class CreateAssistantResponse(BaseModel):
    assistant_id: str
    expert_name: str
    memory_type: str
    client_name: Optional[str] = None

class CreateThreadRequest(BaseModel):
    expert_name: str
    memory_type: str = "expert"
    client_name: Optional[str] = None

class CreateThreadResponse(BaseModel):
    thread_id: str
    expert_name: str
    memory_type: str
    client_name: Optional[str] = None

class AddMessageRequest(BaseModel):
    thread_id: str
    content: str
    role: str = "user"

class AddMessageResponse(BaseModel):
    message_id: str
    thread_id: str
    content: str
    role: str

class RunThreadRequest(BaseModel):
    thread_id: str
    assistant_id: str

class RunThreadResponse(BaseModel):
    run_id: str
    thread_id: str
    assistant_id: str
    status: str

class GetRunStatusRequest(BaseModel):
    thread_id: str
    run_id: str

class GetRunStatusResponse(BaseModel):
    run_id: str
    thread_id: str
    status: str
    response: Optional[str] = None

class GetThreadMessagesRequest(BaseModel):
    thread_id: str
    limit: int = 10

class MessageContent(BaseModel):
    type: str
    text: str

class ThreadMessage(BaseModel):
    id: str
    role: str
    content: List[MessageContent]

class GetThreadMessagesResponse(BaseModel):
    messages: List[ThreadMessage]

class YouTubeTranscriptRequest(BaseModel):
    video_url: str

