# import_milvus_fixed.py
import os, csv, asyncio
from dotenv import load_dotenv
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
MILVUS_HOST = os.getenv("MILVUS_HOST","localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT","19530"))
COL_NAME = os.getenv("MILVUS_COLLECTION_NAME","connect_test_v1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_DIM = int(os.getenv("EMBEDDING_DIM","768"))
CSV_PATH = "data/milvus_input.csv"
BATCH = 64

def ensure_collection():
    if not connections.has_connection("default"):
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, timeout=30)
    if not utility.has_collection(COL_NAME):
        fields = [
            FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=EMBED_DIM),
            FieldSchema("title", DataType.VARCHAR, max_length=256),
            FieldSchema("student_query", DataType.VARCHAR, max_length=10000),
            FieldSchema("counselor_answer", DataType.VARCHAR, max_length=10000),
            FieldSchema("date", DataType.VARCHAR, max_length=20),
            FieldSchema("teacher_name", DataType.VARCHAR, max_length=50),
            FieldSchema("student_name", DataType.VARCHAR, max_length=50),
            FieldSchema("worry_tags", DataType.VARCHAR, max_length=500),
        ]
        Collection(COL_NAME, CollectionSchema(fields)).create_index(
            field_name="embedding",
            index_params={"index_type":"IVF_FLAT","metric_type":"COSINE","params":{"nlist":1024}})
    col = Collection(COL_NAME); col.load(); return col

async def embed_batch(emb_client, texts):
    # emb_client must be created in same event loop
    return await emb_client.aembed_documents(texts)

async def main():
    if not GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY 필요")
    col = ensure_collection()

    # <-- 여기서 임베딩 클라이언트 생성 (반드시 async 루프 안에서) -->
    emb = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_MODEL_EMBED","models/text-embedding-004"),
        google_api_key=GEMINI_API_KEY,
        task_type="retrieval_document"
    )

    rows = []
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        texts = [r.get("student_query","") or "" for r in batch]
        vecs = await embed_batch(emb, texts)
        col.insert([
            vecs,
            [r.get("title","") for r in batch],
            [r.get("student_query","") for r in batch],
            [r.get("counselor_answer","") for r in batch],
            [r.get("date","") for r in batch],
            [r.get("teacher_name","") for r in batch],
            [r.get("student_name","") for r in batch],
            [r.get("worry_tags","") for r in batch],
        ])
        col.flush()
        print(f"Inserted {min(i+BATCH,len(rows))}/{len(rows)}")

if __name__ == "__main__":
    asyncio.run(main())
