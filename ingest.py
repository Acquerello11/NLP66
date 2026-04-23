import os
import time
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. ตั้งค่า API Key และโฟลเดอร์
os.environ["GOOGLE_API_KEY"] = "AIzaSyC_sF1okUEtI03HbZXTch0tZ3Sj48GnJ8A"  # ใส่ API Key ของคุณตรงนี้
DOCS_PATH = "my_documents" 
DB_PATH = "vector_db"      

def start_ingesting():
    if not os.path.exists(DOCS_PATH):
        os.makedirs(DOCS_PATH)
        print(f"สร้างโฟลเดอร์ {DOCS_PATH} แล้ว! เอาไฟล์ไปวางในนั้นก่อนรันอีกรอบนะ")
        return

    print("กำลังเริ่มอ่านไฟล์...")
    
    # 2. Load Documents
    pdf_loader = DirectoryLoader(DOCS_PATH, glob="./*.pdf", loader_cls=PyPDFLoader)
    txt_loader = DirectoryLoader(DOCS_PATH, glob="./*.txt", loader_cls=TextLoader)
    
    documents = pdf_loader.load() + txt_loader.load()
    
    if not documents:
        print("ไม่เจอไฟล์ในโฟลเดอร์เลย ลองใส่ไฟล์ .pdf หรือ .txt ดูก่อนครับ")
        return

    # 3. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"หั่นไฟล์เป็น {len(chunks)} ชิ้นเรียบร้อย")

    # 4. Embed & Store (ส่งข้อมูลทีละก้อนเพื่อไม่ให้โดนแบน)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # สร้างฐานข้อมูลเปล่าๆ มารอรับ
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    
    batch_size = 80
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(f"กำลังนำเข้าข้อมูลชิ้นที่ {i+1} ถึง {i+len(batch)}...")
        
        # ค่อยๆ ยัดข้อมูลลงฐาน
        vector_db.add_documents(batch)
        
        # ถ้ายังไม่ถึงก้อนสุดท้าย ให้หยุดพัก 60 วินาที
        if i + batch_size < len(chunks):
            print("⏳ พักหายใจ 60 วินาที ให้โควต้า Google รีเซ็ตก่อน...")
            time.sleep(60)

    print(f"✅ บันทึกความจำลง {DB_PATH} เรียบร้อยแล้วครับ!")

if __name__ == "__main__":
    start_ingesting()