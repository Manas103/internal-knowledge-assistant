// Pure logic, factored out of the fetch handler so it can be unit tested
// without a live AI binding or Vectorize index (neither is bound in this
// build environment; see README Honest framing). This is the deployed-shape
// equivalent of assistant/answer.py's extractive drafting: no generative
// model writes the answer text, the top match's own metadata is quoted.

export interface VectorizeMatch {
  id: string;
  score: number;
  metadata: {
    doc_id: string;
    page_number: number;
    title: string;
    snippet: string;
  };
}

export interface Citation {
  answerText: string;
  citedDocId: string;
  citedPageNumber: number;
  confidence: number;
}

export function citationFromMatches(matches: VectorizeMatch[]): Citation {
  if (matches.length === 0) {
    return { answerText: "No supporting passage was found for this question.", citedDocId: "", citedPageNumber: -1, confidence: 0 };
  }
  const top = matches[0];
  const runnerUpScore = matches.length > 1 ? matches[1].score : 0;
  return {
    answerText: `${top.metadata.snippet} (source: ${top.metadata.title}, page ${top.metadata.page_number})`,
    citedDocId: top.metadata.doc_id,
    citedPageNumber: top.metadata.page_number,
    confidence: top.score - runnerUpScore,
  };
}
