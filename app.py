"""
RAGenix - Advanced RAG Agent
app.py

Main Chainlit application entry-point.

Features
--------
- PDF upload & multi-page extraction
- Hybrid BM25 + Qdrant vector search
- Cohere reranker for contextual compression
- Streaming final answers
- Source citations in every reply
- Chat history & multi-turn conversation (NEW)
- Graceful error handling with user-visible messages (IMPROVED)
- Support for multiple simultaneous PDF uploads (NEW)
"""

import chainlit as cl
from io import BytesIO
import PyPDF2

from configure_models import (
    bge_embeddings,
    compressor,
    llm,
    text_splitter,
)

from langchain.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.retrievers import (
    BM25Retriever,
    EnsembleRetriever,
    ContextualCompressionRetriever,
)
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain


# ---------------------------------------------------------------------------
# Helper: extract text from an uploaded PDF
# ---------------------------------------------------------------------------
def extract_pdf_text(file_content: bytes) -> str:
    """Return all text extracted from a PDF byte-string."""
    pdf_stream = BytesIO(file_content)
    reader = PyPDF2.PdfReader(pdf_stream)
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)
    return "\n".join(pages_text)


# ---------------------------------------------------------------------------
# Helper: build retrieval chain from text chunks
# ---------------------------------------------------------------------------
async def build_retrieval_chain(texts: list[str], metadatas: list[dict]):
    """
    Build an ensemble (BM25 + Qdrant) retriever with Cohere reranking,
    then wrap it in a ConversationalRetrievalChain with memory.
    """
    # BM25 lexical retriever
    bm25_retriever = BM25Retriever.from_texts(texts, metadatas=metadatas)
    bm25_retriever.k = 5

    # Qdrant dense retriever (in-memory)
    docsearch = await cl.make_async(Qdrant.from_texts)(
        texts,
        bge_embeddings,
        location=":memory:",
        metadatas=metadatas,
    )
    qdrant_retriever = docsearch.as_retriever(search_kwargs={"k": 5})

    # Hybrid ensemble
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, qdrant_retriever],
        weights=[0.5, 0.5],
    )

    # Contextual compression with Cohere rerank
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=ensemble_retriever,
    )

    # Conversation memory (last 5 turns)
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        k=5,
        return_messages=True,
        output_key="answer",
    )

    # Conversational chain (supports follow-up questions)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=compression_retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
    )

    return chain


# ---------------------------------------------------------------------------
# on_chat_start — upload & index
# ---------------------------------------------------------------------------
@cl.on_chat_start
async def init():
    """Prompt the user for PDF file(s) and build the retrieval index."""

    # Welcome banner
    await cl.Message(
        content=(
            "## 🔍 RAGenix — Advanced RAG Agent\n\n"
            "Upload one or more PDF files to get started. "
            "Once processed, you can ask questions and I'll retrieve "
            "precise answers with source citations."
        )
    ).send()

    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="📎 Please upload a PDF file to begin!",
            accept=["application/pdf"],
            max_size_mb=20,
            max_files=3,           # allow up to 3 PDFs at once
            timeout=120,
        ).send()

    # Process all uploaded files
    all_texts: list[str] = []
    all_metadatas: list[dict] = []
    processed_names: list[str] = []

    for file in files:
        processing_msg = cl.Message(content=f"⚙️ Processing `{file.name}`…")
        await processing_msg.send()

        try:
            pdf_text = extract_pdf_text(file.content)
            if not pdf_text.strip():
                await cl.Message(
                    content=f"⚠️ `{file.name}` appears to be empty or scanned (no extractable text). Skipping."
                ).send()
                continue

            chunks = text_splitter.split_text(pdf_text)
            metadatas = [
                {"source": f"{file.name}::chunk-{i}", "file": file.name}
                for i in range(len(chunks))
            ]
            all_texts.extend(chunks)
            all_metadatas.extend(metadatas)
            processed_names.append(file.name)

            processing_msg.content = f"✅ `{file.name}` processed — {len(chunks)} chunks indexed."
            await processing_msg.update()

        except Exception as exc:
            await cl.Message(
                content=f"❌ Failed to process `{file.name}`: {exc}"
            ).send()

    if not all_texts:
        await cl.Message(
            content="No processable content found. Please restart and upload a valid PDF."
        ).send()
        return

    # Build the retrieval chain
    build_msg = cl.Message(content="🔧 Building retrieval index…")
    await build_msg.send()

    try:
        chain = await build_retrieval_chain(all_texts, all_metadatas)
    except Exception as exc:
        await cl.Message(content=f"❌ Failed to build retrieval chain: {exc}").send()
        return

    # Persist session state
    cl.user_session.set("chain", chain)
    cl.user_session.set("metadatas", all_metadatas)
    cl.user_session.set("texts", all_texts)
    cl.user_session.set("processed_files", processed_names)

    build_msg.content = (
        f"✅ Ready! Indexed **{len(all_texts)} chunks** from "
        f"{', '.join(f'`{n}`' for n in processed_names)}.\n\n"
        "Ask me anything about your document(s)!"
    )
    await build_msg.update()


# ---------------------------------------------------------------------------
# on_message — question answering
# ---------------------------------------------------------------------------
@cl.on_message
async def process_response(message: cl.Message):
    """Handle an incoming user question and stream the answer."""
    chain = cl.user_session.get("chain")

    if chain is None:
        await cl.Message(
            content="⚠️ No document loaded. Please restart the chat and upload a PDF."
        ).send()
        return

    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True,
        answer_prefix_tokens=["FINAL", "ANSWER"],
    )
    cb.answer_reached = True

    try:
        res = await chain.acall(
            {"question": message.content},
            callbacks=[cb],
        )
    except Exception as exc:
        await cl.Message(content=f"❌ An error occurred while processing your question: {exc}").send()
        return

    answer = res.get("answer", res.get("result", "No answer returned."))
    source_documents = res.get("source_documents", [])

    source_elements: list[cl.Text] = []
    cited_sources: list[str] = []

    for doc in source_documents:
        src_label = doc.metadata.get("source", "unknown")
        if src_label not in cited_sources:
            cited_sources.append(src_label)
            source_elements.append(
                cl.Text(content=doc.page_content, name=src_label, display="side")
            )

    if cited_sources:
        answer += f"\n\n**Sources:** {', '.join(cited_sources)}"
    else:
        answer += "\n\n*No specific sources identified.*"

    if cb.has_streamed_final_answer:
        cb.final_stream.elements = source_elements
        await cb.final_stream.update()
    else:
        await cl.Message(content=answer, elements=source_elements).send()


# ---------------------------------------------------------------------------
# Entry-point hint (run with: chainlit run app.py)
# ---------------------------------------------------------------------------
