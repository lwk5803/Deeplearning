"""
app.py
------
사회복지 대상자 정보 관리 - 로컬 프로토타입 (1단계)

실행 방법:
    streamlit run app.py

지금은 로그인 인증 없이, 내 컴퓨터에서만 혼자 테스트하는 단계입니다.
동료들과 함께 쓰거나 외부에 배포하기 전에는 반드시 인증을 추가해야 합니다.
"""

import streamlit as st
import pandas as pd
from io import BytesIO

import database as db

st.set_page_config(page_title="사회복지 대상자 관리", layout="wide")

# 앱이 처음 실행될 때 테이블이 없으면 만들어줍니다.
db.init_db()

st.title("사회복지 대상자 관리 (로컬 프로토타입)")

menu = st.sidebar.radio(
    "메뉴",
    ["대상자 목록", "신규 등록", "엑셀 내보내기"],
)

WELFARE_TYPES = ["기초생활수급", "차상위계층", "장애인", "노인", "한부모가정", "기타"]


# ----------------------------------------------------------------------
# 1) 대상자 목록 - 조회, 수정, 삭제
# ----------------------------------------------------------------------
if menu == "대상자 목록":
    st.subheader("대상자 목록")

    df = db.get_all_clients()

    if df.empty:
        st.info("등록된 대상자가 없습니다. '신규 등록' 메뉴에서 추가해보세요.")
    else:
        st.dataframe(
            df[["id", "name", "birth_date", "welfare_type", "manager"]],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("상세 조회 / 수정 / 삭제")

        # 이름과 id를 함께 보여줘서 동명이인이 있어도 구분되게 합니다.
        options = {f"{row['id']} - {row['name']}": row["id"] for _, row in df.iterrows()}
        selected_label = st.selectbox("대상자 선택", options.keys())
        selected_id = options[selected_label]
        client = db.get_client(selected_id)

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("성명", value=client["name"])
                birth_date = st.text_input("생년월일 (예: 1990-01-01)", value=client["birth_date"] or "")
                address = st.text_input("주소", value=client["address"] or "")
                phone = st.text_input("연락처", value=client["phone"] or "")
            with col2:
                welfare_type = st.selectbox(
                    "복지 유형",
                    WELFARE_TYPES,
                    index=WELFARE_TYPES.index(client["welfare_type"])
                    if client["welfare_type"] in WELFARE_TYPES else 0,
                )
                manager = st.text_input("담당자", value=client["manager"] or "")
                note = st.text_area("비고", value=client["note"] or "")

            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("수정하기", use_container_width=True)
            with col_b:
                deleted = st.form_submit_button(
                    "삭제하기", use_container_width=True, type="secondary"
                )

        if submitted:
            db.update_client(
                selected_id, name, birth_date, address, phone, welfare_type, manager, note
            )
            st.success(f"'{name}' 님의 정보를 수정했습니다.")
            st.rerun()

        if deleted:
            db.delete_client(selected_id)
            st.warning(f"'{client['name']}' 님의 정보를 삭제했습니다.")
            st.rerun()


# ----------------------------------------------------------------------
# 2) 신규 등록
# ----------------------------------------------------------------------
elif menu == "신규 등록":
    st.subheader("신규 대상자 등록")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("성명 *")
            birth_date = st.text_input("생년월일 (예: 1990-01-01)")
            address = st.text_input("주소")
            phone = st.text_input("연락처")
        with col2:
            welfare_type = st.selectbox("복지 유형", WELFARE_TYPES)
            manager = st.text_input("담당자")
            note = st.text_area("비고")

        submitted = st.form_submit_button("등록하기", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("성명은 필수 입력 항목입니다.")
        else:
            db.add_client(name, birth_date, address, phone, welfare_type, manager, note)
            st.success(f"'{name}' 님을 등록했습니다.")


# ----------------------------------------------------------------------
# 3) 엑셀 내보내기
# ----------------------------------------------------------------------
elif menu == "엑셀 내보내기":
    st.subheader("엑셀 내보내기")

    df = db.get_all_clients()

    if df.empty:
        st.info("내보낼 데이터가 없습니다.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="대상자목록")
        buffer.seek(0)

        st.download_button(
            label="엑셀 파일 다운로드",
            data=buffer,
            file_name="대상자목록.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
