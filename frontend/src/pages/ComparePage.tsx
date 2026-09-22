import { useState } from "react";
import { api, ApiError } from "../api/client";
import type { CompareResponse } from "../api/types";
import { CompareSlotPicker } from "../components/CompareSlotPicker";
import { ComparisonView } from "../components/ComparisonView";
import { ErrorBanner } from "../components/ErrorBanner";
import { LoadingSpinner } from "../components/LoadingSpinner";

interface Selection {
  ticker: string;
  accessionNumber: string;
}

export function ComparePage() {
  const [slotA, setSlotA] = useState<Selection | null>(null);
  const [slotB, setSlotB] = useState<Selection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  async function handleCompare() {
    if (!slotA || !slotB) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const response = await api.compare(
        slotA.ticker,
        slotA.accessionNumber,
        slotB.ticker,
        slotB.accessionNumber,
      );
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong comparing these filings.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-10 px-6 py-8">
      <div>
        <h2 className="text-sm font-semibold tracking-wide text-text-primary uppercase">
          Compare Two Filings
        </h2>
        <p className="mt-1 text-sm text-text-secondary">
          Select an earlier filing (A) and a later filing (B) from the same or different companies to
          see what changed.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <CompareSlotPicker
          label="Filing A (earlier)"
          onSelect={(ticker, accessionNumber) => setSlotA({ ticker, accessionNumber })}
        />
        <CompareSlotPicker
          label="Filing B (later)"
          onSelect={(ticker, accessionNumber) => setSlotB({ ticker, accessionNumber })}
        />
      </div>

      <button
        onClick={handleCompare}
        disabled={!slotA || !slotB || loading}
        className="rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Comparing…" : "Compare Filings"}
      </button>

      {error && <ErrorBanner message={error} />}
      {loading && <LoadingSpinner label="Analyzing both filings and generating the comparison" />}
      {result && <ComparisonView comparison={result.comparison} />}
    </div>
  );
}
