import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Roast My Bug 🔥", page_icon="🐛", layout="centered")
st.title("🔥 Roast My Bug v2.0")
st.subheader("อัปโหลดโค้ดที่พัง แล้วให้รุ่นพี่วิเคราะห์แบบจัดเต็ม")

# 1. รับ API Key
api_key = st.text_input("🔑 ใส่ Gemini API Key ของนายตรงนี้:", type="password")

st.divider()

# 2. เพิ่มระบบอัปโหลดไฟล์ Python
st.markdown("### 📁 1. อัปโหลดไฟล์โค้ดของนายมาดูหน่อย")
uploaded_file = st.file_uploader("ลากไฟล์ .py มาวางตรงนี้", type=['py'])

# 3. รับ Error Message
st.markdown("### 🐛 2. ก๊อป Error Log มาวาง")
user_error = st.text_area("ก๊อป Stack Trace สีแดงๆ จาก Terminal มาแปะ:", height=150)

# 4. ปุ่มประมวลผล
if st.button("🚀 รันการวิเคราะห์!"):
    if not api_key:
        st.warning("ใส่ API Key ก่อนสิเฮ้ย!")
    elif not uploaded_file:
        st.warning("อัปโหลดไฟล์โค้ดมาด้วย จะให้วิเคราะห์อากาศเหรอ!")
    elif not user_error:
        st.warning("ใส่ Error Log มาด้วย พี่จะได้รู้ว่ามันพังตรงไหน!")
    else:
        # อ่านเนื้อหาในไฟล์ที่อัปโหลดมา
        code_content = uploaded_file.read().decode("utf-8")
        
        with st.spinner("พี่กำลังสแกนโค้ดของนายอยู่ แป๊บนึง..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction="""
                    คุณคือรุ่นพี่ Senior Developer ประจำคณะ ที่โคตรเก่งแต่ขี้รำคาญ หน้าที่ของคุณคือด่าและอธิบาย Error Code ให้รุ่นน้องฟัง

                    กฎการใช้ภาษา:
                    1. ไม่ Overacting พูดจาเหมือนผู้ชายปกติวัย 20 ต้นๆ คุยกัน กวนๆ แต่หน้าตาย
                    2. ห้ามใช้คำหยาบ (มึง, กู, สัตว์, เหี้ย) ใช้คำว่า นาย, บอล, พี่, หรือ แก แทน
                    
                    โครงสร้างการตอบ:
                    - [แซะแบบคนเบื่อโลก]: ถอนหายใจ หรือแซะความยาว/ความมั่วของไฟล์โค้ดที่อ่านเจอ
                    - [วิเคราะห์สาเหตุ]: อธิบายว่าทำไมโค้ดบรรทัดนั้นถึงพัง โดยอ้างอิงจาก 'ตัวโค้ดเต็มๆ' ที่เห็น 
                    - [วิธีแก้]: ให้ Code Snippet ที่แก้ไขแล้ว พร้อมบอกให้เอาไปรันใหม่
                    """
                )
                
                # ประกอบร่าง Prompt โดยส่งทั้ง "โค้ดเต็ม" และ "Error" ให้ AI ดูพร้อมกัน
                final_prompt = f"""
                พี่ครับ โค้ดผมพัง ช่วยดูหน่อย
                นี่คือโค้ดทั้งไฟล์ของผม:
                ```python
                {code_content}
                ```
                
                และนี่คือ Error ที่ขึ้นใน Terminal:
                ```text
                {user_error}
                ```
                """
                
                response = model.generate_content(final_prompt)
                
                st.success("✅ สแกนเสร็จแล้ว!")
                st.markdown("### 💬 รุ่นพี่บอกว่า:")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"ระบบหลังบ้านพัง: {e}")