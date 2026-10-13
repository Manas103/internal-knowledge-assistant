import math

from assistant.dense_embed import DIM, embed_text


def test_embed_text_is_unit_normalized():
    idf = {"cache": 2.0, "memory": 1.5, "disaggregation": 3.0}
    vec = embed_text("cache memory disaggregation cache", idf)
    assert len(vec) == DIM
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 1e-9


def test_embed_text_empty_string_is_zero_vector():
    vec = embed_text("", {"a": 1.0})
    assert vec == [0.0] * DIM


def test_embed_text_is_deterministic_across_calls():
    idf = {"cxl": 2.0, "pcie": 1.0}
    v1 = embed_text("CXL and PCIe interoperate", idf)
    v2 = embed_text("CXL and PCIe interoperate", idf)
    assert v1 == v2


def test_shared_rare_term_gives_smaller_angle_than_unrelated_text():
    """Two sentences sharing one high-idf term but no other tokens should be
    closer (smaller angle / larger dot product) than two sentences sharing
    nothing at all, the property that makes dense retrieval worth fusing in."""
    idf = {"disaggregation": 5.0, "alpha": 0.1, "beta": 0.1, "gamma": 0.1, "delta": 0.1}
    a = embed_text("alpha disaggregation", idf)
    b = embed_text("beta disaggregation", idf)
    c = embed_text("gamma delta", idf)

    dot_ab = sum(x * y for x, y in zip(a, b))
    dot_ac = sum(x * y for x, y in zip(a, c))
    assert dot_ab > dot_ac
