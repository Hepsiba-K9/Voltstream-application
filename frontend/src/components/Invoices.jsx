import { AlertTriangle, CalendarDays, Landmark, ReceiptText, WalletCards } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getBillingSummary, getBillingTrend, updateBillingLimit } from "../api";
import { useAsync } from "../hooks";
import { ErrorState, LoadingState } from "../ui/State";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "INR",
});

function buildBillingPeriod(selectedDate) {
  const date = new Date(`${selectedDate}T00:00:00`);
  const longMonth = new Intl.DateTimeFormat("en-US", { month: "long" }).format(date);
  const selectedLabel = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);

  return {
    period: `January 1 - ${selectedLabel}`,
    selectedMonth: longMonth,
  };
}

function getTodayDateValue() {
  const today = new Date();
  const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 10);
}

export function Invoices() {
  const { data, error, loading, setData } = useAsync(getBillingSummary, []);
  const { data: trendData, error: trendError, loading: trendLoading } = useAsync(getBillingTrend, []);
  const [selectedDate, setSelectedDate] = useState(getTodayDateValue);
  const [customLimit, setCustomLimit] = useState("");
  const [limitStatus, setLimitStatus] = useState("");
  const billingPeriod = useMemo(() => buildBillingPeriod(selectedDate), [selectedDate]);

  useEffect(() => {
    if (!customLimit && data?.budget_limit) {
      setCustomLimit(String(data.budget_limit));
    }
  }, [customLimit, data?.budget_limit]);

  if (loading || trendLoading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Billing unavailable"} />;
  if (trendError || !trendData) return <ErrorState message={trendError ?? "Billing trend unavailable"} />;

  const activeLimit = Number(customLimit) > 0 ? Number(customLimit) : data.budget_limit;
  const overBudgetAmount = Math.max(0, data.projected_bill - activeLimit);
  const overBudgetPercent = Math.round((overBudgetAmount / activeLimit) * 100);
  const budgetPercent = Math.min(100, Math.round((data.projected_bill / activeLimit) * 100));
  const isOverBudget = data.projected_bill > activeLimit;
  const billingSeries = [
    {
      key: "current",
      label: "Current Bill",
      color: "blue",
      stroke: "#2563eb",
      values: trendData.map((item) => ({
        ...item,
        value: item.current_bill,
      })),
    },
    {
      key: "savings",
      label: "Savings",
      color: "green",
      stroke: "#16a34a",
      values: trendData.map((item) => ({
        ...item,
        value: item.savings,
      })),
    },
    {
      key: "projected",
      label: "Projected Bill",
      color: "orange",
      stroke: "#ea580c",
      values: trendData.map((item) => ({
        ...item,
        value: item.projected_bill,
      })),
    },
  ];
  const chartMax = Math.max(
    activeLimit,
    ...trendData.map((item) => Math.max(item.projected_bill, item.current_bill, item.savings)),
    ...billingSeries.flatMap((line) => line.values.map((item) => item.value)),
    1
  );
  const billingCards = [
    {
      label: "Current Balance",
      value: currency.format(data.current_balance),
      note: `As of selected date`,
      icon: WalletCards,
      color: "green",
    },
    {
      label: "Projected Bill",
      value: currency.format(data.projected_bill),
      note: `For ${billingPeriod.selectedMonth}`,
      icon: ReceiptText,
      color: "orange",
    },
    {
      label: "Budget Limit",
      value: currency.format(activeLimit),
      note: "Your custom limit",
      icon: Landmark,
      color: "purple",
    },
  ];

  async function handleLimitChange(value) {
    setCustomLimit(value);
    setLimitStatus("");
    const nextLimit = Number(value);
    if (!Number.isFinite(nextLimit) || nextLimit <= 0) {
      return;
    }

    try {
      const updatedSummary = await updateBillingLimit(nextLimit);
      setData(updatedSummary);
    } catch (err) {
      setLimitStatus(err instanceof Error ? err.message : "Could not save budget limit.");
    }
  }

  return (
    <section className="app-page billing-page">
      <header className="section-header">
        <div>
          <h1>Billing</h1>
          <p>Monthly cost, projected bill, and budget alert if over limit.</p>
        </div>
        <div className="period-chip">
          <CalendarDays size={16} />
          <span>Billing Period: {billingPeriod.period}</span>
        </div>
      </header>

      <div className="billing-date-picker">
        <label>
          Choose billing date
          <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>
        <label>
          Set your monthly limit
          <input
            min="1"
            step="1"
            type="number"
            value={customLimit}
            onChange={(event) => handleLimitChange(event.target.value)}
            placeholder="120"
          />
        </label>
        <p>Showing billing data for {new Date(`${selectedDate}T00:00:00`).getFullYear()} up to {billingPeriod.selectedMonth}.</p>
        {limitStatus && <p className="form-status error">{limitStatus}</p>}
      </div>

      <div className="billing-card-grid">
        {billingCards.map(({ label, value, note, icon: Icon, color }) => (
          <article className="billing-stat-card" key={label}>
            <div className={`billing-icon ${color}`}>
              <Icon size={24} />
            </div>
            <div>
              <span className={color}>{label}</span>
              <strong>{value}</strong>
              <p>{note}</p>
            </div>
          </article>
        ))}
      </div>

      {isOverBudget && (
        <div className="budget-alert strong-alert">
          <AlertTriangle size={22} />
          <span>
            Projected bill exceeds budget limit by {currency.format(overBudgetAmount)} ({overBudgetPercent}%).
            Consider reducing usage.
          </span>
        </div>
      )}

      {!isOverBudget && <div className="budget-ok">Projected bill is within your selected budget limit.</div>}

      <article className="budget-progress-card">
        <div>
          <h2>Budget Progress</h2>
          <p>{budgetPercent}% of your custom monthly limit is projected to be used.</p>
        </div>
        <div className="budget-progress-meta">
          <strong>{currency.format(data.projected_bill)}</strong>
          <span>of {currency.format(activeLimit)}</span>
        </div>
        <div className="budget-progress-track" aria-label={`Budget progress ${budgetPercent}%`}>
          <span className={isOverBudget ? "over" : ""} style={{ width: `${budgetPercent}%` }} />
        </div>
      </article>

      <article className="billing-chart-card">
        <div className="billing-chart-head">
          <div>
            <h2>Monthly Billing Comparison</h2>
            <p>Each month shows current bill, projected bill, and savings with matching trend lines.</p>
          </div>
        </div>
        <div className="billing-chart-legend top">
          {billingSeries.map((line) => (
            <span className={`billing-bar-dot ${line.color}`} key={line.key}>{line.label}</span>
          ))}
        </div>
        <div className="billing-line-chart-card">
          <div className="billing-chart-axis">
            <span>{currency.format(chartMax)}</span>
            <span>{currency.format(chartMax * 0.5)}</span>
            <span>{currency.format(0)}</span>
          </div>
          <div className="billing-monthly-combo-plot">
            {trendData.map((item) => (
              <div className="billing-month-group" key={item.label}>
                <div className="billing-month-bars">
                  {billingSeries.map((series) => {
                    const monthValue = series.values.find((value) => value.label === item.label)?.value ?? 0;

                    return (
                      <span
                        className={series.color}
                        key={series.key}
                        style={{ height: `${Math.max(8, (monthValue / chartMax) * 100)}%` }}
                        title={`${item.label} ${series.label}: ${currency.format(monthValue)}`}
                      />
                    );
                  })}
                </div>
                <strong>{item.label}</strong>
              </div>
            ))}
          </div>
        </div>
      </article>

      <p className="muted-footer">All amounts in INR.</p>
    </section>
  );
}
