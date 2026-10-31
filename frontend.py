import streamlit as st
import  requests 




MAIN_API = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")   # cloud URL online, localhost on your PC

API_URL =  f"{MAIN_API}/upload"
vector_URL =  f"{MAIN_API}/vectordb"
askqa =  f"{MAIN_API}/askqa"



if not "step" in st.session_state:
    st.session_state["step"] = "upload"


if not "messages" in st.session_state:
    st.session_state["messages"] = [
        {"role":"AI" ,"prompt":"Hi User ! You can ask any 2 queries for free !"}
    ]
    
    
if not "query_count" in st.session_state:    
    st.session_state["query_count"] = 0
    
    
    
    
    
    
def upload_page():
    
    
    
    
    st.markdown("# welcome to chat with documents !")
    
    st.markdown("**you can ask any 2 queries with the AI agent for free !**")


    uploaded_file =  st.file_uploader(label="upload pdf files upto 10 pages !",type="pdf")

    submit  = st.button("submit")


    if submit:

        if uploaded_file != None : 
        
        
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            
            with st.spinner("Uploading file .... "): 
            
                status_file =  requests.post(API_URL,files=files).json()
                
                if "message" not in status_file:
                    st.error(f"Upload failed ({status_file.status_code}): {status_file.get('detail', status_file)}")
                    st.caption(f"URL used: {API_URL}")
                    return

                pages =  status_file["message"] 
                
                
                with st.spinner("dividing into chunks ...."):
            
                    if pages != None :
                        status_vector =  requests.get(vector_URL,{"pages":pages}).json()
                        
                        if "chunks"  in status_vector:
                            st.write(f"Divided into chunks : {status_vector['chunks']}" )
                            st.session_state["step"] =  "chat"
                            st.rerun()
        else:
            st.toast("pls upload a pdf file !")
        
        
        
def answer_the_query(query):
    
    try :
        response =  requests.get(askqa,{"ques":query}).json()
        
        return response["message"]
    
    except:
        
        return "Can't answer the question"
        
    

def chat_message():
    
    
    

    
    # <display all the messages >
    for x in  st.session_state.messages:
        with st.chat_message(x["role"]):
            st.markdown(x["prompt"])

        


    # take chat input 
    chat_input =  st.chat_input(placeholder="Ask 2 queries here !")

    if chat_input:
        
         
        # take the chat input of user and show and save it 
        st.chat_message("user").markdown(chat_input)
        st.session_state.messages.append({"role":"user","prompt":chat_input})
        
        
        # generate the answer from backend and show and save it 
        
        if st.session_state["query_count"] < 2:
            
            answer = answer_the_query(chat_input)
            
            st.chat_message("AI").markdown(answer)
            st.session_state.messages.append({"role":"AI","prompt":answer})
            
            st.session_state["query_count"]  += 1 
        
        else:
            
            st.session_state["step"] = "thanx"
            st.rerun()
        
        


def thanx():
    st.markdown("""
        # Thanx a lot for visiting page !
        # Regards Rishabh !          
        **Your 2 queries are done**
                
""")
    
    
    
    
# register pages and automatically show it 

steps = {
    "upload":upload_page,
     "chat":chat_message,
    "thanx":thanx
         }
steps[st.session_state["step"]]()

    



        
    





