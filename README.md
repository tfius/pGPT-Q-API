# FORK OF A FORK OF A FORK

This is a fork of: 
   https://github.com/su77ungr/CASALIOY
   which is a fork of 
   https://github.com/imartinez/privateGPT/
   and then added fastapi similar to 
   https://github.com/menloparklab/privateGPT-app/
 

### This was put together in a hackish way to test things out. 

#### TODO
- [ ] fix container build workflow
- [ ] add tests
- [ ] add more documentation
- [ ] add more features
- [ ] add more models
- [ ] add more datas

Documentation below is from forked repo, container is not built correctly, poetry install might not work, 
install all with ```pip install -r requirements.txt```

## Server
to start server run ```uvicorn main:app --reload```


### build requrements
pipreqs --ignore bin,etc,include,lib,lib64,models,source_documents,.github --encoding utf-8



### Build it from source

> First install all requirements:

```shell
python -m pip install poetry
python -m poetry config virtualenvs.in-project true
python -m poetry install
. .venv/bin/activate
python -m pip install --force streamlit sentence_transformers  # Temporary bandaid fix, waiting for streamlit >=1.23
pre-commit install
```

If you want GPU support for llama-ccp:

```shell
pip uninstall -y llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install --force llama-cpp-python
```

> Edit the example.env to fit your models and rename it to .env

```env
# Generic
MODEL_N_CTX=1024
TEXT_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
TEXT_EMBEDDINGS_MODEL_TYPE=HF  # LlamaCpp or HF
USE_MLOCK=true

# Ingestion
PERSIST_DIRECTORY=db
DOCUMENTS_DIRECTORY=source_documents
INGEST_CHUNK_SIZE=500
INGEST_CHUNK_OVERLAP=50

# Generation
MODEL_TYPE=LlamaCpp # GPT4All or LlamaCpp
MODEL_PATH=eachadea/ggml-vicuna-7b-1.1/ggml-vic7b-q5_1.bin
MODEL_TEMP=0.8
MODEL_STOP=[STOP]
CHAIN_TYPE=stuff
N_RETRIEVE_DOCUMENTS=100 # How many documents to retrieve from the db
N_FORWARD_DOCUMENTS=6 # How many documents to forward to the LLM, chosen among those retrieved

# option helps prevent the model from generating repetitive or monotonous text. A higher value (e.g., 1.5) will penalize repetitions more strongly, while a lower value (e.g., 0.9) will be more lenient. The default value is 1.1.
MODEL_REPEAT_PENALTY=1.3 
MODEL_TOP_K=50 
MODEL_TOP_P=1
MODEL_NO_REPEAT_NGRAM_SIZE=6
```

This should look like this

```
└── repo
      ├── startLLM.py
      ├── casalioy
      │   └── ingest.py, load_env.py, startLLM.py, gui.py, ...
      ├── source_documents
      │   └── sample.csv
      │   └── ...
      ├── models
      │   ├── ggml-vic7b-q5_1.bin
      │   └── ...
      └── .env, convert.py, Dockerfile
```


> 👇 Update your installation!


      git pull && poetry install



## Ingesting your own dataset

To automatically ingest different data types (.txt, .pdf, .csv, .epub, .html, .docx, .pptx, .eml, .msg)


> inside `source_documents` to run tests with.

```shell
python retrive/ingest.py # optional <path_to_your_data_directory>
```

Optional: use `y` flag to purge existing vectorstore and initialize fresh instance

```shell
python retrive/ingest.py # optional <path_to_your_data_directory> y
```

This spins up a local qdrant namespace inside the `db` folder containing the local vectorstore. Will take time,
depending on the size of your document.
You can ingest as many documents as you want by running `ingest`, and all will be accumulated in the local embeddings
database. To remove dataset simply remove `db` folder.

## Ask questions to your documents, locally!

In order to ask a question, run a command like:

```shell
python retrive/startLLM.py
```

And wait for the script to require your input.

```shell
> Enter a query:
```

Hit enter. You'll need to wait 20-30 seconds (depending on your machine) while the LLM model consumes the prompt and
prepares the answer. Once done, it will print the answer and the 4 sources it used as context from your documents; you
can then ask another question without re-running the script, just wait for the prompt again.

Note: you could turn off your internet connection, and the script inference would still work. No data gets out of your
local environment.

Type `exit` to finish the script.


```shell
streamlit run retrive/gui.py
```

## Disclaimer
see DISCLAIMER.md
