from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from maintenance_record import load_maintenance_records


def retrieve_similar_records(
    equipment_type: str,
    fault_description: str,
    top_k: int = 2,
    min_score: float = 0.05,
) -> list[tuple[dict, float]]:
    """从相同设备类型的历史记录中返回相似案例和分数。"""
    if not fault_description.strip() or top_k <= 0:
        return []
    records = [
        record for record in load_maintenance_records()
        if record.get("equipment_type") == equipment_type
        and record.get("fault_description", "").strip()
    ]
    if not records:
        return []
    texts = [record["fault_description"] for record in records]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    record_vectors = vectorizer.fit_transform(texts)
    query_vector = vectorizer.transform([fault_description])
    scores = cosine_similarity(query_vector, record_vectors)[0]
    ranked_indexes = scores.argsort()[::-1][:top_k]
    return [(records[index], float(scores[index])) for index in ranked_indexes if scores[index] >= min_score]
