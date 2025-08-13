import os
import asyncio
from typing import List, Optional, Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection, utility
)
import google.generativeai as genai

# =========================
# 환경 설정 로드
# =========================
load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "counseling_records_v4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_EMBED = os.getenv("GEMINI_MODEL_EMBED", "models/text-embedding-004")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))  

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=GEMINI_API_KEY)

router = APIRouter()

# =========================
# Pydantic 모델 (간단화)
# =========================
TitleStr = Annotated[str, Field(min_length=1, max_length=256)]
LongText = Annotated[str, Field(min_length=1, max_length=10000)]
DateStr = Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]
Name = Annotated[str, Field(min_length=1, max_length=50)]
WorryTagsStr = Annotated[str, Field(min_length=0, max_length=500)]
ShortID = Annotated[str, Field(min_length=1, max_length=100)]

class AddRecordRequest(BaseModel):
    title: Optional[TitleStr] = None
    student_query: LongText
    counselor_answer: LongText
    teacher_name: Optional[Name] = None
    student_name: Optional[Name] = None
    date: DateStr
    # 이미지 스키마에 맞춰 worry_tags는 단일 VarChar(콤마 구분 스트링)로 둠
    worry_tags: Optional[WorryTagsStr] = ""

class SearchRecordsRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=1000)]
    worry_tag: Optional[Annotated[str, Field(max_length=100)]] = None
    top_k: Annotated[int, Field(default=5, ge=1, le=20)]

# =========================
# 전역
# =========================
_collection: Optional[Collection] = None
_embedding_semaphore = asyncio.Semaphore(5)

# run_in_executor 래퍼
async def _run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

# Gemini 임베딩 (문서/쿼리용)
async def get_gemini_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        raise ValueError("빈 문자열은 임베딩할 수 없습니다.")
    async with _embedding_semaphore:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await _run_blocking(
                    genai.embed_content,
                    model=GEMINI_MODEL_EMBED,
                    content=text,
                    task_type="retrieval_document"
                )
                if isinstance(result, dict) and "embedding" in result:
                    return result["embedding"]
                data = result.get("data") if isinstance(result, dict) else None
                if data and isinstance(data, list) and len(data) > 0:
                    emb = data[0].get("embedding") if isinstance(data[0], dict) else None
                    if emb:
                        return emb
                raise RuntimeError("임베딩 응답에서 벡터를 찾을 수 없습니다.")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Gemini API 호출 실패: {e}")
                await asyncio.sleep(2 ** attempt)

async def get_gemini_query_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        raise ValueError("빈 검색 쿼리입니다.")
    async with _embedding_semaphore:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await _run_blocking(
                    genai.embed_content,
                    model=GEMINI_MODEL_EMBED,
                    content=text,
                    task_type="retrieval_query"
                )
                if isinstance(result, dict) and "embedding" in result:
                    return result["embedding"]
                data = result.get("data") if isinstance(result, dict) else None
                if data and isinstance(data, list) and len(data) > 0:
                    emb = data[0].get("embedding") if isinstance(data[0], dict) else None
                    if emb:
                        return emb
                raise RuntimeError("임베딩 응답에서 벡터를 찾을 수 없습니다.")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Gemini 검색 임베딩 실패: {e}")
                await asyncio.sleep(2 ** attempt)

# =========================
# Milvus 초기화 (이미지 스키마 반영)
# 필드 순서(중요): id(Int64, auto_id=True), embedding, title, student_query,
# counselor_answer, date, teacher_name, student_name, worry_tags
# =========================
def get_milvus_collection() -> Collection:
    global _collection
    if _collection is None:
        _collection = init_milvus_collection()
    return _collection

