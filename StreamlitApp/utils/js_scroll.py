import streamlit.components.v1 as components

# Streamlit에서 JavaScript 코드를 실행하기 위한 유틸리티 함수 모음 

# 방향 컨트롤 
def inject_scroll(direction="top"):
    js_code = """
    <script>
        const container = window.parent.document.querySelector('.main');
        if (container) {
            const scrollTarget = direction === "top" ? 0 : container.scrollHeight;
            container.scrollTo({ top: scrollTarget, behavior: "smooth" });
        }
    </script>
    """
    js_code = js_code.replace("direction", f'"{direction}"')
    components.html(js_code, height=0)

# 특정 요소로 스크롤 이동
def scroll_to_element(js_path: str, offset: int = 0, delay: int = 0):
    js_code = f"""
    <script>
        setTimeout(function() {{
            const element = {js_path};
            if (element) {{
                const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
                const offsetPosition = elementPosition - {offset};
                window.scrollTo({{
                    top: offsetPosition,
                    behavior: "smooth"
                }});
            }}
        }}, {delay});
    </script>
    """
    components.html(js_code, height=0)

# 화면 우하단에 고정된 Top 버튼 렌더링 
def render_scroll_to_top_button():
    components.html("""
        <!-- Bootstrap Icons 아이콘 스타일을 불러오기 위한 CDN 링크 -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
        
        <script>
            function scrollToAnchor() {
                const el = window.parent.document.querySelector('#scroll-anchor');
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        </script>
        
        <style>
            #scroll-btn {
                position: fixed;
                bottom: 30px;
                right: calc((100vw - 75rem) / 2 - 4px); 
                background-color: #F7F9FB;
                color: #333;
                border: 1.5px solid #888;  
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease;
                z-index: 9999;
            }                   
            #scroll-btn i {
                font-size: 22px;
            }
            #scroll-btn:hover {
                transform: scale(1.05);
            }
            @media screen and (max-width: 1200px) {
                #scroll-btn {
                    right: 24px;  
                }
            }
        </style>

        <button id="scroll-btn" onclick="scrollToAnchor()">
            <i class="bi bi-arrow-up-circle-fill"></i> Top
        </button>
    """, height=100, width=0)
