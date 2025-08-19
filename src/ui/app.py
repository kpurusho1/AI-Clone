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
    ["Create expert", "Query Expert", "Update Expert"]
)
def create_expert(expert_name, domain_name, qa_pairs, document_urls, pdf_documents=None):
    try:
        print(f"[UI DEBUG] create_expert: Creating expert '{expert_name}' in domain '{domain_name}'")
        
        request_data = {
            "expert_name": expert_name,
            "domain_name": domain_name,
            "qa_pairs": qa_pairs,
            "document_urls": document_urls
        }
        
        # Add PDF documents to request if available
        if pdf_documents and len(pdf_documents) > 0:
            # Convert bytes to base64 strings for JSON serialization
            import base64
            encoded_pdfs = {}
            for name, pdf_bytes in pdf_documents.items():
                encoded_pdfs[name] = base64.b64encode(pdf_bytes).decode('utf-8')
            
            request_data["pdf_documents"] = encoded_pdfs
            print(f"[UI DEBUG] create_expert: Added {len(encoded_pdfs)} PDF documents to request")
        
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

def update_expert(expert_name, domain_name, qa_pairs=None, document_urls=None, pdf_documents=None):
    """Combined function to update expert context and/or memory"""
    try:
        print(f"[UI DEBUG] update_expert: Updating expert '{expert_name}' in domain '{domain_name}'")
        
        # Build the request data with available parameters
        request_data = {
            "expert_name": expert_name,
            "domain_name": domain_name
        }
        
        # Add optional parameters if provided
        if qa_pairs:
            request_data["qa_pairs"] = qa_pairs
            print(f"[UI DEBUG] update_expert: Including {len(qa_pairs)} QA pairs")
            
        if document_urls:
            request_data["document_urls"] = document_urls
            print(f"[UI DEBUG] update_expert: Including {len(document_urls)} document URLs")
            
        if pdf_documents and len(pdf_documents) > 0:
            # Convert bytes to base64 strings for JSON serialization
            import base64
            encoded_pdfs = {}
            for name, pdf_bytes in pdf_documents.items():
                encoded_pdfs[name] = base64.b64encode(pdf_bytes).decode('utf-8')
            
            request_data["pdf_documents"] = encoded_pdfs
            print(f"[UI DEBUG] update_expert: Including {len(encoded_pdfs)} PDF documents")
        
        print(f"[UI DEBUG] update_expert: Request data: {request_data}")
        
        # Call the combined API endpoint
        response = requests.post(
            f"{API_BASE_URL}/expert/update",
            json=request_data
        )
        
        print(f"[UI DEBUG] update_expert: Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"[UI DEBUG] update_expert: Response data: {response_data}")
            return response_data, response.status_code
        except Exception as e:
            print(f"[UI ERROR] update_expert: Failed to parse JSON response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}, response.status_code
    except Exception as e:
        print(f"[UI ERROR] update_expert: Request failed: {str(e)}")
        return {"error": str(e)}, 500

def get_experts():
    try:
        response = requests.get(f"{API_BASE_URL}/experts")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

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
             
# update_expert_memory function has been combined into the update_expert function

# Helper functions for OpenAI Assistant API
# Note: create_assistant and create_thread functions have been removed
# as they are now handled directly by the query_expert_with_assistant function

def query_expert_with_assistant(expert_name, query, memory_type="expert", thread_id=None):
    try:
        print(f"[UI DEBUG] query_expert_with_assistant: Querying expert '{expert_name}' with memory type '{memory_type}'")
        
        request_data = {
            "expert_name": expert_name,
            "query": query,
            "memory_type": memory_type
        }
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

if page == "Create expert":
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
        
        # Add tabs for URL and PDF upload options
        # Initialize active tab in session state if not present
        if 'active_doc_tab' not in st.session_state:
            st.session_state.active_doc_tab = 0
            
        # Create tabs and track which one is selected
        tab_names = ["Document URLs", "PDF Uploads"]
        doc_tabs = st.tabs(tab_names)
        
        # Add radio buttons to track which tab is active
        st.session_state.active_doc_tab = st.radio(
            "Select document type to add:",
            options=[0, 1],
            format_func=lambda x: tab_names[x],
            horizontal=True,
            label_visibility="collapsed",
            key="doc_tab_selector"
        )
        
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
        
        # URL Documents Tab - continued
        with doc_tabs[0]:
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
            
            # We can't use st.button() inside a form, so we'll handle this with the main form submission
        
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
                        # Read the PDF file bytes
                        pdf_bytes = pdf_file.read()
                        pdf_documents[pdf_name] = pdf_bytes
                        st.success(f"PDF '{pdf_name}' uploaded successfully!")
                    else:
                        st.warning(f"Document name '{pdf_name}' already exists. Please use a different name.")
            
            # We can't use st.button() inside a form, so we'll handle this with the main form submission
        
        # Submit buttons for the form
        col1, col2 = st.columns(2)
        with col1:
            add_more = st.form_submit_button("Add Another Document")
        with col2:
            submitted = st.form_submit_button("Create Expert")
    
    # Handle the 'Add Another Document' button
    if add_more:
        # Check which tab is active and add the appropriate type of document input
        active_tab = st.session_state.get('active_doc_tab', 0)
        if active_tab == 0:  # URL Documents tab
            st.session_state.expert_doc_inputs = st.session_state.get('expert_doc_inputs', 3) + 1
        else:  # PDF Documents tab
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
            
        if expert_name and domain_name and formatted_qa_pairs and has_documents:
            result, status_code = create_expert(expert_name, domain_name, formatted_qa_pairs, doc_pairs, pdf_documents)
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
            elif not domain_name:
                st.warning("Please enter a Domain")
            elif not qa_pairs:
                st.warning("Please answer at least one question for the Expert Context")
            elif not has_documents:
                st.warning("Please add at least one document (URL or PDF)")
                
        # Show a summary of what was submitted
        if has_documents:
            with st.expander("Submission Summary"):
                st.write(f"**Expert Name:** {expert_name}")
                st.write(f"**Domain:** {domain_name}")
                st.write(f"**URL Documents:** {len(doc_pairs)}")
                st.write(f"**PDF Documents:** {len(pdf_documents)}")
                st.write(f"**Context QA Pairs:** {len(formatted_qa_pairs)}")
            
elif page == "Query Expert":
    st.title("Query Expert using Threads")
    
    # Get experts
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    
    # Memory type selection
    memory_options = ["llm", "Other"]
    selected_memory = st.selectbox("Select Memory Type", memory_options, index=1)  # Default to "Other"
    
    # Create unique keys for this expert/memory combination
    thread_key = f"thread_messages_{selected_expert}_{selected_memory}"
    thread_id_key = f"thread_id_{selected_expert}_{selected_memory}"
    
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
    if selected_expert != "--Select an expert--":
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
                    expert_name=selected_expert,
                    query=prompt,
                    memory_type=selected_memory,
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
        with st.chat_message("assistant"):
            st.write("Please select an expert first.")

elif page == "Update Expert":
    st.title("Update Expert")
    
    # Get experts
    experts = get_experts()
    expert_names = [expert["name"] for expert in experts] if experts else []
    
    # Expert selection
    selected_expert = st.selectbox("Select Expert", ["--Select an expert--"] + expert_names)
    
    if selected_expert != "--Select an expert--":
        # Get domain for this expert
        domain_name = get_expert_domains(selected_expert)
        st.success(f"Expert {selected_expert} is associated with domain: {domain_name}")
        
        # Create form wrapper for the entire update process
        with st.form("update_expert_form"):
            # Create tabs for Context and Documents
            update_tabs = st.tabs(["Expert Context", "Expert Documents"])
            
            # Initialize variables
            formatted_qa_pairs = []
            doc_pairs = {}
            pdf_documents = {}
            
            # Expert Context Tab
            with update_tabs[0]:
                # Create a container for displaying the current context
                current_context_container = st.container()
                
                # Get and display current context
                current_context, status_code = get_expert_context(selected_expert)
                with current_context_container:
                    st.subheader("Current Context")
                    st.text_area("Current Context", value=current_context, height=150, disabled=True, key="current_context")
                
                st.subheader("Update Expert Context - Answer the following questions")
            
            with update_tabs[0]:
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
                
                # Format qa_pairs as a list of dictionaries with question and answer keys
                formatted_qa_pairs = []
                for question, answer in new_qa_pairs.items():
                    formatted_qa_pairs.append({"question": question, "answer": answer})
        
            # Expert Documents Tab
            with update_tabs[1]:
                # Get existing documents for this expert/domain combination
                existing_documents = get_documents_by_expert_domain(selected_expert, domain_name)
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
                    st.info(f"No existing documents found for domain {domain_name}.")
            
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
                                # Read the PDF file bytes
                                pdf_bytes = pdf_file.read()
                                pdf_documents[pdf_name] = pdf_bytes
                                st.success(f"PDF '{pdf_name}' uploaded successfully!")
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
        
        # Handle form submission
        if submitted:
            has_updates = len(formatted_qa_pairs) > 0 or len(doc_pairs) > 0 or len(pdf_documents) > 0
            
            if has_updates:
                # Call the combined API endpoint
                result, status_code = update_expert(
                    expert_name=selected_expert,
                    domain_name=domain_name,
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
                            current_context, _ = get_expert_context(selected_expert)
                            with update_tabs[0]:
                                with current_context_container:
                                    st.subheader("Current Context (Updated)")
                                    st.text_area("Current Context", value=current_context, height=150, disabled=True, key="updated_context")
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



