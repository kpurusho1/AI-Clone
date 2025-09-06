import streamlit as st
import requests
import json
import os

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="AI Clone",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for 1hat.in branding and healthcare theme
st.markdown("""
<style>
    /* Main color scheme inspired by healthcare/medical themes */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --success-color: #4CAF50;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
        --light-blue: #E3F2FD;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 4rem;
        color: white;
        text-align: center;
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        margin-bottom: 2rem;
    }
    
    .logo-container img {
        max-height: 60px;
        width: auto;
    }
    
    /* Sidebar styling - multiple selectors for compatibility */
    .css-1d391kg, 
    .css-1lcbmhc,
    .css-17eq0hr,
    section[data-testid="stSidebar"] {
        background-color: #1e3a8a !important;
        padding: 0.5rem !important;
        margin: 0 !important;
    }
    
    /* Sidebar content wrapper */
    section[data-testid="stSidebar"] > div {
        background-color: #1e3a8a !important;
        padding: 0.5rem !important;
        margin: 0 !important;
    }
    
    /* Reduce sidebar internal spacing */
    section[data-testid="stSidebar"] .block-container {
        padding: 0.5rem !important;
        margin: 0 !important;
    }
    
    /* All text in sidebar */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Sidebar headers and subheaders */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: white !important;
    }
    
    /* Radio button styling in sidebar */
    section[data-testid="stSidebar"] .stRadio > label,
    section[data-testid="stSidebar"] .stRadio > div,
    section[data-testid="stSidebar"] [role="radiogroup"] label {
        color: white !important;
    }
    
    /* Radio button selected state */
    section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] + label {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, var(--secondary-color), var(--primary-color));
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid var(--light-blue);
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(46, 134, 171, 0.2);
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 4px solid var(--success-color);
    }
    
    .stError {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #F44336;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--light-blue);
        border-radius: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-color);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        background-color: white;
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid var(--light-blue);
        margin: 0.25rem 0;
    }
    
    .stCheckbox > label:hover {
        border-color: var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

# Get the current directory of the app.py file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the logo file in the same directory as app.py
logo_path = os.path.join(current_dir, "1Hat Logo_transparent.png")
sidebar_logo_path = os.path.join(current_dir, "1Hat_logo.png")   

# Create a two-column layout for the header
header_col1, header_col2 = st.columns([1, 4])

# Display the logo in the first column if the file exists
if os.path.exists(logo_path):
    with header_col1:
        st.image(logo_path, width=100)
else:
    st.warning("Logo file not found. Please check the path.")
    
# Display the title and subtitle in the second column
with header_col2:
    st.markdown("<h1 style='margin: 0; font-size: 2.5rem;'>AI Clone</h1>", unsafe_allow_html=True)

# Sidebar navigation with logo
# Display the logo in the sidebar if the file exists
if os.path.exists(sidebar_logo_path):
    st.sidebar.image(sidebar_logo_path, width=80)

# Display the title in the sidebar
st.sidebar.markdown("<h2 style='color: white; margin: 0; font-size: 1.5rem; text-align: left;'>AI Clone</h2>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Select a page:",
    ["Create Hospital", "Create Specialty", "Create expert", "Create client","Assistant", "Update", "Update Expert"]
)

def get_domains(org_id):
    """Get all domains for an organization"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/domains?org_id={org_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting domains: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting domains: {str(e)}")
        return []

def get_organizations():
    try:
        response = requests.get(f"{API_BASE_URL}/api/organization")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting organizations: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting organizations: {str(e)}")
        return []

def get_expert_domains(expert_id):
    """Get domains associated with an expert"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/experts/{expert_id}/domains")
        if response.status_code == 200:
            print(f"[UI DEBUG] get_expert_domains: Response data: {response.json()}")
            return response.json().get("domains", [])
        return []
    except Exception as e:
        print(f"[UI ERROR] get_expert_domains: Request failed: {str(e)}")
        return []

def get_available_domains(expert_id, org_id):
    """Get available domains for an expert"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/experts/{expert_id}/available-domains?org_id={org_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting available domains: {response.text}")
            return {}
    except Exception as e:
        print(f"Error getting available domains: {str(e)}")
        return {}

