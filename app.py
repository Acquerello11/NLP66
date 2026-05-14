import customtkinter as ctk
import threading
import os
import shutil
import sys
import time
import json
import hashlib
import webbrowser
from pathlib import Path
from tkinter import filedialog
from dotenv import load_dotenv

# นำเข้า Library ทั้งหมดที่ใช้ (รวมของ ingest และ chat)
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import langchain_text_splitters
import langchain_community.vectorstores
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.schema import HumanMessage

# ──────────────────────────────────────────────
# 1. ส่วนตั้งค่าและการจัดการข้อมูล (Ingest Logic)
# ──────────────────────────────────────────────
DOCS_PATH = Path("my_documents")
DB_PATH   = "vector_db"
MANIFEST  = Path("ingested_manifest.json")
BATCH     = 80      # จำนวน chunk ต่อ batch
SLEEP     = 60      # วินาทีที่รอระหว่าง batch เพื่อกัน API Limit
SUPPORTED = {".pdf": PyPDFLoader, ".txt": TextLoader}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_manifest() -> dict:
    if MANIFEST.exists():
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: dict):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def scan_new_files(manifest: dict) -> list[Path]:
    new_files = []
    for ext in SUPPORTED:
        for path in sorted(DOCS_PATH.glob(f"*{ext}")):
            key = str(path)
            h   = sha256(path)
            if manifest.get(key) != h:
                new_files.append(path)
    return new_files

def load_documents(path: Path):
    loader_cls = SUPPORTED[path.suffix.lower()]
    try:
        return loader_cls(str(path)).load()
    except Exception as e:
        if path.suffix.lower() == ".txt":
            try:
                with open(path, "rb") as f:
                    raw = f.read()
                text = None
                for enc in ("utf-8", "utf-8-sig", "cp874", "cp1252", "latin-1"):
                    try:
                        text = raw.decode(enc)
                        break
                    except Exception:
                        text = None
                if text is None:
                    text = raw.decode("utf-8", errors="replace")
                return [Document(page_content=text, metadata={"source": str(path)})]
            except Exception:
                raise
        raise

def start_ingesting(api_key: str):
    """ฟังก์ชันหลักในการประมวลผลไฟล์ (ถูกเรียกใช้แบบเบื้องหลัง)"""
    DOCS_PATH.mkdir(exist_ok=True)
    manifest  = load_manifest()
    new_files = scan_new_files(manifest)

    if not new_files:
        return # ไม่มีไฟล์ใหม่ ให้ข้ามไปเลย

    all_chunks     = []
    splitter = langchain_text_splitters.RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    for path in new_files:
        docs   = load_documents(path)
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)

    # ใช้โมเดล Embedding เวอร์ชัน 2 ตามที่คุณต้องการ
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key,
    )

    vector_db = None
    if Path(DB_PATH).exists():
        try:
            vector_db = langchain_community.vectorstores.FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        except Exception:
            vector_db = None

    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        if vector_db is None:
            vector_db = langchain_community.vectorstores.FAISS.from_documents(batch, embeddings)
        else:
            vector_db.add_documents(batch)
        if i + BATCH < len(all_chunks):
            time.sleep(SLEEP)

    if vector_db is not None:
        Path(DB_PATH).mkdir(parents=True, exist_ok=True)
        vector_db.save_local(DB_PATH)

    for path in new_files:
        manifest[str(path)] = sha256(path)
    save_manifest(manifest)

# ──────────────────────────────────────────────
# 2. ส่วนของหน้าจอโปรแกรม (GUI & App Logic)
# ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONT_TITLE = ("Arial", 20, "bold")
FONT_NORMAL = ("Arial", 14)
FONT_SMALL = ("Arial", 12)

class AIBOApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AIBO - Document Assistant")
        self.geometry("1000x700")
        
        self.docs_path = DOCS_PATH
        self.docs_path.mkdir(exist_ok=True)
        self.api_key = ""

        self.setup_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")

        Path('.env').touch(exist_ok=True)
        load_dotenv()
        existing_key = os.getenv("GOOGLE_API_KEY")

        if existing_key:
            self.api_key = existing_key
            self.show_main_ui() 
        else:
            self.show_setup_ui() 

    def show_setup_ui(self):
        self.main_frame.pack_forget() 
        self.setup_frame.pack(fill="both", expand=True) 

        container = ctk.CTkFrame(self.setup_frame, fg_color="#212121", corner_radius=8)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(container, text="ระบบผู้ช่วยจัดการเอกสาร", font=FONT_TITLE).pack(pady=(40, 10))
        ctk.CTkLabel(container, text="กรุณาระบุ Google Gemini API Key เพื่อเริ่มการทำงาน", font=FONT_NORMAL, text_color="#aaaaaa").pack(pady=(0, 10), padx=50)

        link_label = ctk.CTkLabel(container, text="คลิกที่นี่เพื่อขอรับ API Key ฟรีจาก Google AI Studio", 
                                  font=FONT_SMALL, text_color="#4da6ff", cursor="hand2")
        link_label.pack(pady=(0, 20))
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        entry_frame = ctk.CTkFrame(container, fg_color="transparent")
        entry_frame.pack(pady=10)

        self.key_entry = ctk.CTkEntry(entry_frame, width=320, height=40, show="*", placeholder_text="ระบุ API Key ของคุณที่นี่...", font=FONT_NORMAL)
        self.key_entry.grid(row=0, column=0, padx=(0, 10))

        paste_btn = ctk.CTkButton(entry_frame, text="วางข้อมูล", width=80, height=40, font=FONT_NORMAL, 
                                  fg_color="#424242", hover_color="#616161", command=self.paste_key)
        paste_btn.grid(row=0, column=1)

        self.setup_status = ctk.CTkLabel(container, text="", font=FONT_SMALL)
        self.setup_status.pack(pady=(10, 0))

        self.submit_btn = ctk.CTkButton(container, text="เข้าสู่ระบบ", height=40, width=200, font=FONT_NORMAL, command=self.verify_and_save_key)
        self.submit_btn.pack(pady=(10, 15))

        if self.api_key != "":
            self.cancel_btn = ctk.CTkButton(container, text="ยกเลิกการเปลี่ยนแปลง", height=40, width=200, 
                                            fg_color="transparent", border_width=1, text_color="#aaaaaa", font=FONT_NORMAL, command=self.show_main_ui)
            self.cancel_btn.pack(pady=(0, 40))
        else:
            self.submit_btn.pack_configure(pady=(10, 40))

    def paste_key(self):
        try:
            clipboard_data = self.clipboard_get()
            self.key_entry.delete(0, "end") 
            self.key_entry.insert(0, clipboard_data) 
        except Exception:
            pass

    def verify_and_save_key(self):
        user_key = self.key_entry.get().strip()
        if not user_key:
            self.setup_status.configure(text="กรุณาระบุข้อมูลให้ครบถ้วน", text_color="#ff5252")
            return
        
        self.submit_btn.configure(state="disabled", text="กำลังตรวจสอบ...")
        self.setup_status.configure(text="กำลังตรวจสอบการเชื่อมต่อระบบ...", text_color="#ffb74d")
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(state="disabled")

        threading.Thread(target=self._test_api_thread, args=(user_key,), daemon=True).start()

    def _test_api_thread(self, key):
        try:
            # กลับไปใช้ Gemini 2.5 Flash และ Embedding 2 ตามต้องการ
            test_llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", google_api_key=key)
            test_llm.invoke([HumanMessage(content="Hi")])

            test_emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=key)
            test_emb.embed_query("Test")

            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GOOGLE_API_KEY={key}\n")
            
            self.api_key = key
            self.after(0, lambda: self.setup_status.configure(text=""))
            self.after(0, self.show_main_ui)

        except Exception as e:
            error_msg = str(e).lower()
            if "api key not valid" in error_msg or "invalid argument" in error_msg or "unauthorized" in error_msg:
                display_text = "API Key ไม่ถูกต้อง โปรดตรวจสอบอีกครั้ง"
            elif "quota" in error_msg or "429" in error_msg:
                display_text = "API Key นี้ใช้งานเกินโควต้า (Quota Exceeded)"
            elif "network" in error_msg or "connection" in error_msg:
                display_text = "ไม่สามารถเชื่อมต่ออินเทอร์เน็ตได้"
            else:
                display_text = f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {str(e)}"

            self.after(0, lambda: self.setup_status.configure(text=display_text, text_color="#ff5252"))
            
        finally:
            self.after(0, lambda: self.submit_btn.configure(state="normal", text="เข้าสู่ระบบ"))
            if hasattr(self, 'cancel_btn'):
                self.after(0, lambda: self.cancel_btn.configure(state="normal"))

    def show_main_ui(self):
        self.setup_frame.pack_forget() 
        self.main_frame.pack(fill="both", expand=True) 

        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self.main_frame, width=240, corner_radius=0, fg_color="#1e1e1e")
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="● ระบบพร้อมทำงาน", text_color="#4caf50", font=FONT_SMALL)
        self.status_label.pack(padx=20, pady=(30, 20), anchor="w")

        self.add_file_btn = ctk.CTkButton(self.sidebar, text="นำเข้าเอกสารใหม่", command=self.add_file, 
                                          font=FONT_NORMAL, fg_color="#333333", hover_color="#424242", anchor="w", height=40)
        self.add_file_btn.pack(padx=20, pady=5, fill="x")

        self.clear_btn = ctk.CTkButton(self.sidebar, text="ล้างประวัติการสนทนา", command=self.clear_chat, 
                                       font=FONT_NORMAL, fg_color="#333333", hover_color="#424242", anchor="w", height=40)
        self.clear_btn.pack(padx=20, pady=5, fill="x")

        self.reset_key_btn = ctk.CTkButton(self.sidebar, text="ตั้งค่า API Key", command=self.show_setup_ui, 
                                           font=FONT_NORMAL, fg_color="transparent", border_width=1, anchor="w", height=40)
        self.reset_key_btn.pack(padx=20, pady=(30, 10), fill="x")

        self.chat_display = ctk.CTkTextbox(self.main_frame, state="disabled", font=FONT_NORMAL, wrap="word", fg_color="#121212")
        self.chat_display.grid(row=0, column=1, padx=30, pady=(30, 0), sticky="nsew")

        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=30, pady=20, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="พิมพ์ข้อซักถามจากเอกสารที่นี่...", height=45, font=FONT_NORMAL, corner_radius=20)
        self.entry.grid(row=0, column=0, padx=(0, 15), sticky="ew")
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_frame, text="ส่ง", width=90, height=45, font=FONT_NORMAL, corner_radius=20, command=self.send_message)
        self.send_btn.grid(row=0, column=1)

        self.chain = self.get_safe_chain()
        self.clear_chat() 
        
        if self.chain is None:
            self.append_chat("System", "ระบบยังไม่พบฐานข้อมูล กรุณาใช้เมนู 'นำเข้าเอกสารใหม่' เพื่อเตรียมความพร้อมของระบบ")
        else:
            self.append_chat("AIBO", "สวัสดีครับ ระบบอ่านเอกสารเรียบร้อยแล้ว มีข้อมูลส่วนใดให้ผมช่วยสรุปหรืออธิบายเพิ่มเติมไหมครับ?")

    def get_safe_chain(self):
        if not Path(DB_PATH).exists():
            return None
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=self.api_key)
            llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3, google_api_key=self.api_key)
            vector_db = langchain_community.vectorstores.FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
            
            prompt = ChatPromptTemplate.from_template("""
            คุณคือผู้ช่วยปัญญาประดิษฐ์ระดับองค์กรที่มีความเชี่ยวชาญด้านการวิเคราะห์เอกสาร
            หน้าที่ของคุณคือการตอบคำถามโดยอ้างอิงจากข้อมูลใน Context ด้านล่างนี้เท่านั้น
            ให้ใช้ภาษาที่สุภาพ เป็นทางการ ชัดเจน และตรงไปตรงมา
            หากข้อมูลใน Context ไม่เพียงพอในการตอบคำถาม ให้ตอบตามความเป็นจริงว่า "ไม่พบข้อมูลที่ตรงกับคำถามในเอกสารอ้างอิงครับ" ห้ามคาดเดาหรือแต่งเติมข้อมูลเองเด็ดขาด
            
            Context: {context}
            คำถาม: {input}
            คำตอบ:""")
            
            combine_chain = create_stuff_documents_chain(llm, prompt)
            return create_retrieval_chain(vector_db.as_retriever(search_kwargs={"k": 3}), combine_chain)
        except Exception:
            return None

    def add_file(self):
        file_paths = filedialog.askopenfilenames(
            title="เลือกไฟล์เอกสาร", filetypes=[("PDF and Text Files", "*.pdf *.txt")]
        )
        if not file_paths: return

        self.docs_path.mkdir(parents=True, exist_ok=True)
        self.status_label.configure(text="● กำลังคัดลอกไฟล์...", text_color="#ffb74d")
        self.update_idletasks()

        for path in file_paths:
            shutil.copy(path, self.docs_path)

        self.status_label.configure(text="● กำลังประมวลผลข้อมูล...", text_color="#2196f3")
        self.append_chat("System", f"กำลังดำเนินการนำเข้าเอกสารจำนวน {len(file_paths)} ไฟล์ โปรดรอสักครู่")
        
        threading.Thread(target=self.run_ingestion, daemon=True).start()

    def run_ingestion(self):
        try:
            start_ingesting(self.api_key) 
            self.chain = self.get_safe_chain()
            self.after(0, lambda: self.status_label.configure(text="● ระบบพร้อมทำงาน", text_color="#4caf50"))
            self.after(0, lambda: self.append_chat("System", "กระบวนการนำเข้าเอกสารเสร็จสมบูรณ์ สามารถเริ่มใช้งานได้ทันที"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text="● พบข้อผิดพลาด", text_color="#ff5252"))
            self.after(0, lambda: self.append_chat("System", f"เกิดข้อผิดพลาด: {str(e)}"))

    def append_chat(self, role, message):
        self.chat_display.configure(state="normal")
        if role == "You":
            self.chat_display.insert("end", f"ผู้ใช้งาน:\n{message}\n\n")
        elif role == "System":
            self.chat_display.insert("end", f"[{message}]\n\n")
        else:
            self.chat_display.insert("end", f"{role}:\n{message}\n\n{'—'*40}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_query = self.entry.get()
        if not user_query: return
        if self.chain is None:
            self.append_chat("System", "โปรดนำเข้าไฟล์เอกสารก่อนเริ่มต้นใช้งาน")
            return

        self.append_chat("You", user_query)
        self.entry.delete(0, "end")
        self.status_label.configure(text="● กำลังสร้างคำตอบ...", text_color="#2196f3")
        threading.Thread(target=self.process_ai, args=(user_query,), daemon=True).start()

    def process_ai(self, query):
        try:
            result = self.chain.invoke({"input": query})
            answer = result["answer"]
            self.after(0, lambda: self.append_chat("AIBO", answer))
            self.after(0, lambda: self.status_label.configure(text="● ระบบพร้อมทำงาน", text_color="#4caf50"))
        except Exception as e:
            self.after(0, lambda: self.append_chat("System", f"ข้อผิดพลาดจากระบบ: {str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="● ปัญหาการเชื่อมต่อ", text_color="#ff5252"))

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")

if __name__ == "__main__":
    app = AIBOApp()
    app.mainloop()