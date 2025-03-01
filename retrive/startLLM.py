"""start the local LLM"""

import qdrant_client
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import Qdrant
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text.html import html_escape

from retrive.CustomChains import RefineQA, StuffQA
from retrive.load_env import (
    chain_type,
    get_embedding_model,
    get_prompt_template_kwargs,
    model_max_tokens,
    model_n_ctx,
    model_path,
    model_stop,
    model_temp,
    model_type,
    model_n_predict,
    model_top_k,
    model_top_p,
    n_forward_documents,
    n_gpu_layers,
    n_retrieve_documents,
    persist_directory,
    use_mlock,
    model_repeat_penalty,
    model_use_mmap,
    model_n_threads,
    model_n_batch,
    model_verbose,
    model_streaming_response,
)
from retrive.utils import print_HTML, prompt_HTML


class QASystem:
    """custom QA system"""

    def __init__(
        self,
        embeddings: Embeddings,
        db_path: str,
        model_path: str,
        n_ctx: int,
        #model_temp: float,
        stop: list[str],
        #use_mlock: bool,
        #n_gpu_layers: int,
        collection="test",
        #top_k=50,
        #top_p=1,
        #n_predict=-1
    ):
        # Get embeddings and local vector store
        self.qdrant_client = qdrant_client.QdrantClient(path=db_path, prefer_grpc=True)
        self.qdrant_langchain = Qdrant(client=self.qdrant_client, collection_name=collection, embeddings=embeddings)

        # Prepare the LLM chain
        callbacks = [StreamingStdOutCallbackHandler()]
        match model_type:
            case "LlamaCpp":
                from langchain.llms import LlamaCpp

                llm = LlamaCpp(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    temperature=model_temp,
                    stop=stop,
                    callbacks=callbacks,
                    verbose=model_verbose,
                    n_threads=model_n_threads,
                    n_batch=model_n_batch,
                    use_mlock=use_mlock,
                    top_k=model_top_k,
                    top_p=model_top_p,
                    n_predict=model_n_predict,
                    n_gpu_layers=n_gpu_layers,
                    max_tokens=model_max_tokens,
                    repeat_penalty=model_repeat_penalty,
                    use_mmap=model_use_mmap,
                    streaming=model_streaming_response,
                )
                # Fix wrong default
                # object.__setattr__(llm, "get_num_tokens", lambda text: len(llm.client.tokenize(b" " + text.encode("utf-8"))))
                # setting state will restart llamacpp, there has to be a better way to apply these params
                #state = llm.client.__getstate__()
                #state["top_k"] = top_k
                #state["top_p"] = top_p
                #state["n_predict"] = n_predict
                #llm.client.__setstate__(state)
                #llm.client.verbose = False

            case "GPT4All":
                from langchain.llms import GPT4All

                llm = GPT4All(
                    model=model_path,
                    n_ctx=n_ctx,
                    callbacks=callbacks,
                    verbose=True,
                    backend="gptj",
                )
            case _:
                raise ValueError("Only LlamaCpp or GPT4All supported right now. Make sure you set up your .env correctly.")

        self.llm = llm
        retriever = self.qdrant_langchain.as_retriever(search_type="mmr")
        if chain_type == "betterstuff":
            self.qa = StuffQA(retriever=retriever, llm=self.llm)
        elif chain_type == "betterrefine":
            self.qa = RefineQA(retriever=retriever, llm=self.llm)
        else:
            self.qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type=chain_type,
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs=get_prompt_template_kwargs(),
            )
        self.qa.retriever.search_kwargs = {**self.qa.retriever.search_kwargs, "k": n_forward_documents, "fetch_k": n_retrieve_documents}

    def prompt_once(self, query: str) -> tuple[str, str]:
        """run a prompt"""
        # Get the answer from the chain
        res = self.qa(query)
        answer, docs = res["result"], res["source_documents"]
        print(f"res:{res} result: {answer}, sources: {docs}")

        # Print the result
        sources_str = "\n\n".join(f">> <source>{html_escape(document.metadata['source'])}</source>:\n{html_escape(document.page_content)}" for document in docs)
        print_HTML(
            f"\n\n> <question><b>Question</b>: {query}</question>\n> <answer><b>Answer</b>: {answer}</answer>\n> <b>Sources</b>:\n{sources_str}",
            query=query,
            answer=answer,
            sources_str=sources_str,
        )

        return answer, sources_str


# noinspection PyMissingOrEmptyDocstring
def main() -> None:
    session = PromptSession(auto_suggest=AutoSuggestFromHistory())
    qa_system = QASystem(get_embedding_model()[0], persist_directory, model_path, model_n_ctx, model_temp, model_stop, use_mlock, n_gpu_layers)
    while True:
        query = prompt_HTML(session, "\n<b>Enter a query</b>: ").strip()
        if query == "exit":
            break
        elif not query:  # check if query empty
            print_HTML("<r>Empty query, skipping</r>")
            continue
        qa_system.prompt_once(query)


if __name__ == "__main__":
    main()
