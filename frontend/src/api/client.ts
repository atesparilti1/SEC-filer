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

// Online demo (GitHub Pages): no backend, so calls are answered from real API
// responses snapshotted by backend/scripts/export_static_demo.py.
const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === "1";
const DEMO_TICKERS = ["AAPL", "NVDA", "AMD", "MSFT", "META"];
const LOCAL_ONLY =
  "The online demo includes AAPL, NVDA, AMD, MSFT and META. Run the app locally to analyze any other company.";

async function demoFile<T>(path: string): Promise<T> {
  const response = await fetch(`${import.meta.env.BASE_URL}demo-api/${path}`);
  if (!response.ok) throw new ApiError(LOCAL_ONLY, 404);
  return response.json() as Promise<T>;
}

function demoTicker(ticker: string): string {
  const t = ticker.trim().toUpperCase();
  if (!DEMO_TICKERS.includes(t)) throw new ApiError(LOCAL_ONLY, 404);
  return t;
}

const staticApi = {
  getCompany: async (ticker: string) => demoFile<CompanyInfo>(`company/${demoTicker(ticker)}.json`),
  getFilings: async (ticker: string) => demoFile<CompanyFilingsResponse>(`filings/${demoTicker(ticker)}.json`),
  getFinancials: async (ticker: string) => demoFile<FinancialsResponse>(`financials/${demoTicker(ticker)}.json`),
  analyze: async (ticker: string, accessionNumber: string) =>
    demoFile<AnalysisRecord>(`analysis/${demoTicker(ticker)}-${accessionNumber}.json`),
  getAnalysis: async (): Promise<AnalysisRecord> => {
    throw new ApiError(LOCAL_ONLY, 404);
  },
  compare: async (): Promise<CompareResponse> => {
    throw new ApiError(
      "Comparing two filings runs the AI model live, so it is not part of the online demo. Run the app locally to use it.",
      501,
    );
  },
};

const liveApi = {
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

export const api = STATIC_DEMO ? staticApi : liveApi;
