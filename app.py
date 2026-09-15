import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# --- 0. 카카오톡 공유 시 나오는 이름표 ---
st.set_page_config(
    page_title="👧 유나 등하원 스케줄", 
    page_icon="📅"
)

# --- 1. 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Sheet1", ttl="0s")
        if df.empty or '날짜' not in df.columns:
            return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])
        
        # 빈 줄 제거 및 날짜를 문자로 확실히 변환 (비교 에러 방지)
        df = df.dropna(how="all")
        df['날짜'] = df['날짜'].astype(str)
        return df
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '등원', '하원', '메모'])

def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# --- 2. 화면 구성 시작 ---
st.title("👧 유나 등하원 스케줄")

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
    
    # ★ 수정 포인트: 기존 날짜 데이터 수정 시 에러가 나지 않도록 튼튼하게 변경
    if date_str in df['날짜'].values:
        # 이미 있는 날짜면 정확한 줄(행) 번호를 찾아 내용만 갈아끼움
        idx = df.index[df['날짜'] == date_str].tolist()[0]
        df.at[idx, '등원'] = drop_off
        df.at[idx, '하원'] = pick_up
        df.at[idx, '메모'] = memo
    else:
        # 없는 날짜면 새로운 줄을 아래에 추가
        new_row = pd.DataFrame([{'날짜': date_str, '등원': drop_off, '하원': pick_up, '메모': memo}])
        df = pd.concat([df, new_row], ignore_index=True)
    
    # 날짜 순서대로 다시 정렬
    df = df.sort_values('날짜')
    save_data(df)
    st.success(f"{date_str} 스케줄이 성공적으로 저장/수정되었습니다!")
    st.rerun()

# --- 3. 확인 섹션 ---
st.header("📅 전체 스케줄 확인")
df = load_data()

if not df.empty:
    # ★ 수정 포인트: 클라우드 서버 시간(UTC) 대신 한국 시간(KST)으로 '오늘' 계산
    kr_time = datetime.utcnow() + timedelta(hours=9)
    today_str = kr_time.strftime("%Y-%m-%d")

    # 왼쪽에 보기 싫은 숫자(0, 1, 2) 대신 '날짜'를 기준점으로 설정
    show_df = df.set_index('날짜')

    # ★ 수정 포인트: 오늘 날짜인 줄(행)만 노란색 배경에 검은 글씨로 칠하는 함수
    def highlight_today(row):
        if row.name == today_str:
            return ['background-color: #FFF2CC; color: #000000'] * len(row)
        else:
            return [''] * len(row)

    # 표에 색상(스타일) 입히기
    styled_df = show_df.style.apply(highlight_today, axis=1)

    # ★ 수정 포인트: 클릭해도 열이 움직이거나 정렬되지 않게 st.table() 사용
    st.table(styled_df)
else:
    st.info("아직 등록된 스케줄이 없습니다.")