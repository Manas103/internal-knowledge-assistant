// Thin GraphQL client for the Spring for GraphQL backend in ../../backend. The
// queue never decides whether a draft was grounded; it only renders what the
// deploy-blocking evaluator already decided and posts a human's decision back
// through the resolveReview mutation.

export interface Draft {
  id: string;
  requestId: string;
  requestText: string;
  citedArticleId: string | null;
  confidence: number;
  grounded: boolean;
  status: string;
  reviewerDecision: string | null;
}

export interface GateStats {
  totalRequests: number;
  publishedCount: number;
  withheldCount: number;
  citationAccuracy: number;
}

const GRAPHQL_URL = import.meta.env.VITE_GRAPHQL_URL ?? "http://127.0.0.1:8080/graphql";

async function graphql<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) throw new Error(`GraphQL request failed: ${res.status}`);
  const body = await res.json();
  if (body.errors) throw new Error(body.errors.map((e: { message: string }) => e.message).join("; "));
  return body.data as T;
}

export async function fetchPendingReviews(): Promise<Draft[]> {
  const data = await graphql<{ pendingReviews: Draft[] }>(
    `query { pendingReviews { id requestId requestText citedArticleId confidence grounded status reviewerDecision } }`,
  );
  return data.pendingReviews;
}

export async function fetchStats(): Promise<GateStats> {
  const data = await graphql<{ stats: GateStats }>(
    `query { stats { totalRequests publishedCount withheldCount citationAccuracy } }`,
  );
  return data.stats;
}

export async function resolveReview(id: string, decision: string): Promise<Draft> {
  const data = await graphql<{ resolveReview: Draft }>(
    `mutation($id: ID!, $decision: String!) {
      resolveReview(id: $id, decision: $decision) { id requestId requestText citedArticleId confidence grounded status reviewerDecision }
    }`,
    { id, decision },
  );
  return data.resolveReview;
}
