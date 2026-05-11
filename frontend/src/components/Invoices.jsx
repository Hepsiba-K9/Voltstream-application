import { AlertTriangle, CalendarDays, Landmark, ReceiptText, WalletCards } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getBillingSummary } from "../api";
import { useAsync } from "../hooks";
import { ErrorState, LoadingState } from "../ui/State";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "INR",
});

const monthCostSeed = [68, 74, 82, 78, 95, 92, 104, 99, 88, 91, 108, 116];

function buildBillingView(selectedDate) {
  const date = new Date(`${selectedDate}T00:00:00`);
  const year = date.getFullYear();
  const month = date.getMonth();
  const selectedDay = date.getDate();
  const lastDate = new Date(year, month + 1, 0).getDate();
  const longMonth = new Intl.DateTimeFormat("en-US", { month: "long" }).format(date);
  const selectedLabel = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
  const trend = Array.from({ length: month + 1 }, (_, index) => {
    const trendDate = new Date(year, index, 1);
    const label = new Intl.DateTimeFormat("en-US", { month: "short" }).format(trendDate);
    const seasonalAdjustment = year === 2026 ? 0 : (year - 2026) * 3;
    const projected = Math.max(45, monthCostSeed[index] + seasonalAdjustment);

    return {
      label,
      actual: index === month ? Math.round((projected * selectedDay) / lastDate) : projected,
      projected,
    };
  });
  const selectedMonthProjected = trend[trend.length - 1].projected;
  const currentBalance = trend[trend.length - 1].actual;

  return {
    currentBalance,
    period: `January 1 - ${selectedLabel}`,
    projectedBill: selectedMonthProjected,
    selectedMonth: longMonth,
    trend,
  };
}

export function Invoices() {
  const { data, error, loading } = useAsync(getBillingSummary, []);
  const [selectedDate, setSelectedDate] = useState("2026-05-06");
  const [customLimit, setCustomLimit] = useState(() => localStorage.getItem("voltstream_budget_limit") ?? "");
  const billingView = useMemo(() => buildBillingView(selectedDate), [selectedDate]);

  useEffect(() => {
    if (!customLimit && data?.budget_limit) {
      setCustomLimit(String(data.budget_limit));
    }
  }, [customLimit, data?.budget_limit]);

  if (loading) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Billing unavailable"} />;

  const activeLimit = Number(customLimit) > 0 ? Number(customLimit) : data.budget_limit;
  const overBudgetAmount = Math.max(0, billingView.projectedBill - activeLimit);
  const overBudgetPercent = Math.round((overBudgetAmount / activeLimit) * 100);
  const budgetPercent = Math.min(100, Math.round((billingView.projectedBill / activeLimit) * 100));
  const isOverBudget = billingView.projectedBill > activeLimit;
  const billingSeries = [
    {
      key: "current",
      label: "Current Bill",
      color: "blue",
      stroke: "#2563eb",
      values: billingView.trend.map((item, index) => ({
        ...item,
        value: Math.max(20, item.actual + [0, 6, -4, 8, -5, 7, -3, 5, -6, 4, -2, 6][index % 12]),
      })),
    },
    {
      key: "savings",
      label: "Savings",
      color: "green",
      stroke: "#16a34a",
      values: billingView.trend.map((item, index) => ({
        ...item,
        value: Math.max(10, activeLimit - item.actual + [34, 16, 28, 12, 38, 20, 30, 14, 26, 18, 24, 15][index % 12]),
      })),
    },
    {
      key: "projected",
      label: "Projected Bill",
      color: "orange",
      stroke: "#ea580c",
      values: billingView.trend.map((item, index) => ({
        ...item,
        value: Math.max(25, item.projected + [-12, 16, -8, 22, 0, 18, -6, 26, 4, 20, -10, 24][index % 12]),
      })),
    },
  ];
  const chartMax = Math.max(
    activeLimit,
    ...billingView.trend.map((item) => Math.max(item.projected, item.actual)),
    ...billingSeries.flatMap((line) => line.values.map((item) => item.value)),
    1
  );
  const billingCards = [
    {
      label: "Current Balance",
      value: currency.format(billingView.currentBalance),
      note: `As of selected date`,
      icon: WalletCards,
      color: "green",
    },
    {
      label: "Projected Bill",
      value: currency.format(billingView.projectedBill),
      note: `For ${billingView.selectedMonth}`,
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

  function handleLimitChange(value) {
    setCustomLimit(value);
    if (Number(value) > 0) {
      localStorage.setItem("voltstream_budget_limit", value);
    } else {
      localStorage.removeItem("voltstream_budget_limit");
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
          <span>Billing Period: {billingView.period}</span>
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
        <p>Showing billing data for {new Date(`${selectedDate}T00:00:00`).getFullYear()} up to {billingView.selectedMonth}.</p>
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
          <strong>{currency.format(billingView.projectedBill)}</strong>
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
            {billingView.trend.map((item) => (
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
