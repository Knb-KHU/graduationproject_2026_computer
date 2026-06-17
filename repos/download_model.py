# 1. 파이썬 파일 생성
from huggingface_hub import snapshot_download
import os

# 모델 다운로드
print("다운로드를 시작합니다...")
snapshot_download(
    repo_id="Qwen/Qwen2.5-3B-Instruct", 
    local_dir="./Qwen2.5-3B-Instruct",
    local_dir_use_symlinks=False
)
print("다운로드 완료!")
