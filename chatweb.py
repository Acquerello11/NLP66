import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ──────────────────────────────────────────────
# CONFIG & SETUP
# ──────────────────────────────────────────────
load_dotenv()
DB_PATH = "vector_db"
API_KEY = os.getenv("GOOGLE_API_KEY")

# ตั้งค่าหน้าตาของเว็บ
st.set_page_config(page_title="AIBO - Personal RAG", page_icon="🤖", layout="wide")

def get_rag_chain():
    # ใช้ st.cache_resource เพื่อให้โหลดโมเดลแค่ครั้งเดียว ไม่โหลดใหม่ทุกครั้งที่กดปุ่ม
    if not Path(DB_PATH).exists():
        st.error(f"ไม่พบฐานข้อมูล '{DB_PATH}' กรุณารัน ingest.py ก่อน")
        return None

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", api_key=API_KEY)
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3, api_key=API_KEY)
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

    prompt = ChatPromptTemplate.from_template("""
    ตอบคำถามจาก Context เท่านั้น เน้นกระชับที่สุด (2-3 ประโยค) 
    ถ้าไม่มีในเอกสารให้บอกว่า "ไม่พบข้อมูลในฐานความรู้ครับ"
    
    Context: {context}
    คำถาม: {input}
    คำตอบ:""")

    combine_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(vector_db.as_retriever(search_kwargs={"k": 2}), combine_chain)

# ──────────────────────────────────────────────
# UI DESIGN
# ──────────────────────────────────────────────
st.title("🤖 AIBO: Personal Doc Assistant")
st.markdown("---")

# ส่วนของ Sidebar สำหรับสถานะ
with st.sidebar:
    st.header("System Status")
    if API_KEY:
        st.success("API Key: Connected")
    else:
        st.error("API Key: Missing")
    
    if Path(DB_PATH).exists():
        st.success("Vector DB: Ready")
    else:
        st.warning("Vector DB: Not Found")

# โหลด Chain
chain = get_rag_chain()

# สร้าง Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติการคุย
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ช่องพิมพ์คำถาม
if prompt := st.chat_input("ถามอะไรผมดีครับ?"):
    # แสดงคำถามผู้ใช้
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ประมวลผลและตอบ
    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูล..."):
            try:
                response = chain.invoke({"input": prompt})
                answer = response["answer"]
                
                # แสดงคำตอบ
                st.markdown(answer)
                
                # แสดงแหล่งอ้างอิงแบบ Expander (ดูสะอาดตา)
                with st.expander("ดูแหล่งอ้างอิง (Sources)"):
                    for doc in response["context"]:
                        src = Path(doc.metadata.get("source", "")).name
                        st.write(f"📄 **{src}**")
                        st.caption(f"{doc.page_content[:200]}...")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")