import { useEffect, useState } from "react";
import { Draft, GateStats, fetchPendingReviews, fetchStats, resolveReview } from "../api";

export function ReviewQueue() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [stats, setStats] = useState<GateStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [pending, gateStats] = await Promise.all([fetchPendingReviews(), fetchStats()]);
      setDrafts(pending);
      setStats(gateStats);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function decide(id: string, decision: "approved" | "rejected") {
    await resolveReview(id, decision);
    await load();
  }

  if (error) return <p role="alert">{error}</p>;

  return (
    <div>
      <h1>Withheld Requests Awaiting Human Review</h1>
      {stats && (
        <dl data-testid="gate-stats">
          <dt>Total requests</dt>
          <dd>{stats.totalRequests}</dd>
          <dt>Published</dt>
          <dd>{stats.publishedCount}</dd>
          <dt>Withheld</dt>
          <dd>{stats.withheldCount}</dd>
          <dt>Citation accuracy</dt>
          <dd>{(stats.citationAccuracy * 100).toFixed(2)}%</dd>
        </dl>
      )}
      {drafts.length === 0 && <p>No pending reviews.</p>}
      <ul>
        {drafts.map((draft) => (
          <li key={draft.id} data-testid="review-item">
            <p>{draft.requestText}</p>
            <p>confidence: {draft.confidence.toFixed(3)}</p>
            <button onClick={() => decide(draft.id, "approved")}>Approve as grounded</button>
            <button onClick={() => decide(draft.id, "rejected")}>Confirm ungrounded</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
