# 필요한 라이브러리들을 불러옵니다.
import os, traceback
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일에서 환경 변수를 불러옵니다. (API 키 관리용)
load_dotenv()

app = Flask(__name__)

# --- Gemini API 설정 ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인하세요.")

    # v1 엔드포인트 + 버전 지정
    genai.configure(
        api_key=api_key,
        api_endpoint="https://generativelanguage.googleapis.com",
        api_version="v1",
    )

    # 사용할 Gemini 모델
    model = genai.GenerativeModel("models/gemini-2.5-flash")

except Exception as e:
    print(f"API 설정 중 에러 발생: {e}")
    model = None

# 매뉴얼 파일명
MANUAL_FILENAME = "a.txt"

# ----------- 라우팅 -----------
@app.route("/")
def home():
    return render_template("index.html")

# 헬스 체크 (UptimeRobot용)
@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/chat", methods=["POST"])
def chat():
    if not model:
        return jsonify({"error": "AI 모델 초기화 실패"}), 500
    try:
        user_message = request.json["message"]

        with open(MANUAL_FILENAME, encoding="utf-8") as f:
            manual_text = f.read()

        prompt = f"""
        당신은 '경기형 학교폭력 사안처리 매뉴얼'을 기반으로 답변하는 전문 AI 챗봇입니다.

        # 지침
        1. 답변은 반드시 <매뉴얼>에 명시된 내용으로만 구성해야 합니다.
        2. 당신의 생각이나 <매뉴얼> 외부의 일반 지식을 추가해서는 안 됩니다.
        3. 매뉴얼에 없으면 "문의하신 내용은 매뉴얼에서 찾을 수 없습니다."라고만 답변하세요.
        4. 답변은 명확하고 간결하게 핵심 정보 위주로 제공해주세요.

        <매뉴얼>
        {manual_text}
        </매뉴얼>

        # 사용자 질문
        {user_message}
        """

        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})

    except FileNotFoundError:
        traceback.print_exc()
        return jsonify({"error": f"'{MANUAL_FILENAME}' 파일을 찾을 수 없습니다."}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"서버 처리 중 오류가 발생했습니다: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