def init_milvus_collection() -> Collection:
    try:
        if not connections.has_connection("default"):
            connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, timeout=30)

        if not utility.has_collection(MILVUS_COLLECTION_NAME):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="student_query", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="counselor_answer", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="teacher_name", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="student_name", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="worry_tags", dtype=DataType.VARCHAR, max_length=500),
            ]
            schema = CollectionSchema(fields=fields, description="상담 기록 - 이미지 기반 스키마")
            col = Collection(name=MILVUS_COLLECTION_NAME, schema=schema)

            # embedding 인덱스 (기존과 동일하게 IVF_FLAT + COSINE, nlist=1024)
            index_params = {"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 1024}}
            col.create_index(field_name="embedding", index_params=index_params)
            col.load()
            print(f"Collection '{MILVUS_COLLECTION_NAME}' created and loaded (dim={EMBEDDING_DIM})")
            return col
        else:
            col = Collection(name=MILVUS_COLLECTION_NAME)
            col.load()
            return col
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Milvus 초기화 실패: {str(e)}")

@router.post("/add-record/")
async def add_record(req: AddRecordRequest):
    try:
        collection = get_milvus_collection()
        emb = await get_gemini_embedding(req.student_query)

        # insertion columns must follow the schema order EXCLUDING auto id column
        insert_data = [
            [emb],                        # embedding
            [req.title or ""],            # title
            [req.student_query],          # student_query
            [req.counselor_answer],       # counselor_answer
            [req.date],                   # date
            [req.teacher_name or ""],     # teacher_name
            [req.student_name or ""],     # student_name
            [req.worry_tags or ""],       # worry_tags (single VarChar, comma-separated if multiple)
        ]

        # Call collection.insert() to get the result.
        insert_result = collection.insert(insert_data)

        # Safely extract primary keys, which is a simple list.
        generated_ids = list(insert_result.primary_keys) if insert_result else []

        # Return a simple dictionary containing only serializable data.
        return {
            "status": "success",
            "generated_ids": generated_ids,
            "embedding_dim": len(emb)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"레코드 추가 실패: {str(e)}")


@router.post("/bulk-add-records/")
async def bulk_add_records(records: List[AddRecordRequest]):
    try:
        collection = get_milvus_collection()
        batch_data = [[], [], [], [], [], [], [], []]  # embedding, title, student_query, counselor_answer, date, teacher_name, student_name, worry_tags
        errors = []
        for i, req in enumerate(records):
            try:
                emb = await get_gemini_embedding(req.student_query)
                batch_data[0].append(emb)
                batch_data[1].append(req.title or "")
                batch_data[2].append(req.student_query)
                batch_data[3].append(req.counselor_answer)
                batch_data[4].append(req.date)
                batch_data[5].append(req.teacher_name or "")
                batch_data[6].append(req.student_name or "")
                batch_data[7].append(req.worry_tags or "")
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        if batch_data[0]:
            insert_result = collection.insert(batch_data)
            collection.flush()

        return {"status": "success", "total": len(records), "successful": len(batch_data[0]), "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일괄 추가 실패: {str(e)}")

@router.post("/search-records/")
async def search_records(req: SearchRecordsRequest):
    try:
        collection = get_milvus_collection()
        emb = await get_gemini_query_embedding(req.query)
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        expr = None
        if req.worry_tag:
            # VarChar 기반 필드에 부분문자열 검색 형태 사용 (LIKE)
            expr = f'worry_tags like "%{req.worry_tag}%"'

        results = collection.search(
            data=[emb],
            anns_field="embedding",
            param=search_params,
            limit=req.top_k,
            expr=expr,
            output_fields=["id", "title", "student_query", "counselor_answer", "date", "teacher_name", "student_name", "worry_tags"],
        )

        output = []
        for hit in results[0]:
            entity_data = {field.name: field.value for field in hit.fields}
            output.append({
                "id": entity_data.get("id"),
                "title": entity_data.get("title"),
                "student_query": entity_data.get("student_query"),
                "counselor_answer": entity_data.get("counselor_answer"),
                "date": entity_data.get("date"),
                "teacher_name": entity_data.get("teacher_name"),
                "student_name": entity_data.get("student_name"),
                "worry_tags": entity_data.get("worry_tags"),
                "similarity": round(1 - hit.distance, 4),
            })

        return {"status": "success", "total_found": len(output), "results": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")


@router.get("/collection-stats/")
def get_collection_stats():
    try:
        collection = get_milvus_collection()
        return {
            "status": "success",
            "collection_name": MILVUS_COLLECTION_NAME,
            "total_entities": collection.num_entities,
            "has_index": collection.has_index(),
            "is_loaded": True,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 앱 생명주기
@router.on_event("startup")
async def startup_event():
    try:
        get_milvus_collection()
        print("✅ Milvus 연결 및 컬렉션 초기화 완료")
    except Exception as e:
        print(f"❌ Milvus 초기화 실패: {e}")

@router.on_event("shutdown")
async def shutdown_event():
    try:
        if connections.has_connection("default"):
            connections.disconnect("default")
        print("✅ Milvus 연결 정리 완료")
    except Exception as e:
        print(f"❌ Milvus 연결 정리 실패: {e}")