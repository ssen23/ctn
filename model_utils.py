from transformers import BertTokenizer, BertForSequenceClassification
import torch
import torch.nn.functional as F
import logging
import time
from tqdm import tqdm
from db_utils import get_news_without_probability, update_news_probability, batch_update_probabilities, get_collection_stats

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPU 사용 가능 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"사용 중인 디바이스: {device}")

# KoBERT 불러오기
try:
    tokenizer = BertTokenizer.from_pretrained("./model2")
    model = BertForSequenceClassification.from_pretrained("./model2")
    model.to(device)
    model.eval()
    logger.info("KoBERT 모델 로딩 완료")
except Exception as e:
    logger.error(f"KoBERT 모델 로딩 실패: {e}")
    raise

# KoBART 요약 관련 모듈
try:
    from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
    import re

    summary_tokenizer = PreTrainedTokenizerFast.from_pretrained("digit82/kobart-summarization")
    summary_model = BartForConditionalGeneration.from_pretrained("digit82/kobart-summarization")
    summary_model.to(device)
    summary_model.eval()
    logger.info("KoBART 요약 모델 로딩 완료")
except Exception as e:
    logger.error(f"KoBART 모델 로딩 실패: {e}")
    # 요약 기능 없이도 동작하도록 설정
    summary_model = None
    summary_tokenizer = None

# ✅ 본문 슬라이딩
def sliding_window(text, window=300, step=150):
    """텍스트를 슬라이딩 윈도우로 분할합니다."""
    if not text or not text.strip():
        return []
    
    words = text.split()
    if len(words) <= window:
        return [text]
    
    slices = []
    for i in range(0, len(words), step):
        part = words[i:i+window]
        if part:
            slices.append(' '.join(part))
        if i + window >= len(words):
            break
    return slices

# ✅ 슬라이스 요약
def summarize_slices(slices):
    """텍스트 슬라이스들을 요약합니다."""
    if not summary_model or not summary_tokenizer:
        return slices  # 요약 모델이 없으면 원본 반환
    
    summaries = []
    for chunk in slices:
        try:
            inputs = summary_tokenizer(
                chunk, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                summary_ids = summary_model.generate(
                    inputs['input_ids'],
                    max_length=64,
                    num_beams=4,
                    early_stopping=True,
                    pad_token_id=summary_tokenizer.pad_token_id
                )
            summary = summary_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"슬라이스 요약 실패: {e}")
            summaries.append(chunk[:200])  # 실패시 앞부분만 사용
    
    return summaries

# ✅ 전체 본문 요약
def generate_summary(body_text):
    """본문을 요약합니다."""
    if not body_text or not body_text.strip():
        return ""
    
    if not summary_model or not summary_tokenizer:
        # 요약 모델이 없으면 앞부분만 사용
        return body_text[:1000]
    
    try:
        tokenized = summary_tokenizer(body_text, return_tensors="pt", truncation=False)
        
        # 토큰 길이가 512 이하면 그대로 반환
        if tokenized['input_ids'].shape[1] <= 512:
            return body_text
        else:
            # 슬라이딩 윈도우로 분할 후 요약
            slices = sliding_window(body_text)
            summaries = summarize_slices(slices)
            return ' '.join(summaries)
    except Exception as e:
        logger.warning(f"본문 요약 실패: {e}")
        return body_text[:1000]  # 실패시 앞부분만 사용

# ✅ KoBERT 불일치 확률 계산
def get_mismatch_probability(title, body):
    """제목과 본문의 불일치 확률을 계산합니다."""
    if not title or not body:
        logger.warning("제목 또는 본문이 비어있습니다.")
        return 0.0
    
    try:
        # 본문 요약
        summarized_body = generate_summary(body)
        
        # 토크나이징
        inputs = tokenizer(
            title, 
            summarized_body, 
            return_tensors="pt", 
            truncation=True, 
            padding=True,
            max_length=512
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # 예측
        with torch.no_grad():
            outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            mismatch_prob = probs[0][1].item()
        
        return mismatch_prob
    
    except Exception as e:
        logger.error(f"확률 계산 실패: {e}")
        return 0.0

# ✅ 전체 뉴스 처리 (개선된 버전)
def update_all_mismatch_probabilities(batch_size=10, max_news=None):
    """모든 뉴스의 불일치 확률을 계산하고 업데이트합니다."""
    
    # 통계 정보 출력
    stats = get_collection_stats()
    if stats:
        logger.info(f"처리 전 통계: {stats}")
    
    # 확률값이 없는 뉴스만 가져오기
    news_list = get_news_without_probability(limit=max_news)
    
    if not news_list:
        logger.info("처리할 뉴스가 없습니다.")
        return
    
    logger.info(f"총 {len(news_list)}개의 뉴스를 처리합니다.")
    
    processed_count = 0
    batch_updates = []
    
    # 진행률 표시와 함께 처리
    for i, news in enumerate(tqdm(news_list, desc="뉴스 처리 중")):
        try:
            title = news.get("title", "").strip()
            body = news.get("body", "").strip()
            
            if not title or not body:
                logger.warning(f"뉴스 ID {news['_id']}: 제목 또는 본문이 비어있습니다.")
                continue
            
            # 확률 계산
            prob = get_mismatch_probability(title, body)
            batch_updates.append((news["_id"], prob))
            processed_count += 1
            
            # 배치 단위로 업데이트
            if len(batch_updates) >= batch_size:
                batch_update_probabilities(batch_updates)
                batch_updates = []
            
        except Exception as e:
            logger.error(f"뉴스 ID {news.get('_id')} 처리 실패: {e}")
            continue
    
    # 남은 데이터 처리
    if batch_updates:
        batch_update_probabilities(batch_updates)
    
    logger.info(f"처리 완료: {processed_count}개 뉴스")
    
    # 최종 통계 출력
    final_stats = get_collection_stats()
    if final_stats:
        logger.info(f"처리 후 통계: {final_stats}")

# ✅ 특정 뉴스 처리
def update_single_news_probability(news_id):
    """특정 뉴스 하나의 확률을 계산하고 업데이트합니다."""
    try:
        from db_utils import collection
        from bson import ObjectId
        
        news = collection.find_one({"_id": ObjectId(news_id)}, {"title": 1, "body": 1})
        if not news:
            logger.error(f"뉴스 ID {news_id}를 찾을 수 없습니다.")
            return False
        
        title = news.get("title", "").strip()
        body = news.get("body", "").strip()
        
        if not title or not body:
            logger.warning(f"뉴스 ID {news_id}: 제목 또는 본문이 비어있습니다.")
            return False
        
        prob = get_mismatch_probability(title, body)
        return update_news_probability(news_id, prob)
        
    except Exception as e:
        logger.error(f"단일 뉴스 처리 실패: {e}")
        return False

# ✅ 메인 실행 함수
def main():
    """메인 실행 함수"""
    logger.info("뉴스 불일치 확률 계산 시작")
    start_time = time.time()
    
    # 전체 뉴스 처리 (배치 크기 20, 최대 100개)
    update_all_mismatch_probabilities(batch_size=20, max_news=201)
    
    end_time = time.time()
    logger.info(f"처리 완료. 소요 시간: {end_time - start_time:.2f}초")

if __name__ == "__main__":
    main()