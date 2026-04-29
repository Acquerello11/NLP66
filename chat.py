import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
load_dotenv()
os.environ["CHROMA_TELEMETRY_NOOP"] = "True"
API_KEY = os.getenv("GOOGLE_API_KEY")
DB_PATH = "vector_db"
TOP_K   = 2

# ──────────────────────────────────────────────
# COLORS
# ──────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    RED    = "\033[91m"
    WHITE  = "\033[97m"

def banner():
    print(f"""
{C.CYAN}{C.BOLD}
  ██████╗  █████╗  ██████╗      █████╗ ██╗
  ██╔══██╗██╔══██╗██╔════╝     ██╔══██╗██║
  ██████╔╝███████║██║  ███╗    ███████║██║
  ██╔══██╗██╔══██║██║   ██║    ██╔══██║██║
  ██║  ██║██║  ██║╚██████╔╝    ██║  ██║██║
  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝     ╚═╝  ╚═╝╚═╝
{C.RESET}{C.DIM}  Personal Document Assistant · Powered by Gemini + ChromaDB{C.RESET}
""")

def separator(char="─", n=55, color=C.DIM):
    print(f"{color}{char * n}{C.RESET}")

def print_answer(text: str):
    print(f"\n{C.GREEN}{C.BOLD} คำตอบ{C.RESET}")
    separator()
    for para in text.strip().split("\n"):
        print(f"  {para}")
    separator()

def print_sources(docs: list):
    if not docs:
        return
    print(f"\n{C.YELLOW}{C.BOLD} แหล่งอ้างอิง ({len(docs)} ชิ้น){C.RESET}")
    seen = set()
    for i, doc in enumerate(docs, 1):
        src   = doc.metadata.get("source", "ไม่ทราบแหล่งที่มา")
        fname = Path(src).name
        page  = doc.metadata.get("page", "")
        page_str = f"  หน้า {int(page)+1}" if page != "" else ""

        if fname not in seen:
            seen.add(fname)
            print(f"  {C.BLUE}[{i}]{C.RESET} {C.WHITE}{fname}{C.RESET}{C.DIM}{page_str}{C.RESET}")

        snippet = doc.page_content[:120].replace("\n", " ").strip()
        print(f"      {C.DIM}{snippet}...{C.RESET}")

# ──────────────────────────────────────────────
# RAG CHAIN
# ──────────────────────────────────────────────
def build_chain():
    if not Path(DB_PATH).exists():
        print(f"{C.RED} ยังไม่มีฐานข้อมูล '{DB_PATH}/' — รัน python ingest.py ก่อนนะครับ{C.RESET}")
        sys.exit(1)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        api_key=API_KEY,
    )
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.0-flash", 
        temperature=0.3,
        api_key=API_KEY,
    )

    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

    prompt = ChatPromptTemplate.from_template("""
ตอบคำถามจาก Context เท่านั้น 
เน้นความกระชับที่สุด (ไม่เกิน 2-3 ประโยค) 
ถ้าไม่มีในเอกสารให้บอกว่า "ไม่พบข้อมูล"

Context: {context}
คำถาม: {input}
คำตอบ:""")

    combine_chain   = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(
        vector_db.as_retriever(search_kwargs={"k": TOP_K}),
        combine_chain,
    )
    return retrieval_chain

def ask(chain, query: str):
    print(f"\n{C.MAGENTA} กำลังค้นหาและประมวลผล...{C.RESET}")
    result = chain.invoke({"input": query})
    print_answer(result["answer"])
    print_sources(result["context"])

# ──────────────────────────────────────────────
# ENTRY POINTS
# ──────────────────────────────────────────────
def interactive_mode(chain):
    separator("═", 55, C.CYAN)
    print(f"  {C.CYAN}พิมพ์คำถาม แล้วกด Enter{C.RESET}  {C.DIM}(exit / quit เพื่อออก){C.RESET}")
    separator("═", 55, C.CYAN)

    history = []
    while True:
        try:
            q = input(f"\n{C.BOLD}{C.WHITE} คำถาม: {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.DIM} ลาก่อนครับ!{C.RESET}")
            break

        if not q:
            continue
        if q.lower() in ("exit", "quit", "ออก", "q"):
            print(f"{C.DIM} ลาก่อนครับ!{C.RESET}")
            break

        history.append(q)
        ask(chain, q)

def one_shot_mode(chain, query: str):
    ask(chain, query)

def main():
    banner()
    print(f"{C.DIM}กำลังโหลดโมเดลและเชื่อมต่อฐานข้อมูล...{C.RESET}")
    chain = build_chain()
    print(f"{C.GREEN} พร้อมใช้งาน!{C.RESET}")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        one_shot_mode(chain, query)
    else:
        interactive_mode(chain)

if __name__ == "__main__":
    main()
