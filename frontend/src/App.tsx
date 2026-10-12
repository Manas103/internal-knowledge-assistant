import { useState } from "react";
import { askQuestion, type AskResponse } from "./api";

type Outcome = "sent_unedited" | "edited" | "escalated";

interface HistoryEntry {
  question: string;
  draft: AskResponse;
  outcome: Outcome;
}

// The point of this screen is not the Q&A box, it is the three decision buttons: this
// project's resume claim is adoption instrumentation, not answer quality alone, so every
// reviewer decision (not just the draft) is kept in the visible history table below.
export function App() {
  const [question, setQuestion] = useState("");
  const [draft, setDraft] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  async function handleAsk() {
    setError(null);
    try {
      const result = await askQuestion(question);
      setDraft(result);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function recordOutcome(outcome: Outcome) {
    if (!draft) return;
    setHistory((prev) => [...prev, { question, draft, outcome }]);
    setDraft(null);
    setQuestion("");
  }

  return (
    <main>
      <h1>Internal Knowledge Assistant</h1>
      <label htmlFor="question-input">Question</label>
      <input
        id="question-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about PCIe or CXL"
      />
      <button onClick={handleAsk} disabled={!question.trim()}>
        Ask
      </button>
      {error && <p role="alert">{error}</p>}

      {draft && (
        <section aria-label="draft-answer">
          <p>{draft.answer_text}</p>
          <p>
            Citation: {draft.cited_doc_id}, page {draft.cited_page_number} (confidence{" "}
            {draft.confidence.toFixed(2)})
          </p>
          <button onClick={() => recordOutcome("sent_unedited")}>Send as-is</button>
          <button onClick={() => recordOutcome("edited")}>Edit before sending</button>
          <button onClick={() => recordOutcome("escalated")}>Escalate to reviewer</button>
        </section>
      )}

      <h2>Session history</h2>
      <table>
        <thead>
          <tr>
            <th>Question</th>
            <th>Citation</th>
            <th>Outcome</th>
          </tr>
        </thead>
        <tbody>
          {history.map((entry, i) => (
            <tr key={i}>
              <td>{entry.question}</td>
              <td>
                {entry.draft.cited_doc_id}, page {entry.draft.cited_page_number}
              </td>
              <td>{entry.outcome}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
