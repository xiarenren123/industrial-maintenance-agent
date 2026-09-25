from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def retrieve_relevant_chunks(
    query: str, chunks: list[str], top_k: int = 2, min_score: float = 0.05
) -> list[tuple[str, float]]:
    """返回与问题最相关的文本块和相似度分数。"""
    if not query.strip() or not chunks or top_k <= 0:
        return []

    # 使用字符片段，中文不需要额外的分词工具也能进行匹配。
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    chunk_vectors = vectorizer.fit_transform(chunks)
    query_vector = vectorizer.transform([query])

    # 余弦相似度越大，表示文本块和用户问题越相似。
    scores = cosine_similarity(query_vector, chunk_vectors)[0]
    ranked_indexes = scores.argsort()[::-1][:top_k]
    return [
        (chunks[index], float(scores[index]))
        for index in ranked_indexes
        if scores[index] >= min_score
    ]
