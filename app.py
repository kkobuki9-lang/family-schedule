import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # 구글 시트 데이터 불러오기 (캐시를 비워 항상 최신 데이터를 가져옴)
        df = conn.read(worksheet="Sheet1", ttl="0s")
        if df.empty or '날짜' not in df.columns:
            return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])
        return df.dropna(how="all")
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])

def save_data(df):
    # 수정된 데이터프레임을 구글 시트에 덮어쓰기
    conn.update(worksheet="Sheet1", data=df)

# --- 2. 화면 구성 ---
st.title("👨‍👩‍👧 우리 가족 등하원 스케줄러")

# 입력 섹션
st.header("스케줄 입력")
col1, col2, col3 = st.columns(3)

with col1:
    selected_date = st.date_input("날짜 선택")
with col2:
    # 요청하신 등원 담당자 목록 업데이트
    drop_off = st.selectbox("등원 담당", ["엄마", "아빠", "외할머니", "친할머니", "할아버지", "이모", "고모"])
with col3:
    # 요청하신 하원 담당자 목록 업데이트 (연장반 추가)
    pick_up = st.selectbox("하원 담당", ["엄마", "아빠", "외할머니", "친할머니", "할아버지", "이모", "고모", "연장반"])

memo = st.text_input("메모 (예: 비 오는 날 우산 챙기기)")

if st.button("저장하기"):
    df = load_data()
    date_str = str(selected_date)
    
    if date_str in df['날짜'].values:
        df.loc[df['날짜'] == date_str, ['등원', '하원', '메모']] = [drop_off, pick_up, memo]
    else:
        new_data = pd.DataFrame({'날짜': [date_str], '등원': [drop_off], '하원': [pick_up], '메모': [memo]})
        df = pd.concat([df, new_data], ignore_index=True)
    
    df = df.sort_values('날짜')
    save_data(df)
    st.success(f"{date_str} 스케줄이 구글 시트에 안전하게 저장되었습니다!")
    st.rerun()

# 확인 섹션
st.header("📅 전체 스케줄 확인")
df = load_data()

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("아직 등록된 스케줄이 없습니다.")