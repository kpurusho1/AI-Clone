# AI Clone API Documentation

This document provides comprehensive documentation for the AI Clone API, which enables the creation and management of AI experts with domain-specific knowledge using OpenAI's Assistant API and vector stores.

## Table of Contents
1. [Introduction](#introduction)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [API Models](#api-models)
5. [API Endpoints](#api-endpoints)
   - [Domain Management](#domain-management)
   - [Expert Management](#expert-management)
   - [Vector Store Management](#vector-store-management)
   - [Document Management](#document-management)
   - [Memory Management](#memory-management)
   - [OpenAI Assistant Integration](#openai-assistant-integration)
   - [Query and Chat](#query-and-chat)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

## Introduction

The AI Clone API allows you to create and manage AI experts with domain-specific knowledge. The system uses OpenAI's Assistant API and vector stores to provide contextual responses based on the expert's knowledge domain.

Key concepts:
- **Domains**: Knowledge areas that contain documents and information
- **Experts**: Personas with specific knowledge in domains
- **Vector Stores**: Storage for document embeddings used for retrieval
- **Memory Types**: Different levels of knowledge access (llm, domain, expert, client)

## Base URL

```
http://localhost:8000/api
```

## Authentication

Authentication details should be provided here. The API currently uses Supabase for database operations.

## API Models

### Core Models

#### Expert
```json
{
  "name": "string",
  "domain": "string",
  "context": "string"
}
```

#### ExpertCreate
```json
{
  "name": "string",
  "domain": "string",
  "context": "string",
  "use_default_domain_knowledge": true
}
```

#### ExpertResponse
```json
{
  "id": "uuid",
  "name": "string",
  "domain": "string",
  "context": "string"
}
```

#### DomainCreate
```json
{
  "domain_name": "string"
}
```

### Vector Store Models

#### UpdateVectorStoreRequest
```json
{
  "domain_name": "string (optional)",
  "expert_name": "string (optional)",
  "document_urls": {
    "document_name1": "url1",
    "document_name2": "url2"
  }
}
```

#### VectorStoreQuery
```json
{
  "domain_name": "string (optional)",
  "expert_name": "string (optional)",
  "client_name": "string (optional)",
  "owner": "string (optional)" // 'domain', 'expert', or 'client'
}
```

### Document Models

#### AddFilesToDomainVectorCreate
```json
{
  "domain_name": "string",
  "document_urls": {
    "document_name1": "url1",
    "document_name2": "url2"
  }
}
```

#### UpdateFilesToDomainVectorCreate
```json
{
  "domain_name": "string",
  "document_urls": {
    "document_name1": "url1",
    "document_name2": "url2"
  },
  "append_files": true
}
```

#### AddFilesToExpertVectorCreate
```json
{
  "expert_name": "string",
  "document_urls": {
    "document_name1": "url1",
    "document_name2": "url2"
  },
  "use_for_specific_client": false,
  "client_name": "string (optional)"
}
```

#### UpdateFilesToExpertVectorCreate
```json
{
  "expert_name": "string",
  "document_urls": {
    "document_name1": "url1",
    "document_name2": "url2"
  },
  "use_for_specific_client": false,
  "client_name": "string (optional)",
  "append_files": true
}
```

### Query Models

#### QueryRequest
```json
{
  "query": "string",
  "expert_name": "string",
  "memory_type": "string", // Options: "llm", "domain", "expert", "client"
  "client_name": "string (optional)"
}
```

#### QueryResponse
```json
{
  "response": {
    "text": "string",
    "citations": [
      {
        "quote": "string",
        "source": "string"
      }
    ]
  }
}
```

### OpenAI Assistant Models

#### CreateAssistantRequest
```json
{
  "expert_name": "string",
  "memory_type": "string", // Options: "llm", "domain", "expert", "client"
  "client_name": "string (optional)",
  "model": "string" // Default: "gpt-4o"
}
```

#### CreateThreadRequest
```json
{
  "expert_name": "string",
  "memory_type": "string", // Options: "llm", "domain", "expert", "client"
  "client_name": "string (optional)"
}
```

#### AddMessageRequest
```json
{
  "thread_id": "string",
  "content": "string",
  "role": "string" // Default: "user"
}
```

#### RunThreadRequest
```json
{
  "thread_id": "string",
  "assistant_id": "string"
}
```

## API Endpoints

### Domain Management

#### Create Domain
```
POST /domains
```
Creates a new domain with a custom name and initializes a default vector store.

**Request Body**: `DomainCreate`

**Response**:
```json
{
  "domain_name": "string",
  "vector_id": "string",
  "message": "string"
}
```

#### Get All Domains
```
GET /domains
```
Returns a list of all domains.

**Response**:
```json
[
  {
    "domain_name": "string",
    "expert_names": ["string"]
  }
]
```

#### Get Expert Domain
```
GET /experts/{expert_name}/domain
```
Gets the domain name for a specific expert.

**Response**:
```json
{
  "domain_name": "string"
}
```

### Expert Management

#### Create Expert
```
POST /experts
```
Creates a new expert with domain and context.

**Request Body**: `ExpertCreate`

**Response**:
```json
{
  "id": "uuid",
  "name": "string",
  "domain": "string",
  "context": "string"
}
```

#### Get All Experts
```
GET /experts
```
Returns a list of all experts.

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "string",
    "domain": "string",
    "context": "string"
  }
]
```

#### Get Expert Context
```
GET /experts/{expert_name}/context
```
Gets the context for a specific expert.

**Response**:
```json
{
  "context": "string"
}
```

#### Update Expert Context
```
PUT /experts/context
```
Updates an expert's context.

**Request Body**: `ExpertUpdate`

**Response**:
```json
{
  "name": "string",
  "context": "string",
  "message": "string"
}
```

#### Update Expert Persona
```
POST /experts/persona/update
PUT /experts/persona/update
```
Generates a persona from QA data and updates the expert's context.

**Request Body**: `UpdateExpertPersonaRequest`

**Response**:
```json
{
  "expert_name": "string",
  "persona": "string",
  "message": "string"
}
```

### Vector Store Management

#### Create Expert Domain Vector
```
POST /vectors/expert-domain
```
Creates or updates vector IDs for an expert based on domain.

**Request Body**: `ExpertVectorCreate`

**Response**:
```json
{
  "expert_name": "string",
  "domain_name": "string",
  "vector_id": "string",
  "message": "string"
}
```

#### Update Expert Domain Vector
```
POST /vectors/expert-domain/update
```
Updates the preferred vector store ID for an expert.

**Request Body**: `ExpertVectorUpdate`

**Response**:
```json
{
  "expert_name": "string",
  "domain_name": "string",
  "vector_id": "string",
  "message": "string"
}
```

#### Create Expert Client Vector
```
POST /vectors/expert-client
```
Creates a vector store for an expert with a specific client.

**Request Body**: `ExpertClientVectorCreate`

**Response**:
```json
{
  "expert_name": "string",
  "client_name": "string",
  "vector_id": "string",
  "message": "string"
}
```

#### Update Vector Store
```
POST /vectors/update
```
Updates an existing vector store by adding new documents.

**Request Body**: `UpdateVectorStoreRequest`

**Response**:
```json
{
  "status": "string",
  "message": "string",
  "vector_id": "string",
  "domain_name": "string",
  "expert_name": "string (optional)",
  "client_name": "string (optional)",
  "new_file_ids": ["string"],
  "all_file_ids": ["string"],
  "batch_id": "string"
}
```

#### Delete Vector Memory
```
DELETE /vectors/memory
```
Deletes a vector memory based on domain, expert, and/or client name.

**Request Body**: `DeleteVectorRequest`

**Response**:
```json
{
  "message": "string",
  "deleted_vector_id": "string"
}
```

### Document Management

#### Add Files to Domain Vector
```
POST /vectors/domain/files
```
Adds files to a domain's default vector store.

**Request Body**: `AddFilesToDomainVectorCreate`

**Response**:
```json
{
  "domain_name": "string",
  "vector_id": "string",
  "file_ids": ["string"],
  "batch_id": "string",
  "status": "string",
  "message": "string"
}
```

#### Update Files to Domain Vector
```
POST /vectors/domain/files/update
```
Updates files in a domain's default vector store.

**Request Body**: `UpdateFilesToDomainVectorCreate`

**Response**:
```json
{
  "domain_name": "string",
  "vector_id": "string",
  "file_ids": ["string"],
  "batch_id": "string",
  "status": "string",
  "message": "string"
}
```

#### Add Files to Domain Vector from Config
```
POST /vectors/domain/files/config
```
Adds files to a domain's default vector store from a configuration file.

**Request Body**: `DomainFilesConfigRequest`

**Response**:
```json
{
  "domain_name": "string",
  "vector_id": "string",
  "file_ids": ["string"],
  "batch_id": "string",
  "status": "string",
  "document_count": "integer",
  "message": "string"
}
```

#### Add Files to Expert Vector
```
POST /vectors/expert/files
```
Adds files to an expert vector store.

**Request Body**: `AddFilesToExpertVectorCreate`

**Response**:
```json
{
  "expert_name": "string",
  "client_name": "string (optional)",
  "vector_id": "string",
  "file_ids": ["string"],
  "batch_id": "string",
  "status": "string",
  "message": "string"
}
```

#### Update Files to Expert Vector
```
PUT /vectors/expert/files
```
Updates files in an expert vector store.

**Request Body**: `UpdateFilesToExpertVectorCreate`

**Response**:
```json
{
  "expert_name": "string",
  "client_name": "string (optional)",
  "vector_id": "string",
  "file_ids": ["string"],
  "all_file_ids": ["string"],
  "batch_id": "string",
  "status": "string",
  "append_mode": "boolean",
  "message": "string"
}
```

#### Get Documents
```
GET /documents
```
Gets documents filtered by domain, expert, and client.

**Query Parameters**:
- `domain`: string (optional)
- `created_by`: string (optional)
- `client_name`: string (optional)

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "string",
    "document_link": "string",
    "domain_name": "string",
    "created_by": "string",
    "client_name": "string (optional)",
    "file_id": "string"
  }
]
```

### Memory Management

#### Initialize Expert Memory
```
POST /memory/expert/initialize
```
Initializes an expert's memory by creating domain, adding files, generating persona, and creating expert.

**Request Body**: `InitializeExpertMemoryRequest`

**Response**:
```json
{
  "expert_name": "string",
  "domain_name": "string",
  "status": "string",
  "message": "string",
  "results": {
    "domain": {},
    "domain_files": {},
    "persona": {},
    "expert": {},
    "expert_files": {}
  }
}
```

#### Generate Persona from QA Data
```
POST /persona/generate
```
Generates a persona summary from QA data.

**Request Body**: `PersonaGenerationRequest`

**Response**:
```json
{
  "persona": "string",
  "qa_pairs_count": "integer"
}
```

### OpenAI Assistant Integration

#### Create Assistant
```
POST /create_assistant
```
Creates an OpenAI Assistant for a specific expert and memory type.

**Request Body**: `CreateAssistantRequest`

**Response**: `CreateAssistantResponse`

#### Create Thread
```
POST /create_thread
```
Creates a new thread for conversation.

**Request Body**: `CreateThreadRequest`

**Response**: `CreateThreadResponse`

#### Add Message
```
POST /add_message
```
Adds a message to a thread.

**Request Body**: `AddMessageRequest`

**Response**: `AddMessageResponse`

#### Run Thread
```
POST /run_thread
```
Runs a thread with an assistant.

**Request Body**: `RunThreadRequest`

**Response**: `RunThreadResponse`

#### Get Run Status
```
POST /get_run_status
```
Gets the status of a run.

**Request Body**: `GetRunStatusRequest`

**Response**: `GetRunStatusResponse`

#### Get Thread Messages
```
POST /get_thread_messages
```
Gets messages from a thread.

**Request Body**: `GetThreadMessagesRequest`

**Response**: `GetThreadMessagesResponse`

### Query and Chat

#### Query Expert
```
POST /query
```
Queries an expert using their vector index based on the specified memory type.

**Request Body**: `QueryRequest`

**Response**: `QueryResponse`

#### Query Expert with Assistant
```
POST /query_expert_with_assistant
```
Queries an expert using the OpenAI Assistant API.

**Request Body**: `QueryRequest`

**Response**:
```json
{
  "response": "string",
  "thread_id": "string",
  "assistant_id": "string"
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with an error message:

```json
{
  "detail": "Error message"
}
```

## Examples

### Creating a Domain and Expert

1. Create a domain:
```
POST /domains
{
  "domain_name": "AI Education"
}
```

2. Create an expert:
```
POST /experts
{
  "name": "AI Expert",
  "domain": "AI Education",
  "context": "Expert in artificial intelligence education",
  "use_default_domain_knowledge": true
}
```

3. Add documents to domain:
```
POST /domain_files
{
  "domain_name": "AI Education",
  "document_urls": {
    "AI Basics": "https://example.com/ai-basics.pdf",
    "Machine Learning": "https://example.com/ml-intro.pdf"
  }
}
```

4. Add documents to expert:
```
POST /expert_files
{
  "expert_name": "AI Expert",
  "document_urls": {
    "Teaching AI": "https://example.com/teaching-ai.pdf",
    "AI Curriculum": "https://example.com/ai-curriculum.pdf"
  }
}
```

5. Query the expert:
```
POST /query
{
  "query": "What are the best practices for teaching AI?",
  "expert_name": "AI Expert",
  "memory_type": "expert"
}
```

### Using the OpenAI Assistant API

1. Create an assistant:
```
POST /assistant
{
  "expert_name": "AI Expert",
  "memory_type": "expert",
  "model": "gpt-4o"
}
```

2. Create a thread:
```
POST /thread
{
  "expert_name": "AI Expert",
  "memory_type": "expert"
}
```

3. Add a message:
```
POST /add_message
{
  "thread_id": "thread_abc123",
  "content": "What are the best practices for teaching AI?"
}
```

4. Run the thread:
```
POST /run_thread
{
  "thread_id": "thread_abc123",
  "assistant_id": "asst_abc123"
}
```

5. Get the run status:
```
POST /get_run_status
{
  "thread_id": "thread_abc123",
  "run_id": "run_abc123"
}
```

6. Get thread messages:
```
POST /get_thread_messages
{
  "thread_id": "thread_abc123",
  "limit": 10
}
```
