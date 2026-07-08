import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
import json
from datetime import datetime, timedelta

# =========================================================================
# ⚙️ ส่วนระบุรหัสเชื่อมต่อ LINE Messaging API
# =========================================================================
# ⚠️ คุณข้าวหอมเอารหัสจริงมาวางแทนคำว่า วางรหัส... ในเครื่องหมายคำพูดได้เลยครับ
LINE_CHANNEL_ACCESS_TOKEN = "1cb67231c9862f5354d6274bcbedf7c7"
LINE_USER_ID = "C039904d88e1bc08adccbf29ecb7edacb"

TEMP_MIN_SAFE = 2.0
TEMP_MAX_SAFE = 6.0

# --- แก้ไขฟังก์ชันส่งข้อความช่วงบรรทัดที่ 19 เป็นต้นไป ให้เป็นแบบนี้ครับ ---
def send_line_message_api(message):
    # ลบเงื่อนไขดักคำว่า "ตรงนี้" เก่าออกให้หมด เหลือแค่วิ่งไปส่งข้อมูลเลย
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    try:
        requests.post(url, headers=headers, data=json.dumps(payload))
    except pass

# =========================================================================
# 🖥️ เริ่มต้นระบบหน้าจอ Dashboard (Streamlit)
# =========================================================================
st.set_page_config(page_title="ตู้แช่เลือดที่ 1 - Smart Monitor", page_icon="🩸", layout="wide")

st.markdown("<h1 style='text-align: center; color: #58a6ff;'>🩸 ระบบตรวจวัดและบันทึกอุณหภูมิอัจฉริยะสำหรับตู้แช่เลือด (Whole Blood)</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #8b949e;'>🏥 โรงพยาบาล - อุปกรณ์หมายเลข: ตู้แช่ที่ 1 (แจ้งเตือนสภาวะเกือบวิกฤต)</h3>", unsafe_allow_html=True)
st.markdown("---")

MAX_POINTS = 24

if 'temp_history' not in st.session_state:
    base_time = datetime.now() - timedelta(hours=MAX_POINTS)
    st.session_state.temp_history = []
    st.session_state.time_history = []
    
    for i in range(MAX_POINTS):
        past_time = base_time + timedelta(hours=i)
        simulated_past_temp = round(float(4.0 + np.random.uniform(-0.1, 0.1)), 2)
        st.session_state.temp_history.append(simulated_past_temp)
        st.session_state.time_history.append(past_time.strftime("%d/%m %H:00"))
        
    st.session_state.last_logged_hour = (datetime.now() - timedelta(hours=1)).strftime("%H")
    st.session_state.last_alert_status = "SAFE"
    st.session_state.previous_temp = 4.0

# 🌡️ สุ่มจำลองค่าอุณหภูมิ (มีโอกาส 15% ที่อุณหภูมิจะแกว่งไปช่วงเตือนภัย/วิกฤต เพื่อให้ทดสอบ LINE ได้)
rand_val = np.random.rand()
if rand_val > 0.93:
    current_temp = round(float(st.session_state.previous_temp + np.random.uniform(1.2, 2.5)), 2) # พุ่งแรง
elif rand_val > 0.85:
    current_temp = round(float(5.6 + np.random.uniform(-0.1, 0.3)), 2) # เข้าช่วงเกือบวิกฤตตอนบน
else:
    current_temp = round(float(4.0 + np.random.uniform(-0.08, 0.08)), 2) # ปกติ

current_time = datetime.now().strftime("%H:%M:%S")
current_hour_str = datetime.now().strftime("%H")
current_hour_label = datetime.now().strftime("%d/%m %H:00")

temp_diff = round(current_temp - st.session_state.previous_temp, 2)

if current_hour_str != st.session_state.last_logged_hour:
    st.session_state.temp_history.append(current_temp)
    st.session_state.time_history.append(current_hour_label)
    st.session_state.last_logged_hour = current_hour_str
    if len(st.session_state.temp_history) > MAX_POINTS:
        st.session_state.temp_history.pop(0)
        st.session_state.time_history.pop(0)

# =========================================================================
# 🚨 Logic การตรวจจับสภาวะวิกฤต และ "เกือบวิกฤต (Warning)"
# =========================================================================
status_label = "SAFE"
status_color = "#3fb950"  
bg_box_color = "rgba(63, 185, 80, 0.1)"
status_text_desc = "🟢 อุณหภูมิตู้ที่ 1 คงที่และปลอดภัย"
line_msg = ""

