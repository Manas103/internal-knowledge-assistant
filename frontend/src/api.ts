export interface AskResponse {
  answer_text: string;
  cited_doc_id: string;
  cited_page_number: number;
  confidence: number;
}

export async function askQuestion(question: string, baseUrl = ""): Promise<AskResponse> {
  const resp = await fetch(`${baseUrl}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!resp.ok) {
    throw new Error(`ask failed: ${resp.status}`);
  }
  return (await resp.json()) as AskResponse;
}
