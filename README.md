<img src="https://capsule-render.vercel.app/api?type=waving&color=E0C3FC&height=180&section=header&text=문장%20의미분석을%20이용한%20CTN%20판별%20모델%20개발&fontColor=000000&fontSize=36" />

## 📌 프로젝트 개요

> **CTN (Clickbait-Type News) 명명**  
> 독자의 **클릭을 유도**하기 위해 본문과의 **의미 일치도가 낮은 제목**을 사용하는 뉴스 기사

이 프로젝트는 **문장 의미 분석 기반의 AI 모델**을 통해 CTN을 자동으로 판별하고, 신뢰도 높은 뉴스 소비를 유도하는 것을 목표로 합니다.

---

## 🎯 프로젝트 목적

- 뉴스 제목과 본문 간 **의미 불일치 정도 자동 분석**
- 소비자에게 **신뢰할 수 있는 기사 선별** 도구 제공  → CTN 기사를 자동 판별하여 불필요한 클릭 방지  
- **뉴스 소비 효율 향상**  → 본문과 일치하는 기사만 소비하여 시간·인지 자원 절약  
- **미디어 리터러시 향상** → 클릭 유도 뉴스의 패턴을 파악함으로써 **비판적 뉴스 해석 능력** 강화  
- 독자 **참여도와 화제성** 평가를 통한 기사 영향력 판단
- **언론사별 신뢰도 분석**으로 투명한 미디어 환경 조성

---

## 🚨 주요 기능

### 🔍 클릭베이트 탐지
- **불일치 확률** 산출 (0~1):  
  - ✅ **저위험 (< 0.4)**  
  - ⚠️ **중위험 (0.4 ~ 0.7)**  
  - 🚨 **고위험 (≥ 0.7)**

### 📈 독자 참여도 분석
- `참여도 점수 = (공감수 × 0.3) + (댓글수 × 0.7)`
- 🟢 고참여 (≥ 20점)  
  🟡 중참여 (10~20점)  
  🔴 저참여 (< 10점)

### 💬 화제성 지표
- `화제성 비율 = 댓글수 ÷ 공감수`
- 비율이 높을수록 **논란/토론 유발 기사**

### 📰 언론사 신뢰도 평가
- `고위험 기사 비율 = (고위험 기사 수 ÷ 전체 기사 수) × 100`
- 🟢 높음 (< 20%)  
  🟡 보통 (20~50%)  
  🔴 낮음 (≥ 50%)

---

## 📊 대시보드 주요 기능

- **실시간 통계**: 총 기사 수, 평균 불일치율, 총 댓글수 등
- **정렬/필터링**: 위험도, 참여도, 최신순
- **시각화**:  
  - 도넛 차트 기반 언론사별 고위험 기사 분포  
  - 색상 코드 기반 위험도 표시  
  - 카드 형태 기사 표시

---

## 🛠️ 기술 스택

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![VSCode](https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-000000?style=for-the-badge&logo=python&logoColor=white)

---

## 🚀 향후 개선 방향

- 뉴스 **카테고리 자동 분류** 확장
- 사용자 맞춤형 대시보드 제공
- **실시간 데이터 스트리밍 기반** 확장

---

## 📰구현 화면

![image](https://github.com/user-attachments/assets/3fd3820f-310e-49c8-8d03-4e9be05ce203)
![image](https://github.com/user-attachments/assets/62e4ce6b-37cb-4159-92e1-ac1702eab245)
![image](https://github.com/user-attachments/assets/c7d54492-8e5a-4cef-af73-2babbf3a8714)
![image](https://github.com/user-attachments/assets/d4a3e2b4-cc50-4e5f-9490-56285b80e1cb)


