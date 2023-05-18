import os
import urllib.parse
import shutil
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
print(os. getcwd())


from fastapi import FastAPI, UploadFile, File
from typing import List, Optional

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Qdrant
from ingest import Ingester
# from retrive.startLLM import startLLM

from retrive.load_env import (
    chain_type,
    text_embeddings_model,
    persist_directory,
    collection_name,
    documents_directory,
    get_embedding_model,
    get_prompt_template_kwargs,
    model_max_tokens,
    model_n_ctx,
    model_path,
    model_stop,
    model_temp,
    model_type,
    n_forward_documents,
    n_gpu_layers,
    n_retrieve_documents,
    use_mlock,
    model_top_k,
    model_top_p,
    model_n_predict,
    chunk_size,
    chunk_overlap
)

from retrive.startLLM import QASystem

app = FastAPI()
app.embeddings = HuggingFaceEmbeddings(model_name=text_embeddings_model)

# async def model_download():
#     match model_type:
#         case "LlamaCpp":
#             url = "https://gpt4all.io/models/ggml-gpt4all-l13b-snoozy.bin"
#         case "GPT4All":
#             url = "https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin"
#     folder = "models"
#     parsed_url = urllib.parse.urlparse(url)
#     filename = os.path.join(folder, os.path.basename(parsed_url.path))
#     # Check if the file already exists
#     if os.path.exists(filename):
#         print("File already exists.")
#         return
#     # Create the folder if it doesn't exist
#     os.makedirs(folder, exist_ok=True)
#     # Run wget command to download the file
#     os.system(f"wget {url} -O {filename}")
#     global model_path 
#     model_path = filename
#     print("model downloaded")
    

# Starting the app with embedding and llm download
@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    # await model_download()
    
@app.get("/")
async def root():
    return {"message": "Hello, the APIs are now ready for your embeds and queries!"}

@app.post("/embed")
async def embed(files: List[UploadFile], collection_name: Optional[str] = None):
    if collection_name is None:         # Handle the case when the collection_name is not defined
       collection_name = "test"
    saved_files = []
    # Save the files to the specified folder
    for file in files:
        file_path = os.path.join(documents_directory, file.filename)
        saved_files.append(file_path)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
    
    # os.system(f'python ingest.py --collection {collection_name}')
    ingester = Ingester(persist_directory)
    ingester.add_one_file(Path(file_path), collection_name, chunk_size, chunk_overlap)
    ingester = None # free up memory
    # Delete the contents of the folder
    # [os.remove(os.path.join(source_directory, item)) if os.path.isfile(os.path.join(source_directory, item)) else shutil.rmtree(os.path.join(source_directory, item)) for item in os.scandir(source_directory)]
    [os.remove(os.path.join(documents_directory, file.filename)) or os.path.join(documents_directory, file.filename) for file in files]
    
    return {"message": "Files embedded successfully", "saved_files": saved_files}

@app.post("/query")
async def query(query: str, collection_name: Optional[str] = None):
    if collection_name is None:         # Handle the case when the collection_name is not defined
       collection_name = "test"
    
    print(f"querying {query} from {collection_name}")
    
    # qdrant_client = qdrant_client.QdrantClient(path=persist_directory, prefer_grpc=True)
    # qdrant_langchain = Qdrant(client=qdrant_client, collection_name=collection_name, embeddings=app.embeddings)
    qa = QASystem(app.embeddings.client.encode, persist_directory, model_path, model_n_ctx, model_temp, model_stop, use_mlock, n_gpu_layers, collection_name, model_top_k, model_top_p, model_n_predict)
    res = qa.prompt_once(query)
    #print(res)   
    #answer, docs = res['result'], res['source_documents']
    answer, docs = res[0], res[1]
    return {"results": answer, "docs":docs}    
    
    # embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    # db = Chroma(persist_directory=persist_directory,collection_name=collection_name, embedding_function=embeddings, client_settings=CHROMA_SETTINGS)
    # retriever = db.as_retriever()
    # # Prepare the LLM
    # callbacks = [StreamingStdOutCallbackHandler()]
    # match model_type:
    #     case "LlamaCpp":
    #         llm = LlamaCpp(model_path=model_path, n_ctx=model_n_ctx, callbacks=callbacks, verbose=False)
    #     case "GPT4All":
    #         llm = GPT4All(model=model_path, n_ctx=model_n_ctx, backend='gptj', callbacks=callbacks, verbose=False)
    #     case _default:
    #         print(f"Model {model_type} not supported!")
    #         exit;
    # qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)
    
    # # Get the answer from the chain
