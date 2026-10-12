import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";

function mockFetchOnce(body: unknown, ok = true) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok,
      status: ok ? 200 : 500,
      json: async () => body,
    })
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("asks a question and shows the citation", async () => {
    mockFetchOnce({
      answer_text: "Flow control credits are returned... (source: Fixture Spec B, page 1)",
      cited_doc_id: "doc-b",
      cited_page_number: 1,
      confidence: 5.2,
    });
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("Question"), "What is flow control?");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByText(/Citation: doc-b, page 1/)).toBeInTheDocument();
  });

  it("records a reviewer decision into the session history table", async () => {
    mockFetchOnce({
      answer_text: "...",
      cited_doc_id: "doc-a",
      cited_page_number: 2,
      confidence: 3.1,
    });
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("Question"), "What is CXL memory pooling?");
    await user.click(screen.getByRole("button", { name: "Ask" }));
    await user.click(await screen.findByRole("button", { name: "Send as-is" }));

    expect(screen.getByText("sent_unedited")).toBeInTheDocument();
    expect(screen.getByText("What is CXL memory pooling?")).toBeInTheDocument();
  });

  it("surfaces a fetch failure as an alert instead of silently discarding it", async () => {
    mockFetchOnce({}, false);
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("Question"), "anything");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
