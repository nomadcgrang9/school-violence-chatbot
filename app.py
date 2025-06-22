# 필요한 라이브러리들을 불러옵니다.
import os
import traceback
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일에서 환경 변수를 불러옵니다. (API 키 관리용)
load_dotenv()

# Flask 웹 애플리케이션을 생성합니다.
app = Flask(__name__)

# --- Gemini API 설정 ---
try:
    # 환경 변수에서 API 키를 가져옵니다.
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인하세요.")
    
    genai.configure(api_key=api_key)
    
    # 사용할 Gemini 모델을 설정합니다.
    model = genai.GenerativeModel('models/gemini-2.5-flash-latest')
except Exception as e:
    # API 설정 중 에러가 발생하면 터미널에 메시지를 출력합니다.
    print(f"API 설정 중 에러 발생: {e}")
    model = None

# --- 파일명 설정 ---
# 사용자가 알려준 매뉴얼 파일명을 변수로 저장합니다.
MANUAL_FILENAME = "a.txt"

# --- 라우팅 설정 ---

# 기본 URL('/')로 접속했을 때, 채팅 UI(index.html)를 보여주는 라우트입니다.
@app.route('/')
def home():
    # render_template 함수는 templates 폴더에서 index.html 파일을 찾아 렌더링합니다.
    return render_template('index.html')

# '/chat' URL로 POST 요청이 왔을 때, 챗봇 응답을 처리하는 라우트입니다.
@app.route('/chat', methods=['POST'])
def chat():
    # 모델 설정이 실패했으면 에러 메시지를 반환합니다.
    if not model:
        return jsonify({'error': '서버의 AI 모델이 제대로 설정되지 않았습니다. 터미널 로그를 확인하세요.'}), 500

    try:
        # 프론트엔드에서 보낸 JSON 데이터에서 사용자 메시지를 추출합니다.
        user_message = request.json['message']

        # 매뉴얼 파일을 읽어옵니다. 'utf-8' 인코딩을 사용합니다.
        with open(MANUAL_FILENAME, 'r', encoding='utf-8') as f:
            manual_text = f.read()

        # AI에게 전달할 프롬프트를 생성합니다.
        prompt = f"""
        당신은 '경기형 학교폭력 사안처리 매뉴얼'을 기반으로 답변하는 전문 AI 챗봇입니다.
        당신의 임무는 오직 아래에 제공되는 <매뉴얼>의 내용만을 근거로 하여 사용자 질문에 답변하는 것입니다.
        
        # 지침
        1. 답변은 반드시 <매뉴얼>에 명시된 내용으로만 구성해야 합니다.
        2. 당신의 생각이나 <매뉴얼> 외부의 일반 지식을 추가해서는 안 됩니다.
        3. 만약 <매뉴얼>에서 질문에 대한 답을 찾을 수 없다면, "문의하신 내용은 매뉴얼에서 찾을 수 없습니다."라고만 답변하세요.
        4. 답변은 명확하고 간결하게 핵심 정보 위주로 제공해주세요.

        <매뉴얼>
        {manual_text}
        </매뉴얼>

        # 사용자 질문
        {user_message}
        """

        # 완성된 프롬프트를 Gemini 모델에 보내고 응답을 받습니다.
        response = model.generate_content(prompt)
        
        # AI의 답변을 JSON 형식으로 프론트엔드에 반환합니다.
        return jsonify({'reply': response.text})

    except FileNotFoundError:
        # 콘솔에도 에러 원인을 출력해 디버깅할 수 있도록 합니다.
        traceback.print_exc()
        error_message = f"'{MANUAL_FILENAME}' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 파일이 있는지 확인해주세요."
        return jsonify({'error': error_message}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'서버 처리 중 오류가 발생했습니다: {str(e)}'}), 500

# 이 스크립트가 직접 실행될 때만 Flask 서버를 구동합니다.
if __name__ == '__main__':
    app.run(debug=True, port=5000)
