import streamlit as st
from openai import OpenAI
import pandas as pd

st.title("💬 중소기업 지원사업 추천 서비스")
st.write("지역과 업종을 알려주시면 맞춤 지원사업을 추천해 드려요! 예: '부산 제조업 지원사업 알려줘'")

# 더미 데이터 (실제로는 CSV나 DB로 대체)
support_programs = pd.DataFrame({
    "name": ["스마트서비스 지원", "창업지원 프로그램"],
    "region": ["부산", "서울"],
    "industry": ["제조업", "IT"],
    "amount": ["6천만 원", "5천만 원"],
    "deadline": ["2025-05-15", "2025-06-01"]
})

openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.error("유효한 OpenAI API 키를 입력해 주세요.", icon="🚨")
else:
    client = OpenAI(api_key=openai_api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    def extract_keywords(prompt):
        keywords = {"region": None, "industry": None}
        if "부산" in prompt:
            keywords["region"] = "부산"
        if "서울" in prompt:
            keywords["region"] = "서울"
        if "제조업" in prompt:
            keywords["industry"] = "제조업"
        if "IT" in prompt:
            keywords["industry"] = "IT"
        return keywords

    def recommend_programs(keywords):
        filtered = support_programs
        if keywords["region"]:
            filtered = filtered[filtered["region"] == keywords["region"]]
        if keywords["industry"]:
            filtered = filtered[filtered["industry"] == keywords["industry"]]
        return filtered

    if prompt := st.chat_input("어떤 지원사업을 찾으세요?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        keywords = extract_keywords(prompt)
        recommendations = recommend_programs(keywords)

        if not recommendations.empty:
            rec_text = recommendations.to_string(index=False)
            gpt_prompt = f"사용자가 '{prompt}'라고 물었어요. 다음 지원사업을 자연스럽게 설명해 주세요:\n{rec_text}"
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": gpt_prompt}],
                stream=True,
            )
            with st.chat_message("assistant"):
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.table(recommendations[["name", "amount", "deadline"]])
        else:
            response = "아직 적합한 지원사업을 찾지 못했어요. 질문을 조금 더 구체적으로 해 주시면 더 잘 도와드릴게요!"
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
