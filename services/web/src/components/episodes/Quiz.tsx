"use client";

import { useState } from "react";
import type { EpisodeQuiz } from "@/lib/contract";

export function Quiz({ quiz }: { quiz: EpisodeQuiz }) {
  const [shown, setShown] = useState(false);
  return (
    <section aria-labelledby="quiz-heading" className="card p-6">
      <div className="eyebrow cat-text mb-2" style={{ ["--cat" as string]: "var(--gold)" }}>Daily quiz</div>
      <h2 id="quiz-heading" className="text-lg font-semibold">{quiz.question}</h2>
      <ul className="mt-4 grid gap-2 sm:grid-cols-3">
        {quiz.options.map((o, i) => (
          <li
            key={o}
            className={`rounded-lg border px-4 py-3 text-sm ${shown && quiz.answer === o ? "border-up bg-up/10" : "border-line"}`}
          >
            <span className="num mr-2 text-muted">{String.fromCharCode(65 + i)}</span>
            {o}
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => setShown((v) => !v)}
        aria-expanded={shown}
        className="mt-4 rounded-lg border border-line-strong px-4 py-2 text-sm font-medium hover:bg-surface-2"
      >
        {shown ? "Hide answer" : "Reveal answer"}
      </button>
      {shown && (
        <p className="mt-3 text-sm" role="status">
          <strong>Answer: {quiz.answer ?? quiz.reveal}.</strong>{" "}
          {quiz.answer ? <span className="text-muted">{quiz.reveal}</span> : null}
        </p>
      )}
    </section>
  );
}
