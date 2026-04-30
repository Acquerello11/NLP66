import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
WATCH_PATH = "my_documents"  # โฟลเดอร์ที่ต้องการเฝ้าดู
INGEST_SCRIPT = "ingest.py"   # ไฟล์ที่จะสั่งรัน
EXTENSIONS = {".pdf", ".txt"} # นามสกุลไฟล์ที่สนใจ

class IngestHandler(FileSystemEventHandler):
    """จัดการเหตุการณ์เมื่อมีการเปลี่ยนแปลงในโฟลเดอร์"""
    
    def on_created(self, event):
        if not event.is_directory and Path(event.src_path).suffix.lower() in EXTENSIONS:
            print(f"\n[DETECTED] พบไฟล์ใหม่: {Path(event.src_path).name}")
            self.run_ingest()

    def on_modified(self, event):
        # บางครั้งการแก้ไขไฟล์เดิมก็ต้องการ Re-ingest
        if not event.is_directory and Path(event.src_path).suffix.lower() in EXTENSIONS:
            print(f"\n[DETECTED] ไฟล์ถูกแก้ไข: {Path(event.src_path).name}")
            self.run_ingest()

    def run_ingest(self):
        print(f"--- กำลังรัน {INGEST_SCRIPT} อัตโนมัติ ---")
        try:
            # รันสคริปต์ ingest.py ผ่าน subprocess
            subprocess.run([sys.executable, INGEST_SCRIPT], check=True)
            print("--- อัปเดตฐานข้อมูลสำเร็จ! ---")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะรัน ingest: {e}")

if __name__ == "__main__":
    # ตรวจสอบว่ามีโฟลเดอร์หรือยัง
    Path(WATCH_PATH).mkdir(exist_ok=True)
    
    event_handler = IngestHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    
    print(f"👀 กำลังเฝ้าดูโฟลเดอร์ '{WATCH_PATH}'...")
    print("ระบบจะรัน ingest.py ทันทีที่คุณเพิ่มหรือแก้ไขไฟล์ PDF/TXT")
    print("กด Ctrl+C เพื่อหยุดการทำงาน")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nหยุดการเฝ้าดูแล้ว ลาก่อนครับ!")
    observer.join()