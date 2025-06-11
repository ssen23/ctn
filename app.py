from flask import Flask, render_template_string, request, jsonify
from db_utils import get_all_news as get_articles
from datetime import datetime
import logging
from collections import Counter
import json



logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CTN 뉴스 분석</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet"/>
  <style>
    body { font-family: 'Noto Sans KR', sans-serif; }
    .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card-hover { transition: all 0.3s ease; }
    .card-hover:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    .mismatch-high { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
    .mismatch-medium { background: linear-gradient(135deg, #feca57, #ff9ff3); }
    .mismatch-low { background: linear-gradient(135deg, #48dbfb, #0abde3); }
    .date-badge { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); }
    .stat-icon { font-size: 2rem; }
    .engagement-high { color: #10b981; }
    .engagement-medium { color: #f59e0b; }
    .engagement-low { color: #ef4444; }
    .chart-container { background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); }
  </style>
</head>
<body class="bg-gray-50 min-h-screen">
  <div class="gradient-bg text-white py-8 mb-8">
    <div class="max-w-7xl mx-auto px-2 sm:px-4">
      <h1 class="text-4xl font-bold mb-2">CTN 뉴스 분석</h1>
      <p class="text-lg opacity-90">제목과 내용의 불일치 정도 및 참여도 분석</p>
      <div class="mt-4 text-sm opacity-75">
        📅 업데이트: 2025. 6. 9
      </div>
    </div>
  </div>
  
  
<!-- Top Horizontal Navbar -->
<nav class="w-full bg-white shadow-md px-6 py-4 flex justify-center sticky top-0 z-50"> 
  <ul class="flex space-x-10 text-gray-700 text-lg">
    <li><a href="#" class="hover:text-blue-600">대시보드</a></li>
    <li><a href="#trust" class="hover:text-blue-600">언론사 신뢰도 분석</a></li>
    <li><a href="#articlesGrid" class="hover:text-blue-600">기사 보기</a></li>
    <li><a href="#performance" class="hover:text-blue-600">참여도 분석</a></li>
    <li><a href="#performance" class="hover:text-blue-600">성능 지표</a></li>
  </ul>
</nav>


  <div class="max-w-7xl mx-auto px-2 sm:px-4 pb-12">
  <div class="mb-6"></div>
  
    <!-- 메인 통계 대시보드 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-2xl p-6 shadow-lg card-hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-gray-800">{{ total_articles }}</div>
            <div class="text-gray-600">총 기사 수</div>
          </div>
          <div class="stat-icon">📰</div>
        </div>
      </div>
      
      <div class="bg-white rounded-2xl p-6 shadow-lg card-hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-red-500">{{ high_mismatch_count }}</div>
            <div class="text-gray-600">고위험 기사</div>
          </div>
          <div class="stat-icon">🚨</div>
        </div>
      </div>
      
      <div class="bg-white rounded-2xl p-6 shadow-lg card-hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-blue-500">{{ avg_mismatch|round(1) }}%</div>
            <div class="text-gray-600">평균 불일치율</div>
          </div>
          <div class="stat-icon">📊</div>
        </div>
      </div>
      
      <div class="bg-white rounded-2xl p-6 shadow-lg card-hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-2xl font-bold text-green-500">{{ avg_engagement|round(1) }}</div>
            <div class="text-gray-600">평균 참여율</div>
          </div>
          <div class="stat-icon">💬</div>
        </div>
      </div>
    </div>

    <!-- 새로운 지표 섹션 -->
<div id="trust" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
  <!-- 언론사별 신뢰도 분석 -->
  <div class="bg-white rounded-2xl p-6 shadow-lg">
    <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
      <span class="mr-2">🏢</span>
      언론사 신뢰도 분석
    </h3>
    <div class="space-y-3">
      {% for media_stat in media_stats %}
      <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div class="flex-1">
          <div class="font-medium text-gray-800">{{ media_stat.media }}</div>
          <div class="text-sm text-gray-600">
            총 {{ media_stat.total_articles }}개 기사 중 
            <span class="font-semibold text-red-500">{{ media_stat.high_risk_articles }}개</span> 고위험
          </div>
        </div>
        <div class="text-right">
          <div class="text-lg font-bold 
            {% if media_stat.high_risk_ratio < 0.2 %}
              text-green-500
            {% elif media_stat.high_risk_ratio < 0.5 %}
              text-yellow-500
            {% else %}
              text-red-500
            {% endif %}
          ">
            {{ '%.1f'|format(media_stat.high_risk_ratio * 100) }}%
          </div>
          <div class="text-xs text-gray-500">고위험 비율</div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
      
    <!-- 고위험 기사 분포 원그래프 -->
  <div class="bg-white rounded-2xl p-6 shadow-lg">
    <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
      <span class="mr-2">📊</span>
      고위험 기사 분포
    </h3>
    <div class="flex justify-center items-center">
      <div style="width: 250px; height: 250px;">
        <canvas id="riskPieChart"></canvas>
      </div>
    </div>
    <div class="mt-4 text-center">
      <div class="text-sm text-gray-600">총 {{ high_mismatch_count }}개 고위험 기사</div>
    </div>
  </div>
</div>
    
    <!-- 정렬 옵션 -->
    <div class="max-w-7xl mx-auto px-2 sm:px-4 pb-12">
    <div class="mb-6"></div>
    <div class="flex justify-end mb-6">
      <form method="get" id="sortForm">
        <label for="sort" class="mr-2 text-sm text-gray-700 font-medium">정렬:</label>
        <select name="sort" id="sort" class="text-sm px-3 py-2 rounded-md border border-gray-300 shadow-sm">
          <option value="risk" {% if sort_order == 'risk' %}selected{% endif %}>위험순</option>
          <option value="safe" {% if sort_order == 'safe' %}selected{% endif %}>안전순</option>
          <option value="engagement" {% if sort_order == 'engagement' %}selected{% endif %}>참여도순</option>
          <option value="latest" {% if sort_order == 'latest' %}selected{% endif %}>최신순</option>
        </select>
      </form>
    </div>
    </div>
    
    <!-- 기사 그리드 -->
    
    <div class="max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
    <div id="articlesGrid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
      {% for article in articles %}
      <div class="bg-white rounded-2xl shadow-lg overflow-hidden card-hover">
        <div class="{% if article.mismatch_prob >= 0.7 %}mismatch-high{% elif article.mismatch_prob >= 0.4 %}mismatch-medium{% else %}mismatch-low{% endif %} p-4 text-white relative">
          <div class="flex justify-between items-start">
            <div>
              <div class="text-2xl font-bold">{{ '%.1f'|format(article.mismatch_prob * 100) }}%</div>
              <div class="text-sm opacity-90">불일치 확률</div>
            </div>
            <div class="date-badge px-3 py-1 rounded-full text-xs">{{ article.date if article.date else '날짜 미상' }}</div>
          </div>
          <div class="mt-3 flex justify-between items-center">
            <div>
              {% if article.mismatch_prob >= 0.7 %}
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-white bg-opacity-20">🚨 고위험</span>
              {% elif article.mismatch_prob >= 0.4 %}
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-white bg-opacity-20">⚠️ 중위험</span>
              {% else %}
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-white bg-opacity-20">✅ 저위험</span>
              {% endif %}
            </div>
            <div class="text-xs opacity-75">{{ article.media }}</div>
          </div>
        </div>
        <div class="p-5">
          <h3 class="font-semibold text-gray-800 mb-3 line-clamp-2 leading-tight">{{ article.title }}</h3>
          
          <!-- 참여도 정보 -->
          <div class="flex items-center justify-between mb-3 text-sm text-gray-600">
            <div class="flex items-center space-x-3">
              <span class="flex items-center">
                <span class="mr-1">👍</span>
                {{ article.like_count }}
              </span>
              <span class="flex items-center">
                <span class="mr-1">💬</span>
                {{ article.comment_count }}
              </span>
            </div>
            <div class="{% if article.engagement_score >= 20 %}engagement-high{% elif article.engagement_score >= 10 %}engagement-medium{% else %}engagement-low{% endif %} font-medium">
              참여도: {{ '%.1f'|format(article.engagement_score) }}
            </div>
          </div>
          
          <!--화제성 지표 -->
          {% if article.controversial_ratio >= 2.0 %}
          <div class="mb-3 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-lg text-center">
            🔥 화제성 기사 (댓글/공감 비율: {{ '%.1f'|format(article.controversial_ratio) }})
          </div>
          {% endif %}
          
          <a href="{{ article.url }}" target="_blank" class="inline-flex items-center justify-center w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition duration-200">
            <span>기사 보기</span>
            <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
            </svg>
          </a>
        </div>
      </div>
      {% endfor %}
    </div>
    </div>

    <div class="mt-6 text-center">
      <button id="loadMoreBtn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">더보기</button>
      <p id="endMessage" class="mt-4 text-gray-500 hidden">마지막 기사입니다.</p>
    </div>
    
    
        <!-- 2열 그리드로 배치 -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
  
  <!-- 참여도 분석 -->
  <div class="bg-white rounded-2xl p-6 shadow-lg">
    <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
      <span class="mr-2">📈</span>
      참여도 분석
    </h3>
    <div class="grid grid-cols-2 gap-4">
      <div class="text-center p-4 bg-blue-50 rounded-lg">
        <div class="text-2xl font-bold text-blue-600">{{ total_likes }}</div>
        <div class="text-sm text-gray-600">총 공감수</div>
      </div>
      <div class="text-center p-4 bg-green-50 rounded-lg">
        <div class="text-2xl font-bold text-green-600">{{ total_comments }}</div>
        <div class="text-sm text-gray-600">총 댓글수</div>
      </div>
      <div class="text-center p-4 bg-purple-50 rounded-lg">
        <div class="text-2xl font-bold text-purple-600">{{ high_engagement_count }}</div>
        <div class="text-sm text-gray-600">고참여 기사</div>
      </div>
      <div class="text-center p-4 bg-orange-50 rounded-lg">
        <div class="text-2xl font-bold text-orange-600">{{ controversial_count }}</div>
        <div class="text-sm text-gray-600">화제성 기사</div>
      </div>
    </div>
  </div>

  <!-- 모델 성능 지표 -->
  <div id="performance" class="bg-gray-100 rounded-2xl p-6 shadow-lg text-gray-700 text-sm">
    <h3 class="text-base font-semibold text-gray-800 mb-4">📊 모델 성능 지표</h3>
    <ul class="space-y-1">
      <li>🔹 정확도(Accuracy): 84.3%</li>
      <li>🔹 정밀도(Precision): 92.9%</li>
      <li>🔹 재현율(Recall): 72.4%</li>
      <li>🔹 F1-score: 81.4%</li>
      <li>🔹 정확도 신뢰구간 (95%): 82.3% ~ 85.7% (±1.7%)</li>
    </ul>
    <div class="mt-4 text-gray-500 text-xs">
      ※ 해당 지표는 테스트 세트 기준으로 측정되었습니다.<br/>
      ※ 모델은 특정 시점의 데이터를 기반으로 훈련되었으며, 실제 기사 판단과 차이가 있을 수 있습니다.
    </div>
  </div>

</div>


    <div class="mt-12 text-center text-gray-500 text-sm">
      <p>AI 기반 뉴스 제목-내용 불일치 및 참여도 분석 시스템</p>
      <p class="mt-1">CTN 뉴스 품질 관리 도구</p>
    </div>
  </div>
  
  

<script>
// 페이지 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', function() {
  // 숫자 포맷팅 함수
  function numberFormat(num) {
    return new Intl.NumberFormat('ko-KR').format(num);
  }

  // 원그래프 데이터 준비
  const pieData = [
    {% for media_stat in media_stats %}
    {
      label: "{{ media_stat.media }}",
      value: {{ media_stat.high_risk_articles }},
      percentage: {{ '%.1f'|format(media_stat.high_risk_ratio * 100) }}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ];

  function generateColor(index) {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
      '#F8C471', '#82E0AA', '#AED6F1', '#F7DC6F', '#D7BDE2'
    ];
    return colors[index % colors.length];
  }

  const ctx = document.getElementById('riskPieChart');
    if (ctx && pieData.length > 0) {
      const topMediaData = pieData.slice(0, 5);
      const otherTotal = pieData.slice(5).reduce((sum, item) => sum + item.value, 0);
    
    if (otherTotal > 0) {
      topMediaData.push({
        label: "기타",
        value: otherTotal,
        percentage: (otherTotal / pieData.reduce((sum, item) => sum + item.value, 0) * 100).toFixed(1)
      });
    }

    const pieChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: topMediaData.map(item => item.label),
        datasets: [{
          data: topMediaData.map(item => item.value),
          backgroundColor: topMediaData.map((item, index) => generateColor(index)),
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 15,
              usePointStyle: true,
              font: {
                size: 12,
                family: 'Noto Sans KR'
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const item = topMediaData[context.dataIndex];
                return `${item.label}: ${item.value}개 (${item.percentage}%)`;
              }
            }
          }
        }
      }
    });
  }
});

  
  const loadMoreBtn = document.getElementById('loadMoreBtn');
  const articlesGrid = document.getElementById('articlesGrid');
  const endMessage = document.getElementById('endMessage');
  const sortSelect = document.getElementById('sort');

  let offset = {{ articles|length }};
  const limit = 30;
  const sortOrder = "{{ sort_order }}";

  loadMoreBtn.addEventListener('click', () => {
    loadMoreBtn.disabled = true;
    loadMoreBtn.textContent = '로딩 중...';

    fetch(`/load_more?offset=${offset}&limit=${limit}&sort=${sortOrder}`)
      .then(response => response.json())
      .then(data => {
        if(data.articles.length === 0) {
          loadMoreBtn.style.display = 'none';
          endMessage.classList.remove('hidden');
          return;
        }

        data.articles.forEach(article => {
          const div = document.createElement('div');
          div.className = 'bg-white rounded-2xl shadow-lg overflow-hidden card-hover';
          let riskClass = 'mismatch-low';
          let riskText = '✅ 저위험';
          if(article.mismatch_prob >= 0.7) {
            riskClass = 'mismatch-high';
            riskText = '🚨 고위험';
          } else if(article.mismatch_prob >= 0.4) {
            riskClass = 'mismatch-medium';
            riskText = '⚠️ 중위험';
          }
          
          let engagementClass = 'engagement-low';
          if(article.engagement_score >= 20) engagementClass = 'engagement-high';
          else if(article.engagement_score >= 10) engagementClass = 'engagement-medium';
          
          let controversialBadge = '';
          if(article.controversial_ratio >= 2.0) {
            controversialBadge = `<div class="mb-3 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-lg text-center">🔥 화제성 기사 (댓글/공감 비율: ${article.controversial_ratio.toFixed(1)})</div>`;
          }
          
          div.innerHTML = `
            <div class="${riskClass} p-4 text-white relative">
              <div class="flex justify-between items-start">
                <div>
                  <div class="text-2xl font-bold">${(article.mismatch_prob * 100).toFixed(1)}%</div>
                  <div class="text-sm opacity-90">불일치 확률</div>
                </div>
                <div class="date-badge px-3 py-1 rounded-full text-xs">${article.date || '날짜 미상'}</div>
              </div>
              <div class="mt-3 flex justify-between items-center">
                <div>
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-white bg-opacity-20">${riskText}</span>
                </div>
                <div class="text-xs opacity-75">${article.media}</div>
              </div>
            </div>
            <div class="p-5">
              <h3 class="font-semibold text-gray-800 mb-3 line-clamp-2 leading-tight">${article.title}</h3>
              <div class="flex items-center justify-between mb-3 text-sm text-gray-600">
                <div class="flex items-center space-x-3">
                  <span class="flex items-center"><span class="mr-1">👍</span>${article.like_count}</span>
                  <span class="flex items-center"><span class="mr-1">💬</span>${article.comment_count}</span>
                </div>
                <div class="${engagementClass} font-medium">참여도: ${article.engagement_score.toFixed(1)}</div>
              </div>
              ${controversialBadge}
              <a href="${article.url}" target="_blank" class="inline-flex items-center justify-center w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition duration-200">
                <span>기사 보기</span>
                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                </svg>
              </a>
            </div>
          `;
          articlesGrid.appendChild(div);
        });

        offset += data.articles.length;
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = '더보기';

        if(data.articles.length < limit) {
          loadMoreBtn.style.display = 'none';
          endMessage.classList.remove('hidden');
        }
      })
      .catch(err => {
        console.error(err);
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = '더보기';
      });
  });

  sortSelect.addEventListener('change', () => {
    document.getElementById('sortForm').submit();
  });

    
