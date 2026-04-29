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
