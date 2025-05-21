import streamlit as st

def embed_dashboard(
    dashboard_url: str,
    height: int = 1200,
    width: str = "100%",
    border_radius: str = "16px",
    description: str = None):

    # 뒤쪽 컨테이너 스타일
    st.markdown(f"""
    <style>
        .element-container:has(iframe) {{
            padding: 0 !important;
            margin: 0 !important;
        }}
        main > div {{
            padding-bottom: 0rem !important;
        }}
        @media screen and (max-width: 768px) {{
            iframe {{
                height: 80vh !important;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

    # 대시보드 설명명
    if description:
        st.markdown(f"<p style='margin-bottom: 0.5rem; color: #444;'>{description}</p>", unsafe_allow_html=True)

    # 대시보드 iframe
    st.markdown(f"""
        <div style="
            background-color: #F7F9FB;
            padding: 2rem;
            border-radius: {border_radius};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            margin-bottom: 1rem;
        ">
            <iframe 
                src="{dashboard_url}"
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                scrolling="no"
                style="border: none; border-radius: {border_radius}; width: 100%;">
            </iframe>
            <noscript>
                <div style="color: red; margin-top: 1rem;">
                    브라우저에서 iframe이 차단되었거나 비활성화되었습니다.<br>
                    <a href="{dashboard_url}" target="_blank">여기</a>를 눌러 새 창에서 확인해 주세요.
                </div>
            </noscript>
        </div>
    """, unsafe_allow_html=True)


