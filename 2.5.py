from transformers import AutoModelForCausalLM, AutoTokenizer

# 모델 파일들이 들어있는 로컬 폴더 경로
local_path = "C:/Users/safas/Downloads/Qwen2.5-3B"

# 경로를 직접 입력 (해당 폴더에 config.json, model.safetensors 등이 있어야 함)
tokenizer = AutoTokenizer.from_pretrained(local_path)
model = AutoModelForCausalLM.from_pretrained(local_path)


# 대화 기록을 유지하기 위한 리스트
chat_history = []

def chat(user_input):
    # 사용자 입력을 대화 기록에 추가
    chat_history.append({"role": "user", "content": user_input})

    # 대화 기록을 하나의 문자열로 변환
    conversation = ""
    for turn in chat_history:
        conversation += f"{turn['role']}: {turn['content']}\n"

    # 토큰화 및 모델 실행
    inputs = tokenizer(conversation, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=200)

    # 결과 디코딩
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 모델 응답을 대화 기록에 추가
    chat_history.append({"role": "assistant", "content": response})

    return response

# 테스트
print(chat("안녕하세요! 오늘 기분이 어때요?"))
print(chat("내일 날씨가 어떨까요?"))

