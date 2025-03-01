"""load env variables"""
import os
from typing import Callable

from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings, LlamaCppEmbeddings
from langchain.prompts import PromptTemplate

from retrive.utils import download_if_repo

load_dotenv()
text_embeddings_model = os.environ.get("TEXT_EMBEDDINGS_MODEL")
text_embeddings_model_type = os.environ.get("TEXT_EMBEDDINGS_MODEL_TYPE")
use_mlock = os.environ.get("USE_MLOCK").lower() == "true"

# ingest
persist_directory = os.environ.get("PERSIST_DIRECTORY")
documents_directory = os.environ.get("DOCUMENTS_DIRECTORY")
chunk_size = int(os.environ.get("INGEST_CHUNK_SIZE", 500))
chunk_overlap = int(os.environ.get("INGEST_CHUNK_OVERLAP", 50))
ingest_n_threads = int(os.environ.get("INGEST_N_THREADS", 1))

collection_name = os.environ.get("COLLECTION_NAME", "test")
model_streaming_response = os.environ.get("MODEL_STREAMING_RESPONSE", "false").lower() == "true"

# generate
model_type = os.environ.get("MODEL_TYPE")
model_path = os.environ.get("MODEL_PATH")
model_n_ctx = int(os.environ.get("MODEL_N_CTX"))
model_max_tokens = int(os.environ.get("MODEL_MAX_TOKENS"))
model_n_threads = int(os.environ.get("MODEL_N_THREADS", 4))
model_n_batch = int(os.environ.get("MODEL_N_BATCH", 1000))
model_verbose = os.environ.get("MODEL_VERBOSE", "false").lower() == "true"
model_temp = float(os.environ.get("MODEL_TEMP", "0.8"))
model_stop = os.environ.get("MODEL_STOP", "")
model_stop = model_stop.split(",") if model_stop else []
model_repeat_penalty = float(os.environ.get("MODEL_REPEAT_PENALTY", "1.1"))
chain_type = os.environ.get("CHAIN_TYPE", "refine")

n_retrieve_documents = int(os.environ.get("N_RETRIEVE_DOCUMENTS", 25))
n_forward_documents = int(os.environ.get("N_FORWARD_DOCUMENTS", 3))
n_gpu_layers = int(os.environ.get("N_GPU_LAYERS", 0))

model_use_mmap = os.environ.get("MODEL_USE_MMAP", "false").lower() == "true"

model_top_k = float(os.environ.get("MODEL_TOP_K", 40))
model_top_p = float(os.environ.get("MODEL_TOP_P", 0.95))
model_n_predict = int(os.environ.get("MODEL_N_PREDICT", -1))

text_embeddings_model = download_if_repo(text_embeddings_model)
model_path = download_if_repo(model_path)


def get_embedding_model() -> tuple[HuggingFaceEmbeddings | LlamaCppEmbeddings, Callable]:
    """get the text embedding model
    :returns: tuple[the model, its encoding function]"""
    match text_embeddings_model_type:
        case "HF":
            model = HuggingFaceEmbeddings(model_name=text_embeddings_model)
            return model, model.client.encode
        case "LlamaCpp":
            model = LlamaCppEmbeddings(model_path=text_embeddings_model, n_ctx=model_n_ctx, n_gpu_layers=n_gpu_layers)
            return model, lambda inpt: model.client.embed(inpt) if isinstance(inpt, str) else [
                model.client.embed(e) for e in inpt
            ]  # no batched embedding in llamacpp
        case _:
            raise ValueError(f"Unknown embedding type {text_embeddings_model_type}")


def get_prompt_template_kwargs() -> dict[str, PromptTemplate]:
    """get an improved prompt template"""
    match chain_type:
        case "stuff":
            question_prompt = """HUMAN: Answer the question using ONLY the given context. If you are unsure of the answer, respond with "Unknown[STOP]". Conclude your response with "[STOP]" to indicate the completion of the answer.

Context: {context}

Question: {question}

ASSISTANT:"""
            return {"prompt": PromptTemplate(template=question_prompt, input_variables=["context", "question"])}
        case "refine":
            question_prompt = """HUMAN: Answer the question using ONLY the given context.
Indicate the end of your answer with "[STOP]" and refrain from adding any additional information beyond that which is provided in the context.

Question: {question}

Context: {context_str}

ASSISTANT:"""
            refine_prompt = """HUMAN: Refine the original answer to the question using the new context.
Use ONLY the information from the context and your previous answer.
If the context is not helpful, use the original answer.
Indicate the end of your answer with "[STOP]" and avoid adding any extraneous information.

Original question: {question}

Existing answer: {existing_answer}

New context: {context_str}

ASSISTANT:"""
            return {
                "question_prompt": PromptTemplate(template=question_prompt, input_variables=["context_str", "question"]),
                "refine_prompt": PromptTemplate(template=refine_prompt, input_variables=["context_str", "existing_answer", "question"]),
            }
        case _:
            return {}
