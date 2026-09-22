import { useState } from "react";
import { api, ApiError } from "../api/client";
import type { CompanyFilingsResponse } from "../api/types";
import { Card } from "./Card";
import { ErrorBanner } from "./ErrorBanner";
import { FilingSelector } from "./FilingSelector";
import { LoadingSpinner } from "./LoadingSpinner";
import { SearchBar } from "./SearchBar";

interface CompareSlotPickerProps {
  label: string;
  onSelect: (ticker: string, accessionNumber: string) => void;
}

export function CompareSlotPicker({ label, onSelect }: CompareSlotPickerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filingsData, setFilingsData] = useState<CompanyFilingsResponse | null>(null);
  const [selectedAccession, setSelectedAccession] = useState<string | null>(null);

  async function handleSearch(ticker: string) {
    setError(null);
    setFilingsData(null);
    setSelectedAccession(null);
    setLoading(true);
    try {
      const data = await api.getFilings(ticker);
      setFilingsData(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load filings.");
    } finally {
      setLoading(false);
    }
  }

  function handleSelectFiling(accessionNumber: string) {
    setSelectedAccession(accessionNumber);
    if (filingsData) onSelect(filingsData.company.ticker, accessionNumber);
  }

  return (
    <Card className="space-y-4">
      <p className="text-xs font-semibold tracking-wide text-text-secondary uppercase">{label}</p>
      <SearchBar onSearch={handleSearch} loading={loading} />
      {error && <ErrorBanner message={error} />}
      {loading && <LoadingSpinner label="Loading filings" />}
      {filingsData && !loading && (
        <FilingSelector
          filings={filingsData.filings}
          selected={selectedAccession}
          onSelect={handleSelectFiling}
        />
      )}
    </Card>
  );
}
