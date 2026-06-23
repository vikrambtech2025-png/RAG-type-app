import os
import tempfile
from pathlib import Path

import streamlit as st
from rag_engine import RAGEngine

st.set_page_config(
    page_title="RAG Chat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp header {display: none;}
    .upload-section {border: 2px dashed #4a90d9; border-radius: 12px; padding: 2rem; text-align: center;}
    .chat-message {padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;}
    .user-msg {background: #1e293b; border-left: 3px solid #4a90d9;}
    .assistant-msg {background: #0f172a; border-left: 3px solid #22c55e;}
    .source-box {background: #1e293b; border-radius: 6px; padding: 0.75rem; margin: 0.5rem 0; font-size: 0.85rem;}
    .stChatInput {position: fixed; bottom: 0; width: 75%;}
</style>
""", unsafe_allow_html=True)

if "rag" not in st.session_state:
    st.session_state.rag = RAGEngine()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()

def reset_conversation():
    st.session_state.messages = []

def reset_all():
    st.session_state.rag.clear()
    st.session_state.messages = []
    st.session_state.uploaded_files = set()

def get_llm_answer(query: str, context: str) -> str:
    backend = st.session_state.get("llm_backend", "none")
    if backend == "none":
        return None

    if backend == "openai":
        try:
            from openai import OpenAI
            api_key = st.session_state.get("openai_api_key", "") or os.getenv("OPENAI_API_KEY", "")
            model = st.session_state.get("openai_model", "gpt-4o-mini")
            if not api_key:
                return "⚠️ OpenAI API key not configured."
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Answer the question based solely on the provided context. If the context doesn't contain enough information, say so."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ OpenAI error: {e}"

    if backend == "ollama":
        try:
            import httpx
            base_url = st.session_state.get("ollama_url", "http://localhost:11434")
            model = st.session_state.get("ollama_model", "llama3")
            resp = httpx.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Answer the question based solely on the provided context. If the context doesn't contain enough information, say so."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except Exception as e:
            return f"⚠️ Ollama error: {e}"

    return "⚠️ No LLM backend configured."

with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("🤖 LLM Backend")
    backend = st.selectbox(
        "Choose backend",
        ["none", "openai", "ollama"],
        index=0,
        key="llm_backend",
        label_visibility="collapsed",
    )

    if backend == "openai":
        st.text_input(
            "OpenAI API Key",
            type="password",
            key="openai_api_key",
            placeholder="sk-...",
        )
        st.text_input(
            "Model",
            value="gpt-4o-mini",
            key="openai_model",
        )
    elif backend == "ollama":
        st.text_input(
            "Ollama URL",
            value="http://localhost:11434",
            key="ollama_url",
        )
        st.text_input(
            "Model",
            value="llama3",
            key="ollama_model",
        )

    st.subheader("🔤 Embeddings")
    st.text_input(
        "Model",
        value="sentence-transformers/all-MiniLM-L6-v2",
        key="embed_model",
        disabled=True,
    )

    st.divider()
    st.subheader("📁 Documents")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 New Chat", use_container_width=True):
            reset_conversation()
            st.rerun()
    with col2:
        if st.button("🗑️ Reset All", use_container_width=True):
            reset_all()
            st.rerun()

    if st.session_state.rag.get_chunk_count() > 0:
        st.divider()
        st.caption(f"**{st.session_state.rag.get_chunk_count()}** chunks across **{len(st.session_state.uploaded_files)}** file(s)")
        for src in st.session_state.rag.get_document_sources():
            st.caption(f"📄 {src}")

st.title("📚 RAG Chat")
st.caption("Upload documents (PDF, DOCX, TXT, MD, CSV, HTML) and ask questions about them.")

uploaded_files = st.file_uploader(
    "Drag & drop files here",
    type=["pdf", "txt", "md", "docx", "csv", "html", "htm"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    status_placeholder = st.empty()
    new_files = 0
    for f in uploaded_files:
        if f.name in st.session_state.uploaded_files:
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
            tmp.write(f.getvalue())
            tmp_path = tmp.name
        try:
            count = st.session_state.rag.add_file(tmp_path)
            st.session_state.uploaded_files.add(f.name)
            new_files += count
        except Exception as e:
            status_placeholder.error(f"❌ {f.name}: {e}")
        finally:
            os.unlink(tmp_path)
    if new_files:
        status_placeholder.success(f"✅ Indexed {new_files} chunks from {len(uploaded_files)} file(s)")
        st.rerun()

st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📖 View sources", expanded=False):
                for i, src in enumerate(msg["sources"]):
                    st.markdown(f"**Source {i+1}:** `{src.metadata.get('source_file', 'unknown')}`")
                    st.markdown(f"```\n{src.page_content[:500]}\n```")

if prompt := st.chat_input("Ask a question about your documents..."):
    if not st.session_state.rag.is_indexed:
        st.warning("Please upload at least one document first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            docs = st.session_state.rag.search(prompt, k=4)

        if not docs:
            response = "No relevant content found in the uploaded documents."
            st.markdown(response)
        else:
            context = "\n\n".join(d.page_content for d in docs)
            answer = get_llm_answer(prompt, context)

            if answer:
                st.markdown(answer)
            else:
                st.markdown("**Retrieved chunks (no LLM backend configured):**")
                for i, d in enumerate(docs):
                    src = d.metadata.get("source_file", "unknown")
                    st.markdown(f"""
<div class="source-box">
<strong>📄 {src}</strong> <em>(similarity rank #{i+1})</em><br>
{d.page_content[:600]}{'...' if len(d.page_content) > 600 else ''}
</div>
""", unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer or "*(See retrieved chunks above)*",
                "sources": docs,
            })

st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem; font-size: 0.85rem;">
Built with Streamlit + LangChain + FAISS + Sentence-Transformers
</div>
""", unsafe_allow_html=True)
