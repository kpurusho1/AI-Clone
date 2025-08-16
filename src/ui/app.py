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
    ["Create expert", "Query Expert using Threads", "Update Expert Context", "Update Expert memory", "Update Domain Memory", "YouTube Transcript"]
)
def create_expert(expert_name, domain_name, qa_pairs, document_urls):
    try:
        print(f"[UI DEBUG] create_expert: Creating expert '{expert_name}' in domain '{domain_name}'")
        
        request_data = {
            "expert_name": expert_name,
            "domain_name": domain_name,
            "qa_pairs": qa_pairs,
            "document_urls": document_urls
        }
        print(f"[UI DEBUG] create_expert: Request data: {request_data}")
        print(f"[UI DEBUG] create_expert: Request URL: {API_BASE_URL}/memory/expert/initialize")
        
        response = requests.post(
            f"{API_BASE_URL}/memory/expert/initialize",
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

def update_expert_context(expert_name, qa_pairs):
    try:
        response = requests.put(
            f"{API_BASE_URL}/experts/persona/update",
            json={
                "expert_name": expert_name,
                "qa_pairs": qa_pairs
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

def get_expert_domains(expert_name):
    # Get domains associated with an expert
    try:
        response = requests.get(f"{API_BASE_URL}/experts/{expert_name}/domain")
        if response.status_code == 200:
            return response.json().get("domain_name")
        return None
    except Exception:
        return None
        
def get_documents_by_expert_domain(expert_name, domain_name):
    # Get documents for a specific expert and domain
    try:
        response = requests.get(
            f"{API_BASE_URL}/documents",
            params={"domain": domain_name, "created_by": expert_name}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"[UI ERROR] get_documents_by_expert_domain: {str(e)}")
        return []
        
def get_documents_by_domain(domain_name):
    # Get documents for a specific domain
    try:
        response = requests.get(
            f"{API_BASE_URL}/documents",
            params={"domain": domain_name}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"[UI ERROR] get_documents_by_domain: {str(e)}")
        return []
        
def update_domain_memory(domain_name, document_urls):
    # Update domain memory with documents
    try:
        print(f"[UI DEBUG] update_domain_memory: Updating memory for domain '{domain_name}'")
        
        request_data = {
            "domain_name": domain_name,
            "expert_name": None,
            "document_urls": document_urls,
        }
        
        print(f"[UI DEBUG] update_domain_memory: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/vectors/update",
            json=request_data
        )
        
        print(f"[UI DEBUG] update_domain_memory: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] update_domain_memory: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] update_domain_memory: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] update_domain_memory: Request failed: {str(e)}")
        return {"error": str(e)}, 500
        
def update_expert_memory(domain_name, expert_name, document_urls):
    # Update expert memory with documents
    try:
        print(f"[UI DEBUG] update_expert_memory: Updating memory for expert '{expert_name}'")
        
        request_data = {
            "domain_name": domain_name,
            "expert_name": expert_name,
            "document_urls": document_urls,
        }
        
        print(f"[UI DEBUG] update_expert_memory: Request data: {request_data}")
        
        response = requests.post(
            f"{API_BASE_URL}/vectors/update",
            json=request_data
        )
        
        print(f"[UI DEBUG] update_expert_memory: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] update_expert_memory: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] update_expert_memory: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] update_expert_memory: Request failed: {str(e)}")
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

# Function to get YouTube transcript
def get_youtube_transcript_from_api(video_url):
    try:
        response = requests.post(
            f"{API_BASE_URL}/youtube/transcript",
            json={"video_url": video_url}
        )
        if response.status_code == 200:
            response_json = response.json()
            return response_json, response.status_code
        return {"error": f"Error: {response.status_code} - {response.text}"}, response.status_code
    except Exception as e:
        print(f"Error in get_youtube_transcript_from_api: {str(e)}")
        return {"error": str(e)}, 500

# YouTube Transcript page
if page == "YouTube Transcript":
    st.title("YouTube Transcript Extractor")
    
    st.write("Enter a YouTube video URL to extract its transcript.")
    
    # Input for YouTube URL
    video_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=example")
    
    # Create columns for the buttons
    button_cols = st.columns([1, 3])
    
    with button_cols[0]:
        if st.button("Extract Transcript", key="extract_transcript"):
            if video_url:
                with st.spinner("Extracting transcript..."):
                    try:
                        transcript, status_code = get_youtube_transcript_from_api(video_url)
                        
                        if transcript:
                            st.success("Transcript extracted successfully!")
                            
                            st.subheader("Transcript")
                            with st.expander("View Full Transcript", expanded=True):
                                st.text_area(f"Transcript", transcript, height=400)
                                
                        else:
                            st.error("No transcript found for this video.")
                    except Exception as e:
                        st.error(f"Error extracting transcript: {str(e)}")
            else:
                st.warning("Please enter a YouTube video URL.")

elif page == "Create expert":
    st.title("Create Expert")
    
    with st.form("expert_form"):
        expert_name = st.text_input("Expert Name")
        domain_name = st.text_input("Domain")
        
        # Display questions from pediatrician_persona_config.json with text boxes for answers
        st.subheader("Expert Context - Answer the following questions")
        
        # Questions from the pediatrician_persona_config.json
        questions = [
            "What is your area of expertise?",
            "What is your claim to fame?",
            "What is your communication style with clients?",
            "What recent advances in your field are you excited about?",
            "Explain more about your experience?"
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
        
        # Submit buttons for the form
        col1, col2 = st.columns(2)
        with col1:
            add_more = st.form_submit_button("Add Another Document")
        with col2:
            submitted = st.form_submit_button("Create Expert")
    
    # Handle the add document button click
    if add_more:
        st.session_state.expert_doc_inputs = num_doc_inputs + 1
        st.experimental_rerun()
    
    # Process form submission
    if submitted:
        # Format qa_pairs as a list of dictionaries with question and answer keys
        formatted_qa_pairs = []
        for question, answer in qa_pairs.items():
            formatted_qa_pairs.append({"question": question, "answer": answer})
            
        if expert_name and domain_name and formatted_qa_pairs and doc_pairs:
            result, status_code = create_expert(expert_name, domain_name, formatted_qa_pairs, doc_pairs)
            if status_code == 200:
                st.success(f"Expert {expert_name} created successfully!")
            else:
                st.error(f"Error creating expert: {result.get('error', 'Unknown error')}")
        else:
            if not expert_name:
                st.warning("Please enter an Expert Name")
            elif not domain_name:
                st.warning("Please enter a Domain")
            elif not qa_pairs:
                st.warning("Please answer at least one question for the Expert Context")
            elif not doc_pairs:
                st.warning("Please add at least one document")
            
elif page == "Query Expert using Threads":
    st.title("Query Expert using Threads")
    
    # Get experts
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    
    # Memory type selection
    memory_options = ["llm", "Other"]
    selected_memory = st.selectbox("Select Memory Type", memory_options, index=0)  # Default to "expert"
    
    if selected_expert != "--Select an expert--" and selected_memory == "Other":
        # Create unique keys for this expert/memory/client combination
        thread_key = f"thread_messages_{selected_expert}_{selected_memory}"
        thread_id_key = f"thread_id_{selected_expert}_{selected_memory}"
        assistant_id_key = f"assistant_id_{selected_expert}_{selected_memory}"
    else:
        thread_key = f"thread_messages_{selected_expert}_llm"
        thread_id_key = f"thread_id_{selected_expert}_llm"
        assistant_id_key = f"assistant_id_{selected_expert}_llm"
    
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
                assistant_result, assistant_status = create_assistant(
                    expert_name=selected_expert,
                    memory_type=selected_memory,
                    client_name=None
                )
                
                if assistant_status == 200:
                    st.session_state[assistant_id_key] = assistant_result.get("assistant_id")
                    
                    # Create thread
                    thread_result, thread_status = create_thread(
                        expert_name=selected_expert,
                        memory_type=selected_memory,
                        client_name=None
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
                
                result, status_code = query_expert_with_assistant(
                    expert_name=selected_expert,
                    query=prompt,
                    memory_type=selected_memory,
                    client_name=None,
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
        
        st.subheader("Update Expert Context - Answer the following questions")
        
        # Questions from the pediatrician_persona_config.json
        questions = [
            "What is your area of expertise?",
            "How do you approach difficult situations?",
            "What is your communication style with clients?",
            "What recent advances in your field are you excited about?",
            "Explain more about your experience?"
        ]
        
        # Dictionary to store answers
        new_qa_pairs = {}
        
        # Create a text box for each question
        for i, question in enumerate(questions):
            st.write(f"**{question}**")
            answer = st.text_area(f"Answer {i+1}", key=f"update_answer_{i}", height=100)
            if answer:  # Only add non-empty answers
                new_qa_pairs[question] = answer
        
        submitted = st.form_submit_button("Update Context")
        if submitted:
            # Format qa_pairs as a list of dictionaries with question and answer keys
            formatted_qa_pairs = []
            for question, answer in new_qa_pairs.items():
                formatted_qa_pairs.append({"question": question, "answer": answer})
                
            if expert_name and formatted_qa_pairs:
                result, status_code = update_expert_context(expert_name, formatted_qa_pairs)
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
                if not expert_name:
                    st.warning("Please select an expert")
                elif not new_qa_pairs:
                    st.warning("Please answer at least one question")

elif page == "Update Expert memory":
    st.title("Update Expert Memory")
    
    # Get experts
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    domain_name = None
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    
    if selected_expert != "--Select an expert--":
        # Get domain for this expert
        domain_name = get_expert_domains(selected_expert)
        st.success(f"Expert {selected_expert} is associated with domain: {domain_name}")
            
        # Get existing documents for this expert/domain combination
        existing_documents = get_documents_by_expert_domain(selected_expert, domain_name)
        all_urls = {}
                
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
                doc_selections[doc_name] = st.checkbox(f"{doc_name}", value=True, key=f"doc_{doc.get('id')}")
            # Create a dictionary with selected existing URLs and new document pairs
                
            # Add selected existing documents with their original URLs
            for doc in existing_documents:
                doc_name = doc.get("name", "Unnamed Document")
                if doc_selections.get(doc_name, False):
                    all_urls[doc_name] = doc.get("document_link", "")
        else:
            st.info(f"No existing documents found for domain {domain_name}.")
            
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
        num_new_doc_inputs = st.session_state.get('expert_mem_doc_inputs', 3)
            
        for i in range(num_new_doc_inputs):
            new_doc_cols = st.columns(2)
            with new_doc_cols[0]:
                new_doc_name = st.text_input(f"New Name {i+1}", key=f"expert_mem_doc_name_{i}", label_visibility="collapsed")
            with new_doc_cols[1]:
                new_doc_url = st.text_input(f"New URL {i+1}", key=f"expert_mem_doc_url_{i}", label_visibility="collapsed")
                
            if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                if new_doc_name not in existing_doc_names:
                    new_doc_pairs[new_doc_name] = new_doc_url
                else:
                    st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
                
            # Add button for more document inputs
        if st.button("Add Another Document", key="expert_mem_add_doc"):
            st.session_state.expert_mem_doc_inputs = num_new_doc_inputs + 1
            st.experimental_rerun()
            
        # Add new documents
        all_urls.update(new_doc_pairs)
            
        # Create columns for the buttons
        button_cols = st.columns(2)
            
        with button_cols[0]:
            if st.button("Update Memory", key="update_memory"):
                if all_urls:
                    # Call the API to replace vector store
                    result, status_code = update_expert_memory(domain_name, selected_expert, all_urls)
                        
                    if status_code == 200:
                        st.success(f"Expert memory for {selected_expert} updated successfully!")
                                
                        # Display details about the updated documents
                        if "new_file_ids" in result:
                            st.write(f"New file IDs: {', '.join(result['new_file_ids'][:5])}" + 
                                         ("..." if len(result['new_file_ids']) > 5 else ""))
                                
                        if "all_file_ids" in result:
                            st.write(f"Total files in memory: {len(result['all_file_ids'])}")
                        else:
                            st.error(f"Error replacing expert memory: {result.get('error', 'Unknown error')}")
                    else:
                        st.warning("No documents selected or added. Please select at least one document.")
                
        with button_cols[1]:
            if st.button("Cancel", key="cancel_update"):
                st.experimental_rerun()
    else:
        st.info("Please select an expert to update their memory.")

elif page == "Update Domain Memory":
    st.title("Update Domain Memory")
    
    # Get domains
    domains = get_domains()
    domain_names = [domain["domain_name"] for domain in domains] if domains else []
    
    # Domain selection
    selected_domain = st.selectbox("Select Domain", ["--Select a domain--"] + domain_names)
    # Create a dictionary with selected existing URLs and new document pairs
    all_urls = {}
    
    if selected_domain != "--Select a domain--":
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
                doc_selections[doc_name] = st.checkbox(f"{doc_name}", value=True, key=f"domain_doc_{doc.get('id')}")
            # Add button for more document inputs
            if st.button("Add Another Document", key="domain_mem_add_doc"):
                st.session_state.domain_mem_doc_inputs = num_new_doc_inputs + 1
                st.experimental_rerun()
            
            # Add selected existing documents with their original URLs
            for doc in existing_documents:
                doc_name = doc.get("name", "Unnamed Document")
                if doc_selections.get(doc_name, False):
                    all_urls[doc_name] = doc.get("document_link", "")
        else:
            st.info(f"No existing documents found for domain {domain_name}.")
        
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
        num_new_doc_inputs = st.session_state.get('domain_mem_doc_inputs', 3)
            
        for i in range(num_new_doc_inputs):
            new_doc_cols = st.columns(2)
            with new_doc_cols[0]:
                new_doc_name = st.text_input(f"New Name {i+1}", key=f"domain_mem_doc_name_{i}", label_visibility="collapsed")
            with new_doc_cols[1]:
                new_doc_url = st.text_input(f"New URL {i+1}", key=f"domain_mem_doc_url_{i}", label_visibility="collapsed")
                
            if new_doc_name and new_doc_url:  # Only add if both name and URL are provided
                if new_doc_name not in existing_doc_names:
                    new_doc_pairs[new_doc_name] = new_doc_url
                else:
                    st.warning(f"Document name '{new_doc_name}' already exists. Please use a different name.")
            
        # Add new documents
        all_urls.update(new_doc_pairs)
            
        # Create columns for the buttons
        button_cols = st.columns(2)
            
        with button_cols[0]:
            if st.button("Update Memory", key="domain_update_memory"):
                if all_urls:
                    # Call the API to update vector store
                    result, status_code = update_domain_memory(selected_domain, all_urls)
                        
                    if status_code == 200:
                        st.success(f"Domain memory for {selected_domain} updated successfully!")
                            
                        # Display details about the updated documents
                        if "file_ids" in result:
                            st.write(f"New file IDs: {', '.join(result['file_ids'][:5])}" + 
                                     ("..." if len(result['file_ids']) > 5 else ""))
                            
                        if "message" in result:
                            st.write(result["message"])
                        else:
                            st.error(f"Error updating domain memory: {result.get('error', 'Unknown error')}")
                    else:
                        st.warning("No documents selected or added. Please select at least one document.")
            
        with button_cols[1]:
            if st.button("Cancel", key="domain_cancel_update"):
                st.experimental_rerun()        
    else:
        st.info("Please select a domain to update its memory.")





