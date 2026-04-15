from transformers import AutoTokenizer,AutoModelForCausalLM
import torch

import re,json

def locextractor(userinput):
    # 모델
    local_path="/local_datasets/Qwen2.5-3B/"
    model_id = "Qwen/Qwen2.5-3B" # Reverting to the original Qwen3.5-2B model
    model = AutoModelForCausalLM.from_pretrained(local_path, dtype=torch.float16, local_files_only=True).to("cuda")
    tokenizer = AutoTokenizer.from_pretrained(local_path, local_files_only=True)

    # Tool 정의 (JSON Schema)
    functions = [
        {
            "name": "extract_location",
            "description": "문장에서 장소명만 추출합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추출된 장소명 리스트"
                    }
                },
                "required": ["locations"]
            }
        }
    ]

    # 프롬프트
    prompt = f"""
    다음 예시를 참고하세요.

    문장: 나는 서울시에 있는 강남역의 스타벅스와 노원구에 있는 공릉역의 다이소에 가고 싶어.
    출력: {{\"locations\": [\"서울시 강남역 스타벅스\",\"노원구 공릉역 다이소\"]}}

    문장: 홍대입구에서 올리브영 들렀어
    출력: {{\"locations\": [\"홍대입구 올리브영\"]}}

    문장: {userinput}
    출력:
    """

    # 추론
    inputs = tokenizer(prompt, add_generation_prompt=False, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256,do_sample=False,temperature=0.0,)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 디코딩
    print(result)
    match = re.findall(r"\{.*?\}", result, re.DOTALL)
    all_loc=[json.loads(m)["locations"]for m in match]
    if match:
        try:
            data = all_loc[2]
            """loc=""
            for i in data:
                loc+=i"""
            print("장소:", data)
            return data
        except json.JSONDecodeError:
            print("JSON 디코딩 실패:", match)
    else:
        print("JSON 패턴을 찾지 못했습니다:", result)
locextractor("나는 노원구에 있는 다이소 그리고 청량리에 있는 올리브영도 가고 싶어.")
