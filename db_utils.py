from pymongo import MongoClient, UpdateOne
from bson import ObjectId
import logging
from typing import List, Tuple, Union, Dict, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 연결
try:
    client = MongoClient(
        "mongodb+srv://PASSWORD",
        serverSelectionTimeoutMS=5000
    )
    client.admin.command('ping')  # 연결 테스트
    db = client["news_politics"]
    collections = db.list_collection_names()  # 컬렉션 이름 리스트 가져오기

    all_documents = []
    for col_name in collections:
        collection = db[col_name]
        docs = list(collection.find())  # 해당 컬렉션 모든 문서 조회
        all_documents.extend(docs)  # 전체 문서 리스트에 추가

    print(f"총 문서 수: {len(all_documents)}")
    # all_documents 안에 news_politics DB 내 모든 컬렉션 문서들이 들어있음
    
    #db = client["news_politics"]
    #collection = db["2025.06.09"]


    logger.info("✅ MongoDB 연결 성공")
except Exception as e:
    logger.error(f"❌ MongoDB 연결 실패: {e}")
    raise


# 확률값이 없는 뉴스 가져오기
def get_news_without_probability(limit: Optional[int] = None) -> List[Dict]:
    try:
        query = {"mismatch_probability": {"$exists": False}}
        cursor = collection.find(query, {"_id": 1, "title": 1, "body": 1})
        if limit:
            cursor = cursor.limit(limit)
        news_list = list(cursor)
        logger.info(f"📥 확률값 없는 뉴스 {len(news_list)}개 조회")
        return news_list
    except Exception as e:
        logger.error(f"❌ 뉴스 조회 실패: {e}")
        return []


# 모든 뉴스 가져오기
"""
def get_all_news(limit: Optional[int] = None) -> List[Dict]:
    try:
        cursor = collection.find({}, {"_id": 1, "title": 1, "body": 1, "mismatch_probability": 1, "URL": 1, "date": 1, "media":1, "like_count":1, "comment_count":1 })
        if limit:
            cursor = cursor.limit(limit)
        news_list = list(cursor)
        logger.info(f"📥 전체 뉴스 {len(news_list)}개 조회")
        return news_list
    except Exception as e:
        logger.error(f"❌ 전체 뉴스 조회 실패: {e}")
        return []
"""
def get_all_news(limit: Optional[int] = None) -> List[Dict]:
    all_news = []
    try:
        for col_name in collections:
            collection = db[col_name]
            cursor = collection.find({}, {"_id": 1, "title": 1, "body": 1, "mismatch_probability": 1,
                                          "URL": 1, "date": 1, "media":1, "like_count":1, "comment_count":1})
            if limit:
                cursor = cursor.limit(limit)
            all_news.extend(list(cursor))
        logger.info(f"📥 전체 뉴스 {len(all_news)}개 조회")
        return all_news
    except Exception as e:
        logger.error(f"❌ 전체 뉴스 조회 실패: {e}")
        return []


# 단일 뉴스 업데이트
def update_news_probability(news_id: Union[str, ObjectId], prob: float) -> bool:
    try:
        if isinstance(news_id, str):
            news_id = ObjectId(news_id)

        result = collection.update_one(
            {"_id": news_id},
            {"$set": {"mismatch_probability": prob}}
        )

        if result.modified_count > 0:
            logger.info(f"✅ 뉴스 {news_id} 확률값 업데이트 완료: {prob:.4f}")
            return True
        else:
            logger.warning(f"⚠️ 뉴스 {news_id} 업데이트 실패 (변경 없음)")
            return False
    except Exception as e:
        logger.error(f"❌ 뉴스 {news_id} 확률 업데이트 실패: {e}")
        return False


# 배치 업데이트
def batch_update_probabilities(news_prob_list: List[Tuple[Union[str, ObjectId], float]]) -> int:
    try:
        operations = []
        for news_id, prob in news_prob_list:
            try:
                if isinstance(news_id, str):
                    news_id = ObjectId(news_id)
                operations.append(UpdateOne(
                    {"_id": news_id},
                    {"$set": {"mismatch_probability": prob}}
                ))
            except Exception as conv_err:
                logger.warning(f"⚠️ ID 변환 실패로 건너뜀: {news_id} ({conv_err})")
                continue

        if not operations:
            logger.warning("⚠️ 배치 업데이트할 문서가 없습니다.")
            return 0

        result = collection.bulk_write(operations)
        logger.info(f"✅ 배치 업데이트 완료: {result.modified_count}개 문서 수정")
        return result.modified_count
    except Exception as e:
        logger.error(f"❌ 배치 업데이트 실패: {e}")
        return 0


# 통계 정보
def get_collection_stats() -> Optional[Dict[str, Union[int, float]]]:
    try:
        total_count = collection.count_documents({})
        with_prob_count = collection.count_documents({"mismatch_probability": {"$exists": True}})
        without_prob_count = total_count - with_prob_count
        completion_rate = (with_prob_count / total_count * 100) if total_count else 0

        stats = {
            "total_news": total_count,
            "with_probability": with_prob_count,
            "without_probability": without_prob_count,
            "completion_rate": completion_rate
        }

        logger.info(
            f"📊 통계 - 전체: {total_count}, 있음: {with_prob_count}, 없음: {without_prob_count}, 완료율: {completion_rate:.2f}%"
        )
        return stats
    except Exception as e:
        logger.error(f"❌ 통계 조회 실패: {e}")
        return None