# 1. ตรวจสอบสภาวะวิกฤตเด็ดขาด (Critical) หลุด 2-6 องศา
if current_temp > TEMP_MAX_SAFE or current_temp < TEMP_MIN_SAFE:
    status_label = "CRITICAL"
    status_color = "#ff7b72" # สีแดง
    bg_box_color = "rgba(255, 123, 114, 0.15)"
    status_text_desc = f"🔴 วิกฤต: ค่าอุณหภูมิหลุดช่วงวิกฤตความปลอดภัย (2-6 °C)"
    line_msg = f"🚨 [ตู้แช่เลือดที่ 1: CRITICAL]\n⚠️ อุณหภูมิตู้หลุดเกณฑ์วิกฤตปลอดภัยสากล!\n🌡️ ปัจจุบัน: {current_temp} °C\n🔒 เกณฑ์กำหนด: {TEMP_MIN_SAFE} - {TEMP_MAX_SAFE} °C\n🕒 เวลา: {current_time}\nโปรดเข้าไปตรวจสอบตู้แช่ด่วน!"

# 2. ตรวจสอบอัตราความไม่คงที่กระทันหัน (เปิดตู้/ไฟดับ)
elif temp_diff >= 0.5:
    status_label = "INFLUX_ALERT"
    status_color = "#ff7b72" # สีแดง
    bg_box_color = "rgba(255, 123, 114, 0.15)"
    status_text_desc = f"🔴 ตรวจพบค่าไม่คงที่! อุณหภูมิพุ่งขึ้นผิดปกติ +{temp_diff} °C"
    line_msg = f"⚠️ [ตู้แช่เลือดที่ 1: UNSTABLE]\nตรวจพบอุณหภูมิแกว่งตัวกะทันหัน!\n🚪 คาดว่ามีการเปิดตู้ค้างไว้ หรือระบบทำความเย็นมีปัญหา\n📈 เปลี่ยนแปลง: +{temp_diff} °C\n🌡️ ปัจจุบัน: {current_temp} °C\n🕒 เวลา: {current_time}"

# 3. [เพิ่มใหม่] ตรวจสอบสภาวะ "เกือบวิกฤต" (Warning Zone: 2.0-2.5 หรือ 5.5-6.0)
elif (TEMP_MIN_SAFE <= current_temp <= 2.5) or (5.5 <= current_temp <= TEMP_MAX_SAFE):
    status_label = "WARNING"
    status_color = "#e3b341" # สีเหลือง/ส้ม
    bg_box_color = "rgba(227, 179, 65, 0.15)"
    status_text_desc = f"🟡 เฝ้าระวัง: อุณหภูมิเข้าใกล้จุดวิกฤตอันตราย"
    line_msg = f"⚠️ [ตู้แช่เลือดที่ 1: WARNING]\n📢 แจ้งเตือน: อุณหภูมิกำลังเข้าใกล้จุดวิกฤต!\n🌡️ ปัจจุบัน: {current_temp} °C\n💡 (เริ่มเบี่ยงเบนออกจากค่ามาตรฐาน 4°C)\n🕒 เวลา: {current_time}"

# 4. สภาวะกลับคืนสู่ความปลอดภัยปกติ
else:
    if st.session_state.last_alert_status != "SAFE":
        line_msg = f"✅ [ตู้แช่เลือดที่ 1: NORMAL]\nสภาวะตู้กลับคืนสู่ความคงที่และปลอดภัยปกติแล้ว\n🌡️ ปัจจุบัน: {current_temp} °C\n🕒 เวลา: {current_time}"

# สั่งยิงไลน์เมื่อมีการเปลี่ยนสถานะ
if status_label != st.session_state.last_alert_status and line_msg != "":
    send_line_message_api(line_msg)
    st.session_state.last_alert_status = status_label

st.session_state.previous_temp = current_temp

# คำนวณค่า SD
temperatures_np = np.array(st.session_state.temp_history)
sd_value = np.std(temperatures_np)
variance_status = "🟢 มั่นคงสูงมาก (Excellent)" if sd_value < 0.2 else "🟡 เริ่มแกว่งตัว (Warning)" if sd_value < 0.5 else "🔴 แปรปรวนสูง (Critical)"

# --- วาดหน้าจอ Dashboard ---
st.markdown("### 📊 บันทึกสภาวะปัจจุบัน: ตู้แช่ที่ 1")
col1, col2, col3 = st.columns([1, 1, 1.2])

