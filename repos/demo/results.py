import re,json

s=""" Evaluation Criteria: 청결도, 가성비, 맛, 서비스

    The answers are a review about a place.
    Please rate each place on a scale of 1 to 5 for each criterion,
    then provide an overall score (average).
    Finally, rank the answers from best to worst.
    If the answer lacks information about a criteria,
    rate it as the medium of that criteria.

    Respond strictly in JSON with the following structure:
    {
      "evaluations": [
        {
          "answer_id": int,
          "scores": {
            "청결도": int,
            "가성비": int,
            "맛": int,
            ...
            "criteria[i]": int
          },
          "overall": float,
          "comments": "short explanation"
        }
      ],
      "ranking": [int, int, ...]
    }
     ```json
    {
      "evaluations": [
        {
          "answer_id": 1,
          "scores": {
            "청결도": 3,
            "가성비": 2,
            "맛": 3,
            "서비스": 2
          },
          "overall": 3.0,
          "comments": "주로 맛과 서비스에만 신경 쓰고 청결도와 가성비는 높지 않다."
        },
        {
          "answer_id": 3,
          "scores": {
            "청결도": 4,
            "가성비": 4,
            "맛": 4,
            "서비스": 4
          },
          "overall": 4.0,
          "comments": "매우 만족스러운 경험으로 청결도, 가성비, 맛, 서비스 모두 최고다."
        },
        {
          "answer_id": 4,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 5,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 6,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 7,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 8,
          "scores": {
            "청결도": 2,
            "가성비": 2,
            "맛": 2,
            "서비스": 2
          },
          "overall": 2.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 9,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        },
        {
          "answer_id": 10,
          "scores": {
            "청결도": 3,
            "가성비": 3,
            "맛": 3,
            "서비스": 3
          },
          "overall": 3.0,
          "comments": "중간 중간 좋은 점이 있지만 전체적으로 만족스럽지 못하다."
        }
      ],
      "ranking": [3, 1, 4, 5, 6, 7, 8, 9, 10]
    }
    ``` ```json
    {
      "evaluations": [
        {
          "answer_id": 1,
          "scores": {
            "청결도": 3,
            "가성비": 2,
            "맛": 3,
            "서비스": 2
          },
          "overall": 3.0,
          "comments": "주로 맛과 서비스에만 신경 쓰고 청결도와 가성비는 높지 않다."
        },
        {
          "answer_id": 3,
          "scores": {
            "청결도": 4,
            "가성비": 4,
            "맛": 4,
            "서비스": 4
          },
          "overall": 4.0,
          "comments": "매우 만족스러운 경험으로 청결도, 가성비, 맛, 서비스 모두 최고다."
        },
       """
match = re.findall(r"json.*?json", s, re.DOTALL)
m=match[0].replace("json","").replace("`","")
j=re.findall(r"overall.*?,",m,re.DOTALL)
for i in range (len(j)):
    j[i]=float(j[i].replace("overall\":","").replace(",",""))
print(j)
"""
allscores=[]
for m in match:
    if "overall" in m:
        allscores.append(m)
    

all_scores=[]
if match:
    try:
        for i in range (len(answers)):
            all_scores.append(allscores[i])
            
    except json.JSONDecodeError:
        print("JSON 디코딩 실패:", match)
else:
    print("JSON 패턴을 찾지 못했습니다:", response)

for i in range (len(allscores)):
    print(f"i:",allscores[i])

"""
