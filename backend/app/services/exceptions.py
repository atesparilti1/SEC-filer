class SECFilingAnalyzerError(Exception):
    """Base class for all domain errors surfaced to the API layer as 4xx/5xx."""


class TickerNotFoundError(SECFilingAnalyzerError):
    pass


class SECUnavailableError(SECFilingAnalyzerError):
    pass


class FilingNotFoundError(SECFilingAnalyzerError):
    pass


class FilingParsingError(SECFilingAnalyzerError):
    pass


class AIAnalysisError(SECFilingAnalyzerError):
    pass


class FinancialDataUnavailableError(SECFilingAnalyzerError):
    pass