def create_expert(expert_name, domain_name, qa_pairs, document_urls, org_id, pdf_documents=None):
    try:
        print(f"[UI DEBUG] create_expert: Creating expert '{expert_name}' in domain '{domain_name}'")
        
        # Generate a new UUID for the expert
        import uuid
        expert_id = str(uuid.uuid4())
        
        request_data = {
            "org_id": org_id,
            "expert_id": expert_id,
            "expert_name": expert_name,
            "domain_name": domain_name,
            "qa_pairs": qa_pairs,
            "document_urls": document_urls
        }
        
        # Add PDF documents to request if available
        if pdf_documents and len(pdf_documents) > 0:
            # PDF documents now contain file paths instead of bytes
            request_data["pdf_documents"] = pdf_documents
            print(f"[UI DEBUG] create_expert: Added {len(pdf_documents)} PDF file paths to request")
        
        print(f"[UI DEBUG] create_expert: Request URL: {API_BASE_URL}/api/memory/expert/initialize")
        
        response = requests.post(
            f"{API_BASE_URL}/api/memory/expert/initialize",
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

def get_expert_context(expert_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/experts/{expert_id}/context")
        if response.status_code == 200:
            print(f"[UI DEBUG] get_expert_context: Response data: {response.json()}")
            return response.json()
        return {"context": ""}
    except Exception as e:
        print(f"[UI ERROR] get_expert_context: Request failed: {str(e)}")
        return {"context": ""}

def update_memory(memory_type, org_id, expert_id= None, expert_name= None, domain_name= None, client_id= None, qa_pairs=None, document_urls=None, pdf_documents=None):
    try:
        print(f"[UI DEBUG] update_memory: Updating expert '{expert_name}' in domain '{domain_name}'")
        print(f"[UI DEBUG] update_memory: memory_type={memory_type}, org_id={org_id}, expert_id={expert_id}")
        
        request_data = {
            "memory_type": memory_type,
            "org_id": org_id,
            "expert_id": expert_id,
            "client_id": client_id,
            "expert_name": expert_name,
            "domain_name": domain_name
        }
        
        # Add QA pairs to request if available
        if qa_pairs and len(qa_pairs) > 0:
            request_data["qa_pairs"] = qa_pairs
            print(f"[UI DEBUG] update_memory: Added {len(qa_pairs)} QA pairs to request")
        
        # Add document URLs to request if available
        if document_urls and len(document_urls) > 0:
            request_data["document_urls"] = document_urls
            print(f"[UI DEBUG] update_memory: Added {len(document_urls)} document URLs to request")
        
        # Add PDF documents to request if available
        if pdf_documents and len(pdf_documents) > 0:
            request_data["pdf_documents"] = pdf_documents
            print(f"[UI DEBUG] update_memory: Added {len(pdf_documents)} PDF file paths to request")
        
        print(f"[UI DEBUG] update_memory: Request URL: {API_BASE_URL}/api/update")
        print(f"[UI DEBUG] update_memory: Full request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/update",
            json=request_data
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"[UI DEBUG] update_memory: Success response: {response_data}")
            return response_data, response.status_code
        else:
            print(f"[UI ERROR] update_memory: Error {response.status_code}: {response.text}")
            print(f"[UI ERROR] update_memory: Response headers: {response.headers}")
            return {"error": f"Error {response.status_code}: {response.text}"}, response.status_code
    
    except Exception as e:
        print(f"[UI ERROR] update_memory: Exception: {str(e)}")
        return {"error": str(e)}, 500

def create_client(client_name, client_data, org_id, expert_id, org_client_id, document_urls=None, pdf_documents=None, other_doc=None):
    try:
        print(f"[UI DEBUG] create_client: Creating client '{client_name}'")
        
        # Initialize with empty dictionaries if None is provided
        document_urls = document_urls or {}
        pdf_documents = pdf_documents or {}
        other_doc = other_doc or {}
        
        request_data = {
            "org_client_id": org_client_id,
            "org_id": org_id,
            "expert_id": expert_id,
            "client_name": client_name,
            "client_data_jsonb": client_data,
            "document_urls": document_urls,
            "pdf_documents": pdf_documents,
            "other_doc": other_doc
        }
        
        print(f"[UI DEBUG] create_client: Request URL: {API_BASE_URL}/api/memory/client/initialize")
        
        response = requests.post(
            f"{API_BASE_URL}/api/memory/client/initialize",
            json=request_data
        )
        
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            print(f"[UI ERROR] create_client: Error {response.status_code}: {response.text}")
            return {"error": f"Error {response.status_code}: {response.text}"}, response.status_code
    
    except Exception as e:
        print(f"[UI ERROR] create_client: Exception: {str(e)}")
        return {"error": str(e)}, 500

def create_org_memory(org_name, org_data, document_urls=None, pdf_documents=None):
    try:
        print(f"[UI DEBUG] create_org_memory: Creating organization memory for '{org_name}'")
        
        request_data = {
            "org_name": org_name,
            "org_data_jsonb": org_data,
            "document_urls": document_urls or {},
            "pdf_documents": pdf_documents or {}
        }
        
        print(f"[UI DEBUG] create_org_memory: Request URL: {API_BASE_URL}/api/memory/org/initialize")
        
        response = requests.post(
            f"{API_BASE_URL}/api/memory/org/initialize",
            json=request_data
        )
        
        if response.status_code == 200:
            return response.json(), response.status_code
        else:
            print(f"[UI ERROR] create_org_memory: Error {response.status_code}: {response.text}")
            return {"error": f"Error {response.status_code}: {response.text}"}, response.status_code
    
    except Exception as e:
        print(f"[UI ERROR] create_org_memory: Exception: {str(e)}")
        return {"error": str(e)}, 500

def get_experts(org_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/experts", params={"org_id": org_id})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def get_clients(org_id, expert_id=None):
    try:
        params = {"org_id": org_id}
        if expert_id:
            params["expert_id"] = expert_id
        response = requests.get(f"{API_BASE_URL}/api/clients", params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []
       
def get_documents(owner_id):
    # Get documents for a specific expert and domain
    try:
        # Get documents where owner_id is the expert_id
        # This will get documents associated with this expert
        response = requests.get(
            f"{API_BASE_URL}/api/documents",
            params={"owner_id": owner_id}
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"[UI ERROR] get_documents: {str(e)}")
        return []

def get_documents_by_vector_name(vector_name):
    # Get documents for a specific expert and domain
    try:
        # Get documents where owner_id is the expert_id
        # This will get documents associated with this expert
        response = requests.get(
            f"{API_BASE_URL}/api/documents/vector-name",
            params={"vector_name": vector_name}
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"[UI ERROR] get_documents_by_vector_name: {str(e)}")
        return []
             

# Helper functions for OpenAI Assistant API
# Note: create_assistant and create_thread functions have been removed
# as they are now handled directly by the query_expert_with_assistant function

def query_expert_with_assistant(expert_name, query, memory_type="expert", org_id=None, expert_id=None, client_id=None, domain_name=None, thread_id=None):
    try:
        print(f"[UI DEBUG] query_expert_with_assistant: Querying expert '{expert_name}' with memory type '{memory_type}'")
        
        request_data = {
            "expert_name": expert_name,
            "query": query,
            "memory_type": memory_type,
            "org_id": org_id,
            "expert_id": expert_id
        }
        if domain_name:
            request_data["domain_name"] = domain_name
        if client_id:
            request_data["client_id"] = client_id
        if thread_id:
            request_data["thread_id"] = thread_id
            
        print(f"[UI DEBUG] query_expert_with_assistant: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/query_expert_with_assistant",
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

if page == "Create expert":
    st.title("Create Expert")
    
    # Get organizations first
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org = st.selectbox("Select Organization", org_options)
    
    if selected_org != "--Select an organization--":
        # Find the organization by name to get its ID
        org_id = None
        for org in organizations:
            if org['org_name'] == selected_org:
                org_id = org['id']
                break
        
        with st.form("expert_form"):
            expert_name = st.text_input("Expert Name")
            
            # Get all domains for the organization
            all_domains = get_domains(org_id)
            
            if all_domains:
                st.subheader("Select Domains")
                st.write("Select the domains this expert will be associated with:")
                
                # Create checkboxes for each domain
                selected_domains = []
                for domain in all_domains:
                    domain_name = domain['domain_name']
                    domain_id = domain['id']
                    
                    # For new experts, all domains are available for selection
                    is_selected = st.checkbox(
                        domain_name, 
                        key=f"domain_{domain_id}",
                        value=False
                    )
                    
                    if is_selected:
                        selected_domains.append(domain_name)
            else:
                st.warning("No domains found for this organization. Please create domains first.")
                selected_domains = []
            
            # Display simplified questions
            st.subheader("Expert Context - Answer the following questions")
            
            # Simplified questions as requested
            questions = [
                "Explain more about your experience.",
                "What is your communication preference with clients?"
            ]
            
            # Dictionary to store answers
            qa_pairs = {}
            
            # Create a text box for each question
            for i, question in enumerate(questions):
                st.write(f"**{question}**")
                answer = st.text_area(f"Answer {i+1}", key=f"answer_{i}", height=100)
                if answer:  # Only add non-empty answers
                    qa_pairs[question] = answer
                    
            # Document inputs with name-URL pairs
            st.subheader("Document Inputs")
            st.write("Add both URL documents and PDF uploads as needed:")
            
            # Remove radio buttons and show both sections directly
            tab_names = ["Document URLs", "PDF Uploads"]
            doc_tabs = st.tabs(tab_names)
            
            # Initialize document pairs dictionary
            doc_pairs = {}
            
            # Initialize PDF documents dictionary
            pdf_documents = {}
            
            # URL Documents Tab
            with doc_tabs[0]:
                # Create columns for document name and URL inputs
                doc_cols = st.columns(2)
                with doc_cols[0]:
                    st.write("Document Name")
                with doc_cols[1]:
                    st.write("Document URL")
            
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
            
            # PDF Documents Tab
            with doc_tabs[1]:
                st.write("Upload PDF documents with names")
                
                # Start with 3 empty PDF upload slots
                num_pdf_uploads = st.session_state.get('expert_pdf_uploads', 3)
                
                for i in range(num_pdf_uploads):
                    pdf_cols = st.columns(2)
                    with pdf_cols[0]:
                        pdf_name = st.text_input(f"PDF Name {i+1}", key=f"expert_pdf_name_{i}")
                    with pdf_cols[1]:
                        pdf_file = st.file_uploader(f"Upload PDF {i+1}", type=["pdf"], key=f"expert_pdf_file_{i}")
                    
                    if pdf_name and pdf_file is not None:  # Only add if both name and file are provided
                        # Check if the document name already exists
                        if pdf_name not in pdf_documents and pdf_name not in doc_pairs:
                            # Upload PDF via API endpoint without reading into memory
                            try:
                                files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
                                data = {"pdf_name": pdf_name}
                                
                                response = requests.post(
                                    f"{API_BASE_URL}/api/upload-pdf/",
                                    files=files,
                                    data=data
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    pdf_documents[pdf_name] = result["file_path"]
                                    st.success(f"PDF uploaded: {result['message']}")
                                else:
                                    st.error(f"Failed to upload PDF: {response.text}")
                                    
                            except Exception as e:
                                st.error(f"Error uploading PDF: {str(e)}")
                        else:
                            st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")
        
            # Submit buttons for the form
            col1, col2 = st.columns(2)
            with col1:
                add_more = st.form_submit_button("Add Another Document")
            with col2:
                submitted = st.form_submit_button("Create Expert")
        
        # Handle the 'Add Another Document' button
        if add_more:
            # Add both URL and PDF inputs
            st.session_state.expert_doc_inputs = st.session_state.get('expert_doc_inputs', 3) + 1
            st.session_state.expert_pdf_uploads = st.session_state.get('expert_pdf_uploads', 3) + 1
            st.experimental_rerun()
        
        # Process form submission
        if submitted:
            # Format qa_pairs as a list of dictionaries with question and answer keys
            formatted_qa_pairs = []
            for question, answer in qa_pairs.items():
                formatted_qa_pairs.append({"question": question, "answer": answer})
            
            # Check if we have at least one document (either URL or PDF)
            has_documents = len(doc_pairs) > 0 or len(pdf_documents) > 0
                
            if expert_name and selected_domains and formatted_qa_pairs and has_documents:
                # Pass selected domains as a list for the API call
                result, status_code = create_expert(expert_name, selected_domains, formatted_qa_pairs, doc_pairs, org_id, pdf_documents)
                if status_code == 200:
                    st.success(f"Expert {expert_name} created successfully!")
                    # Clear the session state for PDF uploads to avoid resubmission issues
                    if 'expert_pdf_uploads' in st.session_state:
                        del st.session_state['expert_pdf_uploads']
                else:
                    st.error(f"Error creating expert: {result.get('error', 'Unknown error')}")
            else:
                if not expert_name:
                    st.warning("Please enter an Expert Name")
                elif not selected_domains:
                    st.warning("Please select at least one domain")
                elif not qa_pairs:
                    st.warning("Please answer at least one question for the Expert Context")
                elif not has_documents:
                    st.warning("Please add at least one document (URL or PDF)")
                    
            # Show a summary of what was submitted
            if has_documents:
                with st.expander("Submission Summary"):
                    st.write(f"**Expert Name:** {expert_name}")
                    st.write(f"**Selected Domains:** {', '.join(selected_domains)}")
                    st.write(f"**URL Documents:** {len(doc_pairs)}")
                    st.write(f"**PDF Documents:** {len(pdf_documents)}")
                    st.write(f"**Context QA Pairs:** {len(formatted_qa_pairs)}")
    else:
        st.info("Please select an organization to create an expert.")
            
elif page == "Assistant":
    st.title("Query Expert using Threads")
    
    # Get organizations first
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org = st.selectbox("Select Organization", org_options)
    
    # Initialize variables
    org_id = None
    experts = []
    expert_names = []
    clients = []
    domains = []
    selected_memory = "expert"  # Default memory type
    selected_memory_types = ["expert"]  # Default selected memory types
    selected_expert_id = None
    selected_client_id = None
    selected_domain = None
    
    if selected_org != "--Select an organization--":
        # Find the organization by name to get its ID
        for org in organizations:
            if org['org_name'] == selected_org:
                org_id = org['id']
                break
        
        # Get experts and domains for this organization
        experts = get_experts(org_id)
        expert_names = [expert["name"] for expert in experts] if experts else []
        domains = get_domains(org_id)
        domain_names = [domain["domain_name"] for domain in domains] if domains else []
        
        # Memory type selection with radio buttons
        st.subheader("Select Memory Type")
        memory_options = ["llm", "organization", "domain", "expert", "client", "myclient"]
        
        # Default to expert selected
        default_selection = "expert"
        default_index = memory_options.index(default_selection)
        
        # Create a radio button for memory type selection
        selected_memory = st.radio(
            "Memory Type",
            options=memory_options,
            index=default_index,
            format_func=lambda x: x.capitalize(),
            horizontal=True,
            key="memory_type_radio"
        )
        
        # For compatibility with existing code
        selected_memory_types = [selected_memory]
        
        # Show conditional dropdowns based on memory type
        selected_expert_id = None
        selected_client_id = None
        selected_domain = None
        selected_expert = None
        
        # Expert selection - show if expert or myclient is selected
        if selected_memory in ["expert", "myclient"]:
            if expert_names:
                selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
                
                if selected_expert != "--Select an expert--":
                    # Find the expert ID
                    for expert in experts:
                        if expert['name'] == selected_expert:
                            selected_expert_id = expert['id']
                            break
            else:
                st.warning("No experts found for this organization. Please create an expert first.")
        
        # Client selection - show if client or myclient is selected
        if selected_memory in ["client", "myclient"]:
            clients = get_clients(org_id)
            if clients:
                client_options = ["--Select a client--"] + [f"{client['client_name']}" for client in clients]
                selected_client = st.selectbox("Select Client", client_options)
                
                if selected_client != "--Select a client--":
                    # Find the client ID
                    for client in clients:
                        if client['client_name'] == selected_client:
                            selected_client_id = client['id']
                            break
            else:
                st.warning("No clients found for this organization. Please create a client first.")
        
        # Domain selection - show if domain is selected
        if selected_memory == "domain":
            if domain_names:
                selected_domain = st.selectbox("Select Domain", ["--Select a domain--"] + domain_names)
                if selected_domain == "--Select a domain--":
                    selected_domain = None
                    st.warning("Please select a domain for domain memory type.")
            else:
                st.warning("No domains found for this organization. Please create domains first.")
                # If no domains available, don't allow domain memory type
                st.error("Cannot use domain memory type without available domains. Please select a different memory type.")
                # Reset memory type to expert
                selected_memory = "expert"
    
    # Create unique keys for this conversation based on selections
    # Use the first selected memory type for the key if defined, otherwise use default
    conversation_key = f"{selected_org}_{selected_memory}"
    if selected_expert_id:
        conversation_key += f"_{selected_expert_id}"
    if selected_client_id:
        conversation_key += f"_{selected_client_id}"
    if selected_domain:
        conversation_key += f"_{selected_domain}"
    
    thread_key = f"thread_messages_{conversation_key}"
    thread_id_key = f"thread_id_{conversation_key}"
    
    # Initialize session state for thread ID and messages if not already present
    if thread_id_key not in st.session_state:
        st.session_state[thread_id_key] = None
    
    if thread_key not in st.session_state:
        st.session_state[thread_key] = []
    
    # Display chat messages
    for message in st.session_state[thread_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    can_chat = True
    
    # Validate that all required selections are made based on memory type
    if selected_memory == "expert" and not selected_expert_id:
        st.warning("Please select an expert to continue.")
        can_chat = False
    
    if selected_memory == "client" and not selected_client_id:
        st.warning("Please select a client to continue.")
        can_chat = False
    
    if selected_memory == "myclient" and (not selected_expert_id or not selected_client_id):
        st.warning("Please select both an expert and a client to continue.")
        can_chat = False
    
    if selected_memory == "domain" and not selected_domain:
        st.warning("Please select a domain to continue.")
        can_chat = False
    
    if can_chat:
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
                # Pass the thread_id if we have one from a previous interaction
                result, status_code = query_expert_with_assistant(
                    expert_name=selected_expert if selected_expert_id else None,
                    query=prompt,
                    memory_type=selected_memory,
                    org_id=org_id,
                    expert_id=selected_expert_id,
                    client_id=selected_client_id,
                    domain_name=selected_domain,
                    thread_id=st.session_state[thread_id_key]
                )
                
                if status_code == 200:
                    # Update thread ID if it was returned
                    if result.get("thread_id"):
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
        if selected_org == "--Select an organization--":
            with st.chat_message("assistant"):
                st.write("Please select an organization first.")
        # The other warnings are already displayed above

elif page == "Update":
    st.title("Update")
    
    # Memory type selection
    memory_type = st.radio(
        "Select Memory Type to Update:",
        ["organization", "domain", "expert", "client", "myclient"],
        horizontal=True
    )
    
    # Get organizations first (mandatory for all memory types)
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org_update = st.selectbox("Select Organization", org_options, key="update_org_select")
    
    # Initialize variables
    org_id = None
    domain_id = None
    expert_id = None
    client_id = None
    vector_name = None
    selected_name = "Unknown"
    selected_expert = None
    domain_name = None
    
    # Get organization ID if selected
    if selected_org_update != "--Select an organization--":
        # Find the organization by name to get its ID
        for org in organizations:
            if org['org_name'] == selected_org_update:
                org_id = org['id']
                print(f"Found organization: {org_id}")
                break
    
        # Based on memory type, show appropriate selection fields
        if memory_type == "organization":
            # For organization memory type, we just need the org_id
            vector_name = str(org_id)
            selected_name = selected_org_update
            
        elif memory_type == "domain":
            # Get domains for this organization
            domains = get_domains(org_id)
            domain_options = ["--Select a domain--"] + [domain["domain_name"] for domain in domains]
            selected_domain = st.selectbox("Select Domain", domain_options)
            
            if selected_domain != "--Select a domain--":
                # Find the domain ID
                domain_id = next((domain['id'] for domain in domains if domain['domain_name'] == selected_domain), None)
                if domain_id:
                    vector_name = str(domain_id)
                    selected_name = selected_domain
                    domain_name = selected_domain
                    print(f"Selected domain: {selected_domain}, ID: {domain_id}")
                
        elif memory_type == "expert":
            # Get experts for this organization
            experts = get_experts(org_id)
            expert_options = ["--Select an expert--"] + [expert["name"] for expert in experts]
            selected_expert = st.selectbox("Select Expert", expert_options)
            
            if selected_expert != "--Select an expert--":
                # Find the expert ID
                expert_id = next((expert['id'] for expert in experts if expert['name'] == selected_expert), None)
                if expert_id:
                    vector_name = str(expert_id)
                    selected_name = selected_expert
                    print(f"Selected expert: {selected_expert}, ID: {expert_id}")
                
        elif memory_type == "client":
            # Get clients for this organization
            response = requests.get(f"{API_BASE_URL}/api/clients", params={"org_id": org_id})
            if response.status_code == 200:
                clients = response.json()
                client_options = ["--Select a client--"] + [client["client_name"] for client in clients]
                selected_client = st.selectbox("Select Client", client_options)
                
                if selected_client != "--Select a client--":
                    # Find the client ID
                    client_id = next((client['id'] for client in clients if client['client_name'] == selected_client), None)
                    if client_id:
                        vector_name = str(client_id)
                        selected_name = selected_client
                        print(f"Selected client: {selected_client}, ID: {client_id}")
            else:
                st.error(f"Error fetching clients: {response.text}")
                
        elif memory_type == "myclient":
            # First select expert
            experts = get_experts(org_id)
            expert_options = ["--Select an expert--"] + [expert["name"] for expert in experts]
            selected_expert = st.selectbox("Select Expert", expert_options)
            
            if selected_expert != "--Select an expert--":
                # Find the expert ID
                expert_id = next((expert['id'] for expert in experts if expert['name'] == selected_expert), None)
                if expert_id:
                    # Then get clients for this expert
                    response = requests.get(
                        f"{API_BASE_URL}/api/clients", 
                        params={"org_id": org_id, "expert_id": expert_id}
                    )
                    if response.status_code == 200:
                        clients = response.json()
                        client_options = ["--Select a client--"] + [client["client_name"] for client in clients]
                        selected_client = st.selectbox("Select Client", client_options)
                        
                        if selected_client != "--Select a client--":
                            # Find the client ID
                            client_id = next((client['id'] for client in clients if client['client_name'] == selected_client), None)
                            if client_id:
                                vector_name = str("myclient" + str(client_id))
                                selected_name = f"{selected_expert}'s client {selected_client}"
                                print(f"Selected myclient: Expert {selected_expert} (ID: {expert_id}), Client {selected_client} (ID: {client_id})")
                    else:
                        st.error(f"Error fetching clients for expert: {response.text}")
    
    # Only proceed if we have a valid vector_name
    if vector_name and org_id:
        st.success(f"Updating {memory_type}: {selected_name}")
        
        # Get documents for this vector name
        response = requests.get(f"{API_BASE_URL}/api/documents/vector-name", params={"vector_name": vector_name})
        existing_documents = []
        if response.status_code == 200:
            existing_documents = response.json()
            print(f"Found {len(existing_documents)} existing documents for vector_name: {vector_name}")
        
        # Create form wrapper for the update process
        with st.form("update_memory_form"):
            # Create tabs for Context and Documents
            update_tabs = st.tabs(["Documents", "Context"])
            
            # Initialize variables
            formatted_qa_pairs = []
            doc_pairs = {}
            pdf_documents = {}
            
            # Expert Documents Tab
            with update_tabs[0]:
         
                existing_documents = get_documents_by_vector_name(vector_name) if vector_name else []
                existing_doc_names = []
                
                if existing_documents:
                    st.subheader("Current Documents")
                    # Create a dictionary to store document selection status
                    doc_selections = {}
                    
                    # Display existing documents with checkboxes
                    for doc in existing_documents:
                        doc_name = doc.get("name", "Unnamed Document")
                        existing_doc_names.append(doc_name)
                        doc_url = doc.get("document_link", "")
                        # Default to selected (True)
                        doc_selections[doc_name] = st.checkbox(f"{doc_name}", value=True, key=f"doc_{doc.get('id')}")
                    
                    # Add selected existing documents with their original URLs
                    for doc in existing_documents:
                        doc_name = doc.get("name", "Unnamed Document")
                        if doc_selections.get(doc_name, False):
                            doc_pairs[doc_name] = doc.get("document_link", "")
                else:
                    memory_name = selected_name if selected_name != "Unknown" else memory_type
                    st.info(f"No existing documents found for {memory_type} {memory_name}.")
            
                # Create tabs for URL and PDF documents
                doc_tabs = st.tabs(["Document URLs", "PDF Uploads"])
                
                # Initialize active tab in session state if not present
                if 'active_update_doc_tab' not in st.session_state:
                    st.session_state.active_update_doc_tab = 0
                    
                # Add radio buttons to track which tab is active
                st.session_state.active_update_doc_tab = st.radio(
                    "Select document type to add:",
                    options=[0, 1],
                    format_func=lambda x: ["Document URLs", "PDF Uploads"][x],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="update_doc_tab_selector"
                )
                
                # URL Documents Tab
                with doc_tabs[0]:
                    st.subheader("Add New URL Documents")
                    # Create columns for document name and URL inputs
                    new_doc_cols = st.columns(2)
                    with new_doc_cols[0]:
                        st.write("Document Name")
                    with new_doc_cols[1]:
                        st.write("Document URL")
                
                with doc_tabs[0]:
                    # Initialize new document pairs dictionary
                    new_doc_pairs = {}
                    
                    # Start with 3 empty document input pairs
                    num_new_doc_inputs = st.session_state.get('expert_update_doc_inputs', 3)
                    
                    for i in range(num_new_doc_inputs):
                        new_doc_cols = st.columns(2)
                        with new_doc_cols[0]:
                            new_doc_name = st.text_input(f"New Name {i+1}", key=f"expert_update_doc_name_{i}", label_visibility="collapsed")
                        with new_doc_cols[1]:
                            new_doc_url = st.text_input(f"New URL {i+1}", key=f"expert_update_doc_url_{i}", label_visibility="collapsed")
                        
                        if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                            if new_doc_name not in existing_doc_names and new_doc_name not in new_doc_pairs:
                                new_doc_pairs[new_doc_name] = new_doc_url
                            else:
                                st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
                    
                    # We can't use st.button() inside a form, so we'll handle this with the main form submission
                    
                    # Add new documents to the main document pairs
                    doc_pairs.update(new_doc_pairs)
            
                # PDF Documents Tab
                with doc_tabs[1]:
                    st.subheader("Add New PDF Documents")
                    
                    # Start with 3 empty PDF upload slots
                    num_pdf_uploads = st.session_state.get('expert_update_pdf_uploads', 3)
                    
                    for i in range(num_pdf_uploads):
                        pdf_cols = st.columns(2)
                        with pdf_cols[0]:
                            pdf_name = st.text_input(f"PDF Name {i+1}", key=f"expert_update_pdf_name_{i}")
                        with pdf_cols[1]:
                            pdf_file = st.file_uploader(f"Upload PDF {i+1}", type=["pdf"], key=f"expert_update_pdf_file_{i}")
                        
                        if pdf_name and pdf_file is not None:  # Only add if both name and file are provided
                            # Check if the document name already exists
                            if pdf_name not in existing_doc_names and pdf_name not in doc_pairs and pdf_name not in pdf_documents:
                                # Upload PDF via API endpoint without reading into memory
                                try:
                                    files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
                                    data = {"pdf_name": pdf_name}
                                    
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/upload-pdf/",
                                        files=files,
                                        data=data
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        pdf_documents[pdf_name] = result["file_path"]
                                        st.success(f"PDF uploaded: {result['message']}")
                                    else:
                                        st.error(f"Failed to upload PDF: {response.text}")
                                        
                                except Exception as e:
                                    st.error(f"Error uploading PDF: {str(e)}")
                            else:
                                st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")
                    
                    # We can't use st.button() inside a form, so we'll handle this with the main form submission
        
                # Add buttons for adding more documents and updating expert
                col1, col2, col3 = st.columns(3)
                with col1:
                    add_more_url = st.form_submit_button("Add More URL Documents")
                with col2:
                    add_more_pdf = st.form_submit_button("Add More PDF Documents")
                with col3:
                    submitted = st.form_submit_button("Update Expert")

            # Context Tab
            with update_tabs[1]:
                # For now, only show context update for experts
                if memory_type == "expert" and expert_id:
                    # Create a container for displaying the current context
                    current_context_container = st.container()
                    
                    # Get and display current context
                    current_context = get_expert_context(expert_id)
                    with current_context_container:
                        st.subheader("Current Context")
                        st.text_area("Current Context", value=current_context["context"], height=150, disabled=True, key="current_context")
                    
                    st.subheader("Update Context - Answer the following questions")
                    
                    # Questions from the pediatrician_persona_config.json
                    questions = [
                        "Explain more about your experience",
                        "What is your communication preference with clients?",
                    ]
                    
                    # Dictionary to store answers
                    new_qa_pairs = {}
                    
                    # Create a text box for each question
                    for i, question in enumerate(questions):
                        st.write(f"**{question}**")
                        answer = st.text_area(f"Answer {i+1}", key=f"update_answer_{i}", height=100)
                        if answer:  # Only add non-empty answers
                            new_qa_pairs[question] = answer
                    
                    # Format qa_pairs as a list of dictionaries with question and answer keys
                    formatted_qa_pairs = []
                    for question, answer in new_qa_pairs.items():
                        formatted_qa_pairs.append({"question": question, "answer": answer})
                else:
                    st.info(f"Context updates are currently only supported for expert memory type.")
                
        # Handle form submission
        if submitted:
            has_updates = len(formatted_qa_pairs) > 0 or len(doc_pairs) > 0 or len(pdf_documents) > 0
            
            if has_updates:
                # Call the combined API endpoint
                result, status_code = update_memory(
                    memory_type=memory_type,
                    org_id=org_id,
                    expert_id=expert_id,
                    client_id=client_id,
                    expert_name=selected_expert if selected_expert and selected_expert != "--Select an expert--" else "",
                    domain_name=domain_name if isinstance(domain_name, str) else (domain_name[0] if isinstance(domain_name, list) and domain_name else ""),
                    qa_pairs=formatted_qa_pairs if formatted_qa_pairs else None,
                    document_urls=doc_pairs if doc_pairs else None,
                    pdf_documents=pdf_documents if pdf_documents else None
                )
                
                if status_code == 200:
                    memory_name = selected_name if selected_name != "Unknown" else memory_type
                    st.success(f"{memory_type.capitalize()} {memory_name} updated successfully!")
                    
                    # Show update details
                    with st.expander("Update Details"):
                        st.write(f"**Status:** {result.get('status', 'Unknown')}")
                        st.write(f"**Message:** {result.get('message', 'No message provided')}")
                        
                        # If context was updated, refresh it
                        if len(formatted_qa_pairs) > 0:
                            current_context = get_expert_context(selected_expert_id)
                            with update_tabs[0]:
                                with current_context_container:
                                    st.subheader("Current Context (Updated)")
                                    st.text_area("Current Context", value=current_context.get("context"), height=150, disabled=True, key="updated_context")
                else:
                    st.error(f"Error updating expert: {result.get('error', 'Unknown error')}")
            else:
                st.warning("No updates provided. Please add context questions, URL documents, or PDF documents.")
        
        # Handle adding more document inputs
        if add_more_url:
            st.session_state.expert_update_doc_inputs = st.session_state.get('expert_update_doc_inputs', 3) + 1
            st.experimental_rerun()
        
        if add_more_pdf:
            st.session_state.expert_update_pdf_uploads = st.session_state.get('expert_update_pdf_uploads', 3) + 1
            st.experimental_rerun()
    else:
        st.info("Please select an expert to update.")

elif page == "Update Expert":
    st.title("Update Expert")
    
    # Get organizations first
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org_update = st.selectbox("Select Organization", org_options, key="update_org_select")
    
    experts = []
    expert_names = []
    org_id = None
    domain_names = []
    if selected_org_update != "--Select an organization--":
        # Find the organization by name to get its ID
        for org in organizations:
            if org['org_name'] == selected_org_update:
                org_id = org['id']
                print(f"Found {org_id}")
                break
    
        # Get experts for this organization
        experts = get_experts(org_id)
        expert_names = [expert["name"] for expert in experts] if experts else []
    print(f"Found {len(experts)} experts and their names are {expert_names}")
    
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    selected_expert_id = next((expert['id'] for expert in experts if expert['name'] == selected_expert), None)
    if selected_expert != "--Select an expert--":
        # Get domain for this expert
        domain_name = get_expert_domains(selected_expert_id)
        expert_context = get_expert_context(selected_expert_id)
        #st.success(f"Expert {selected_expert} is associated with domain: {domain_name}")
        #st.success(f"Expert {selected_expert} is associated with context: {expert_context.get('context', '')}")

        # Create form wrapper for the entire update process
        with st.form("update_expert_form"):
            # Create tabs for Context and Documents
            update_tabs = st.tabs(["Expert Docs", "Expert Context"])
            
            # Initialize variables
            formatted_qa_pairs = []
            doc_pairs = {}
            pdf_documents = {}
            
            # Expert Docs Tab
            with update_tabs[0]:
                # Get existing documents for this expert/domain combination
                existing_documents = get_documents(selected_expert_id)
                existing_doc_names = []
                
                if existing_documents:
                    st.subheader("Current Documents")
                    # Create a dictionary to store document selection status
                    doc_selections = {}
                    
                    # Display existing documents with checkboxes
                    for doc in existing_documents:
                        doc_name = doc.get("name", "Unnamed Document")
                        existing_doc_names.append(doc_name)
                        doc_url = doc.get("document_link", "")
                        # Default to selected (True)
                        doc_selections[doc_name] = st.checkbox(f"{doc_name}", value=True, key=f"doc_{doc.get('id')}")
                    
                    # Add selected existing documents with their original URLs
                    for doc in existing_documents:
                        doc_name = doc.get("name", "Unnamed Document")
                        if doc_selections.get(doc_name, False):
                            doc_pairs[doc_name] = doc.get("document_link", "")
                else:
                    st.info(f"No existing documents found for expert {selected_expert}.")
            
                # Create tabs for URL and PDF documents
                doc_tabs = st.tabs(["Document URLs", "PDF Uploads"])
                
                # Initialize active tab in session state if not present
                if 'active_update_doc_tab' not in st.session_state:
                    st.session_state.active_update_doc_tab = 0
                    
                # Add radio buttons to track which tab is active
                st.session_state.active_update_doc_tab = st.radio(
                    "Select document type to add:",
                    options=[0, 1],
                    format_func=lambda x: ["Document URLs", "PDF Uploads"][x],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="update_doc_tab_selector"
                )
                
                # URL Documents Tab
                with doc_tabs[0]:
                    st.subheader("Add New URL Documents")
                    # Create columns for document name and URL inputs
                    new_doc_cols = st.columns(2)
                    with new_doc_cols[0]:
                        st.write("Document Name")
                    with new_doc_cols[1]:
                        st.write("Document URL")
                
                with doc_tabs[0]:
                    # Initialize new document pairs dictionary
                    new_doc_pairs = {}
                    
                    # Start with 3 empty document input pairs
                    num_new_doc_inputs = st.session_state.get('expert_update_doc_inputs', 3)
                    
                    for i in range(num_new_doc_inputs):
                        new_doc_cols = st.columns(2)
                        with new_doc_cols[0]:
                            new_doc_name = st.text_input(f"New Name {i+1}", key=f"expert_update_doc_name_{i}", label_visibility="collapsed")
                        with new_doc_cols[1]:
                            new_doc_url = st.text_input(f"New URL {i+1}", key=f"expert_update_doc_url_{i}", label_visibility="collapsed")
                        
                        if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                            if new_doc_name not in existing_doc_names and new_doc_name not in new_doc_pairs:
                                new_doc_pairs[new_doc_name] = new_doc_url
                            else:
                                st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
                    
                    # We can't use st.button() inside a form, so we'll handle this with the main form submission
                    
                    # Add new documents to the main document pairs
                    doc_pairs.update(new_doc_pairs)
            
                # PDF Documents Tab
                with doc_tabs[1]:
                    st.subheader("Add New PDF Documents")
                    
                    # Start with 3 empty PDF upload slots
                    num_pdf_uploads = st.session_state.get('expert_update_pdf_uploads', 3)
                    
                    for i in range(num_pdf_uploads):
                        pdf_cols = st.columns(2)
                        with pdf_cols[0]:
                            pdf_name = st.text_input(f"PDF Name {i+1}", key=f"expert_update_pdf_name_{i}")
                        with pdf_cols[1]:
                            pdf_file = st.file_uploader(f"Upload PDF {i+1}", type=["pdf"], key=f"expert_update_pdf_file_{i}")
                        
                        if pdf_name and pdf_file is not None:  # Only add if both name and file are provided
                            # Check if the document name already exists
                            if pdf_name not in existing_doc_names and pdf_name not in doc_pairs and pdf_name not in pdf_documents:
                                # Upload PDF via API endpoint without reading into memory
                                try:
                                    files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
                                    data = {"pdf_name": pdf_name}
                                    
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/upload-pdf/",
                                        files=files,
                                        data=data
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        pdf_documents[pdf_name] = result["file_path"]
                                        st.success(f"PDF uploaded: {result['message']}")
                                    else:
                                        st.error(f"Failed to upload PDF: {response.text}")
                                        
                                except Exception as e:
                                    st.error(f"Error uploading PDF: {str(e)}")
                            else:
                                st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")
                    
                    # We can't use st.button() inside a form, so we'll handle this with the main form submission
        
                # Add buttons for adding more documents and updating expert
                col1, col2, col3 = st.columns(3)
                with col1:
                    add_more_url = st.form_submit_button("Add More URL Documents")
                with col2:
                    add_more_pdf = st.form_submit_button("Add More PDF Documents")
                with col3:
                    submitted = st.form_submit_button("Update Expert")

            with update_tabs[1]:
                # Create a container for displaying the current context
                current_context_container = st.container()
                
                # Get and display current context
                current_context = get_expert_context(selected_expert_id)
                with current_context_container:
                    st.subheader("Current Context")
                    st.text_area("Current Context", value=current_context["context"], height=150, disabled=True, key="current_context")
                
                st.subheader("Update Expert Context - Answer the following questions")

            with update_tabs[1]:
                # Questions from the pediatrician_persona_config.json
                questions = [
                    "Explain more about your experience",
                    "What is your communication preference with clients?",
                ]
                
                # Dictionary to store answers
                new_qa_pairs = {}
                
                # Create a text box for each question
                for i, question in enumerate(questions):
                    st.write(f"**{question}**")
                    answer = st.text_area(f"Answer {i+1}", key=f"update_answer_{i}", height=100)
                    if answer:  # Only add non-empty answers
                        new_qa_pairs[question] = answer
                
                # Format qa_pairs as a list of dictionaries with question and answer keys
                formatted_qa_pairs = []
                for question, answer in new_qa_pairs.items():
                    formatted_qa_pairs.append({"question": question, "answer": answer})
                
        # Handle form submission
        if submitted:
            has_updates = len(formatted_qa_pairs) > 0 or len(doc_pairs) > 0 or len(pdf_documents) > 0
            
            if has_updates:
                # Call the combined API endpoint
                result, status_code = update_memory(
                    memory_type="expert",
                    org_id=org_id,
                    expert_id=selected_expert_id,
                    client_id=None,  # Not needed for expert memory type
                    expert_name=selected_expert if selected_expert and selected_expert != "--Select an expert--" else "",
                    domain_name=domain_name if isinstance(domain_name, str) else (domain_name[0] if isinstance(domain_name, list) and domain_name else ""),
                    qa_pairs=formatted_qa_pairs if formatted_qa_pairs else None,
                    document_urls=doc_pairs if doc_pairs else None,
                    pdf_documents=pdf_documents if pdf_documents else None
                )
                
                if status_code == 200:
                    st.success(f"Expert {selected_expert} updated successfully!")
                    
                    # Show update details
                    with st.expander("Update Details"):
                        st.write(f"**Status:** {result.get('status', 'Unknown')}")
                        st.write(f"**Message:** {result.get('message', 'No message provided')}")
                        
                        # If context was updated, refresh it
                        if len(formatted_qa_pairs) > 0:
                            current_context = get_expert_context(selected_expert_id)
                            with update_tabs[0]:
                                with current_context_container:
                                    st.subheader("Current Context (Updated)")
                                    st.text_area("Current Context", value=current_context.get("context"), height=150, disabled=True, key="updated_context")
                else:
                    st.error(f"Error updating expert: {result.get('error', 'Unknown error')}")
            else:
                st.warning("No updates provided. Please add context questions, URL documents, or PDF documents.")
        
        # Handle adding more document inputs
        if add_more_url:
            st.session_state.expert_update_doc_inputs = st.session_state.get('expert_update_doc_inputs', 3) + 1
            st.experimental_rerun()
        
        if add_more_pdf:
            st.session_state.expert_update_pdf_uploads = st.session_state.get('expert_update_pdf_uploads', 3) + 1
            st.experimental_rerun()
    else:
        st.info("Please select an expert to update.")

# Create client page
elif page == "Create client":
    st.title("Create Client")
    st.write("Create a new client with JSON data or update an existing client.")
    
    # Initialize session state variables if needed
    if "clear_client_form" in st.session_state and st.session_state["clear_client_form"]:
        # Reset the form by removing the flag
        st.session_state["clear_client_form"] = False
        # We don't need to clear the inputs here as they'll be reset on rerun
    
    # Get organizations first
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org = st.selectbox("Select Organization", org_options, key="client_org_select")
    
    if selected_org != "--Select an organization--":
        # Find the organization by name to get its ID
        org_id = None
        for org in organizations:
            if org['org_name'] == selected_org:
                org_id = org['id']
                break
        
        # Get experts for the selected organization
        experts = get_experts(org_id)
        expert_options = ["--Select an expert--"] + [f"{expert['name']}" for expert in experts]
        selected_expert = st.selectbox("Select Expert", expert_options, key="client_expert_select")
        
        if selected_expert != "--Select an expert--":
            # Find the expert by name to get its ID
            expert_id = None
            for expert in experts:
                if expert['name'] == selected_expert:
                    expert_id = expert['id']
                    break
            
            # Generate random org_client_id internally (not visible in UI)
            import random
            org_client_id = random.randint(1000, 9999)
            
            # Client name input
            client_name = st.text_input("Client Name", key="client_name_input")
            
            # JSON data input
            st.subheader("Client Data (JSON)")
            
            # Option to load sample JSON
            sample_option = st.selectbox(
                "Load sample JSON",
                ["None", "Sample 1", "Sample 2", "Sample 3"],
                key="sample_json_select"
            )
    
            # Load sample JSON if selected
            json_filename = ""
            other_doc = {}
            sample_json = {}
            if sample_option != "None":
                sample_num = sample_option.split()[-1]
                try:
                    with open(f"/Users/karthi/CascadeProjects/AI Clone/Docs/sample{sample_num}.json", "r") as f:
                        # Read the content of the file
                        json_filename = f"sample{sample_num}.json"
                        content = f.read()
                        #if this is retrieved from the database, it will be a json object or string
                        # DATABASE VERSION (COMMENTED OUT):
                        # if database_response.data and len(database_response.data) > 0:
                        #     # Extract the JSONB content from the response
                        #     content = database_response.data[0]["content"]
                        #     
                        #     # Process the JSON data
                        #     api_response = requests.post(
                        #         f"{API_BASE_URL}/api/parse-json-string-json",
                        #         json={"json_data": content}
                        #     )
                        #     
                        #     if api_response.status_code == 200:
                        #         result = api_response.json()
                        #         return result['data'], json_filename
                        #     else:
                        #         st.error(f"Failed to parse JSON: {api_response.text}")
                        #         return {}, ""
                        # else:
                        #     st.error(f"Sample {json_filename} not found in database")
                        #     return {}, ""
                        response = requests.post(
                            f"{API_BASE_URL}/api/parse-json-string",
                            data={"json_string": content}
                        )
                                
                        if response.status_code == 200:
                            result = response.json()
                            sample_json = result['data']
                            st.success(f"JSON parsed: {result['message']}")
                        else:
                            st.error(f"Failed to parse JSON: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error loading sample JSON: {str(e)}")
                    print(f"[UI ERROR] Sample JSON loading error: {str(e)}")

            
            # JSON editor
            json_str = st.text_area(
                "Edit JSON data",
                value=json.dumps(sample_json, indent=2) if sample_json else "",
                height=300,
                key="client_json_input"
            )    
            # Validate JSON
            valid_json = True
            client_data = {}
            if json_str:
                try:
                    client_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    valid_json = False
                    st.error(f"Invalid JSON: {str(e)}")
    
            # Only add to other_doc if we have a valid filename and client data
            if json_filename and client_data:
                other_doc[json_filename] = client_data

            # Document inputs with name-URL pairs
            st.subheader("Document Inputs")
            st.write("Add both URL documents and PDF uploads as needed:")
            
            # Document tabs
            tab_names = ["Document URLs", "PDF Uploads"]
            doc_tabs = st.tabs(tab_names)
            
            # Initialize document pairs dictionary
            doc_pairs = {}
            
            # Initialize PDF documents dictionary
            pdf_documents = {}
    
            # URL Documents Tab
            with doc_tabs[0]:
                # Create columns for document name and URL inputs
                doc_cols = st.columns(2)
                with doc_cols[0]:
                    st.write("Document Name")
                with doc_cols[1]:
                    st.write("Document URL")
            
                # Start with 3 empty document input pairs
                num_doc_inputs = st.session_state.get('client_doc_inputs', 3)
                
                for i in range(num_doc_inputs):
                    doc_cols = st.columns(2)
                    with doc_cols[0]:
                        doc_name = st.text_input(f"Name {i+1}", key=f"client_doc_name_{i}", label_visibility="collapsed")
                    with doc_cols[1]:
                        doc_url = st.text_input(f"URL {i+1}", key=f"client_doc_url_{i}", label_visibility="collapsed")
                    
                    if doc_name and doc_url:  # Only add if both name and URL are provided
                        # Check if the document name already exists in our pairs
                        if doc_name not in doc_pairs:
                            doc_pairs[doc_name] = doc_url
                        else:
                            st.warning(f"Document name '{doc_name}' already exists. Please use a different name.")
    
            # PDF Documents Tab
            with doc_tabs[1]:
                st.write("Upload PDF documents with names")
                
                # Start with 3 empty PDF upload slots
                num_pdf_uploads = st.session_state.get('client_pdf_uploads', 3)
                
                for i in range(num_pdf_uploads):
                    pdf_cols = st.columns(2)
                    with pdf_cols[0]:
                        pdf_name = st.text_input(f"PDF Name {i+1}", key=f"client_pdf_name_{i}")
                    with pdf_cols[1]:
                        pdf_file = st.file_uploader(f"Upload PDF {i+1}", type=["pdf"], key=f"client_pdf_file_{i}")
                    
                    if pdf_name and pdf_file is not None:  # Only add if both name and file are provided
                        # Check if the document name already exists
                        if pdf_name not in pdf_documents:
                            # Upload the PDF file
                            try:
                                # Create form data for the file upload
                                files = {'file': (pdf_file.name, pdf_file.getvalue(), 'application/pdf')}
                                data = {'pdf_name': pdf_name}
                                
                                response = requests.post(
                                    f"{API_BASE_URL}/api/upload-pdf/",
                                    files=files,
                                    data=data
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    pdf_documents[pdf_name] = result["file_path"]
                                    st.success(f"PDF uploaded: {result['message']}")
                                else:
                                    st.error(f"Failed to upload PDF: {response.text}")
                                    
                            except Exception as e:
                                st.error(f"Error uploading PDF: {str(e)}")
                        else:
                            st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")

            # Use a form instead of a button to prevent auto-resubmission
            with st.form("client_create_form"):
                # Submit buttons for the form
                col1, col2 = st.columns(2)
                with col1:
                    add_more = st.form_submit_button("Add Another Document")
                with col2:
                    submit_button = st.form_submit_button("Create/Update Client")
            
            # Handle the 'Add Another Document' button
            if add_more:
                # Add both URL and PDF inputs
                st.session_state.client_doc_inputs = st.session_state.get('client_doc_inputs', 3) + 1
                st.session_state.client_pdf_uploads = st.session_state.get('client_pdf_uploads', 3) + 1
                st.experimental_rerun()
            
            if submit_button:
                if not client_name:
                    st.error("Please enter a client name")
                elif not json_str:
                    st.error("Please enter JSON data")
                elif not valid_json:
                    st.error("Please fix the JSON errors before submitting")
                else:
                    # Check if we've already processed this submission
                    submission_key = f"{client_name}_{hash(json_str)}"
                    if "last_client_submission" not in st.session_state or st.session_state["last_client_submission"] != submission_key:
                        # Create other_doc with client data using the filename as the key
                        
                        # Call API to create/update client
                        result, status_code = create_client(client_name, client_data, org_id, expert_id, org_client_id, doc_pairs, pdf_documents, other_doc)
                        
                        # Store this submission to prevent duplicates
                        st.session_state["last_client_submission"] = submission_key
                        
                        if status_code == 200:
                            st.success(f"Client '{client_name}' created/updated successfully!")
                            
                            # Show details
                            with st.expander("Details"):
                                st.write(f"**Status:** {result.get('status', 'Unknown')}")
                                st.write(f"**Message:** {result.get('message', 'No message provided')}")
                                st.write(f"**Client Name:** {result.get('client_name', 'Unknown')}")
                                st.write(f"**Org Client ID:** {result.get('org_client_id', 'Unknown')}")
                                
                            # Clear form on next load without triggering rerun
                            st.session_state["clear_client_form"] = True
                        else:
                            st.error(f"Error creating/updating client: {result.get('error', 'Unknown error')}")
                    else:
                        st.info("Form already submitted. Refresh the page to submit again.")
                        # Clear the submission tracking after showing the message
                        del st.session_state["last_client_submission"]
        else:
            st.info("Please select an organization and expert to create a client.")

elif page == "Create Specialty":
    st.title("Create Specialty")
    st.write("Create a new specialty (domain) in the hospital with associated documents.")
    
    # Get organizations first
    organizations = get_organizations()
    org_options = ["--Select an organization--"] + [f"{org['org_name']}" for org in organizations]
    selected_org = st.selectbox("Select Organization", org_options)
    
    if selected_org != "--Select an organization--":
        # Find the organization by name to get its ID
        org_id = None
        for org in organizations:
            if org['org_name'] == selected_org:
                org_id = org['id']
                break
        
        with st.form("specialty_form"):
            specialty_name = st.text_input("Specialty Name (Domain)")
            
            # Document inputs with name-URL pairs
            st.subheader("Document Inputs")
            st.write("Add both URL documents and PDF uploads as needed:")
            
            # Document tabs
            tab_names = ["Document URLs", "PDF Uploads"]
            doc_tabs = st.tabs(tab_names)
            
            # Initialize document pairs dictionary
            doc_pairs = {}
            
            # Initialize PDF documents dictionary
            pdf_documents = {}
            
            # URL Documents Tab
            with doc_tabs[0]:
                # Create columns for document name and URL inputs
                doc_cols = st.columns(2)
                with doc_cols[0]:
                    st.write("Document Name")
                with doc_cols[1]:
                    st.write("Document URL")
            
                # Start with 3 empty document input pairs
                num_doc_inputs = st.session_state.get('specialty_doc_inputs', 3)
                
                for i in range(num_doc_inputs):
                    doc_cols = st.columns(2)
                    with doc_cols[0]:
                        doc_name = st.text_input(f"Name {i+1}", key=f"specialty_doc_name_{i}", label_visibility="collapsed")
                    with doc_cols[1]:
                        doc_url = st.text_input(f"URL {i+1}", key=f"specialty_doc_url_{i}", label_visibility="collapsed")
                    
                    if doc_name and doc_url:  # Only add if both name and URL are provided
                        # Check if the document name already exists in our pairs
                        if doc_name not in doc_pairs:
                            doc_pairs[doc_name] = doc_url
                        else:
                            st.warning(f"Document name '{doc_name}' already exists. Please use a different name.")
            
            # PDF Documents Tab
            with doc_tabs[1]:
                st.write("Upload PDF documents with names")
                
                # Start with 3 empty PDF upload slots
                num_pdf_uploads = st.session_state.get('specialty_pdf_uploads', 3)
                
                for i in range(num_pdf_uploads):
                    pdf_cols = st.columns(2)
                    with pdf_cols[0]:
                        pdf_name = st.text_input(f"PDF Name {i+1}", key=f"specialty_pdf_name_{i}")
                    with pdf_cols[1]:
                        pdf_file = st.file_uploader(f"Upload PDF {i+1}", type=["pdf"], key=f"specialty_pdf_file_{i}")
                    
                    if pdf_name and pdf_file is not None:  # Only add if both name and file are provided
                        # Check if the document name already exists
                        if pdf_name not in pdf_documents and pdf_name not in doc_pairs:
                            # Upload PDF via API endpoint without reading into memory
                            try:
                                files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
                                data = {"pdf_name": pdf_name}
                                
                                response = requests.post(
                                    f"{API_BASE_URL}/api/upload-pdf/",
                                    files=files,
                                    data=data
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    pdf_documents[pdf_name] = result["file_path"]
                                    st.success(f"PDF uploaded: {result['message']}")
                                else:
                                    st.error(f"Failed to upload PDF: {response.text}")
                                    
                            except Exception as e:
                                st.error(f"Error uploading PDF: {str(e)}")
                        else:
                            st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")
            
            # Submit buttons for the form
            col1, col2 = st.columns(2)
            with col1:
                add_more = st.form_submit_button("Add Another Document")
            with col2:
                submitted = st.form_submit_button("Create Specialty")
        
        # Handle the 'Add Another Document' button
        if add_more:
            # Add both URL and PDF inputs
            st.session_state.specialty_doc_inputs = st.session_state.get('specialty_doc_inputs', 3) + 1
            st.session_state.specialty_pdf_uploads = st.session_state.get('specialty_pdf_uploads', 3) + 1
            st.experimental_rerun()
        
        # Process form submission
        if submitted:
            # Check if we have at least one document (either URL or PDF)
            has_documents = len(doc_pairs) > 0 or len(pdf_documents) > 0
                
            if specialty_name and has_documents:
                # Create specialty/domain
                try:
                    request_data = {
                        "org_id": org_id,
                        "domains": [{
                            "domain_name": specialty_name,
                            "document_urls": doc_pairs,
                            "pdf_documents": pdf_documents,
                            "other_doc": {}
                        }]
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/domains/initialize",
                        json=request_data
                    )
                    
                    if response.status_code == 200:
                        st.success(f"Specialty '{specialty_name}' created successfully!")
                        # Clear the session state for uploads to avoid resubmission issues
                        if 'specialty_pdf_uploads' in st.session_state:
                            del st.session_state['specialty_pdf_uploads']
                        if 'specialty_doc_inputs' in st.session_state:
                            del st.session_state['specialty_doc_inputs']
                    else:
                        st.error(f"Error creating specialty: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error creating specialty: {str(e)}")
            else:
                if not specialty_name:
                    st.warning("Please enter a Specialty Name")
                elif not has_documents:
                    st.warning("Please add at least one document (URL or PDF)")
                    
            # Show a summary of what was submitted
            if has_documents:
                with st.expander("Submission Summary"):
                    st.write(f"**Specialty Name:** {specialty_name}")
                    st.write(f"**Organization:** {selected_org.split('(')[0].strip()}")
                    st.write(f"**URL Documents:** {len(doc_pairs)}")
                    st.write(f"**PDF Documents:** {len(pdf_documents)}")
    else:
        st.info("Please select an organization to create a specialty.")
            
elif page == "Create Hospital":
    st.title("Create Hospital")
    st.write("Create a hospital with its general information documents.")
    
    # Initialize session state variables
    if "clear_hospital_form" in st.session_state and st.session_state["clear_hospital_form"]:
        st.session_state["clear_hospital_form"] = False
    
    with st.form("hospital_specialty_form"):
        st.subheader("Hospital Information")
        
        # Hospital basic info
        hospital_name = st.text_input("Hospital Name", key="hospital_name_input")
        
        # Hospital data (JSON)
        st.subheader("Hospital Data (JSON)")
        
        # Option to load sample JSON
        sample_option = st.selectbox(
            "Load sample hospital JSON",
            ["None", "OrgSample 1", "OrgSample 2", "OrgSample 3"],
            key="hospital_sample_json_select"
        )
        
        # Load sample JSON if selected
        sample_json = {}
        if sample_option != "None":
            sample_num = sample_option.split()[-1]
            try:
                with open(f"/Users/karthi/CascadeProjects/AI Clone/Docs/orgsample{sample_num}.json", "r") as f:
                    content = f.read()
                    json_str = content.strip()
                    brace_count = 0
                    end_pos = 0
                    
                    for i, char in enumerate(json_str):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    if end_pos > 0:
                        first_json = json_str[:end_pos]
                        sample_json = json.loads(first_json)
                        st.success(f"Loaded {sample_option} JSON data")
                    else:
                        st.error("Could not find a complete JSON object")
            except Exception as e:
                st.error(f"Error loading sample JSON: {str(e)}")
        
        # JSON editor for hospital data
        hospital_json_str = st.text_area(
            "Edit Hospital JSON data",
            value=json.dumps(sample_json, indent=2) if sample_json else "",
            height=200,
            key="hospital_json_input"
        )
        
        # Validate hospital JSON
        valid_hospital_json = True
        hospital_data = {}
        if hospital_json_str:
            try:
                hospital_data = json.loads(hospital_json_str)
            except json.JSONDecodeError as e:
                valid_hospital_json = False
                st.error(f"Invalid Hospital JSON: {str(e)}")
        
        # Hospital Documents Section
        st.subheader("Hospital Documents")
        
        # Create tabs for hospital documents
        hospital_doc_tabs = st.tabs(["Document URLs", "PDF Uploads"])
        
        hospital_doc_pairs = {}
        hospital_pdf_documents = {}
        
        # Hospital URL Documents Tab
        with hospital_doc_tabs[0]:
            st.write("Hospital Document URLs")
            num_hospital_docs = st.session_state.get('hospital_doc_inputs', 2)
            
            for i in range(num_hospital_docs):
                doc_cols = st.columns(2)
                with doc_cols[0]:
                    doc_name = st.text_input(f"Hospital Doc Name {i+1}", key=f"hospital_doc_name_{i}")
                with doc_cols[1]:
                    doc_url = st.text_input(f"Hospital Doc URL {i+1}", key=f"hospital_doc_url_{i}")
                
                if doc_name and doc_url:
                    if doc_name not in hospital_doc_pairs:
                        hospital_doc_pairs[doc_name] = doc_url
                    else:
                        st.warning(f"Hospital document name '{doc_name}' already exists.")
        
        # Hospital PDF Documents Tab
        with hospital_doc_tabs[1]:
            st.write("Upload Hospital PDF documents")
            num_hospital_pdfs = st.session_state.get('hospital_pdf_uploads', 2)
            
            for i in range(num_hospital_pdfs):
                pdf_cols = st.columns(2)
                with pdf_cols[0]:
                    pdf_name = st.text_input(f"Hospital PDF Name {i+1}", key=f"hospital_pdf_name_{i}")
                with pdf_cols[1]:
                    pdf_file = st.file_uploader(f"Upload Hospital PDF {i+1}", type=["pdf"], key=f"hospital_pdf_file_{i}")
                
                if pdf_name and pdf_file is not None:
                    if pdf_name not in hospital_pdf_documents and pdf_name not in hospital_doc_pairs:
                        try:
                            files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
                            data = {"pdf_name": pdf_name}
                            
                            response = requests.post(
                                f"{API_BASE_URL}/api/upload-pdf/",
                                files=files,
                                data=data
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                hospital_pdf_documents[pdf_name] = result["file_path"]
                                st.success(f"Hospital PDF uploaded: {result['message']}")
                            else:
                                st.error(f"Failed to upload hospital PDF: {response.text}")
                        except Exception as e:
                            st.error(f"Error uploading hospital PDF: {str(e)}")
                    else:
                        st.warning(f"Hospital document name '{pdf_name}' already exists.")
        
        # Form submission buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Hospital")
        with col2:
            add_more_hospital_docs = st.form_submit_button("Add More Hospital Documents")
    
    # Handle adding more hospital documents
    if add_more_hospital_docs:
        st.session_state.hospital_doc_inputs = st.session_state.get('hospital_doc_inputs', 2) + 1
        st.experimental_rerun()
    
    # Process form submission
    if submitted:
        if not hospital_name:
            st.error("Please enter a hospital name")
        elif hospital_json_str and not valid_hospital_json:
            st.error("Please fix the hospital JSON errors before submitting")
        else:
            # Check if we've already processed this submission
            submission_key = f"{hospital_name}_{hash(hospital_json_str)}"
            if "last_hospital_submission" not in st.session_state or st.session_state["last_hospital_submission"] != submission_key:
                
                with st.spinner("Creating hospital..."):
                    try:
                        # Step 1: Create hospital organization with memory
                        hospital_result, hospital_status = create_org_memory(
                            org_name=hospital_name,
                            org_data=hospital_data if hospital_data else {},
                            document_urls=hospital_doc_pairs,
                            pdf_documents=hospital_pdf_documents
                        )
                        
                        if hospital_status == 200:
                            org_id = hospital_result.get("org_id")
                            st.success(f"Hospital '{hospital_name}' created successfully!")
                            
                                    
                                    # Show detailed results
                            with st.expander("Creation Details"):
                                st.write(f"**Hospital:** {hospital_name}")
                                st.write(f"**Organization ID:** {org_id}")
                                st.write(f"**Hospital Documents:** {len(hospital_doc_pairs) + len(hospital_pdf_documents)}")
                                        
                                    
                                # Store submission to prevent duplicates
                                st.session_state["last_hospital_submission"] = submission_key
                                st.session_state["clear_hospital_form"] = True
                        else:
                            st.error(f"Error creating hospital: {hospital_result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"Error during creation process: {str(e)}")
            else:
                st.info("Form already submitted. Refresh the page to submit again.")
                del st.session_state["last_hospital_submission"]
