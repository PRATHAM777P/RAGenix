"""
RAGenix - Advanced RAG Agent
configure_models.py

Model configuration and initialization module.
All credentials are loaded from environment variables (.env file).
Never hardcode credentials or local paths in this file.
"""

import os
import chainlit as cl
from io import BytesIO
import PyPDF2
import yaml
from cohere import Client
from dotenv import load_dotenv

from langchain.vectorstores import Qdrant
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain, RetrievalQA

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import (
    BM25Retriever,
    EnsembleRetriever,
    ContextualCompressionRetriever,
)

# ---------------------------------------------------------------------------
# Load credentials from environment variables
# ---------------------------------------------------------------------------
# Option 1: Use a .env file (recommended for local dev — never commit .env!)
# Option 2: Set env vars directly in your shell / deployment platform

load_dotenv()  # reads .env if present; silently skips if absent

REQUIRED_ENV_VARS = [
    "OPENAI_API_TYPE",
    "AZURE_OPENAI_VERSION",
    "AZURE_OPENAI_BASE",
    "AZURE_OPENAI_KEY",
    "AZURE_DEPLOYMENT_NAME",
    "AZURE_ENGINE",
    "COHERE_API_KEY",
]

missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
if missing:
    raise EnvironmentError(
        f"Missing required environment variables: {missing}\n"
        "Create a .env file (see .env.example) or export them in your shell."
    )

os.environ["OPENAI_API_TYPE"]    = os.getenv("OPENAI_API_TYPE")
os.environ["OPENAI_API_VERSION"] = os.getenv("AZURE_OPENAI_VERSION")
os.environ["OPENAI_API_BASE"]    = os.getenv("AZURE_OPENAI_BASE")
os.environ["OPENAI_API_KEY"]     = os.getenv("AZURE_OPENAI_KEY")
os.environ["COHERE_API_KEY"]     = os.getenv("COHERE_API_KEY")

# ---------------------------------------------------------------------------
# Device selection (GPU if available, else CPU)
# ---------------------------------------------------------------------------
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
bge_embeddings = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": DEVICE},
    encode_kwargs={"normalize_embeddings": True},
)

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
    model_name=os.getenv("AZURE_ENGINE"),
    temperature=0.75,
    max_tokens=1500,
)

# ---------------------------------------------------------------------------
# Cohere reranker
# ---------------------------------------------------------------------------
cohere_client = Client(api_key=os.environ["COHERE_API_KEY"])
compressor = CohereRerank(client=cohere_client, user_agent="langchain")

# ---------------------------------------------------------------------------
# Text splitter
# ---------------------------------------------------------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
system_template = """Use the following pieces of context to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
ALWAYS return a "SOURCES" part in your answer.
The "SOURCES" part should be a reference to the source of the document from which you got your answer.

Begin!
- - - - - - - -
{summaries}"""

messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}"),
]
prompt = ChatPromptTemplate.from_messages(messages)
chain_type_kwargs = {"prompt": prompt}
