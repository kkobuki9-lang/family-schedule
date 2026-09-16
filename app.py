import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# --- 0. 카카오톡 공유 시 나오는 이름표 & 이모티콘 설정 ---
st.set_page_config(
    page_title="유나 스케줄", 
    page_icon="🏫"
)

# --- 1. 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl="0s")
        if df.empty or '날짜' not in df.columns:
            return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])
        
        df = df.dropna(how="all")
        
        # 빈칸 처리 로직
        df = df.fillna("")
        df = df.astype(str)
        df = df.replace("nan", "") 
        df = df.replace("None", "")
        
        return df
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# --- 2. 화면 구성 시작 ---
st.title("👧 유나 등하원 스케줄")

# 한국 시간(KST)을 미리 계산
kr_time = datetime.utcnow() + timedelta(hours=9)
kr_date = kr_time.date()
today_str = kr_time.strftime("%Y-%m-%d")
current_month_str = kr_time.strftime("%Y-%m") # 예: '2026-09'

# 입력 섹션
st.header("스케줄 입력")
col1, col2, col3 = st.columns(3)

with col1:
    selected_date = st.date_input("날짜 선택", value=kr_date)
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

# --- 3. 확인 섹션 (월별 조회 기능 추가) ---
st.header("📅 스케줄 확인")
df = load_data()

if not df.empty:
    # '연도-월' (예: 2026-09) 형태의 숨겨진 기준 열 만들기
    df['연월'] = df['날짜'].str.slice(0, 7)
    
    # 저장된 데이터에서 존재하는 월(Month)들만 뽑아서 내림차순(최신순) 정렬
    unique_months = sorted(df['연월'].unique().tolist(), reverse=True)
    
    # 기본으로 선택될 월 설정 (이번 달 데이터가 있으면 이번 달, 없으면 가장 최신 달)
    default_index = unique_months.index(current_month_str) if current_month_str in unique_months else 0
    
    # 월 선택 드롭다운
    selected_month = st.selectbox("조회할 달을 선택하세요", unique_months, index=default_index)
    
    # 선택한 월의 데이터만 추려내기
    filtered_df = df[df['연월'] == selected_month].copy()
    
    # 화면에 보여줄 땐 '연월' 숨김 열은 삭제
    filtered_df = filtered_df.drop(columns=['연월'])

    if not filtered_df.empty:
        # 오늘 날짜 노란색 강조 함수
        def highlight_today(row):
            if str(row['날짜']) == today_str:
                return ['background-color: #FFF2CC; color: #000000; font-weight: bold;'] * len(row)
            else:
                return [''] * len(row)

        # 스타일 적용하여 표 그리기
        styled_df = filtered_df.style.apply(highlight_today, axis=1)
        st.table(styled_df)
    else:
        st.info(f"{selected_month}월에 등록된 스케줄이 없습니다.")
else:
    st.info("아직 등록된 스케줄이 없습니다.")