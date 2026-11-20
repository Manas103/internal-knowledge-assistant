// The deployed-shape query path for the Knowledge-Gap Audit: Workers AI
// embeds the question, Vectorize finds the nearest passage, this handler
// returns the same citation shape assistant/answer.py returns. Not
// deployed or exercised live in this build (no Cloudflare account bound in
// this environment); every measured number in the README comes from the
// Python BM25 path in ../ingest.py and ../labeling.py, not from this file.
import { citationFromMatches, type VectorizeMatch } from "./citation.js";

export interface Env {
  AI: Ai;
  VECTORIZE_INDEX: VectorizeIndex;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const question = url.searchParams.get("q");
    if (!question) {
      return new Response(JSON.stringify({ error: "missing ?q=" }), { status: 400 });
    }

    const embedding = await env.AI.run("@cf/baai/bge-base-en-v1.5", { text: [question] });
    const vector = (embedding as { data: number[][] }).data[0];
    const result = await env.VECTORIZE_INDEX.query(vector, { topK: 3, returnMetadata: "all" });

    const matches: VectorizeMatch[] = result.matches.map((m) => ({
      id: m.id,
      score: m.score,
      metadata: m.metadata as VectorizeMatch["metadata"],
    }));

    return new Response(JSON.stringify(citationFromMatches(matches)), {
      headers: { "content-type": "application/json" },
    });
  },
};
