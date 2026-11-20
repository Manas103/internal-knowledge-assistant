import { describe, expect, it } from "vitest";
import { citationFromMatches, type VectorizeMatch } from "../src/citation.js";

function match(id: string, score: number, docId: string, page: number): VectorizeMatch {
  return { id, score, metadata: { doc_id: docId, page_number: page, title: `Title ${docId}`, snippet: `Snippet for ${docId}` } };
}

describe("citationFromMatches", () => {
  it("returns a no-match response for an empty result set", () => {
    const result = citationFromMatches([]);
    expect(result.citedDocId).toBe("");
    expect(result.citedPageNumber).toBe(-1);
    expect(result.confidence).toBe(0);
  });

  it("cites the top match and reports the score margin as confidence", () => {
    const result = citationFromMatches([match("a", 0.9, "docs-vectorize", 2), match("b", 0.4, "docs-r2", 1)]);
    expect(result.citedDocId).toBe("docs-vectorize");
    expect(result.citedPageNumber).toBe(2);
    expect(result.confidence).toBeCloseTo(0.5, 5);
    expect(result.answerText).toContain("docs-vectorize");
  });

  it("reports 0 confidence with only one match (no runner-up to compare against)", () => {
    const result = citationFromMatches([match("a", 0.7, "docs-workers-ai", 1)]);
    expect(result.confidence).toBe(0.7);
  });
});
