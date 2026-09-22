interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-severity-high/40 bg-severity-high-soft px-4 py-3">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-severity-high">⚠</span>
        <p className="text-sm text-text-primary">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="shrink-0 rounded-md border border-border-strong px-3 py-1 text-xs font-medium text-text-secondary transition hover:border-accent hover:text-accent"
        >
          Retry
        </button>
      )}
    </div>
  );
}
