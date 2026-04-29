# 🧠 Personal RAG Assistant

ผู้ช่วย AI สำหรับค้นหาและวิเคราะห์เอกสารส่วนตัว ด้วย Retrieval-Augmented Generation (RAG)
สร้างด้วย LangChain · Gemini 1.5 Flash · ChromaDB

---

## 📋 สารบัญ

- [ภาพรวม](#-ภาพรวม)
- [โครงสร้างโปรเจค](#-โครงสร้างโปรเจค)
- [ความต้องการของระบบ](#-ความต้องการของระบบ)
- [การติดตั้ง](#-การติดตั้ง)
- [การตั้งค่า API Key](#-การตั้งค่า-api-key)
- [วิธีใช้งาน](#-วิธีใช้งาน)
- [การทำงานของระบบ](#-การทำงานของระบบ)
- [คำอธิบายไฟล์](#-คำอธิบายไฟล์)
- [แก้ปัญหาที่พบบ่อย](#-แก้ปัญหาที่พบบ่อย)

---

## 🔍 ภาพรวม

โปรเจคนี้สร้างระบบ RAG (Retrieval-Augmented Generation) ที่ให้ AI ตอบคำถามจากเอกสารส่วนตัวของคุณ โดยไม่ต้อง fine-tune โมเดล และไม่มีปัญหา hallucination เพราะ AI จะอ้างอิงแหล่งที่มาทุกครั้ง

**ทำอะไรได้บ้าง:**
- อ่านและจดจำไฟล์ `.pdf` และ `.txt` ในโฟลเดอร์ที่กำหนด
- ตอบคำถามแบบ semantic search — ไม่ต้องจำคำเป๊ะๆ
- บอกได้ว่าคำตอบมาจากไฟล์ไหน หน้าไหน
- อัปเดตอัตโนมัติเมื่อมีไฟล์ใหม่ — ไม่ ingest ไฟล์ซ้ำ

---

## 📁 โครงสร้างโปรเจค

```
personal-rag/
│
├── ingest.py                  # สร้างและอัปเดต Vector Database
├── chat.py                    # CLI สำหรับถามคำถาม
│
├── my_documents/              # 📂 วางไฟล์เอกสารที่นี่
│   ├── example.pdf
│   └── notes.txt
│
├── vector_db/                 # 🗄️ สร้างอัตโนมัติโดย ingest.py
├── ingested_manifest.json     # 📋 บันทึกไฟล์ที่ ingest แล้ว
│
├── .env                       # 🔑 ไฟล์เก็บ API Key (ไม่ commit ขึ้น git)
└── requirements.txt           # 📦 รายชื่อ library ที่ต้องใช้
```

---

## 💻 ความต้องการของระบบ

| รายการ | เวอร์ชัน |
|--------|---------|
| Python | 3.11
 |
| pip | ล่าสุด |
| Gemini API Key | จาก Google AI Studio |
| พื้นที่ดิสก์ | ขึ้นอยู่กับขนาดเอกสาร |

---

## 📦 การติดตั้ง

### 1. Clone หรือดาวน์โหลดโปรเจค

```bash
git clone <your-repo-url>
cd personal-rag
```

### 2. สร้าง Virtual Environment (แนะนำ)

```bash
# สร้าง venv
python -m venv venv

# เปิดใช้งาน (macOS / Linux)
source venv/bin/activate

# เปิดใช้งาน (Windows)
venv\Scripts\activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt ที่ต้องมี:**
```
langchain
langchain-community
langchain-chroma
langchain-google-genai
langchain-text-splitters
chromadb
pypdf
python-dotenv
```

---

## 🔑 การตั้งค่า API Key

### 1. ขอ Gemini API Key

1. ไปที่ [Google AI Studio](https://aistudio.google.com/app/apikey)
2. คลิก **Create API Key**
3. คัดลอก key ที่ได้

### 2. สร้างไฟล์ `.env`

สร้างไฟล์ชื่อ `.env` ที่ root ของโปรเจค แล้วใส่:

```env
GEMINI_API_KEY=your_api_key_here
```

> ⚠️ อย่า commit ไฟล์ `.env` ขึ้น GitHub เด็ดขาด! เพิ่ม `.env` ลงใน `.gitignore`

---

## 🚀 วิธีใช้งาน

### Step 1 — เพิ่มเอกสาร

วางไฟล์ `.pdf` หรือ `.txt` ลงในโฟลเดอร์ `my_documents/`

```bash
# ตัวอย่าง
cp ~/Downloads/คู่มือ.pdf my_documents/
cp ~/Desktop/notes.txt my_documents/
```

### Step 2 — สร้าง / อัปเดต Vector Database

```bash
python ingest.py
```

**ผลลัพธ์ที่จะเห็น:**
```
=======================================================
   🧠  Personal RAG — Smart Ingestion Pipeline
=======================================================

🔍 พบไฟล์ใหม่/แก้ไข 2 ไฟล์:
   + คู่มือ.pdf
   + notes.txt

📖 กำลังอ่านและหั่นเอกสาร...
   ✂️  คู่มือ.pdf → 47 chunks
   ✂️  notes.txt → 8 chunks

📦 รวมทั้งหมด 55 chunks พร้อม embed
⚡ กำลัง Embed และบันทึกลงฐานข้อมูล...

✅ เสร็จสิ้น!
```

> ✅ รัน `ingest.py` ซ้ำได้เรื่อยๆ — ไฟล์ที่เคย ingest แล้วจะถูกข้ามอัตโนมัติ

### Step 3 — ถามคำถาม

**โหมด Interactive** (แนะนำ):

```bash
python chat.py
```

```
❓ คำถาม: วิธีซ่อมมอเตอร์ในคู่มือบอกว่าไง?

⏳ กำลังค้นหาและประมวลผล...

🤖 คำตอบ
───────────────────────────────────────────────────────
  ตามคู่มือ หน้า 23 การซ่อมมอเตอร์ให้ทำตามขั้นตอนดังนี้:
  1. ปิดสวิตช์และรอให้เครื่องเย็น...
───────────────────────────────────────────────────────

📚 แหล่งอ้างอิง (3 ชิ้น)
  [1] คู่มือ.pdf  หน้า 23
      "การซ่อมบำรุงมอเตอร์ควรทำโดยช่างที่ได้รับการอบรม…"
```

**โหมด One-shot** (พิมพ์คำถามพร้อมคำสั่ง):

```bash
python chat.py "สรุปเนื้อหาของไฟล์ notes.txt"
python chat.py "มีข้อกำหนดอะไรในสัญญาบ้าง?"
```

**ออกจากโปรแกรม:** พิมพ์ `exit` หรือกด `Ctrl+C`

---

## ⚙️ การทำงานของระบบ

```
Phase 1: Data Ingestion (ingest.py)
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Load files  │ →  │ Split chunks │ →  │    Embed     │ →  │  Store DB    │
│  PDF / TXT   │    │  1000 chars  │    │  Gemini API  │    │  ChromaDB    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

Phase 2: Retrieval & Generation (chat.py)
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  User query  │ →  │  Embed query │ →  │  Retrieve k3 │ →  │  Generate    │
│  คำถามของคุณ │    │  Gemini API  │    │  Cosine sim  │    │  Flash 1.5   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### ไฟล์ที่ระบบสร้างขึ้นเอง

| ไฟล์ | คำอธิบาย |
|------|---------|
| `vector_db/` | ChromaDB เก็บ vector embeddings ทั้งหมด |
| `ingested_manifest.json` | บันทึก SHA-256 hash ของไฟล์ที่ ingest แล้ว |
| `my_documents/` | โฟลเดอร์สำหรับวางเอกสาร (สร้างถ้าไม่มี) |

---

## 📄 คำอธิบายไฟล์

### `ingest.py`

| ฟังก์ชัน | หน้าที่ |
|---------|--------|
| `sha256(path)` | คำนวณ hash ของไฟล์เพื่อตรวจการเปลี่ยนแปลง |
| `load_manifest()` | โหลดรายการไฟล์ที่เคย ingest แล้ว |
| `save_manifest()` | บันทึก manifest หลัง ingest เสร็จ |
| `scan_new_files()` | เปรียบเทียบ hash — คืนเฉพาะไฟล์ใหม่/แก้ไข |
| `start_ingesting()` | ฟังก์ชันหลัก ประสาน pipeline ทั้งหมด |

**ค่าที่ปรับได้:**

```python
DOCS_PATH = Path("my_documents")   # โฟลเดอร์เอกสาร
DB_PATH   = "vector_db"            # ที่เก็บ DB
BATCH     = 80                     # chunks ต่อ batch
SLEEP     = 60                     # วินาทีพักระหว่าง batch
```

### `chat.py`

| ฟังก์ชัน | หน้าที่ |
|---------|--------|
| `build_chain()` | สร้าง RAG chain เชื่อมต่อ DB + LLM |
| `ask(chain, query)` | ส่งคำถามและแสดงผลลัพธ์ |
| `interactive_mode()` | REPL loop สำหรับถามหลายคำถาม |
| `one_shot_mode()` | ถามคำถามเดียวจาก argument |

**ค่าที่ปรับได้:**

```python
TOP_K = 3        # จำนวน chunk ที่ดึงมาอ้างอิง (เพิ่มเพื่อความครอบคลุม)
temperature = 0.3  # ความสร้างสรรค์ของคำตอบ (0 = ตรงที่สุด, 1 = สร้างสรรค์)
```

---

## 🛠️ แก้ปัญหาที่พบบ่อย

### ❌ `GEMINI_API_KEY not found`

```
แก้: ตรวจสอบว่ามีไฟล์ .env และ key ถูกต้อง
```

```bash
# ตรวจสอบไฟล์ .env
cat .env
# ควรเห็น: GEMINI_API_KEY=AIza...
```

### ❌ `No module named 'langchain_chroma'`

```bash
pip install -r requirements.txt
# หรือ
pip install langchain-chroma langchain-google-genai chromadb
```

### ❌ `429 Resource Exhausted` (quota หมด)

ระบบจะพัก 60 วินาทีระหว่าง batch อัตโนมัติ ถ้ายังเจอ:

```python
# แก้ใน ingest.py
BATCH = 40     # ลด batch size ลง
SLEEP = 120    # เพิ่มเวลาพัก
```

### ❌ `vector_db/ not found` ตอนรัน chat.py

```bash
# ต้องรัน ingest.py ก่อนเสมอ
python ingest.py
```

### ❌ ไฟล์ไม่ถูก ingest ทั้งที่เพิ่งเพิ่ม

```bash
# ลบ manifest แล้ว ingest ใหม่ทั้งหมด
rm ingested_manifest.json
python ingest.py
```

---

## 🔒 Security

- ไม่ส่งข้อมูลไปเก็บที่เซิร์ฟเวอร์ — Vector DB อยู่บนเครื่องคุณเท่านั้น
- เฉพาะข้อความที่ดึงมาตอบคำถามเท่านั้นที่ถูกส่งไป Gemini API
- API Key เก็บใน `.env` ไม่ถูก hardcode ในโค้ด

---

## 📜 License

MIT License — ใช้งานได้เสรี ทั้งส่วนตัวและเชิงพาณิชย์

---

*สร้างด้วย ❤️ สำหรับโปรเจคสายปัญญาประดิษฐ์*
