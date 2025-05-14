import streamlit as st

# components.v1.html() 안에서는 미리 지정한 css가 적용되지 않음 -> css 코드를 style 태그로 같이 넣기 
def embed_dashboard(dashboard_url: str, height: int = 1200, width: str = "100%", border_radius: str = "12px" ,description: str = None):
    
    st.components.v1.html(f"""
        <style>
        .dashboard-container {{
            background-color: #F7F9FB;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }}
        </style>
        <div class="dashboard-container">
            <iframe 
                src="{dashboard_url}"
                width="100%" 
                height="{height}" 
                frameborder="0" 
                style="border: none; border-radius: 12px;">
            </iframe>
        </div>
        """,
        height=height + 80)