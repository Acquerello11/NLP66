# 🧠 Personal RAG Assistant

ผู้ช่วย AI สำหรับค้นหาและวิเคราะห์เอกสารส่วนตัว ด้วย Retrieval-Augmented Generation (RAG)  
สร้างด้วย **LangChain · Gemini 2.5 Pro · ChromaDB**

---

## 📋 สารบัญ

- [ภาพรวม](#-ภาพรวม)
- [โครงสร้างโปรเจค](#-โครงสร้างโปรเจค)
- [ความต้องการของระบบ](#-ความต้องการของระบบ)
- [การติดตั้ง](#-การติดตั้ง)
- [การตั้งค่า API Key](#-การตั้งค่า-api-key)
- [วิธีใช้งาน](#-วิธีใช้งาน)
- [การทำงานของระบบ](#-การทำงานของระบบ)
- [โมเดลที่ใช้งาน](#-โมเดลที่ใช้งาน)
- [คำอธิบายไฟล์](#-คำอธิบายไฟล์)
- [แก้ปัญหาที่พบบ่อย](#-แก้ปัญหาที่พบบ่อย)
- [Security](#-security)

---

## 🔍 ภาพรวม

โปรเจคนี้สร้างระบบ RAG (Retrieval-Augmented Generation) ที่ให้ AI ตอบคำถามจากเอกสารส่วนตัวของคุณ  
โดยไม่ต้อง fine-tune โมเดล และลด hallucination เพราะ AI จะอิงคำตอบจากเอกสารจริงเสมอ

**ความสามารถหลัก:**

| ความสามารถ | รายละเอียด |
|-----------|-----------|
| 📄 รองรับไฟล์ | `.pdf` และ `.txt` |
| 🔍 ค้นหาแบบ Semantic | ไม่ต้องจำคำเป๊ะๆ — ถามด้วยความหมายก็ได้ |
| 📌 อ้างอิงแหล่งที่มา | บอกได้ว่าคำตอบมาจากไฟล์ไหน หน้าไหน |
| ♻️ Smart Ingestion | ไม่ ingest ไฟล์ซ้ำ — ตรวจด้วย SHA-256 hash |
| 🖥️ CLI ใช้งานง่าย | รองรับทั้ง Interactive mode และ One-shot mode |

---

## 📁 โครงสร้างโปรเจค

```
personal-rag/
│
├── ingest.py                  # สร้างและอัปเดต Vector Database
├── chat.py                    # CLI สำหรับถามคำถาม
│
├── my_documents/              # 📂 วางไฟล์เอกสารที่นี่ (.pdf / .txt)
│   ├── example.pdf
│   └── notes.txt
│
├── vector_db/                 # 🗄️ สร้างอัตโนมัติโดย ingest.py (อย่าแก้ไขมือ)
├── ingested_manifest.json     # 📋 บันทึก SHA-256 ของไฟล์ที่ ingest แล้ว
│
├── .env                       # 🔑 ไฟล์เก็บ API Key (ห้าม commit ขึ้น git)
└── requirements.txt           # 📦 รายชื่อ library ที่ต้องใช้
```

> ⚠️ **สำคัญ:** โฟลเดอร์ `vector_db/` และ `ingested_manifest.json` สร้างขึ้นอัตโนมัติ ห้ามแก้ไขหรือลบด้วยมือ

---

## 💻 ความต้องการของระบบ

| รายการ | เวอร์ชัน / หมายเหตุ |
|--------|-------------------|
| Python | 3.11 ขึ้นไป |
| pip | เวอร์ชันล่าสุด |
| Google Gemini API Key | ได้จาก [Google AI Studio](https://aistudio.google.com/app/apikey) (ฟรี) |
| พื้นที่ดิสก์ | ขึ้นอยู่กับขนาดเอกสาร (vector_db ≈ 2–10× ขนาดต้นฉบับ) |
| การเชื่อมต่ออินเตอร์เน็ต | ต้องใช้สำหรับ Gemini API |

---

## 📦 การติดตั้ง

### 1. Clone หรือดาวน์โหลดโปรเจค

```bash
git clone <your-repo-url>
cd personal-rag
```

### 2. สร้าง Virtual Environment (แนะนำอย่างยิ่ง)

```bash
# สร้าง venv
python -m venv venv

# เปิดใช้งาน — macOS / Linux
source venv/bin/activate

# เปิดใช้งาน — Windows
venv\Scripts\activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

**รายการ library ใน `requirements.txt`:**

```
langchain==0.2.16
langchain-core==0.2.38
langchain-community==0.2.16
langchain-chroma==0.1.4
langchain-google-genai==1.0.10
langchain-text-splitters==0.2.4
chromadb==0.5.3
pypdf==4.3.1
python-dotenv==1.0.1

```


> 💡 ถ้า pip รายงานปัญหา dependency conflict ให้ลอง `pip install -r requirements.txt --upgrade`

---

## 🔑 การตั้งค่า API Key

### 1. ขอ Gemini API Key

1. เปิด [Google AI Studio](https://aistudio.google.com/app/apikey)
2. คลิก **Get API key** → **Create API key**
3. คัดลอก key ที่ได้

### 2. สร้างไฟล์ `.env`

สร้างไฟล์ชื่อ **`.env`** (ขึ้นต้นด้วยจุด) ที่ root ของโปรเจค:

```env
GOOGLE_API_KEY=AIzaSy...คีย์ของคุณ...
```

> ⚠️ เพิ่ม `.env` ลงใน `.gitignore` ทุกครั้ง เพื่อป้องกัน key หลุด

**ตรวจสอบว่าไฟล์ถูกสร้างและอ่านได้:**

```bash
# macOS / Linux
cat .env

# Windows
type .env
```

---

## 🚀 วิธีใช้งาน

### Step 1 — เพิ่มเอกสาร

วางไฟล์ `.pdf` หรือ `.txt` ลงในโฟลเดอร์ `my_documents/`

```bash
cp ~/Downloads/คู่มือ.pdf my_documents/
cp ~/Desktop/notes.txt    my_documents/
```

> ✅ รองรับภาษาไทยในชื่อไฟล์และเนื้อหา  
> ✅ รองรับ encoding: UTF-8, TIS-620 (cp874), CP1252, Latin-1

### Step 2 — สร้าง / อัปเดต Vector Database

```bash
python ingest.py
```

**ผลลัพธ์ที่จะเห็น:**

```
=======================================================
   Personal RAG - Smart Ingestion Pipeline
=======================================================

พบไฟล์ใหม่/แก้ไข 2 ไฟล์:
   + คู่มือ.pdf
   + notes.txt

กำลังอ่านและหั่นเอกสาร...
   คู่มือ.pdf -> 47 chunks
   notes.txt -> 8 chunks

รวมทั้งหมด 55 chunks พร้อม embed

กำลัง Embed และบันทึกลงฐานข้อมูล...
   Batch 1: chunk 1-55

เสร็จสิ้น! บันทึก 2 ไฟล์ลง vector_db/ และอัปเดต manifest แล้ว
=======================================================
```

> ✅ รัน `ingest.py` ซ้ำได้เรื่อยๆ — ไฟล์ที่ไม่มีการเปลี่ยนแปลงจะถูกข้ามอัตโนมัติ  
> ✅ ถ้าแก้ไขไฟล์เดิม ระบบจะตรวจพบการเปลี่ยนแปลงและ ingest ใหม่โดยอัตโนมัติ

### Step 3 — ถามคำถาม

**โหมด Interactive** (แนะนำ — ถามได้หลายคำถามต่อเนื่อง):

```bash
python chat.py
```

```
 คำถาม: วิธีซ่อมมอเตอร์ในคู่มือบอกว่าไง?

 กำลังค้นหาและประมวลผล...

 คำตอบ
───────────────────────────────────────────────────────
  ตามคู่มือ หน้า 23 การซ่อมมอเตอร์ให้ทำตามขั้นตอนดังนี้:
  1. ปิดสวิตช์และรอให้เครื่องเย็น...
───────────────────────────────────────────────────────

 แหล่งอ้างอิง (3 ชิ้น)
  [1] คู่มือ.pdf  หน้า 23
      การซ่อมบำรุงมอเตอร์ควรทำโดยช่างที่ได้รับการอบรม...
```

**โหมด One-shot** (ถามคำถามเดียวแล้วออก):

```bash
python chat.py "สรุปเนื้อหาของไฟล์ notes.txt"
python chat.py "มีข้อกำหนดอะไรในสัญญาบ้าง?"
```

**ออกจากโปรแกรม:** พิมพ์ `exit`, `quit`, หรือกด `Ctrl+C`

---

## ⚙️ การทำงานของระบบ

```
╔══════════════════════════════════════════════════════════════╗
║  Phase 1: Data Ingestion  (python ingest.py)                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [PDF/TXT files]                                             ║
║       │                                                      ║
║       ▼                                                      ║
║  [Hash Check] ─── ไฟล์เคย ingest แล้ว? ──► Skip             ║
║       │ ใหม่/แก้ไข                                           ║
║       ▼                                                      ║
║  [Split Chunks]  chunk_size=1000, overlap=100                ║
║       │                                                      ║
║       ▼                                                      ║
║  [Embed]  models/gemini-embedding-2  (Google)                ║
║       │                                                      ║
║       ▼                                                      ║
║  [ChromaDB]  บันทึกลง vector_db/                             ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Phase 2: Retrieval & Generation  (python chat.py)          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [คำถามของคุณ]                                               ║
║       │                                                      ║
║       ▼                                                      ║
║  [Embed Query]  models/gemini-embedding-2                    ║
║       │                                                      ║
║       ▼                                                      ║
║  [Cosine Similarity Search]  ดึง Top-K=3 chunks              ║
║       │                                                      ║
║       ▼                                                      ║
║  [Prompt + Context]  ส่งให้ LLM พร้อม context               ║
║       │                                                      ║
║       ▼                                                      ║
║  [gemini-2.5-pro]  สร้างคำตอบ + แหล่งอ้างอิง             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**ไฟล์ที่ระบบสร้างขึ้นเอง:**

| ไฟล์/โฟลเดอร์ | สร้างโดย | คำอธิบาย |
|-------------|---------|---------|
| `vector_db/` | `ingest.py` | ChromaDB เก็บ vector embeddings ทั้งหมด |
| `ingested_manifest.json` | `ingest.py` | บันทึก SHA-256 hash ของไฟล์ที่ ingest แล้ว |
| `my_documents/` | `ingest.py` | สร้างโฟลเดอร์ให้ถ้ายังไม่มี |

---

## 🤖 โมเดลที่ใช้งาน

| บทบาท | โมเดล | หมายเหตุ |
|-------|-------|---------|
| Embedding | `models/gemini-embedding-2` | แปลงข้อความเป็น vector (ใช้ทั้ง ingest และ chat) |
| LLM | `gemini-2.5-pro` | สร้างคำตอบจาก context ที่ดึงมา |

> ⚠️ **Critical:** โมเดล Embedding ต้องเป็นชื่อ **เดียวกัน** ทั้งใน `ingest.py` และ `chat.py` เสมอ  
> ถ้าชื่อต่างกัน vector space จะไม่ตรงกัน และระบบจะดึงข้อมูลผิดพลาดโดยไม่มี error แจ้ง

---

## 📄 คำอธิบายไฟล์

### `ingest.py`

| ฟังก์ชัน | หน้าที่ |
|---------|--------|
| `sha256(path)` | คำนวณ hash ของไฟล์เพื่อตรวจว่าเปลี่ยนแปลงหรือไม่ |
| `load_manifest()` | โหลดรายการไฟล์ที่เคย ingest แล้วจาก JSON |
| `save_manifest()` | บันทึก manifest หลัง ingest เสร็จ |
| `scan_new_files()` | เปรียบเทียบ hash — คืนเฉพาะไฟล์ใหม่หรือที่แก้ไข |
| `load_documents()` | โหลด PDF/TXT พร้อม fallback encoding สำหรับภาษาไทย |
| `start_ingesting()` | ฟังก์ชันหลัก — ประสาน pipeline ทั้งหมด |

**ค่าที่ปรับได้ใน `ingest.py`:**

```python
DOCS_PATH = Path("my_documents")   # โฟลเดอร์เอกสาร
DB_PATH   = "vector_db"            # ที่เก็บ ChromaDB
BATCH     = 80                     # จำนวน chunks ต่อ batch (ลดถ้า quota หมดบ่อย)
SLEEP     = 60                     # วินาทีพักระหว่าง batch (เพิ่มถ้าเจอ 429 error)
```

### `chat.py`

| ฟังก์ชัน | หน้าที่ |
|---------|--------|
| `build_chain()` | สร้าง RAG chain — เชื่อมต่อ ChromaDB + Prompt + LLM |
| `ask(chain, query)` | ส่งคำถาม รับคำตอบ และแสดงผล |
| `print_answer(text)` | แสดงคำตอบพร้อมจัดรูปแบบ |
| `print_sources(docs)` | แสดงแหล่งอ้างอิงพร้อม snippet |
| `interactive_mode()` | REPL loop — ถามได้หลายคำถามต่อเนื่อง |
| `one_shot_mode()` | ถามคำถามเดียวจาก command-line argument |

**ค่าที่ปรับได้ใน `chat.py`:**

```python
TOP_K       = 3    # จำนวน chunks ที่ดึงมา (เพิ่มเพื่อความครอบคลุม แต่คำตอบช้าลง)
temperature = 0.3  # ความสร้างสรรค์ (0.0 = ตรงที่สุด · 1.0 = สร้างสรรค์สูงสุด)
```

---

## 🛠️ แก้ปัญหาที่พบบ่อย

### ❌ `ModuleNotFoundError: No module named 'langchain_classic'`

```bash
# langchain_classic ไม่มีอยู่จริง — ติดตั้ง dependencies ให้ครบ
pip install -r requirements.txt
```

---

### ❌ `GOOGLE_API_KEY not set` หรือ `API key not valid`

```bash
# 1. ตรวจว่าไฟล์ .env มีอยู่และชื่อถูกต้อง (ต้องขึ้นต้นด้วยจุด)
ls -la | grep .env       # macOS / Linux
dir /a | findstr .env    # Windows

# 2. ตรวจเนื้อหาในไฟล์ .env
cat .env
# ควรเห็น: GOOGLE_API_KEY=AIza...
```

> ❌ ชื่อไฟล์ผิด: `env`, `_env`, `.env.txt` → ✅ ต้องเป็น `.env` เท่านั้น

---

### ❌ `No module named 'langchain_chroma'` หรือ `chromadb`

```bash
pip install langchain-chroma chromadb langchain-google-genai
```

---

### ❌ `429 Resource Exhausted` (Gemini quota หมด)

ระบบพัก 60 วินาทีระหว่าง batch อัตโนมัติ ถ้ายังเจอ ให้ปรับใน `ingest.py`:

```python
BATCH = 40     # ลด batch size ลงครึ่งหนึ่ง
SLEEP = 120    # เพิ่มเวลาพักเป็น 2 นาที
```

---

### ❌ `vector_db/ not found` ตอนรัน `chat.py`

```bash
# ต้องรัน ingest.py ก่อนเสมอ อย่างน้อย 1 ครั้ง
python ingest.py
```

---

### ❌ ไฟล์ไม่ถูก ingest ทั้งที่เพิ่งเพิ่มเข้ามา

```bash
# ลบ manifest แล้ว ingest ใหม่ทั้งหมด
rm ingested_manifest.json        # macOS / Linux
del ingested_manifest.json       # Windows

python ingest.py
```

---

### ❌ คำตอบผิดพลาดหรือไม่เกี่ยวกับเอกสาร (Silent Wrong Results)

สาเหตุที่พบบ่อยที่สุด: **ชื่อ embedding model ใน `ingest.py` กับ `chat.py` ไม่ตรงกัน**

ตรวจสอบให้ทั้งสองไฟล์ใช้ค่าเดียวกัน:

```python
# ทั้ง ingest.py และ chat.py ต้องเป็นชื่อเดียวกัน
model="models/gemini-embedding-2"
```

ถ้าเคยรัน ingest ด้วย model อื่นมาก่อน ให้ลบ DB และ ingest ใหม่:

```bash
rm -rf vector_db/
rm ingested_manifest.json
python ingest.py
```

---

### ❌ ไฟล์ภาษาไทยอ่านไม่ออก / ข้อความเป็น ???

ระบบรองรับ encoding หลายแบบอัตโนมัติ (UTF-8, TIS-620, CP1252)  
ถ้ายังมีปัญหา ให้แปลงไฟล์เป็น UTF-8 ก่อน:

```bash
# macOS / Linux — ใช้ iconv
iconv -f tis620 -t utf-8 input.txt -o output.txt
```

---

## 🔒 Security

| ประเด็น | รายละเอียด |
|--------|-----------|
| Vector DB | เก็บบนเครื่องคุณเท่านั้น — ไม่มีการส่งขึ้น cloud |
| ข้อมูลที่ส่ง Gemini API | เฉพาะ **chunks ที่ดึงมาตอบ** เท่านั้น ไม่ใช่เอกสารทั้งหมด |
| API Key | เก็บใน `.env` ไม่ถูก hardcode ในโค้ด |
| `.gitignore` | ควรเพิ่ม `.env`, `vector_db/`, `ingested_manifest.json` |

**ตัวอย่าง `.gitignore` ที่แนะนำ:**

```gitignore
.env
vector_db/
ingested_manifest.json
__pycache__/
venv/
*.pyc
```

---

## 📜 License

MIT License — ใช้งานได้เสรี ทั้งส่วนตัวและเชิงพาณิชย์
