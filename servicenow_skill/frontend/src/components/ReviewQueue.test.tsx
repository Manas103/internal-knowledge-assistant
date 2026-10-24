import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewQueue } from "./ReviewQueue";

function mockGraphQlResponses(responses: unknown[]) {
  let call = 0;
  globalThis.fetch = vi.fn(async () => {
    const data = responses[Math.min(call, responses.length - 1)];
    call++;
    return {
      ok: true,
      json: async () => ({ data }),
    } as Response;
  });
}

describe("ReviewQueue", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders withheld drafts and gate stats from the GraphQL backend", async () => {
    mockGraphQlResponses([
      {
        pendingReviews: [
          {
            id: "1",
            requestId: "REQ-U-0000",
            requestText: "A user asks about cafeteria lunch menu.",
            citedArticleId: null,
            confidence: 0.1,
            grounded: false,
            status: "WITHHELD",
            reviewerDecision: null,
          },
        ],
      },
      { stats: { totalRequests: 605, publishedCount: 457, withheldCount: 148, citationAccuracy: 1.0 } },
    ]);

    render(<ReviewQueue />);

    await waitFor(() => expect(screen.getByText(/cafeteria lunch menu/)).toBeInTheDocument());
    expect(screen.getByText("605")).toBeInTheDocument();
    expect(screen.getByText("100.00%")).toBeInTheDocument();
  });

  it("calls resolveReview and reloads the queue when a reviewer approves a draft", async () => {
    mockGraphQlResponses([
      {
        pendingReviews: [
          {
            id: "1",
            requestId: "REQ-U-0000",
            requestText: "A user asks about cafeteria lunch menu.",
            citedArticleId: null,
            confidence: 0.1,
            grounded: false,
            status: "WITHHELD",
            reviewerDecision: null,
          },
        ],
      },
      { stats: { totalRequests: 605, publishedCount: 457, withheldCount: 148, citationAccuracy: 1.0 } },
      { resolveReview: { id: "1", requestId: "REQ-U-0000", requestText: "x", citedArticleId: null, confidence: 0.1, grounded: false, status: "REVIEWED", reviewerDecision: "approved" } },
      { pendingReviews: [] },
      { stats: { totalRequests: 605, publishedCount: 457, withheldCount: 148, citationAccuracy: 1.0 } },
    ]);

    render(<ReviewQueue />);
    await waitFor(() => expect(screen.getByTestId("review-item")).toBeInTheDocument());

    await userEvent.click(screen.getByText("Approve as grounded"));

    await waitFor(() => expect(screen.getByText("No pending reviews.")).toBeInTheDocument());
  });
});