</script>
</body>
</html>
"""


def calculate_engagement_score(like_count, comment_count):
    """
    참여도 점수 계산
    공감수와 댓글수를 가중평균하여 참여도 산출
    """
    # 댓글이 공감보다 더 높은 참여를 의미하므로 가중치 부여
    return (like_count * 0.3) + (comment_count * 0.7)

def calculate_controversial_ratio(like_count, comment_count):
    """
    화제성 지표 계산
    댓글 대 공감 비율이 높을수록 화제성이 높음
    """
    if like_count == 0:
        return comment_count if comment_count > 0 else 0
    return comment_count / like_count

def analyze_media_trustworthiness(articles):
    """
    언론사별 신뢰도 분석
    - 고위험 기사(불일치율 ≥ 0.7) 개수 기준 정렬
    - 고위험 기사 비율, 총 기사 수 포함
    """
    media_data = {}

    for article in articles:
        media = article.get("media", "알 수 없음")
        mismatch_prob = article.get("mismatch_probability", 0)

        if media not in media_data:
            media_data[media] = {
                "media": media,
                "total_articles": 0,
                "high_risk_articles": 0
            }

        media_data[media]["total_articles"] += 1
        if mismatch_prob >= 0.7:
            media_data[media]["high_risk_articles"] += 1

    media_stats = []
    for media, data in media_data.items():
        if data["total_articles"] >= 3:  # 최소 3개 기사
            high_risk_ratio = data["high_risk_articles"] / data["total_articles"]
            media_stats.append({
                "media": media,
                "total_articles": data["total_articles"],
                "high_risk_articles": data["high_risk_articles"],
                "high_risk_ratio": high_risk_ratio
            })

    # 각 언론사별 (고위험 기사 순 / 전체 기사) 기준으로 정렬 (비율 높은 순)
    media_stats.sort(key=lambda x: x["high_risk_ratio"], reverse=True)
    return media_stats


def get_sorted_articles(sort_order):
    articles = get_articles()
    results = []
    
    for article in articles:
        title = article.get("title", "")
        url = article.get("URL", "#")
        date = article.get("date", "")
        mismatch_prob = article.get("mismatch_probability", 0)
        media = article.get("media", "알 수 없음")
        like_count = article.get("like_count", 0)
        comment_count = article.get("comment_count", 0)
        
        # 새로운 지표 계산
        engagement_score = calculate_engagement_score(like_count, comment_count)
        controversial_ratio = calculate_controversial_ratio(like_count, comment_count)

        results.append({
            "title": title,
            "url": url,
            "mismatch_prob": mismatch_prob,
            "date": date,
            "media": media,
            "like_count": like_count,
            "comment_count": comment_count,
            "engagement_score": engagement_score,
            "controversial_ratio": controversial_ratio
        })

    # 정렬
    if sort_order == "safe":
        results.sort(key=lambda x: x["mismatch_prob"])
    elif sort_order == "engagement":
        results.sort(key=lambda x: x["engagement_score"], reverse=True)
    elif sort_order == "latest":
        def parse_date(a):
            try:
                return datetime.strptime(a["date"], "%Y-%m-%d %H:%M:%S")
            except:
                return datetime.min
        results.sort(key=parse_date, reverse=True)
    else:  # risk
        results.sort(key=lambda x: x["mismatch_prob"], reverse=True)
    
    return results


@app.route("/")
def index():
    sort_order = request.args.get("sort", "risk")
    all_articles = get_sorted_articles(sort_order)
    total_articles = len(all_articles)

    # 처음 40개만 렌더링
    articles = all_articles[:40]

    # 기존 통계
    high_mismatch_count = sum(1 for a in all_articles if a["mismatch_prob"] >= 0.7)
    avg_mismatch = sum(a["mismatch_prob"] for a in all_articles) / total_articles if total_articles else 0

    # 새로운 통계 계산
    total_likes = sum(a["like_count"] for a in all_articles)
    total_comments = sum(a["comment_count"] for a in all_articles)
    avg_engagement = sum(a["engagement_score"] for a in all_articles) / total_articles if total_articles else 0
    
    # 고참여 기사 (참여도 20 이상)
    high_engagement_count = sum(1 for a in all_articles if a["engagement_score"] >= 20)
    
    # 화제성 기사 (댓글/공감 비율 2.0 이상)
    controversial_count = sum(1 for a in all_articles if a["controversial_ratio"] >= 2.0)
    
    # 언론사별 분석
    raw_articles = get_articles()  # 원본 데이터로 언론사 분석
    media_stats = analyze_media_trustworthiness(raw_articles)

    return render_template_string(
        HTML_TEMPLATE,
        articles=articles,
        total_articles=total_articles,
        high_mismatch_count=high_mismatch_count,
        avg_mismatch=avg_mismatch * 100,  # 백분율로 표시
        avg_engagement=avg_engagement,
        total_likes=total_likes,
        total_comments=total_comments,
        high_engagement_count=high_engagement_count,
        controversial_count=controversial_count,
        media_stats=media_stats,
        sort_order=sort_order
    )


@app.route("/load_more")
def load_more():
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 40))
        sort_order = request.args.get("sort", "risk")
    except ValueError:
        return jsonify({"articles": []})

    all_articles = get_sorted_articles(sort_order)
    slice_articles = all_articles[offset:offset + limit]

    return jsonify({"articles": slice_articles})


if __name__ == "__main__":
    app.run(debug=True)