import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# --- 0. 카카오톡 공유 시 나오는 이름표 ---
st.set_page_config(
    page_title="👧 유나 등하원 스케줄러", 
    page_icon="📅"
)

# --- 1. 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl="0s")
        if df.empty or '날짜' not in df.columns:
            return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])
        
        df = df.dropna(how="all")
        df['날짜'] = df['날짜'].astype(str)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# --- 2. 화면 구성 시작 ---
st.title("👧 유나 등하원 스케줄러")

# 입력 섹션
st.header("스케줄 입력")
col1, col2, col3 = st.columns(3)

with col1:
    selected_date = st.date_input("날짜 선택")
with col2:
    drop_off = st.selectbox("등원 담당", ["엄마", "아빠", "외할머니", "친할머니", "할아버지", "이모", "고모"])
with col3:
    pick_up = st.selectbox("하원 담당", ["엄마", "아빠", "외할머니", "친할머니", "할아버지", "이모", "고모", "연장반"])

memo = st.text_input("메모 (예: 비 오는 날 우산 챙기기)")

if st.button("저장하기"):
    df = load_data()
    date_str = str(selected_date)
    
    # 이미 있는 날짜면 수정, 없으면 추가
    if not df.empty and date_str in df['날짜'].values:
        df.loc[df['날짜'] == date_str, '등원'] = drop_off
        df.loc[df['날짜'] == date_str, '하원'] = pick_up
        df.loc[df['날짜'] == date_str, '메모'] = memo
    else:
        new_row = pd.DataFrame([{'날짜': date_str, '등원': drop_off, '하원': pick_up, '메모': memo}])
        df = pd.concat([df, new_row], ignore_index=True)
    
    # 날짜 순서대로 정렬 후 저장
    df = df.sort_values('날짜')
    save_data(df)
    st.success(f"{date_str} 스케줄이 성공적으로 저장되었습니다!")
    st.rerun()

# --- 3. 확인 섹션 ---
st.header("📅 전체 스케줄 확인")
df = load_data()

if not df.empty:
    # 한국 시간 기준 오늘 날짜 계산
    kr_time = datetime.utcnow() + timedelta(hours=9)
    today_str = kr_time.strftime("%Y-%m-%d")

    # 순수 데이터프레임 상태에서 오늘 날짜 행만 노란색 배경으로 강조
    def highlight_today(row):
        if str(row['날짜']) == today_str:
            return ['background-color: #FFF2CC; color: #000000; font-weight: bold;'] * len(row)
        else:
            return [''] * len(row)

    # 스타일을 적용한 표 생성 (열 클릭 방지를 위해 st.table 사용)
    styled_df = df.style.apply(highlight_today, axis=1)
    
    st.table(styled_df)
else:
    st.info("아직 등록된 스케줄이 없습니다.")