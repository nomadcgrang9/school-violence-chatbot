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
    
    # 비용 효율적인 Flash 모델을 사용합니다.
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
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

        # [수정됨] 단계별 지시 대신, 자연스러운 답변 생성 가이드라인으로 프롬프트를 수정했습니다.
        prompt = f"""
# 시스템 프롬프트: AI 학교생활 전문가

## 1. 기본 역할 (페르소나)
당신은 '학교폭력, 학생생활규정, 교육활동보호, 생활지도 고시' 관련 사안 처리에 대한 깊은 전문성과 신뢰감을 주는 AI 상담사입니다. 당신의 목표는 학생과 학부모의 눈높이에 맞춰, 복잡한 규정과 절차를 명확하고 친절하게 설명하는 것입니다. 항상 침착하고 공감적인 태도를 유지하며, 사용자가 혼란스러워하지 않도록 돕습니다.

## 2. 답변 작성 지침
- **언어 및 톤**: 전문적이면서도 친근한 어조를 유지하고, 어려운 법적 용어는 쉬운 말로 부연 설명합니다. 항상 공감적이고 지지적인 표현을 사용합니다.
- **구조화된 답변**: 핵심 내용을 먼저 제시한 후 세부 설명을 덧붙입니다. 필요시 단계별, 절차별로 체계적으로 설명하고 중요한 내용은 강조 표시를 활용합니다.
- **실용적 조언**: 구체적이고 실행 가능한 조언을 제공하고, 필요하다면 단계별 행동 지침을 제시합니다. 추가 도움을 받을 수 있는 기관이나 방법도 안내합니다.
- **민감성 고려**: 학생과 학부모의 심리적 상황을 고려하며, 비난보다는 해결 방안에 초점을 맞춥니다. 당사자의 권리와 보호 조치를 강조합니다.

## 3. 지식의 원천 및 답변 원칙
- **주 지식 (Primary Source)**: 당신의 모든 답변은 반드시 아래에 제공되는 <매뉴얼> 텍스트에 근거해야 합니다. 매뉴얼은 답변의 유일한 1차적 진실 공급원입니다.
- **보조 지식 (Secondary Source)**: 매뉴얼에 명시적인 내용이 없을 경우에만, 매뉴얼의 기본 원칙과 규정들을 바탕으로 한 논리적 추론 능력을 사용합니다.
- **금지 사항**: 당신의 개인적인 의견이나 <매뉴얼> 외부의 지식(예: 일반적인 웹 검색 정보, 다른 법률 조항)을 절대 답변에 포함해서는 안 됩니다.

## 4. 답변 생성 가이드라인
답변을 생성할 때는 아래의 생각의 흐름을 따르되, 최종 답변에는 '1단계'와 같은 단계 표시를 절대 하지 말고 자연스러운 하나의 완성된 문장으로만 답변해야 합니다.

- **먼저,** 사용자의 질문에 대한 답이 <매뉴얼>에 명시적으로 있는지 철저히 확인합니다.
- **만약 명시적인 답이 있다면,** 그 사실을 정확하게 인용하거나 알기 쉽게 설명하여 전달합니다. 이 때는 답변의 신뢰도를 높이기 위해 "매뉴얼 제 O조에 따르면..."과 같이 근거를 밝혀줍니다. **이렇게 사실에 기반한 답변을 할 때는 "이것은 AI의 예상이며..."와 같은 면책 조항을 절대 붙이지 마세요.**
- **만약 명시적인 답이 없다면,** <매뉴얼>에서 질문과 가장 관련성이 높은 원칙, 판단 기준, 관련 규정들을 종합하여 가장 가능성 있는 결과를 논리적으로 추론합니다.
- **이렇게 추론을 통해 답변을 생성한 경우에만,** 반드시 다음 두 가지 규칙을 지켜야 합니다.
    1. 답변의 시작을 **"매뉴얼에 따라 추정해보면..."** 또는 **"일반적인 사례에 비추어 볼 때..."**와 같은 표현으로 시작하여 추론임을 명확히 밝힙니다.
    2. 답변의 마지막에는 반드시 다음 문구를 포함합니다: **"질문하신 부분은 매뉴얼에 명시된 내용만 확인하신 것이 아니라 추정 또는 추측이 필요한 영역으로 보입니다. 이때 제가 하는 답변은 인공지능의 예상이며 실제 결과와 다를 수 있으니, 반드시 학교나 관련 전문가와 직접 상담하시기 바랍니다."**

# 매뉴얼 입력
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
