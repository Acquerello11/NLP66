<<<<<<< HEAD
"""
ingest.py — Smart RAG Data Ingestion Pipeline
- สร้าง vector_db อัตโนมัติถ้ายังไม่มี
- ตรวจจับไฟล์ใหม่และข้ามไฟล์ที่เคย ingest แล้ว
- ใช้ SHA-256 hash ป้องกันการ ingest ซ้ำ
"""

import os
import time
import json
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
load_dotenv()
API_KEY   = os.getenv("GEMINI_API_KEY")
DOCS_PATH = Path("my_documents")
DB_PATH   = "vector_db"
MANIFEST  = Path("ingested_manifest.json")   # ไฟล์ติดตามว่าอ่านไปแล้วอะไรบ้าง
BATCH     = 80                                # จำนวน chunk ต่อ batch
SLEEP     = 60                                # วินาทีที่รอระหว่าง batch

SUPPORTED = {".pdf": PyPDFLoader, ".txt": TextLoader}

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def sha256(path: Path) -> str:
    """คำนวณ hash ของไฟล์เพื่อตรวจว่าเปลี่ยนแปลงหรือไม่"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    """โหลด manifest {relative_path: hash} จากไฟล์ JSON"""
    if MANIFEST.exists():
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict):
    """บันทึก manifest กลับไปที่ไฟล์"""
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def scan_new_files(manifest: dict) -> list[Path]:
    """คืนรายการไฟล์ที่ยังไม่เคย ingest หรือมีการแก้ไข"""
    new_files = []
    for ext in SUPPORTED:
        for path in sorted(DOCS_PATH.glob(f"*{ext}")):
            key  = str(path)
            h    = sha256(path)
            if manifest.get(key) != h:
                new_files.append(path)
    return new_files


def load_documents(path: Path):
    """โหลด document ตาม loader ที่เหมาะสมกับ extension"""
    loader_cls = SUPPORTED[path.suffix.lower()]
    return loader_cls(str(path)).load()

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def start_ingesting():
    # 0. เตรียมโฟลเดอร์
    DOCS_PATH.mkdir(exist_ok=True)

    print("=" * 55)
    print("   🧠  Personal RAG — Smart Ingestion Pipeline")
    print("=" * 55)

    # 1. โหลด manifest (ไฟล์ที่เคย ingest แล้ว)
    manifest = load_manifest()

    # 2. หาไฟล์ใหม่ / ไฟล์ที่เปลี่ยนแปลง
    new_files = scan_new_files(manifest)

    if not new_files:
        total = len(list(DOCS_PATH.glob("*.pdf")) + list(DOCS_PATH.glob("*.txt")))
        print(f"\n✅ ไม่มีไฟล์ใหม่ — ฐานข้อมูลทันสมัยอยู่แล้ว ({total} ไฟล์ในคลัง)")
        return

    print(f"\n🔍 พบไฟล์ใหม่/แก้ไข {len(new_files)} ไฟล์:")
    for f in new_files:
        print(f"   + {f.name}")

    # 3. โหลดและหั่น document
    print("\n📖 กำลังอ่านและหั่นเอกสาร...")
    all_chunks = []
    file_chunk_map = {}   # เก็บว่าแต่ละไฟล์ได้กี่ chunk

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    for path in new_files:
        docs   = load_documents(path)
        chunks = splitter.split_documents(docs)
        file_chunk_map[path] = len(chunks)
        all_chunks.extend(chunks)
        print(f"   ✂️  {path.name} → {len(chunks)} chunks")

    print(f"\n📦 รวมทั้งหมด {len(all_chunks)} chunks พร้อม embed")

    # 4. เชื่อม / สร้าง Vector DB
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=API_KEY,
    )
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

    db_existed = Path(DB_PATH).exists()
    print(f"\n{'🔧 สร้าง' if not db_existed else '🔗 เชื่อมต่อ'} Vector DB ที่ {DB_PATH}/")

    # 5. Embed ทีละ batch
    print("\n⚡ กำลัง Embed และบันทึกลงฐานข้อมูล...")
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        print(f"   Batch {i // BATCH + 1}: chunk {i+1}–{i+len(batch)}")
        vector_db.add_documents(batch)

        if i + BATCH < len(all_chunks):
            print(f"   ⏳ พักหายใจ {SLEEP}s ให้ quota รีเซ็ต...")
            time.sleep(SLEEP)

    # 6. อัปเดต manifest
    for path in new_files:
        manifest[str(path)] = sha256(path)
    save_manifest(manifest)

    print(f"\n✅ เสร็จสิ้น! บันทึก {len(new_files)} ไฟล์ลง {DB_PATH}/ และอัปเดต manifest แล้ว")
    print("=" * 55)


if __name__ == "__main__":
    start_ingesting()
=======
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
>>>>>>> 5cbcab05c145f19508d4f87f8e94025812ff9187
