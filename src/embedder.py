# embeds fund descriptions with sentence-transformers, stores/searches them in chromadb
# see data/funds/fund_descriptions.json _meta for the synthetic data disclaimer

import json
import os

import chromadb
from sentence_transformers import SentenceTransformer

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "funds", "fund_descriptions.json")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
COLLECTION_NAME = "fund_catalogue"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small + fast, no gpu needed

_model = None  # loading this is slow, only want to do it once


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def load_funds(path=DATA_PATH):
    # file is {_meta, funds: [...]} now, just want the array
    with open(path) as f:
        data = json.load(f)
    return data["funds"]


def build_embedding_text(fund):
    # description alone isn't enough signal, category + risk words help matching
    return (
        f"{fund['fund_name']}. Category: {fund['cifsc_category'].replace('_', ' ')}. "
        f"Risk rating: {fund['risk_rating'].replace('_', ' ')}. "
        f"{fund['description']}"
    )


def get_client(persist_dir=CHROMA_DIR):
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def build_index(funds_path=DATA_PATH, persist_dir=CHROMA_DIR, rebuild=True):
    funds = load_funds(funds_path)
    client = get_client(persist_dir)

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # nothing to delete on first run

    # cosine since we're comparing direction of text vectors, not magnitude
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    model = get_model()
    documents = [build_embedding_text(f) for f in funds]
    embeddings = model.encode(documents, normalize_embeddings=True).tolist()  # batch encode, faster than looping

    collection.add(
        ids=[f["fund_id"] for f in funds],
        documents=documents,
        embeddings=embeddings,
        metadatas=[
            {
                "fund_name": f["fund_name"],
                "fund_family": f["fund_family"],
                "cifsc_category": f["cifsc_category"],
                "risk_rating": f["risk_rating"],
                "mer": f["mer"],
            }
            for f in funds
        ],
    )

    return collection


def get_collection(persist_dir=CHROMA_DIR):
    # so callers don't have to check if the index exists yet
    client = get_client(persist_dir)
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        return build_index(persist_dir=persist_dir)


def semantic_search(query, n_results=5, eligible_categories=None, persist_dir=CHROMA_DIR):
    # eligible_categories comes from rules.py - lets us search only within funds that already passed the hard suitability filter
    collection = get_collection(persist_dir)
    model = get_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    where = {"cifsc_category": {"$in": eligible_categories}} if eligible_categories else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where,
    )

    matches = []
    for i in range(len(results["ids"][0])):
        # chroma nests results in an extra list for batch-query support, we only ever send one query so everything we want is at index [0]
        matches.append(
            {
                "fund_id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "similarity": 1 - results["distances"][0][i],  # flip so higher = better match
                **results["metadatas"][0][i],
            }
        )
    return matches


if __name__ == "__main__":
    print(f"building index from {DATA_PATH} ...")
    collection = build_index()
    print(f"indexed {collection.count()} funds into '{COLLECTION_NAME}' at {CHROMA_DIR}\n")

    sample_queries = [
        "I want maximum long-term growth for retirement and am comfortable with big swings in value",
        "I need stable monthly income with very little risk as I am retired and depend on this money",
        "I want to grow my savings aggressively over the next 25 years and don't mind volatility",
    ]

    for q in sample_queries:
        print(f"query: {q}")
        for m in semantic_search(q, n_results=3):
            print(f"  {m['fund_id']:8s} {m['fund_name']:42s} [{m['cifsc_category']:22s}] sim={m['similarity']:.3f}")
        print()