"use client";

import { FormEvent, useState } from "react";

const suggestions = [
  "Summarize the key risks in launching a new product.",
  "Turn these rough notes into a clear project update.",
  "Explain this concept as if I am new to the topic.",
];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt || loading) return;

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: cleanPrompt }),
      });
      const data = (await response.json()) as { output?: string; error?: string };
      if (!response.ok) throw new Error(data.error || "The model could not respond.");
      setAnswer(data.output || "No response was returned.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <nav className="nav" aria-label="Main navigation">
        <a className="brand" href="#top" aria-label="Promptly home">
          <span className="brand-mark">P</span>
          <span>Promptly</span>
        </a>
        <span className="status"><i /> Model gateway ready</span>
      </nav>

      <section className="hero" id="top">
        <div className="eyebrow"><span>✦</span> Your AI workspace</div>
        <h1>Ask clearly.<br /><em>Get useful answers.</em></h1>
        <p className="intro">A simple, focused space to work with your team&apos;s language model. Type a question, add context, and get a response in seconds.</p>
      </section>

      <section className="workspace" aria-label="AI prompt workspace">
        <div className="input-panel">
          <div className="panel-heading">
            <div><span className="step">01</span><h2>What can we help with?</h2></div>
            <span className="limit">{prompt.length} / 4,000</span>
          </div>
          <form onSubmit={submit}>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value.slice(0, 4000))}
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Describe what you need, include any helpful context…"
              aria-label="Your prompt"
              rows={8}
            />
            <div className="form-footer">
              <span className="hint"><kbd>Ctrl</kbd> + <kbd>Enter</kbd> to send</span>
              <button type="submit" disabled={!prompt.trim() || loading}>
                {loading ? "Thinking…" : "Generate response"}<span aria-hidden="true">→</span>
              </button>
            </div>
          </form>
        </div>

        <div className={`output-panel ${answer || error || loading ? "active" : ""}`} aria-live="polite">
          <div className="panel-heading">
            <div><span className="step">02</span><h2>Response</h2></div>
            {answer && <button className="copy" onClick={() => navigator.clipboard.writeText(answer)}>Copy</button>}
          </div>
          <div className="response-body">
            {loading && <div className="thinking"><span /><span /><span /> Working on your response</div>}
            {error && <p className="error">{error}</p>}
            {answer && <p className="answer">{answer}</p>}
            {!loading && !error && !answer && (
              <div className="empty-state"><div className="spark">✦</div><p>Your response will appear here.</p><span>Send a prompt to get started.</span></div>
            )}
          </div>
        </div>
      </section>

      <section className="suggestions">
        <p>Not sure where to start? Try one of these</p>
        <div className="suggestion-grid">
          {suggestions.map((suggestion) => <button key={suggestion} onClick={() => setPrompt(suggestion)}>{suggestion}<span>↗</span></button>)}
        </div>
      </section>

      <footer><span>Promptly</span><p>Your input is sent securely through the server and is not stored by this website.</p></footer>
    </main>
  );
}