with col1:
    st.markdown(f'<div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d;"><p style="margin:0; color:#8b949e; font-size:14px;">อุณหภูมิปัจจุบัน ของ ตู้แช่ที่ 1</p><h1 style="margin:0; color: {status_color}; font-size: 50px; font-family: \'Courier New\';">{current_temp} °C</h1><p style="margin:5px 0 0 0; color:#8b949e; font-size:12px;">🕒 อัปเดตจอคอม: {current_time}</p></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div style="background-color: {bg_box_color}; padding: 15px; border-radius: 10px; border: 1px solid {status_color}; min-height: 112px;"><p style="margin:0; color:#8b949e; font-size:14px; font-weight: bold;">การตรวจจับเหตุการณ์ไม่คงที่ (LINE Alert)</p><p style="margin:10px 0 0 0; color: {status_color}; font-size: 16px; font-weight: bold;">{status_text_desc}</p></div>', unsafe_allow_html=True)

with col3:
    st.markdown(f'<div style="background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d;"><p style="margin:0; color:#8b949e; font-size:14px; font-weight: bold;">📊 วิเคราะห์ความแปรปรวนย้อนหลัง (24 ชม.)</p><p style="margin:5px 0 0 0; color:#c9d1d9; font-size:14px;">ค่าเบี่ยงเบนมาตรฐาน (SD): <b>{sd_value:.3f}</b></p><p style="margin:2px 0 0 0; color:#58a6ff; font-size:14px;">ประเมินความนิ่งตู้: <b>{variance_status}</b></p></div>', unsafe_allow_html=True)

st.markdown("### 📈 เส้นแนวโน้มความร้อนรายชั่วโมง ตู้แช่ที่ 1 (Sampling Rate: ทุกๆ 1 ชั่วโมง)")
chart_data = pd.DataFrame({
    'วันเวลาบันทึก (Hour Log)': st.session_state.time_history,
    'อุณหภูมิตู้ที่ 1 (°C)': st.session_state.temp_history,
    'ขีดจำกัดบน Max (6°C)': [TEMP_MAX_SAFE] * len(st.session_state.temp_history),
    'ขีดจำกัดล่าง Min (2°C)': [TEMP_MIN_SAFE] * len(st.session_state.temp_history)
})
st.line_chart(chart_data, x='วันเวลาบันทึก (Hour Log)', y=['อุณหภูมิตู้ที่ 1 (°C)', 'ขีดจำกัดบน Max (6°C)', 'ขีดจำกัดล่าง Min (2°C)'], color=["#58a6ff", "#ff7b72", "#e3b341"])

st.markdown("---")
st.markdown("### 📋 ระบบตรวจสอบข้อมูลดิบรายชั่วโมง (Hourly Audit Trail Logs)")
with st.expander("คลิกเพื่อเปิด/ปิด ตารางบันทึกค่ารายชั่วโมง", expanded=False):
    log_df = pd.DataFrame({
        'ลำดับ (No.)': range(1, len(st.session_state.time_history) + 1),
        'เวลาสแกนรายชั่วโมง (Timestamp)': st.session_state.time_history,
        'อุณหภูมิตู้แช่ที่ 1 (°C)': st.session_state.temp_history
    })
    log_df['ผลการประเมิน'] = ["✅ คงที่" if (TEMP_MIN_SAFE <= t <= TEMP_MAX_SAFE) else "❌ ผิดปกติ" for t in st.session_state.temp_history]
    log_df = log_df.iloc[::-1].reset_index(drop=True)


    # --- พิมพ์เพิ่มต่อท้ายที่บรรทัดล่างสุดของไฟล์ Blood2.py ---
import streamlit as st

st.write("---")
st.subheader("🧪 โซนทดสอบระบบแจ้งเตือน (สำหรับนักพัฒนา)")

# สร้างปุ่มกดจำลองบนหน้าเว็บ
if st.button("🚨 กดเพื่อทดสอบยิงไลน์กลุ่ม (จำลองค่าวิกฤต)"):
    # ข้อความที่จะลองยิงเข้ากลุ่ม
    test_message = "🚨 [TEST] ระบบจำลองสถานการณ์: ตู้แช่เลือดที่ 1 อุณหภูมิพุ่งสูงเกินกำหนด (8.5°C) กรุณาตรวจสอบห้องปฏิบัติการ"
    
    try:
        # สั่งให้ฟังก์ชันยิง API ทำงานโดยใช้รหัสกลุ่มตัว C ที่เราตั้งไว้
        send_line_message_api(test_message)
        st.success("✅ ส่งข้อความทดสอบเข้า LINE กลุ่มเรียบร้อยแล้ว! ลองเช็กในมือถือดูนะคะ")
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการส่ง: {e}")
    st.dataframe(log_df, use_container_width=True, hide_index=True)

time.sleep(5)
st.rerun()
