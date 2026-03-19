import React, { useState, useEffect, useCallback } from 'react';

interface UsageSummary {
  period: string;
  totals: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cost_usd: number;
    request_count: number;
  };
  daily_breakdown: Record<string, {
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    requests: number;
  }>;
}

interface LimitInfo {
  spent: number;
  limit: number;
  remaining: number;
  period: string;
}

interface CostDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CostDashboard: React.FC<CostDashboardProps> = ({ isOpen, onClose }) => {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [limitInfo, setLimitInfo] = useState<LimitInfo | null>(null);
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('week');
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [usageRes, limitRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/telemetry/usage?period=${period}`),
        fetch((import.meta.env.VITE_API_URL || '') + '/api/telemetry/limit'),
      ]);

      if (usageRes.ok) {
        const usageData = await usageRes.json();
        setUsage(usageData);
      }

      if (limitRes.ok) {
        const limitData = await limitRes.json();
        setLimitInfo(limitData);
      }
    } catch (error) {
      console.error('Failed to fetch telemetry data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, fetchData]);

  if (!isOpen) return null;

  const getProgressColor = (percentage: number) => {
    if (percentage < 50) return 'bg-jade';
    if (percentage < 80) return 'bg-yellow-500 dark:bg-yellow-400';
    return 'bg-vermillion';
  };

  const spentPercentage = limitInfo ? (limitInfo.spent / limitInfo.limit) * 100 : 0;

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/75 flex items-center justify-center z-50">
      <div className="bg-paper rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col dark:border dark:border-paper-dark">
        {/* Header */}
        <div className="p-4 border-b border-paper-dark flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink">Usage & Costs</h2>
          <button
            onClick={onClose}
            className="text-ink-muted hover:text-ink p-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <svg className="animate-spin h-8 w-8 text-vermillion" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : (
            <>
              {/* Weekly Limit Progress */}
              {limitInfo && (
                <div className="bg-paper-warm rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-ink-light">This Week</span>
                    <span className="text-sm text-ink-muted">
                      ${limitInfo.spent.toFixed(2)} / ${limitInfo.limit.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-3 bg-paper-dark rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getProgressColor(spentPercentage)} transition-all`}
                      style={{ width: `${Math.min(spentPercentage, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center mt-2 text-xs text-ink-muted">
                    <span>{spentPercentage.toFixed(1)}% used</span>
                    <span>${limitInfo.remaining.toFixed(2)} remaining</span>
                  </div>
                  {spentPercentage >= 80 && (
                    <div className="mt-2 text-xs text-vermillion bg-vermillion/10 p-2 rounded">
                      Warning: Approaching weekly limit
                    </div>
                  )}
                </div>
              )}

              {/* Period Selector */}
              <div className="flex gap-2">
                {(['day', 'week', 'month'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-3 py-1 text-sm rounded-lg ${
                      period === p
                        ? 'bg-vermillion/20 text-vermillion'
                        : 'bg-paper-dark text-ink-muted hover:bg-paper-warm hover:text-ink'
                    }`}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>

              {/* Usage Stats */}
              {usage && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-paper-warm rounded-lg p-3">
                    <div className="text-2xl font-bold text-ink">
                      {usage.totals.total_tokens.toLocaleString()}
                    </div>
                    <div className="text-xs text-ink-muted">Total Tokens</div>
                  </div>
                  <div className="bg-paper-warm rounded-lg p-3">
                    <div className="text-2xl font-bold text-ink">
                      ${usage.totals.cost_usd.toFixed(4)}
                    </div>
                    <div className="text-xs text-ink-muted">Total Cost</div>
                  </div>
                  <div className="bg-paper-warm rounded-lg p-3">
                    <div className="text-2xl font-bold text-ink">
                      {usage.totals.request_count}
                    </div>
                    <div className="text-xs text-ink-muted">Requests</div>
                  </div>
                  <div className="bg-paper-warm rounded-lg p-3">
                    <div className="text-2xl font-bold text-ink">
                      {usage.totals.request_count > 0
                        ? Math.round(usage.totals.total_tokens / usage.totals.request_count)
                        : 0}
                    </div>
                    <div className="text-xs text-ink-muted">Avg Tokens/Request</div>
                  </div>
                </div>
              )}

              {/* Daily Breakdown */}
              {usage && Object.keys(usage.daily_breakdown).length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-ink-light mb-2">Daily Breakdown</h3>
                  <div className="space-y-2">
                    {Object.entries(usage.daily_breakdown)
                      .sort(([a], [b]) => b.localeCompare(a))
                      .slice(0, 7)
                      .map(([date, data]) => (
                        <div
                          key={date}
                          className="flex items-center justify-between text-sm p-2 bg-paper-warm rounded"
                        >
                          <span className="text-ink-light">{date}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-ink-muted">
                              {(data.input_tokens + data.output_tokens).toLocaleString()} tokens
                            </span>
                            <span className="font-medium text-ink">
                              ${data.cost_usd.toFixed(4)}
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-paper-dark bg-paper-warm text-xs text-ink-muted">
          Pricing: $0.075/1M input tokens, $0.30/1M output tokens (Gemini Flash)
        </div>
      </div>
    </div>
  );
};

export const CostIndicator: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  const [limitInfo, setLimitInfo] = useState<LimitInfo | null>(null);

  useEffect(() => {
    const fetchLimit = async () => {
      try {
        const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/telemetry/limit');
        if (response.ok) {
          const data = await response.json();
          setLimitInfo(data);
        }
      } catch (error) {
        // Silently fail
      }
    };

    fetchLimit();
    const interval = setInterval(fetchLimit, 60000);
    return () => clearInterval(interval);
  }, []);

  if (!limitInfo) return null;

  const percentage = (limitInfo.spent / limitInfo.limit) * 100;
  const color = percentage < 50 ? 'text-jade' : percentage < 80 ? 'text-yellow-600 dark:text-yellow-400' : 'text-vermillion';

  return (
    <button
      onClick={onClick}
      className={`text-xs ${color} hover:opacity-80 flex items-center gap-1`}
      title="View usage details"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23"/>
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
      ${limitInfo.spent.toFixed(2)}
    </button>
  );
};

export default CostDashboard;
