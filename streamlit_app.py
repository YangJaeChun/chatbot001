import streamlit as st
from openai import OpenAI

# Show title and description
st.title("💬 중소기업 지원사업 추천 서비스")
st.write(
    "지역과 업종을 알려주시면 맞춤형 중소기업 지원사업을 추천해 드립니다! "
    "예: '서울 IT 지원사업 알려줘'. "
    "이 앱을 사용하려면 OpenAI API 키가 필요합니다. [여기](https://platform.openai.com/account/api-keys)에서 발급받으세요."
)

# API 키 입력
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("계속하려면 OpenAI API 키를 입력해 주세요.", icon="🗝️")
else:
    try:
        # OpenAI 클라이언트 생성
        client = OpenAI(api_key=openai_api_key)

        # 세션 상태에 메시지 저장소 초기화
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": "당신은 중소기업 지원사업 추천 전문가입니다. 사용자가 지역과 업종을 물으면 적절한 지원사업을 추천하고, 구체적이지 않은 질문에는 질문을 명확히 하도록 유도하세요."}
            ]

        # 기존 대화 메시지 출력
        for message in st.session_state.messages:
            if message["role"] != "system":  # 시스템 메시지는 화면에 표시하지 않음
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # 사용자 입력 받기
        if prompt := st.chat_input("어떤 지원사업을 찾으세요? (예: '부산 제조업 지원사업')"):
            # 사용자 메시지 저장 및 출력
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # OpenAI API 호출
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )

                # 스트리밍 응답을 플레이스홀더로 관리
                response_content = ""
                with st.chat_message("assistant"):
                    placeholder = st.empty()  # 플레이스홀더 생성
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            response_content += chunk.choices[0].delta.content
                            placeholder.markdown(response_content)  # 같은 위치에서 업데이트
                
                # 완성된 응답을 세션 상태에 저장
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            except Exception as e:
                error_msg = "응답을 생성하는 중 오류가 발생했어요. API 키를 확인하거나 잠시 후 다시 시도해 주세요."
                with st.chat_message("assistant"):
                    st.error(error_msg, icon="⚠️")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

    except Exception as e:
        st.error(f"OpenAI 클라이언트를 초기화할 수 없습니다. API 키가 올바른지 확인해 주세요. 오류: {str(e)}", icon="🚨")
