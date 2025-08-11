import streamlit as st
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL - change this to your actual API URL when deployed
API_BASE_URL = "http://localhost:8000/api"

# Set page configuration
st.set_page_config(
    page_title="AI Clone - RAG Solution",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("AI Clone")
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Create domain", "Create domain memory", "Update domain memory", "Create Expert", "Update Expert Context", 
    "Create expert memory", "Update expert memory", "Query Expert", "Query Expert using Threads", "Delete Memory"]
)

# Helper functions for API calls
def create_expert(name, domain, context, use_default_domain_knowledge=True):
    try:
        print(f"[UI DEBUG] create_expert: Creating expert '{name}' in domain '{domain}'")
        print(f"[UI DEBUG] create_expert: Use default domain knowledge: {use_default_domain_knowledge}")
        
        request_data = {
            "name": name,
            "domain": domain,
            "context": context,
            "use_default_domain_knowledge": use_default_domain_knowledge
        }
        print(f"[UI DEBUG] create_expert: Request data: {request_data}")
        print(f"[UI DEBUG] create_expert: Request URL: {API_BASE_URL}/experts")
        
        response = requests.post(
            f"{API_BASE_URL}/experts",
            json=request_data
        )
        
        print(f"[UI DEBUG] create_expert: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] create_expert: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] create_expert: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] create_expert: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] create_expert: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def get_expert_context(name):
    try:
        response = requests.get(f"{API_BASE_URL}/experts/{name}/context")
        if response.status_code == 200:
            return response.json().get("context", ""), response.status_code
        return "", response.status_code
    except Exception as e:
        return "", 500

def update_expert_context(name, context):
    try:
        response = requests.put(
            f"{API_BASE_URL}/experts/context",
            json={
                "name": name,
                "context": context
            }
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_experts():
    try:
        response = requests.get(f"{API_BASE_URL}/experts")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def get_domains():
    # Get domains from the API
    try:
        response = requests.get(f"{API_BASE_URL}/domains")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def get_domain_names():
    # Return domain names only
    domains = get_domains()
    return [domain["domain_name"] for domain in domains] if domains else []

def get_domain_vector_id(domain_name):
    try:
        response = requests.get(f"{API_BASE_URL}/domains/{domain_name}/vector_id")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting domain vector ID: {e}")
        return None

def get_expert_vector_id(expert_name):
    try:
        response = requests.get(f"{API_BASE_URL}/experts/{expert_name}/vector_id")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting expert vector ID: {e}")
        return None

def get_expert_client_vector_id(expert_name, client_name):
    try:
        response = requests.get(f"{API_BASE_URL}/vectors/expert/{expert_name}/client/{client_name}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting expert-client vector ID: {e}")
        return None

def get_client_names_for_expert(expert_name, domain=None):
    try:
        # Build the URL based on whether domain is provided
        url = f"{API_BASE_URL}/experts/{expert_name}/clients"
        if domain:
            url += f"?domain={domain}"
            
        response = requests.get(url)
        if response.status_code == 200:
            # Add "No specific client" as the first option
            return ["No specific client"] + response.json()
        return ["No specific client"]
    except Exception as e:
        print(f"Error getting client names for expert: {e}")
        return ["No specific client"]

# returns document record from documents table
def get_documents_by_domain(domain):
    try:
        response = requests.get(f"{API_BASE_URL}/documents?domain={domain}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

# returns document record from documents table
def get_documents_by_expert(expert_name, domain=None, client_name=None):
    try:
        url = f"{API_BASE_URL}/documents?created_by={expert_name}"
        if domain:
            url += f"&domain={domain}"
        if client_name and client_name != "No specific client":
            url += f"&client_name={client_name}"
            
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error getting documents by expert: {e}")
        return []

def create_domain(domain_name):
    try:
        print(f"[UI DEBUG] create_domain: Creating domain '{domain_name}'")
        
        request_data = {
            "domain_name": domain_name
        }
        print(f"[UI DEBUG] create_domain: Request data: {request_data}")
        print(f"[UI DEBUG] create_domain: Request URL: {API_BASE_URL}/domains")
        
        response = requests.post(
            f"{API_BASE_URL}/domains",
            json=request_data
        )
        
        print(f"[UI DEBUG] create_domain: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] create_domain: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] create_domain: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] create_domain: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] create_domain: Request failed: {str(e)}")
        return {"error": str(e)}, 500
        
def add_files_to_domain_vector(domain_name, document_urls):
    try:
        print(f"[UI DEBUG] add_files_to_domain_vector: Adding files to domain '{domain_name}'")
        print(f"[UI DEBUG] add_files_to_domain_vector: Document URLs: {document_urls}")
        
        # document_urls is now a dictionary of document_name: document_url
        data = {
            "domain_name": domain_name,
            "document_urls": document_urls
        }
        
        print(f"[UI DEBUG] add_files_to_domain_vector: Request data: {data}")
        print(f"[UI DEBUG] add_files_to_domain_vector: Request URL: {API_BASE_URL}/vectors/domain/files")
        
        response = requests.post(
            f"{API_BASE_URL}/vectors/domain/files",
            json=data
        )
        
        print(f"[UI DEBUG] add_files_to_domain_vector: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] add_files_to_domain_vector: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] add_files_to_domain_vector: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] add_files_to_domain_vector: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] add_files_to_domain_vector: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def create_expert_vector(expert_name, use_for_specific_client=False, client_name=None):
    try:
        print(f"[UI DEBUG] create_expert_vector: Creating vector for expert '{expert_name}'")
        print(f"[UI DEBUG] create_expert_vector: Use for specific client: {use_for_specific_client}")
        print(f"[UI DEBUG] create_expert_vector: Client name: {client_name}")
        
        # If creating client-specific memory, call the expert-client endpoint
        if use_for_specific_client and client_name:
            print(f"[UI DEBUG] create_expert_vector: Creating client-specific vector store")
            
            data = {
                "expert_name": expert_name,
                "client_name": client_name
            }
            
            print(f"[UI DEBUG] create_expert_vector: Request data: {data}")
            print(f"[UI DEBUG] create_expert_vector: Request URL: {API_BASE_URL}/vectors/expert-client")
            
            response = requests.post(
                f"{API_BASE_URL}/vectors/expert-client",
                json=data
            )
        else:
            # Otherwise, call the expert-domain endpoint to use the expert's preferred vector ID
            print(f"[UI DEBUG] create_expert_vector: Creating expert-only vector store")
            
            data = {
                "expert_name": expert_name
            }
            
            print(f"[UI DEBUG] create_expert_vector: Request data: {data}")
            print(f"[UI DEBUG] create_expert_vector: Request URL: {API_BASE_URL}/vectors/expert-domain/update")
            
            response = requests.post(
                f"{API_BASE_URL}/vectors/expert-domain/update",
                json=data
            )
        
        print(f"[UI DEBUG] create_expert_vector: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] create_expert_vector: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] create_expert_vector: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] create_expert_vector: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] create_expert_vector: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def add_files_to_expert_vector(expert_name, document_urls, use_for_specific_client=False, client_name=None):
    try:
        print(f"[UI DEBUG] add_files_to_expert_vector: Adding files for expert '{expert_name}'")
        print(f"[UI DEBUG] add_files_to_expert_vector: Document URLs: {document_urls}")
        print(f"[UI DEBUG] add_files_to_expert_vector: Use for specific client: {use_for_specific_client}")
        print(f"[UI DEBUG] add_files_to_expert_vector: Client name: {client_name}")
        
        # document_urls is now a dictionary of document_name: document_url
        request_data = {
            "expert_name": expert_name,
            "use_for_specific_client": use_for_specific_client,
            "document_urls": document_urls
        }
        
        if use_for_specific_client and client_name:
            request_data["client_name"] = client_name
        
        print(f"[UI DEBUG] add_files_to_expert_vector: Request data: {request_data}")
        print(f"[UI DEBUG] add_files_to_expert_vector: Request URL: {API_BASE_URL}/vectors/expert/files")
        
        response = requests.post(
            f"{API_BASE_URL}/vectors/expert/files",
            json=request_data
        )
        
        print(f"[UI DEBUG] add_files_to_expert_vector: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] add_files_to_expert_vector: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] add_files_to_expert_vector: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] add_files_to_expert_vector: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] add_files_to_expert_vector: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def update_vector_store(vector_id, document_urls):
    try:
        print(f"[UI DEBUG] update_vector_store: Updating vector store '{vector_id}'")
        print(f"[UI DEBUG] update_vector_store: Document URLs: {document_urls}")
        
        # document_urls is now a dictionary of document_name: document_url
        data = {
            "vector_id": vector_id,
            "document_urls": document_urls
        }
        
        print(f"[UI DEBUG] update_vector_store: Request data: {data}")
        print(f"[UI DEBUG] update_vector_store: Request URL: {API_BASE_URL}/vectors/update")
        
        response = requests.post(
            f"{API_BASE_URL}/vectors/update",
            json=data
        )
        
        print(f"[UI DEBUG] update_vector_store: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] update_vector_store: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] update_vector_store: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] update_vector_store: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] update_vector_store: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def query_expert(expert_name, query, memory_type="expert", client_name=None):
    try:
        print(f"[UI DEBUG] query_expert: Sending query to API for expert '{expert_name}'")
        print(f"[UI DEBUG] query_expert: Query text: '{query}'")
        print(f"[UI DEBUG] query_expert: Memory type: '{memory_type}'")
        if client_name:
            print(f"[UI DEBUG] query_expert: Client name: '{client_name}'")
        print(f"[UI DEBUG] query_expert: Request URL: {API_BASE_URL}/query")
        
        request_data = {
            "expert_name": expert_name,
            "query": query,
            "memory_type": memory_type
        }
        
        if client_name and memory_type == "client":
            request_data["client_name"] = client_name
        
        print(f"[UI DEBUG] query_expert: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=request_data
        )
        
        print(f"[UI DEBUG] query_expert: Response status code: {response.status_code}")
        print(f"[UI DEBUG] query_expert: Response headers: {response.headers}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] query_expert: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] query_expert: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] query_expert: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] query_expert: Request failed: {str(e)}")
        return {"error": str(e)}, 500
        
def delete_vector_memory(domain_name=None, expert_name=None, client_name=None):
    try:
        print(f"[UI DEBUG] delete_vector_memory: Deleting memory with domain={domain_name}, expert={expert_name}, client={client_name}")
        
        # Build request data based on provided parameters
        request_data = {}
        if domain_name:
            request_data["domain_name"] = domain_name
        if expert_name:
            request_data["expert_name"] = expert_name
        if client_name:
            request_data["client_name"] = client_name
            
        print(f"[UI DEBUG] delete_vector_memory: Request data: {request_data}")
        print(f"[UI DEBUG] delete_vector_memory: Request URL: {API_BASE_URL}/vectors/memory")
        
        response = requests.delete(
            f"{API_BASE_URL}/vectors/memory",
            json=request_data
        )
        
        print(f"[UI DEBUG] delete_vector_memory: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] delete_vector_memory: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] delete_vector_memory: Failed to parse JSON response: {str(e)}")
            print(f"[UI ERROR] delete_vector_memory: Raw response text: {response.text}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] delete_vector_memory: Request failed: {str(e)}")
        return {"error": str(e)}, 500

# Helper functions for OpenAI Assistant API
def create_assistant(expert_name, memory_type="expert", client_name=None, model="gpt-4o"):
    try:
        print(f"[UI DEBUG] create_assistant: Creating assistant for expert '{expert_name}' with memory type '{memory_type}'")
        
        request_data = {
            "expert_name": expert_name,
            "memory_type": memory_type,
            "model": model
        }
        if client_name:
            request_data["client_name"] = client_name
            
        print(f"[UI DEBUG] create_assistant: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/create_assistant",
            json=request_data
        )
        
        print(f"[UI DEBUG] create_assistant: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] create_assistant: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] create_assistant: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] create_assistant: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def create_thread(expert_name, memory_type="expert", client_name=None):
    try:
        print(f"[UI DEBUG] create_thread: Creating thread for expert '{expert_name}' with memory type '{memory_type}'")
        
        request_data = {
            "expert_name": expert_name,
            "memory_type": memory_type
        }
        if client_name:
            request_data["client_name"] = client_name
            
        print(f"[UI DEBUG] create_thread: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/create_thread",
            json=request_data
        )
        
        print(f"[UI DEBUG] create_thread: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] create_thread: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] create_thread: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] create_thread: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def add_message(thread_id, content, role="user"):
    try:
        print(f"[UI DEBUG] add_message: Adding message to thread {thread_id}")
        
        request_data = {
            "thread_id": thread_id,
            "content": content,
            "role": role
        }
            
        print(f"[UI DEBUG] add_message: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/add_message",
            json=request_data
        )
        
        print(f"[UI DEBUG] add_message: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] add_message: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] add_message: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] add_message: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def run_thread(thread_id, assistant_id):
    try:
        print(f"[UI DEBUG] run_thread: Running thread {thread_id} with assistant {assistant_id}")
        
        request_data = {
            "thread_id": thread_id,
            "assistant_id": assistant_id
        }
            
        print(f"[UI DEBUG] run_thread: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/run_thread",
            json=request_data
        )
        
        print(f"[UI DEBUG] run_thread: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] run_thread: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] run_thread: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] run_thread: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def get_run_status(thread_id, run_id):
    try:
        print(f"[UI DEBUG] get_run_status: Getting status of run {run_id} in thread {thread_id}")
        
        request_data = {
            "thread_id": thread_id,
            "run_id": run_id
        }
            
        print(f"[UI DEBUG] get_run_status: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/get_run_status",
            json=request_data
        )
        
        print(f"[UI DEBUG] get_run_status: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] get_run_status: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] get_run_status: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] get_run_status: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def get_thread_messages(thread_id, limit=10):
    try:
        print(f"[UI DEBUG] get_thread_messages: Getting messages from thread {thread_id}")
        
        request_data = {
            "thread_id": thread_id,
            "limit": limit
        }
            
        print(f"[UI DEBUG] get_thread_messages: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/get_thread_messages",
            json=request_data
        )
        
        print(f"[UI DEBUG] get_thread_messages: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] get_thread_messages: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] get_thread_messages: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] get_thread_messages: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def query_expert_with_assistant(expert_name, query, memory_type="expert", client_name=None, thread_id=None):
    try:
        print(f"[UI DEBUG] query_expert_with_assistant: Querying expert '{expert_name}' with memory type '{memory_type}'")
        
        request_data = {
            "expert_name": expert_name,
            "query": query,
            "memory_type": memory_type
        }
        if client_name and memory_type == "client":
            request_data["client_name"] = client_name
        if thread_id:
            request_data["thread_id"] = thread_id
            
        print(f"[UI DEBUG] query_expert_with_assistant: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/query_expert_with_assistant",
            json=request_data
        )
        
        print(f"[UI DEBUG] query_expert_with_assistant: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] query_expert_with_assistant: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] query_expert_with_assistant: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] query_expert_with_assistant: Request failed: {str(e)}")
        return {"error": str(e)}, 500

# Page content based on selection
if page == "Create domain":
    st.title("Create domain")
    
    # Create new domain section
    st.header("Create New Domain")
    
    with st.form("create_domain_form"):
        new_domain_name = st.text_input("Domain Name")
        domain_description = st.text_area("Domain Description (Optional)", height=100)
        
        submitted = st.form_submit_button("Create Domain")
        if submitted:
            if new_domain_name:
                result, status_code = create_domain(new_domain_name)
                if status_code == 200:
                    st.success(f"Domain '{new_domain_name}' created successfully!")
                else:
                    st.error(f"Error creating domain: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter a domain name")
    
    # Display existing domains
    st.header("Existing Domains")
    
    # Get all domains
    domains = get_domains()
    
    if domains:
        # Create a table to display domains
        domain_data = []
        for domain in domains:
            domain_data.append({
                "Domain Name": domain.get("domain_name", "N/A"),
                "Default Vector ID": domain.get("default_vector_id", "None"),
            })
        
        # Display as a dataframe
        st.dataframe(domain_data)
    else:
        st.info("No domains found. Create a new domain above.")
              
elif page == "Create domain memory":
    st.title("Create domain memory")
    
    # Get selected domain outside the form
    selected_domain = st.selectbox("Select Domain", get_domain_names())
    
    # Document URLs input outside the form
    st.subheader("Add Documents to Domain Memory")
    
    # Create columns for document name and URL inputs
    doc_cols = st.columns(2)
    with doc_cols[0]:
        st.write("Document Name")
    with doc_cols[1]:
        st.write("Document URL")
    
    # Initialize document pairs dictionary
    doc_pairs = {}
    
    # Start with 3 empty document input pairs
    num_doc_inputs = st.session_state.get('num_doc_inputs', 3)
    
    for i in range(num_doc_inputs):
        doc_cols = st.columns(2)
        with doc_cols[0]:
            doc_name = st.text_input(f"Name {i+1}", key=f"doc_name_{i}", label_visibility="collapsed")
        with doc_cols[1]:
            doc_url = st.text_input(f"URL {i+1}", key=f"doc_url_{i}", label_visibility="collapsed")
        
        if doc_name and doc_url:  # Only add if both name and URL are provided
            # Check if the document name already exists in our pairs
            if doc_name not in doc_pairs:
                doc_pairs[doc_name] = doc_url
            else:
                st.warning(f"Document name '{doc_name}' already exists. Please use a different name.")
    
    # Add button for more document inputs
    if st.button("Add Another Document"):
        st.session_state.num_doc_inputs = num_doc_inputs + 1
        st.experimental_rerun()
    
    with st.form("domain_memory_form"):
        # Add a submit button to the form
        submitted = st.form_submit_button("Create Domain Memory")
    
    if submitted:
        if selected_domain:
            # Process document pairs if provided
            if doc_pairs:
                # Call the API to add files to domain vector
                result, status_code = add_files_to_domain_vector(selected_domain, doc_pairs)
                
                if status_code == 200:
                    st.success(f"Domain memory for {selected_domain} created successfully with {len(doc_pairs)} documents!")
                    
                    # Display details about the added documents
                    if "file_ids" in result:
                        st.write(f"File IDs: {', '.join(result['file_ids'][:5])}" + 
                                 ("..." if len(result['file_ids']) > 5 else ""))
                else:
                    st.error(f"Error creating domain memory: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please provide at least one document with both name and URL")
        else:
            st.warning("Please select a domain")

elif page == "Update domain memory":
    st.title("Update Domain Memory")
    
    # Get selected domain outside the form
    selected_domain = st.selectbox("Select Domain", get_domain_names())
    
    if selected_domain:
        # Get domain vector ID
        vector_info = get_domain_vector_id(selected_domain)
        
        if vector_info and vector_info.get("default_vector_id"):
            vector_id = vector_info.get("default_vector_id")
            st.success(f"Found vector store for domain: {selected_domain}")
            
            # Get existing documents for this domain
            existing_documents = get_documents_by_domain(selected_domain)
            
            if existing_documents:
                st.subheader("Current Documents")
                
                # Create a dictionary to store document selection status
                doc_selections = {}
                existing_doc_names = []
                # Display existing documents with checkboxes
                for doc in existing_documents:
                    doc_name = doc.get("name", "Unnamed Document")
                    existing_doc_names.append(doc_name)
                    doc_url = doc.get("document_link", "")
                    # Default to selected (True)
                    doc_selections[doc_url] = st.checkbox(f"{doc_name}", value=True, key=f"doc_{doc.get('id')}")
                
                # Get selected document URLs
                selected_urls = [url for url, selected in doc_selections.items() if selected]
                
                # New document inputs
                st.subheader("Add New Documents")
                
                # Create columns for document name and URL inputs
                new_doc_cols = st.columns(2)
                with new_doc_cols[0]:
                    st.write("Document Name")
                with new_doc_cols[1]:
                    st.write("Document URL")
                
                # Initialize new document pairs dictionary
                new_doc_pairs = {}
                
                # Start with 3 empty document input pairs
                num_new_doc_inputs = st.session_state.get('num_new_doc_inputs', 3)
                
                for i in range(num_new_doc_inputs):
                    new_doc_cols = st.columns(2)
                    with new_doc_cols[0]:
                        new_doc_name = st.text_input(f"New Name {i+1}", key=f"new_doc_name_{i}", label_visibility="collapsed")
                    with new_doc_cols[1]:
                        new_doc_url = st.text_input(f"New URL {i+1}", key=f"new_doc_url_{i}", label_visibility="collapsed")
                    
                    if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                        if new_doc_name not in existing_doc_names:
                            new_doc_pairs[new_doc_name] = new_doc_url
                        else:
                            st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
                
                # Add button for more document inputs
                if st.button("Add Another New Document"):
                    st.session_state.num_new_doc_inputs = num_new_doc_inputs + 1
                    st.experimental_rerun()
                
                # Create a dictionary with selected existing URLs and new document pairs
                all_urls = {}
                
                # Add selected existing documents with their original names
                for doc in existing_documents:
                    doc_url = doc.get("document_link", "")
                    if doc_selections.get(doc_url, False):
                        all_urls[doc.get("name", f"Document {len(all_urls)+1}")] = doc_url
                
                # Add new documents
                all_urls.update(new_doc_pairs)
                
                # Submit button
                if st.button("Update Domain Memory"):
                    if all_urls:
                        # Call the API to update vector store
                        result, status_code = update_vector_store(vector_id, all_urls)
                        
                        if status_code == 200:
                            st.success(f"Domain memory for {selected_domain} updated successfully!")
                            
                            # Display details about the updated documents
                            if "new_file_ids" in result:
                                st.write(f"New file IDs: {', '.join(result['new_file_ids'][:5])}" + 
                                         ("..." if len(result['new_file_ids']) > 5 else ""))
                            
                            if "all_file_ids" in result:
                                st.write(f"Total files in memory: {len(result['all_file_ids'])}")
                        else:
                            st.error(f"Error updating domain memory: {result.get('error', 'Unknown error')}")
                    else:
                        st.warning("No documents selected or added. Please select at least one document.")
            else:
                st.info("No existing documents found for this domain. Please use 'Create domain memory' to add documents first.")
        else:
            st.warning(f"No vector store found for domain: {selected_domain}. Please create domain memory first.")
    else:
        st.warning("Please select a domain")

elif page == "Create Expert":
    st.title("Create Expert")
    
    with st.form("expert_form"):
        name = st.text_input("Expert Name")
        domain = st.selectbox("Domain", get_domain_names())
        context = st.text_area("Expert Context", height=200)
        use_default_domain_knowledge = st.checkbox("Use Default Domain Knowledge", value=True)
        
        submitted = st.form_submit_button("Create Expert")
        if submitted:
            if name and domain and context:
                result, status_code = create_expert(name, domain, context, use_default_domain_knowledge)
                if status_code == 200:
                    st.success(f"Expert {name} created successfully!")
                else:
                    st.error(f"Error creating expert: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please fill in all fields")

elif page == "Update Expert Context":
    st.title("Update Expert Context")
    
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    with st.form("update_context_form"):
        expert_name = st.selectbox("Select Expert", expert_names)
        
        # Create a container for displaying the current context
        current_context_container = st.container()
        
        # Get and display current context when expert is selected
        if expert_name:
            current_context, status_code = get_expert_context(expert_name)
            with current_context_container:
                st.subheader("Current Context")
                st.text_area("Current Context", value=current_context, height=150, disabled=True, key="current_context")
        
        st.subheader("New Context")
        new_context = st.text_area("Enter new context below", height=200, key="new_context")
        
        submitted = st.form_submit_button("Update Context")
        if submitted:
            if expert_name and new_context:
                result, status_code = update_expert_context(expert_name, new_context)
                if status_code == 200:
                    st.success(f"Context for {expert_name} updated successfully!")
                    # Refresh the current context display
                    current_context, status_code = get_expert_context(expert_name)
                    with current_context_container:
                        st.subheader("Current Context")
                        st.text_area("Current Context", value=current_context, height=150, disabled=True, key="updated_context")
                else:
                    st.error(f"Error updating context: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please fill in all fields")

elif page == "Create expert memory":
    st.title("Create expert memory")
    
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Get expert's domain outside the form for document filtering
    expert_domain = None
    selected_expert = st.selectbox("Select Expert", expert_names)
    
    for expert in experts:
        if expert["name"] == selected_expert:
            expert_domain = expert["domain"]
            break
    
    # Options for adding documents
    st.subheader("Add Documents to Expert Memory")
    
    # Client-specific option
    use_for_specific_client = st.checkbox("Create Client-Specific Memory", value=False)
    client_name = None
    if use_for_specific_client:
        client_name = st.text_input("Client Name")
    
    # Document inputs with name-URL pairs
    st.subheader("Document Inputs")
    
    # Create columns for document name and URL inputs
    doc_cols = st.columns(2)
    with doc_cols[0]:
        st.write("Document Name")
    with doc_cols[1]:
        st.write("Document URL")
    
    # Initialize document pairs dictionary
    doc_pairs = {}
    
    # Start with 3 empty document input pairs
    num_doc_inputs = st.session_state.get('expert_doc_inputs', 3)
    
    for i in range(num_doc_inputs):
        doc_cols = st.columns(2)
        with doc_cols[0]:
            doc_name = st.text_input(f"Name {i+1}", key=f"expert_doc_name_{i}", label_visibility="collapsed")
        with doc_cols[1]:
            doc_url = st.text_input(f"URL {i+1}", key=f"expert_doc_url_{i}", label_visibility="collapsed")
        
        if doc_name and doc_url:  # Only add if both name and URL are provided
            # Check if the document name already exists in our pairs
            if doc_name not in doc_pairs:
                doc_pairs[doc_name] = doc_url
            else:
                st.warning(f"Document name '{doc_name}' already exists. Please use a different name.")
    
    # Add button for more document inputs
    if st.button("Add Another Document", key="expert_create_add_doc"):
        st.session_state.expert_doc_inputs = num_doc_inputs + 1
        st.experimental_rerun()
    
    with st.form("expert_memory_form"):
        # Add a submit button to the form
        submitted = st.form_submit_button("Create expert memory")
        
    # Handle form submission outside the form
    if submitted:
        if selected_expert:
            # Check if client name is provided when use_for_specific_client is True
            if use_for_specific_client and not client_name:
                st.error("Client name is required when creating client-specific memory")
                st.stop()
                
            # First create or update the expert's vector store with client-specific parameters if needed
            result, status_code = create_expert_vector(
                selected_expert,
                use_for_specific_client,
                client_name
            )
            
            if status_code != 200:
                st.error(f"Error creating expert memory: {result.get('error', 'Unknown error')}")
                st.stop()
            
            # Process document pairs if provided
            if doc_pairs:
                # Check if client name is provided when use_for_specific_client is True
                if use_for_specific_client and not client_name:
                    st.error("Client name is required when creating client-specific memory")
                else:
                    # Call the API to add files to expert vector
                    result, status_code = add_files_to_expert_vector(
                        selected_expert, 
                        doc_pairs, 
                        use_for_specific_client, 
                        client_name
                    )     
                    if status_code == 200:
                        if use_for_specific_client:
                            st.success(f"Expert memory for {selected_expert} created successfully for client {client_name}!")
                        else:
                            st.success(f"Expert memory for {selected_expert} created successfully with {len(doc_pairs)} documents!")
                            # Display details about the added documents
                            if "file_ids" in result:
                                st.write(f"File IDs: {', '.join(result['file_ids'][:5])}" + 
                                         ("..." if len(result['file_ids']) > 5 else ""))
                    else:
                        st.error(f"Error adding documents: {result.get('error', 'Unknown error')}")
            else:
                # No documents provided, just show success for creating the vector store
                st.success(f"Empty vector store created for {selected_expert}!")
                st.write("You can add documents to this vector store later.")
        else:
            st.warning("Please select an expert")

elif page == "Update expert memory":
    st.title("Update Expert Memory")
    
    # Get selected expert outside the form
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    selected_expert = st.selectbox("Select Expert", expert_names)
    
    if selected_expert:
        # Get clients for this expert using the new endpoint
        client_options = get_client_names_for_expert(selected_expert)
        selected_client = st.selectbox("Select Client", client_options)
        
        # Get vector ID based on expert and client selection
        vector_info = None
        if selected_client and selected_client != "No specific client":
            # Get vector ID for expert-client combination
            vector_info = get_expert_client_vector_id(selected_expert, selected_client)
            vector_id = vector_info.get("vector_id") if vector_info else None
        else:
            # Get preferred vector ID for expert only
            vector_info = get_expert_vector_id(selected_expert)
            vector_id = vector_info.get("preferred_vector_id") if vector_info else None
        
        if vector_id:
            st.success(f"Found vector store for expert: {selected_expert}" + 
                      (f" and client: {selected_client}" if selected_client != "No specific client" else ""))
            
            # Get existing documents for this expert/client combination
            existing_documents = get_documents_by_expert(selected_expert, client_name=selected_client)
            
            if existing_documents:
                st.subheader("Current Documents")
                
                # Create a dictionary to store document selection status
                doc_selections = {}
                existing_doc_names = []
                # Display existing documents with checkboxes
                for doc in existing_documents:
                    doc_name = doc.get("name", "Unnamed Document")
                    existing_doc_names.append(doc_name)
                    doc_url = doc.get("document_link", "")
                    # Default to selected (True)
                    doc_selections[doc_url] = st.checkbox(f"{doc_name}", value=True, key=f"expert_doc_{doc.get('id')}")
                
                # Get selected document URLs
                selected_urls = [url for url, selected in doc_selections.items() if selected]
                
                # New document inputs
                st.subheader("Add New Documents")
                
                # Create columns for document name and URL inputs
                new_doc_cols = st.columns(2)
                with new_doc_cols[0]:
                    st.write("Document Name")
                with new_doc_cols[1]:
                    st.write("Document URL")
                
                # Initialize new document pairs dictionary
                new_doc_pairs = {}
                
                # Start with 3 empty document input pairs
                num_new_doc_inputs = st.session_state.get('expert_num_new_doc_inputs', 3)
                
                for i in range(num_new_doc_inputs):
                    new_doc_cols = st.columns(2)
                    with new_doc_cols[0]:
                        new_doc_name = st.text_input(f"New Name {i+1}", key=f"expert_new_doc_name_{i}", label_visibility="collapsed")
                    with new_doc_cols[1]:
                        new_doc_url = st.text_input(f"New URL {i+1}", key=f"expert_new_doc_url_{i}", label_visibility="collapsed")
                    
                    if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                        if new_doc_name not in existing_doc_names:
                            new_doc_pairs[new_doc_name] = new_doc_url
                        else:
                            st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
                
                # Add button for more document inputs
                if st.button("Add Another New Document", key="expert_add_doc"):
                    st.session_state.expert_num_new_doc_inputs = num_new_doc_inputs + 1
                    st.experimental_rerun()
                
                # Create a dictionary with selected existing URLs and new document pairs
                all_urls = {}
                
                # Add selected existing documents with their original names
                for doc in existing_documents:
                    doc_url = doc.get("document_link", "")
                    if doc_selections.get(doc_url, False):
                        all_urls[doc.get("name", f"Document {len(all_urls)+1}")] = doc_url
                
                # Add new documents
                all_urls.update(new_doc_pairs)
                
                # Submit button
                if st.button("Update Expert Memory"):
                    if all_urls:
                        # Call the API to update vector store
                        result, status_code = update_vector_store(vector_id, all_urls)
                        
                        if status_code == 200:
                            st.success(f"Expert memory for {selected_expert}" + 
                                      (f" and client {selected_client}" if selected_client != "No specific client" else "") + 
                                      " updated successfully!")
                            
                            # Display details about the updated documents
                            if "new_file_ids" in result:
                                st.write(f"New file IDs: {', '.join(result['new_file_ids'][:5])}" + 
                                         ("..." if len(result['new_file_ids']) > 5 else ""))
                            
                            if "all_file_ids" in result:
                                st.write(f"Total files in memory: {len(result['all_file_ids'])}")
                        else:
                            st.error(f"Error updating expert memory: {result.get('error', 'Unknown error')}")
                    else:
                        st.warning("No documents selected or added. Please select at least one document.")
            else:
                st.info("No existing documents found for this expert" + 
                       (f" and client {selected_client}" if selected_client != "No specific client" else "") + 
                       ". Please use 'Create expert memory' to add documents first.")
        else:
            st.warning(f"No vector store found for expert: {selected_expert}" + 
                      (f" and client: {selected_client}" if selected_client != "No specific client" else "") + 
                      ". Please create expert memory first.")
    else:
        st.warning("Please select an expert")

elif page == "Query Expert":
    st.title("Query Expert")
    
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    selected_expert = st.selectbox("Select Expert", expert_names)
    
    # Memory type selection
    memory_type = st.radio(
        "Select memory type:",
        ["Use LLM memory", "Use domain memory", "Use expert memory", "Use client memory"],
        index=2  # Default to "Use expert memory"
    )
    
    # Client selection (only if client memory is selected)
    selected_client = None
    if memory_type == "Use client memory" and selected_expert:
        client_options = get_client_names_for_expert(selected_expert)
        if client_options and len(client_options) > 1:  # Skip "No specific client"
            # Remove "No specific client" option for client memory
            client_options = client_options[1:]
            if client_options:
                selected_client = st.selectbox("Select Client", client_options)
            else:
                st.warning("No clients found for this expert. Please create client-specific memory first.")
        else:
            st.warning("No clients found for this expert. Please create client-specific memory first.")
    
    # Create a unique key for each expert and memory type combination
    if selected_expert:
        # Create a unique session state key for this expert and memory type
        chat_key = f"messages_{selected_expert}_{memory_type}"
        if selected_client and memory_type == "Use client memory":
            chat_key += f"_{selected_client}"
            
        # Initialize chat history for this specific combination if it doesn't exist
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        # Display chat messages for this specific combination
        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Accept user input
        if prompt := st.chat_input("Ask your question..."):
            # Add user message to this specific chat history
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            
            # Display user message in chat
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get response from API only if there's a prompt
            if selected_expert:
                # Map UI memory type to API memory type
                api_memory_type = {
                    "Use LLM memory": "llm",
                    "Use domain memory": "domain",
                    "Use expert memory": "expert",
                    "Use client memory": "client"
                }.get(memory_type, "expert")
                
                # Check if client is selected when needed
                if api_memory_type == "client" and not selected_client:
                    with st.chat_message("assistant"):
                        st.error("Please select a client for client-specific memory.")
                        st.session_state[chat_key].append({"role": "assistant", "content": "Please select a client for client-specific memory."})
                else:
                    with st.spinner("Thinking..."):
                        result, status_code = query_expert(
                            selected_expert, 
                            prompt, 
                            memory_type=api_memory_type, 
                            client_name=selected_client if api_memory_type == "client" else None
                        )
                    
                    # Display assistant response in chat
                    with st.chat_message("assistant"):
                        if status_code == 200:
                            response = result.get("response", "I don't have an answer for that.")
                            st.write(response["text"])
                            # Add assistant response to chat history
                            st.session_state[chat_key].append({"role": "assistant", "content": response["text"]})
                        else:
                            error_msg = f"Error: {result.get('error', 'Unknown error')}"
                            st.error(error_msg)
                            # Add error response to chat history
                            st.session_state[chat_key].append({"role": "assistant", "content": error_msg})
        else:
            with st.chat_message("assistant"):
                st.write("Please select an expert first.")

elif page == "Query Expert using Threads":
    st.title("Query Expert using Threads")
    
    # Get experts
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    
    # Memory type selection
    memory_options = ["llm", "domain", "expert", "client"]
    selected_memory = st.selectbox("Select Memory Type", memory_options, index=2)  # Default to "expert"
    
    # Client selection (only enabled if memory type is "client")
    client_options = ["--No specific client--"]
    client_disabled = selected_memory != "client"
    
    if selected_expert != "--Select an expert--" and selected_memory == "client":
        # Get clients for the selected expert
        clients = get_client_names_for_expert(selected_expert)
        if clients and len(clients) > 1:  # Skip "No specific client" which is already in client_options
            client_options.extend(clients[1:])  # Skip the first item which is "No specific client"
    
    selected_client = st.selectbox("Select Client", client_options, disabled=client_disabled)
    
    # Create unique keys for this expert/memory/client combination
    thread_key = f"thread_messages_{selected_expert}_{selected_memory}"
    thread_id_key = f"thread_id_{selected_expert}_{selected_memory}"
    assistant_id_key = f"assistant_id_{selected_expert}_{selected_memory}"
    
    if selected_memory == "client" and selected_client != "--No specific client--":
        thread_key += f"_{selected_client}"
        thread_id_key += f"_{selected_client}"
        assistant_id_key += f"_{selected_client}"
    
    # Initialize session state for thread ID if not already present
    if thread_id_key not in st.session_state:
        st.session_state[thread_id_key] = None
    
    # Initialize session state for assistant ID if not already present
    if assistant_id_key not in st.session_state:
        st.session_state[assistant_id_key] = None
    
    # Initialize session state for messages if not already present
    
    if thread_key not in st.session_state:
        st.session_state[thread_key] = []
    
    # Display chat messages
    for message in st.session_state[thread_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if selected_expert != "--Select an expert--":
        # Create or get assistant and thread if needed
        if st.session_state[assistant_id_key] is None or st.session_state[thread_id_key] is None:
            with st.spinner("Initializing chat..."):
                # Create assistant
                client_name = selected_client if selected_memory == "client" and selected_client != "--No specific client--" else None
                assistant_result, assistant_status = create_assistant(
                    expert_name=selected_expert,
                    memory_type=selected_memory,
                    client_name=client_name
                )
                
                if assistant_status == 200:
                    st.session_state[assistant_id_key] = assistant_result.get("assistant_id")
                    
                    # Create thread
                    thread_result, thread_status = create_thread(
                        expert_name=selected_expert,
                        memory_type=selected_memory,
                        client_name=client_name
                    )
                    
                    if thread_status == 200:
                        st.session_state[thread_id_key] = thread_result.get("thread_id")
                    else:
                        st.error(f"Error creating thread: {thread_result.get('error', 'Unknown error')}")
                else:
                    st.error(f"Error creating assistant: {assistant_result.get('error', 'Unknown error')}")
        
        # User input
        prompt = st.chat_input("Ask a question...")
        if prompt:
            # Add user message to chat history
            st.session_state[thread_key].append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get response from assistant
            with st.spinner("Thinking..."):
                client_name = selected_client if selected_memory == "client" and selected_client != "--No specific client--" else None
                
                result, status_code = query_expert_with_assistant(
                    expert_name=selected_expert,
                    query=prompt,
                    memory_type=selected_memory,
                    client_name=client_name,
                    thread_id=st.session_state[thread_id_key]
                )
                
                if status_code == 200:
                    # Update thread ID if it changed
                    if result.get("thread_id") and result.get("thread_id") != st.session_state[thread_id_key]:
                        st.session_state[thread_id_key] = result.get("thread_id")
                    
                    # Display assistant response
                    with st.chat_message("assistant"):
                        response_text = result.get("response", {}).get("text", "No response from assistant.")
                        st.write(response_text)
                    
                    # Add assistant response to chat history
                    st.session_state[thread_key].append({"role": "assistant", "content": response_text})
                else:
                    error_msg = f"Error: {result.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    # Add error response to chat history
                    st.session_state[thread_key].append({"role": "assistant", "content": error_msg})
    else:
        with st.chat_message("assistant"):
            st.write("Please select an expert first.")

elif page == "Delete Memory":
    st.title("Delete Memory")
    
    # Get domains and experts
    domains = get_domains()
    domain_names = get_domain_names()
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Domain selection
    selected_domain = st.selectbox("Select Domain", ["--Select a domain--"] + domain_names)
    
    # Expert selection (filtered by domain if domain is selected)
    filtered_experts = expert_names
    if selected_domain and selected_domain != "--Select a domain--":
        # Filter experts by selected domain
        filtered_experts = []
        for expert in experts:
            if expert.get("domain") == selected_domain:
                filtered_experts.append(expert["name"])
    
    expert_options = ["--No specific expert--"] + filtered_experts
    selected_expert = st.selectbox("Select Expert (Optional)", expert_options)
    
    # Client selection (only enabled if expert is selected)
    client_options = ["--No specific client--"]
    if selected_expert and selected_expert != "--No specific expert--":
        # Get clients for the selected expert
        clients = get_client_names_for_expert(selected_expert)
        if clients and len(clients) > 1:  # Skip "No specific client" which is already in client_options
            client_options.extend(clients[1:])  # Skip the first item which is "No specific client"
    
    selected_client = st.selectbox("Select Client (Optional)", client_options)
    
    # Determine what will be deleted based on selections
    delete_type = None
    if selected_domain != "--Select a domain--" and selected_expert == "--No specific expert--":
        delete_type = "domain"
        st.info(f"This will delete the domain memory for '{selected_domain}'")
    elif selected_expert != "--No specific expert--" and selected_client == "--No specific client--":
        delete_type = "expert"
        st.info(f"This will delete the expert memory for '{selected_expert}'")
    elif selected_expert != "--No specific expert--" and selected_client != "--No specific client--":
        delete_type = "client"
        st.info(f"This will delete the client-specific memory for client '{selected_client}' of expert '{selected_expert}'")
    
    # Delete button
    if delete_type and st.button(f"Delete {delete_type.capitalize()} Memory"):
        # Prepare parameters for deletion
        domain_param = selected_domain if selected_domain != "--Select a domain--" else None
        expert_param = selected_expert if selected_expert != "--No specific expert--" else None
        client_param = selected_client if selected_client != "--No specific client--" else None
        
        # Confirm deletion with the user
        confirm_message = f"Are you sure you want to delete the {delete_type} memory?"
        if st.checkbox(confirm_message, key="confirm_delete"):
            # Call the delete endpoint
            result, status_code = delete_vector_memory(
                domain_name=domain_param,
                expert_name=expert_param,
                client_name=client_param
            )
            
            if status_code == 200:
                st.success(f"{delete_type.capitalize()} memory deleted successfully!")
                st.json(result)
            else:
                st.error(f"Error deleting memory: {result.get('error', 'Unknown error')}")
    else:
        if selected_domain == "--Select a domain--":
            st.warning("Please select a domain first")
        elif delete_type is None:
            st.warning("Please make a valid selection of domain, expert, and/or client")

