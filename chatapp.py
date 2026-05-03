import customtkinter as ctk
import threading
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tkinter import filedialog
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ตั้งค่าธีม
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AIBOApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AIBO - Enterprise Desktop Assistant")
        self.geometry("950x700")
        
        self.docs_path = Path("my_documents")
        self.docs_path.mkdir(exist_ok=True)
        self.api_key = ""

        # สร้าง Frame หลัก 2 หน้าต่าง (ซ้อนทับกันอยู่)
        self.setup_frame = ctk.CTkFrame(self)
        self.main_frame = ctk.CTkFrame(self)

        # โหลดไฟล์ .env ถ้ามีอยู่แล้ว
        load_dotenv()
        existing_key = os.getenv("GOOGLE_API_KEY")

        if existing_key:
            self.api_key = existing_key
            self.show_main_ui() # ถ้ามีคีย์อยู่แล้ว ข้ามไปหน้าแชทเลย
        else:
            self.show_setup_ui() # ถ้าไม่มีคีย์ ให้แสดงหน้ากรอกคีย์

    # ================= 1. หน้าต่างตั้งค่า API Key =================
    def show_setup_ui(self):
        self.main_frame.pack_forget() # ซ่อนหน้าแชท
        self.setup_frame.pack(fill="both", expand=True) # แสดงหน้าตั้งค่า

        # กล่องตรงกลางหน้าจอ
        container = ctk.CTkFrame(self.setup_frame, fg_color="#2b2b2b", corner_radius=15)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(container, text="ยินดีต้อนรับสู่ AIBO", font=("Prompt", 24, "bold")).pack(pady=(30, 10))
        ctk.CTkLabel(container, text="กรุณาใส่ Google Gemini API Key เพื่อเริ่มต้นใช้งาน", font=("Prompt", 14), text_color="gray").pack(pady=(0, 20), padx=40)

        # สร้าง Frame เล็กๆ จัดกลุ่มช่องพิมพ์ + ปุ่มวาง (Paste)
        entry_frame = ctk.CTkFrame(container, fg_color="transparent")
        entry_frame.pack(pady=10)

        self.key_entry = ctk.CTkEntry(entry_frame, width=300, height=40, show="*", placeholder_text="AIzaSy...")
        self.key_entry.grid(row=0, column=0, padx=(0, 5))

        paste_btn = ctk.CTkButton(entry_frame, text="📋 วาง", width=60, height=40, fg_color="#7f8c8d", hover_color="#95a5a6", command=self.paste_key)
        paste_btn.grid(row=0, column=1)

        # ป้ายสถานะสำหรับแจ้งเตือน
        self.setup_status = ctk.CTkLabel(container, text="", font=("Prompt", 12))
        self.setup_status.pack()

        # ปุ่มตกลง
        self.submit_btn = ctk.CTkButton(container, text="ตรวจสอบและเข้าสู่ระบบ", height=40, font=("Prompt", 14), command=self.verify_and_save_key)
        self.submit_btn.pack(pady=(10, 30))

    def paste_key(self):
        try:
            # ดึงข้อมูลจาก Clipboard ในเครื่องมาวาง แก้ปัญหา Ctrl+V ไม่ติดตอนพิมพ์ภาษาไทย
            clipboard_data = self.clipboard_get()
            self.key_entry.delete(0, "end") 
            self.key_entry.insert(0, clipboard_data) 
        except Exception:
            pass

    def verify_and_save_key(self):
        user_key = self.key_entry.get().strip()
        if not user_key:
            self.setup_status.configure(text="❌ กรุณากรอก API Key", text_color="#e74c3c")
            return

        self.setup_status.configure(text="⏳ กำลังตรวจสอบการเชื่อมต่อกับ Google...", text_color="#f1c40f")
        self.submit_btn.configure(state="disabled")

        # แยกการตรวจสอบไปรันอีก Thread เพื่อไม่ให้หน้าต่างค้าง
        threading.Thread(target=self._test_api_thread, args=(user_key,), daemon=True).start()

    def _test_api_thread(self, key):
        try:
            # ยิง API ทดสอบสั้นๆ ว่า Key ใช้ได้จริงไหม
            test_llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", api_key=key)
            test_llm.invoke("Hi") 

            # ทำการสร้างหรือเขียนทับไฟล์ .env
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"GOOGLE_API_KEY={key}\n")
            
            self.api_key = key
            
            # เปลี่ยนไปหน้าต่างแชท
            self.after(0, self.show_main_ui)
        except Exception:
            self.after(0, lambda: self.setup_status.configure(text="❌ API Key ไม่ถูกต้อง หรือเชื่อมต่อไม่ได้", text_color="#e74c3c"))
            self.after(0, lambda: self.submit_btn.configure(state="normal"))

    # ================= 2. หน้าต่างแชทหลัก =================
    def show_main_ui(self):
        self.setup_frame.pack_forget() # ซ่อนหน้าตั้งค่า
        self.main_frame.pack(fill="both", expand=True) # แสดงหน้าแชท

        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # ---------- Sidebar ----------
        self.sidebar = ctk.CTkFrame(self.main_frame, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        
        ctk.CTkLabel(self.sidebar, text="AIBO Desktop", font=("Prompt", 22, "bold")).pack(padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(self.sidebar, text="🟢 พร้อมใช้งาน", text_color="#2ecc71", font=("Prompt", 14))
        self.status_label.pack(padx=20, pady=5)

        self.add_file_btn = ctk.CTkButton(self.sidebar, text="📂 เพิ่มไฟล์เอกสาร", command=self.add_file, fg_color="#2980b9")
        self.add_file_btn.pack(padx=20, pady=10)

        self.clear_btn = ctk.CTkButton(self.sidebar, text="🗑️ ล้างประวัติแชท", command=self.clear_chat, fg_color="#c0392b", hover_color="#e74c3c")
        self.clear_btn.pack(padx=20, pady=10)

        # ปุ่มสำหรับสลับกลับไปเปลี่ยน API Key
        self.reset_key_btn = ctk.CTkButton(self.sidebar, text="⚙️ เปลี่ยน API Key", command=self.show_setup_ui, fg_color="#7f8c8d", hover_color="#95a5a6")
        self.reset_key_btn.pack(padx=20, pady=(40, 10))

        # ---------- Chat Window ----------
        self.chat_display = ctk.CTkTextbox(self.main_frame, state="disabled", font=("Prompt", 15), wrap="word")
        self.chat_display.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="nsew")

        # ---------- Input Area ----------
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=20, pady=20, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="สอบถามข้อมูลจากเอกสาร...", height=40, font=("Prompt", 14))
        self.entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_frame, text="ส่งข้อความ", width=100, height=40, font=("Prompt", 14), command=self.send_message)
        self.send_btn.grid(row=0, column=1)

        # โหลดโมเดล
        self.chain = self.get_safe_chain()
        self.clear_chat() # เคลียร์จอเพื่อต้อนรับ
        
        if self.chain is None:
            self.append_chat("System", "⚠️ ยังไม่มีฐานข้อมูล กรุณากดปุ่ม '📂 เพิ่มไฟล์เอกสาร' ทางซ้ายมือ เพื่อให้ระบบเริ่มเรียนรู้ครับ")
        else:
            self.append_chat("AIBO", "สวัสดีครับ! เชื่อมต่อ API สำเร็จและอ่านเอกสารเรียบร้อยแล้ว มีอะไรให้ผมช่วยไหมครับ?")

    # ================= ฟังก์ชันโหลด Chain =================
    def get_safe_chain(self):
        if not Path("vector_db").exists():
            return None
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", api_key=self.api_key)
            llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3, api_key=self.api_key)
            vector_db = Chroma(persist_directory="vector_db", embedding_function=embeddings)
            
            # System Prompt เริ่มต้น
            prompt = ChatPromptTemplate.from_template("""
            ตอบคำถามจาก Context เท่านั้น เน้นความกระชับ ถูกต้อง
            ถ้าไม่มีในเอกสารให้บอกว่า "ไม่พบข้อมูลในเอกสารครับ"
            
            Context: {context}
            คำถาม: {input}
            คำตอบ:""")
            
            combine_chain = create_stuff_documents_chain(llm, prompt)
            return create_retrieval_chain(vector_db.as_retriever(search_kwargs={"k": 3}), combine_chain)
        except Exception:
            return None

    # ================= ฟังก์ชันเพิ่มไฟล์ =================
    def add_file(self):
        file_paths = filedialog.askopenfilenames(
            title="เลือกไฟล์เอกสาร", filetypes=[("PDF and Text Files", "*.pdf *.txt")]
        )
        if not file_paths: return

        self.status_label.configure(text="⏳ กำลังคัดลอกไฟล์...", text_color="#f1c40f")
        self.update_idletasks()

        for path in file_paths:
            shutil.copy(path, self.docs_path)

        self.status_label.configure(text="🧠 AI กำลังเรียนรู้...", text_color="#e67e22")
        self.append_chat("System", f"กำลังนำเข้าเอกสาร {len(file_paths)} ไฟล์... โปรดรอสักครู่")
        
        threading.Thread(target=self.run_ingestion, daemon=True).start()

    def run_ingestion(self):
        try:
            # รันสคริปต์ ingest.py ใน Background
            subprocess.run([sys.executable, "ingest.py"], check=True)
            self.chain = self.get_safe_chain()
            self.after(0, lambda: self.status_label.configure(text="🟢 พร้อมใช้งาน", text_color="#2ecc71"))
            self.after(0, lambda: self.append_chat("System", "✅ นำเข้าข้อมูลและอัปเดตฐานความรู้เสร็จสิ้น! ลองถามคำถามได้เลยครับ"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text="🔴 เกิดข้อผิดพลาด", text_color="#e74c3c"))
            self.after(0, lambda: self.append_chat("System", f"❌ Error: {str(e)}"))

    # ================= ระบบแชท =================
    def append_chat(self, role, message):
        self.chat_display.configure(state="normal")
        if role == "You":
            self.chat_display.insert("end", f"🧑‍💻 คุณ:\n{message}\n\n")
        elif role == "System":
            self.chat_display.insert("end", f"⚙️ {message}\n\n")
        else:
            self.chat_display.insert("end", f"🤖 AIBO:\n{message}\n\n{'─'*40}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_query = self.entry.get()
        if not user_query: return
        
        if self.chain is None:
            self.append_chat("System", "กรุณาเพิ่มไฟล์เอกสารก่อนเริ่มใช้งานครับ")
            return

        self.append_chat("You", user_query)
        self.entry.delete(0, "end")
        
        self.status_label.configure(text="💬 กำลังคิดคำตอบ...", text_color="#3498db")
        threading.Thread(target=self.process_ai, args=(user_query,), daemon=True).start()

    def process_ai(self, query):
        try:
            result = self.chain.invoke({"input": query})
            answer = result["answer"]
            self.after(0, lambda: self.append_chat("AIBO", answer))
            self.after(0, lambda: self.status_label.configure(text="🟢 พร้อมใช้งาน", text_color="#2ecc71"))
        except Exception as e:
            self.after(0, lambda: self.append_chat("System", f"Error: {str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="🔴 เชื่อมต่อ API ล้มเหลว", text_color="#e74c3c"))

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")

if __name__ == "__main__":
    app = AIBOApp()
    app.mainloop()