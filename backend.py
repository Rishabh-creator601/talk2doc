from fastapi import FastAPI,UploadFile,File,HTTPException,Query
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai.chat_models import ChatOpenAI
from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os ,tempfile

load_dotenv()




api_key =  os.environ["OPENAI_API_KEY"]
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key
)

llm = ChatOpenAI(model="gpt-4.1")

sematic_chunker  =  SemanticChunker(
    embeddings,breakpoint_threshold_type="standard_deviation",
    breakpoint_threshold_amount=1.5
    )


app =  FastAPI()

dir_name = "data"
collection_name = "sample"


     
    
# key learnings :  temp file code 

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    
    # 1. save the uploaded file to a temp file so the loader gets a real path
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
    
    try : 
        pages =    PyMuPDFLoader(path).load()
        if len(pages)  > 10 :
            
            raise  HTTPException(status_code=400,detail=f" {file.filename}  has page count more than 10 that is {len(pages)}")
        doc =  "\n".join(p.page_content for p in pages)
        
        return JSONResponse(status_code=200,content={"message":doc})
    
    except :
        raise HTTPException(status_code=400,detail="Only pdf files are allowed !")


  
# key learnings :  send chunks and not vector store length   
@app.get("/vectordb")
def create_vector_db(pages : str ):


    docs  =  sematic_chunker.create_documents([pages])
    vectorstore = Chroma.from_documents(documents=docs,embedding=embeddings,persist_directory=dir_name,collection_name=collection_name)
    
    return JSONResponse(status_code=200,content={"message":"stored vectordb","chunks":len(docs)})


    
def answer_by_query(query) -> str :
    
    vectorstore =  Chroma(persist_directory=dir_name,embedding_function=embeddings,collection_name=collection_name)
    multiquery =  MultiQueryRetriever.from_llm(
     retriever=vectorstore.as_retriever(search_kwargs={"k":2}),
    llm=llm,
    include_original=True
)

    prompt_template =  ChatPromptTemplate.from_template(""""
        Answer using the context :  {context} and query : {query}                                             
    """)
    context  =  multiquery.invoke(query)[0].page_content



    chain =  prompt_template |  llm |  StrOutputParser()
    result = chain.invoke({"context":context,"query":query})

    return result 




@app.get("/summarize")
def summarize():
    
    summary = answer_by_query("summarize the document !")
    
    return JSONResponse(status_code=200,content={"message":summary})




# key learnings :  use the Query for range object 
@app.get("/top_points")
def top_points(n :  int  = Query(gt=0,lt=10)):
    
    top_ans =  answer_by_query(f"top {n} points")
    return JSONResponse(status_code=200,content={"message":top_ans})



@app.get("/askqa")
def askqa(ques :  str):
    
    ans =  answer_by_query(ques)
    return JSONResponse(status_code=200,content={"message":ans})    
    
    
    
    


    
        
@app.delete("/vectordb")
def clear_vector_db():
    vectorstore = Chroma(embedding_function=embeddings, persist_directory="./data/",collection_name=collection_name)
    vectorstore.delete_collection()
    return JSONResponse(status_code=200, content={"message": "vector db cleared"})
    
    
    






