import { useState } from "react";
import type { FormEvent } from "react";

const DEMO_TICKERS = ["AAPL", "NVDA", "AMD", "MSFT", "META"];

interface SearchBarProps {
  onSearch: (ticker: string) => void;
  loading?: boolean;
}

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const ticker = value.trim().toUpperCase();
    if (ticker) onSearch(ticker);
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter a ticker, e.g. AAPL, NVDA, AMD, MSFT"
          className="flex-1 rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none"
          autoCapitalize="characters"
          spellCheck={false}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>
      <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        <span>Try:</span>
        {DEMO_TICKERS.map((ticker) => (
          <button
            key={ticker}
            onClick={() => onSearch(ticker)}
            className="rounded-full border border-border px-2.5 py-1 font-mono-tabular transition hover:border-accent hover:text-accent"
          >
            {ticker}
          </button>
        ))}
      </div>
    </div>
  );
}
