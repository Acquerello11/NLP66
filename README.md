# AIBO: Personal RAG Desktop Assistant

**AIBO** คือระบบผู้ช่วยส่วนตัวอัจฉริยะแบบ Desktop Application ที่ใช้สถาปัตยกรรม Retrieval-Augmented Generation (RAG) แบบกึ่งโลคอล (Hybrid Cloud-Local) เพื่ออ่านและตอบคำถามจากเอกสาร PDF และ TXT ของคุณ โดยใช้ **Google Gemini API** ในการวิเคราะห์ และ **FAISS** ในการจัดเก็บฐานข้อมูลเวกเตอร์ไว้ในเครื่องเพื่อความปลอดภัยของข้อมูลสูงสุด

---

## 🏗️ System Workflow (Architecture Flowchart)
แผนผังการทำงานของระบบ (System Architecture) ตั้งแต่การนำเข้าไฟล์ไปจนถึงการตอบคำถาม


```mermaid
graph TD
    %% User Actions
    User((🧑‍🎓 ผู้ใช้งาน))
    
    %% GUI & Core
    subgraph "AIBO Desktop App (Local)"
        UI[💻 CustomTkinter GUI]
        Ingest[📂 Data Ingestion]
        VectorDB[(🧠 FAISS Vector DB)]
    end
    
    %% Cloud API
    subgraph "Google Cloud (API)"
        Embed[🔢 Gemini Embedding 2]
        LLM[🤖 Gemini 2.5 Flash]
    end

    %% Flow: Upload Document
    User -->|1. อัปโหลด PDF/TXT| UI
    UI -->|2. ส่งไฟล์เข้าสู่ระบบ| Ingest
    Ingest -->|3. แบ่งข้อความ (Chunking)| Embed
    Embed -->|4. แปลงข้อความเป็นเวกเตอร์| VectorDB

    %% Flow: Ask Question
    User -->|5. พิมพ์คำถาม| UI
    UI -->|6. ค้นหาข้อมูลที่เกี่ยวข้อง| VectorDB
    VectorDB -->|7. ส่งบริบท (Context) ที่เจอ| LLM
    LLM -->|8. สังเคราะห์คำตอบ| UI
    UI -->|9. แสดงคำตอบให้ผู้ใช้| User

```

---

## 📋 ข้อกำหนดเบื้องต้น (Prerequisites)

ก่อนเริ่มต้นใช้งาน กรุณาตรวจสอบให้แน่ใจว่าเครื่องคอมพิวเตอร์ของคุณมีโปรแกรมดังต่อไปนี้:

* **Python 3.12** (สามารถดาวน์โหลดได้ที่ [python.org](https://www.python.org/downloads/))
* *สำคัญมากตอนติดตั้ง Python:* อย่าลืมติ๊กถูกที่ช่อง **"Add Python.exe to PATH"** ด้วย



---

## 🚀 วิธีการติดตั้ง (Installation Setup)

ทำตามขั้นตอนเหล่านี้เพียง **ครั้งแรกครั้งเดียว** เพื่อตั้งค่าโปรเจกต์:

1. **เปิด Terminal (หรือ Command Prompt)** และเข้าไปยังโฟลเดอร์โปรเจกต์ของคุณ
2. **สร้าง Virtual Environment (.venv)**
เพื่อป้องกันไม่ให้ไลบรารีไปตีกับโปรเจกต์อื่น พิมพ์คำสั่ง:
```bash
python -m venv .venv

```


3. **เปิดใช้งาน (Activate) Virtual Environment**
* สำหรับ **Windows**:
```bash
.\\.venv\\Scripts\\activate

```


* สำหรับ **macOS / Linux**:
```bash
source .venv/bin/activate

```



*(เมื่อเปิดสำเร็จ จะมีคำว่า `(.venv)` ปรากฏอยู่หน้าบรรทัดคำสั่ง)*
4. **ติดตั้ง Libraries ที่จำเป็น**
```bash
pip install -r requirements.txt

```



---

## 💡 วิธีการเปิดใช้งานแอปพลิเคชัน (Usage)


1. **เปิดใช้งาน .venv ก่อนเสมอ:**
```bash
.\\.venv\\Scripts\\activate

```


2. **รันตัวโปรแกรม AIBO:**
```bash
python app.py

```


3. **หน้าจอแอปพลิเคชันจะเปิดขึ้นมา**
* นำ **Google Gemini API Key** มาใส่และกดยืนยัน (รับคีย์ฟรีได้ที่ Google AI Studio)
* กดปุ่ม **นำเข้าเอกสารใหม่** เพื่อให้ระบบอ่านไฟล์
* เริ่มต้นพิมพ์ถามคำถามจากเอกสารได้ทันที!



---

## 📁 โครงสร้างโฟลเดอร์ (Project Structure)

```text
AIBO_Project/
│
├── .venv/                   # โฟลเดอร์จำลองสภาพแวดล้อม Python (ติดตั้งไลบรารีไว้ที่นี่)
├── my_documents/            # โฟลเดอร์เก็บไฟล์ PDF และ TXT ต้นฉบับ (ระบบสร้างอัตโนมัติ)
├── vector_db/               # โฟลเดอร์เก็บฐานข้อมูลเวกเตอร์ FAISS (ระบบสร้างอัตโนมัติ)
├── .env                     # ไฟล์เก็บ API Key (ระบบสร้างให้อัตโนมัติเมื่อ Log-in สำเร็จ)
├── ingested_manifest.json   # ไฟล์ประวัติการอ่านเอกสาร ป้องกันการอ่านซ้ำ
├── requirements.txt         # รายชื่อไลบรารีที่จำเป็นต้องใช้
└── app.py                   # โค้ดหลักของโปรแกรม (รันไฟล์นี้)

```

"""
