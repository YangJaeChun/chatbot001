import streamlit as st
from openai import OpenAI
import pandas as pd

# 페이지 설정
st.title("💬 경기도 중소기업 지원사업 추천 서비스")
st.write(
    "경기도 중소기업을 위한 맞춤형 지원사업을 찾아드립니다! 예: '수원 IT 지원사업 알려줘' "
    "OpenAI API 키가 필요합니다. [여기](https://platform.openai.com/account/api-keys)에서 발급받으세요."
)

# 더미 데이터 (실제로는 경기기업비서 데이터로 대체 가능)
support_programs = pd.DataFrame({
    "name": ["스마트공장 지원사업", "수출기업 지원", "창업 초기 지원"],
    "region": ["수원", "고양", "성남"],
    "industry": ["제조업", "무역", "IT"],
    "amount": ["5천만 원", "3천만 원", "2천만 원"],
    "deadline": ["2025-06-30", "2025-07-15", "2025-08-01"]
})

# API 키 입력
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("API 키를 입력해 주세요.", icon="🗝️")
else:
    try:
        client = OpenAI(api_key=openai_api_key)

        # 세션 상태 초기화
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": "당신은 '경기기업비서' 챗봇입니다. 경기도 중소기업을 위한 지원사업을 추천하며, 사용자가 지역과 업종을 물으면 구체적인 사업을 제안하고, 불명확한 질문에는 질문을 구체화하도록 유도하세요."}
            ]

        # 이전 대화 출력
        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # 키워드 추출 함수
        def extract_keywords(prompt):
            keywords = {"region": None, "industry": None}
            regions = ["수원", "고양", "성남"]
            industries = ["제조업", "무역", "IT"]
            for r in regions:
                if r in prompt:
                    keywords["region"] = r
            for i in industries:
                if i in prompt:
                    keywords["industry"] = i
            return keywords

        # 추천 함수
        def recommend_programs(keywords):
            filtered = support_programs
            if keywords["region"]:
                filtered = filtered[filtered["region"] == keywords["region"]]
            if keywords["industry"]:
                filtered = filtered[filtered["industry"] == keywords["industry"]]
            return filtered

        # 사용자 입력
        if prompt := st.chat_input("어떤 지원사업을 찾으세요? (예: '수원 제조업 지원사업')"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # 키워드 추출 및 추천
                keywords = extract_keywords(prompt)
                recommendations = recommend_programs(keywords)

                # 추천 결과에 따라 응답 생성
                if not recommendations.empty:
                    rec_text = recommendations.to_string(index=False)
                    gpt_prompt = f"사용자가 '{prompt}'라고 물었어요. 다음 지원사업을 자연스럽게 설명하고 추천해 주세요:\n{rec_text}"
                else:
                    gpt_prompt = f"사용자가 '{prompt}'라고 물었어요. 적합한 지원사업이 없으면 '조건에 맞는 사업을 찾지 못했어요. 지역이나 업종을 구체적으로 알려주세요'라고 답하세요."

                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": gpt_prompt}] + st.session_state.messages,
                    stream=True,
                )

                # 스트리밍 응답 처리
                response_content = ""
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            response_content += chunk.choices[0].delta.content
                            placeholder.markdown(response_content)
                
                # 추천 결과 테이블 표시
                if not recommendations.empty:
                    st.table(recommendations[["name", "amount", "deadline"]])
                
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            except Exception as e:
                error_msg = "응답 생성 중 오류가 발생했어요. API 키를 확인해 주세요."
                with st.chat_message("assistant"):
                    st.error(error_msg, icon="⚠️")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

    except Exception as e:
        st.error(f"OpenAI 연결 실패: {str(e)}", icon="🚨")
