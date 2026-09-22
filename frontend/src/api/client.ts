import type {
  CompanyFilingsResponse,
  CompanyInfo,
  CompareResponse,
  AnalysisRecord,
  FinancialsResponse,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError("Could not reach the SEC Filing Analyzer server.", 0);
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response body wasn't JSON - keep the generic message
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getCompany: (ticker: string) => request<CompanyInfo>(`/company/${ticker}`),

  getFilings: (ticker: string) =>
    request<CompanyFilingsResponse>(`/company/${ticker}/filings`),

  getFinancials: (ticker: string) =>
    request<FinancialsResponse>(`/financials/${ticker}`),

  analyze: (ticker: string, accessionNumber: string, filingType?: string) =>
    request<AnalysisRecord>(`/analyze`, {
      method: "POST",
      body: JSON.stringify({
        ticker,
        accession_number: accessionNumber,
        filing_type: filingType,
      }),
    }),

  getAnalysis: (id: number) => request<AnalysisRecord>(`/analysis/${id}`),

  compare: (
    tickerA: string,
    accessionA: string,
    tickerB: string,
    accessionB: string,
  ) =>
    request<CompareResponse>(`/compare`, {
      method: "POST",
      body: JSON.stringify({
        ticker_a: tickerA,
        accession_number_a: accessionA,
        ticker_b: tickerB,
        accession_number_b: accessionB,
      }),
    }),
};
