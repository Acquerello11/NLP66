import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

os.environ["GOOGLE_API_KEY"] = "AIzaSyC_sF1okUEtI03HbZXTch0tZ3Sj48GnJ8A"
DB_PATH = "vector_db"

def ask_question(query):
    # 1. โหลดฐานข้อมูลความจำที่เราทำไว้ในสเต็ปแรก
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

    # 2. ตั้งค่าสมอง Gemini (ตัวสรุปคำตอบ)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

    # 3. สร้างระบบค้นหา (RAG Chain)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}), # ดึง 3 ชิ้นที่ใกล้เคียงที่สุด
        return_source_documents=True # ให้บอกด้วยว่าเอามาจากไหน
    )

    # 4. ยิงคำถาม
    result = qa_chain.invoke({"query": query})
    
    print(f"\n🤖 คำตอบ: {result['result']}")
    print("\n📚 อ้างอิงจากไฟล์:")
    for doc in result['source_documents']:
        print(f"- {doc.metadata['source']}")

if __name__ == "__main__":
    while True:
        q = input("\nอยากรู้อะไรเกี่ยวกับไฟล์ในเครื่อง (พิมพ์ 'exit' เพื่อเลิก): ")
        if q.lower() == 'exit': break
        ask_question(q)