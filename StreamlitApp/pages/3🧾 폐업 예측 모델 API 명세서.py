import streamlit as st
import json
from utils.css_loader import load_css

st.set_page_config(page_title="API Documentation", layout="wide")

load_css("main.css")
load_css("api_document.css")

st.title("🧾 폐업 예측 모델 API 명세서")
st.write("---")
st.markdown("- 이 페이지는 폐업 예측 모델 API의 엔드포인트를 문서화하고, 요청 및 응답 예시를 제공합니다.")
st.write(" ")

def section_title(title):
    st.markdown(f'''<div class="custom-section-title">{title}</div><hr class="tight-hr">''', unsafe_allow_html=True)

############################################################
###### First Model Section (행안부 데이터 기반 모델 api) ######
############################################################
with st.expander(" /gateway/closure_model_1/invocations", expanded=False):
    
    # Parameters title 
    section_title("Parameters")
    st.markdown("No parameters")

    # Request Body title 
    cols = st.columns([1, 0.25])
    with cols[0]:
        st.markdown('<div class="custom-section-title">Request Body</div>', unsafe_allow_html=True)
    with cols[1]:
        st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_req1")

    st.markdown('<hr class="tight-hr">', unsafe_allow_html=True)
    
    # Request Body title example code & schema 
    req_tab = st.tabs(["Example Value", "Schema"])
    with req_tab[0]:
        example_request_1 = {
            "inputs": [["일반음식점", "서울특별시", "종로구", "운영기간_5년미만"]],
            "params": {}, # optional
            "candidate_count": 1 # optional 
        }
        st.markdown("""```json\n""" + json.dumps(example_request_1, indent=2, ensure_ascii=False) + "\n```")
    
    with req_tab[1]:
        request_schema_1 = {
            "inputs": {
                "type": "array<array<string>>",
                "required": True,
                "example": [["일반음식점", "서울특별시", "종로구", "운영기간_5년미만"]]
            },
            "params": {
                "type": "object",
                "required": False,
                "example": {}
            },
            "candidate_count": {
                "type": "integer",
                "required": False,
                "default": 1,
                "constraints": "[1, 5]",
                "example": 1
            }
        }
        st.json(request_schema_1, expanded=1)

    # Responses section
    section_title("Responses")
    
    # code description: 200 
    st.markdown("""
    <div style="
            display: flex;
            justify-content: flex-start;
            font-weight: 600;
            font-size: 16px;
            gap: 40px;
            margin-bottom: 1px;">
        <span>Code</span>
        <span>Description</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="api-subtitle">200 - Successful Response</div>', unsafe_allow_html=True)
    
    st.write(" ")
    st.markdown("**Media Type**")
    st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_res1_200")
    st.caption("Controls Accept header.")

    # code description: 200 -> example value & schema code 
    success_tab = st.tabs(["Example Value", "Schema"])
    with success_tab[0]:
        success_response_1 = {
            "predictions": [1], # y값 
            "model": "closure_model_1",
            "metadata": {
                "input_shape": [2, 4],
                "route_type": "tabular/inference"
            }
        }
        st.markdown("""```json\n""" + json.dumps(success_response_1, indent=2) + "\n```")
    with success_tab[1]:
        st.json({k: str(type(v)).replace("<class '", "").replace("'>", "") for k, v in success_response_1.items()})
    
    # code description: 442 
    st.markdown('<div class="api-subtitle">422 - Validation Error</div>', unsafe_allow_html=True)

    st.write(" ")
    st.markdown("**Media Type**")
    st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_res1_422")
    st.caption("Controls Accept header.")
    
    # code description: 442 -> example value & schema code 
    error_tab = st.tabs(["Example Value", "Schema"])
    with error_tab[0]:
        validation_response = {
            "detail": [
                {
                    "loc": ["body", "temperature"],
                    "msg": "field required",
                    "type": "value_error"
                }
            ]
        }
        st.markdown("""```json\n""" + json.dumps(validation_response, indent=2) + "\n```")
    with error_tab[1]:
        st.json({"detail": "List[Dict[str, str]]"})


########################################################################
###### Second Model Section (스마트치안빅데이터플랫폼 데이터 기반 모델 api) ######
########################################################################
with st.expander(" /gateway/closure_model_2/invocations", expanded=False):
    
    # Parameters title 
    section_title("Parameters")
    st.markdown("No parameters")

    # Request Body title 
    cols = st.columns([1, 0.25])
    with cols[0]:
        st.markdown('<div class="custom-section-title">Request Body</div>', unsafe_allow_html=True)
    with cols[1]:
        st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_req2")

    st.markdown('<hr class="tight-hr">', unsafe_allow_html=True)
    
    # Request Body example code & schema 
    req_tab2 = st.tabs(["Example Value", "Schema"])
    with req_tab2[0]:
        example_request_2 = {
            "inputs": [[22, 0, 17, 2023, 1.0, 6.123234e-17]],
            "params": {},
            "candidate_count": 1
        }
        st.markdown("""```json\n""" + json.dumps(example_request_2, indent=2) + "\n```")
    with req_tab2[1]:
        request_schema_2 = {
            "inputs": "List[List[float]]  (2D tabular input)",
            "params": "Optional[Dict[str, Any]]",
            "candidate_count": "int (optional)"
        }
        st.json(request_schema_2)

    # Responses section 
    section_title("Responses")

    # code description: 200 
    st.markdown("""
    <div style="
            display: flex;
            justify-content: flex-start;
            font-weight: 600;
            font-size: 16px;
            gap: 40px;
            margin-bottom: 1px;">
        <span>Code</span>
        <span>Description</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="api-subtitle">200 - Successful Response</div>', unsafe_allow_html=True)
    
    st.write(" ")
    st.markdown("**Media Type**")
    st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_res2_200")
    st.caption("Controls Accept header.")

    # code description: 200 -> example value & schema code 
    success_tab2 = st.tabs(["Example Value", "Schema"])
    with success_tab2[0]:
        success_response_2 = {
            "predictions": [0],
            "model": "closure_model_2",
            "metadata": {
                "input_shape": [2, 6],
                "route_type": "tabular/inference"
            }
        }
        st.markdown("""```json\n""" + json.dumps(success_response_2, indent=2) + "\n```")
    with success_tab2[1]:
        st.json({k: str(type(v)).replace("<class '", "").replace("'>", "") for k, v in success_response_2.items()})

    # code description: 442 
    st.markdown('<div class="api-subtitle">422 - Validation Error</div>', unsafe_allow_html=True)

    st.write(" ")
    st.markdown("**Media Type**")
    st.selectbox("Media Type", options=["application/json"], label_visibility="collapsed", key="media_type_res2_422")
    st.caption("Controls Accept header.")
    
    # code description: 442 -> example value & schema code 
    error_tab2 = st.tabs(["Example Value", "Schema"])
    with error_tab2[0]:
        st.markdown("""```json\n""" + json.dumps(validation_response, indent=2) + "\n```")
    with error_tab2[1]:
        st.json({"detail": "List[Dict[str, str]]"})

# 
st.markdown('<div class="custom-section-title">CURL Example</div>', unsafe_allow_html=True)
st.markdown("""
<table class="curl-table">
  <tr>
    <th>Model</th>
    <th>curl Command</th>
  </tr>
  <tr>
    <td><strong>closure_model_1</strong></td>
    <td><pre><code>curl -u token:$DATABRICKS_TOKEN \\
  -X POST \\
  -H "Content-Type: application/json" \\
  -d @data_model_1.json \\
  https://.../closure_model_1/invocations</code></pre></td>
  </tr>
  <tr>
    <td><strong>closure_model_2</strong></td>
    <td><pre><code>curl -u token:$DATABRICKS_TOKEN \\
  -X POST \\
  -H "Content-Type: application/json" \\
  -d @data_model_2.json \\
  https://.../closure_model_2/invocations</code></pre></td>
  </tr>
</table>
""", unsafe_allow_html=True)

