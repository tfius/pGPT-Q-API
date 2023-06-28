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

from https://github.com/imartinez/privateGPT/pull/521

## GPU acceleration
Most importantly the `GPU_IS_ENABLED` variable must be set to `true`. Add this to HuggingfaceEmbeddings:

```python
embeddings_kwargs = {'device': 'cuda'} if gpu_is_enabled else {}
```

### GPU (Windows)
Set `OS_RUNNING_ENVIRONMENT=windows` inside `.env` file

```shell
pip3 install -r requirements_windows.txt
```

Install Visual Studio 2019 - 2022 Code C++ compiler on Windows 10/11:

1. Install Visual Studio.
2. Make sure the following components are selected:
   
   * Universal Windows Platform development
   * C++ `CMake` tools for Windows
3. Download the `MinGW` installer from the [MinGW website](https://sourceforge.net/projects/mingw/).
4. Run the installer and select the `gcc` component.

You can use the included installer batch file to install the required dependencies for GPU acceleration, or:

1. Find your card driver here [NVIDIA Driver Downloads](https://www.nvidia.com/download/index.aspx)
2. Install [NVidia CUDA 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive?target_os=Windows&target_arch=x86_64)
3. Install `llama-cpp-python` package with `cuBLAS` enabled. Run the code below in the directory you want to build the package in.
   
   * Powershell:
   
   ```powershell
   $Env:CMAKE_ARGS="-DLLAMA_CUBLAS=on"; $Env:FORCE_CMAKE=1; pip3 install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
   ```  
   
   * Bash:
   
   ```shell
   CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip3 install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
   ```
4. Enable GPU acceleration in `.env` file by setting `GPU_IS_ENABLED` to `true`
5. Run `ingest.py` and `privateGPT.py` as usual

If the above doesn't work for you, you will have to manually build llama-cpp-python library with CMake:

1. Get repo `git clone https://github.com/abetlen/llama-cpp-python.git`,
   
   * switch to tag this application is using from `requirements-*.txt` file:
   * uninstall your local llama-cpp-python: `pip3 uninstall llama-cpp-python`
2. Open `llama-cpp-python/vendor/llama.cpp/CMakeList.txt` in text editor and add
   `set(LLAMA_CUBLAS 1)` to the line `178` before `if (LLAMA_CUBLAS) line`.
3. Install [CMake](https://cmake.org/download/)
4. Go to `cd llama-cpp-python` and perform the actions:
   
   * perform `git submodule update --init --recursive`
   * `mkdir build` and `cd build`
5. Build llama-cpp-python yourself:
   ```shell
   cmake -G "Visual Studio 16 2019" -A x64 -D CUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8" .. 
   ```
6. Position CLI to this project and install llama from the folder you build, let's say `pip3 install ../llama-cpp-python/`

Next is somewhat @DanielusG already tested on Linux I guess:

### GPU (Linux):
Set `OS_RUNNING_ENVIRONMENT=linux` inside `.env` file

If you have an Nvidia GPU, you can speed things up by installing the `llama-cpp-python` version with CUDA by setting these flags: `export LLAMA_CUBLAS=1`

(some libraries might be different per OS, that's why I separated requirements files)

```shell
pip3 install -r requirements_linux.txt
```

First, you have to uninstall the old torch installation and install CUDA one: Install a proper torch version:

```shell
pip3 uninstall torch
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Now, set environment variables and source them:

```shell
vim ~/.bashrc
```

```shell
export LLAMA_CUBLAS=1
export LLAMA_CLBLAST=1 
export CMAKE_ARGS=-DLLAMA_CUBLAS=on
export FORCE_CMAKE=1
```

```shell
source ~/.bashrc
```

#### LLAMA
llama.cpp doesn't work easily on Windows with GPU,, so you should try with a Linux distro Installing torch with CUDA will only speed up the vector search, not the writing by llama.cpp.

You should install the latest Cuda toolkit:

```shell
conda install -c conda-forge cudatoolkitpip uninstall llama-cpp-python
```

if you're already in conda env you can uninstall llama-cpp-python like this:

```shell
pip3 uninstall llama-cpp-python
```

Install llama:

```shell
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python==0.1.61 --no-cache-dir
```

Modify LLM code to accept `n_gpu_layers`:

```shell
llm = LlamaCpp(model_path=model_path, ..., n_gpu_layers=20)
```

Change environment variable model:

```shell
MODEL_TYPE=llamacpp
MODEL_ID_OR_PATH=models/ggml-vic13b-q5_1.bin
```
