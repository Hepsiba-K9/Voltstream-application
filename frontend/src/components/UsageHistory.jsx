import { useState } from "react";
import { getUsageHistory } from "../api";
import { useAsync } from "../hooks";
import { ErrorState, LoadingState } from "../ui/State";

const periods = ["daily", "weekly", "monthly"];
const periodLabels = {
  daily: "Today",
  weekly: "This week",
  monthly: "12 months",
};

export function UsageHistory() {
  const [period, setPeriod] = useState("daily");
  const { data, error, loading } = useAsync(() => getUsageHistory(period), [period]);
  const chartData = data ?? [];
  const totals = chartData.reduce(
    (summary, item) => ({
      grid: summary.grid + item.grid_kwh,
      solar: summary.solar + item.solar_kwh,
      net: summary.net + item.net_kwh,
    }),
    { grid: 0, solar: 0, net: 0 }
  );
  const maxValue = Math.max(...chartData.map((item) => Math.max(item.grid_kwh, item.solar_kwh)), 1);

  return (
    <section className="page analytics-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Usage History</p>
          <h1>Grid and solar performance</h1>
          <p className="page-subtitle">
            Compare imported grid energy with solar generation for {period === "monthly" ? "all 12 months" : periodLabels[period].toLowerCase()}.
          </p>
        </div>
        <div className="segmented" role="tablist" aria-label="Usage period">
          {periods.map((item) => (
            <button
              className={period === item ? "selected" : ""}
              key={item}
              onClick={() => setPeriod(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </header>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}
      {data && (
        <div className="analytics-stack">
          <div className="analytics-metric-grid">
            <article>
              <span>Grid Usage</span>
              <strong>{totals.grid.toFixed(1)} kWh</strong>
              <p>Energy imported from grid</p>
            </article>
            <article>
              <span>Solar Generated</span>
              <strong>{totals.solar.toFixed(1)} kWh</strong>
              <p>Energy produced by solar</p>
            </article>
            <article className={totals.net < 0 ? "positive" : "warning"}>
              <span>Net Usage</span>
              <strong>{totals.net.toFixed(1)} kWh</strong>
              <p>{totals.net < 0 ? "Exporting more than importing" : "Importing more than exporting"}</p>
            </article>
          </div>

          <div className="chart-panel analytics-panel">
            <div className="chart-heading">
              <div>
                <h2>{period === "monthly" ? "Monthly Energy Usage (Jan - Dec)" : `${periodLabels[period]} Energy Usage`}</h2>
                <p>Grid and solar values are shown in kilowatt-hours.</p>
              </div>
              <span>{period}</span>
            </div>
            <div className="chart-legend">
              <span className="grid-dot">Grid kWh</span>
              <span className="solar-dot">Solar kWh</span>
            </div>
            <div
              className={`bar3d-chart ${period === "monthly" ? "monthly-bars" : ""}`}
              aria-label={`${periodLabels[period]} grid and solar energy chart`}
            >
              <div className="bar3d-axis">
                <span>{Math.ceil(maxValue)}</span>
                <span>{Math.ceil(maxValue * 0.75)}</span>
                <span>{Math.ceil(maxValue * 0.5)}</span>
                <span>{Math.ceil(maxValue * 0.25)}</span>
                <span>0</span>
              </div>
              <div className="bar3d-plot">
                  {chartData.map((item) => {
                  const gridHeight = Math.max(8, (item.grid_kwh / maxValue) * 100);
                  const solarHeight = Math.max(8, (item.solar_kwh / maxValue) * 100);

                  return (
                    <div className="bar3d-group" key={item.label}>
                      <div className="bar3d-columns">
                        <div className="bar3d-shell">
                          <div
                            className="bar3d-fill grid"
                            style={{ height: `${gridHeight}%` }}
                            title={`Grid: ${item.grid_kwh} kWh`}
                          >
                            <span>{Math.round((item.grid_kwh / maxValue) * 100)}%</span>
                          </div>
                        </div>
                        <div className="bar3d-shell">
                          <div
                            className="bar3d-fill solar"
                            style={{ height: `${solarHeight}%` }}
                            title={`Solar: ${item.solar_kwh} kWh`}
                          >
                            <span>{Math.round((item.solar_kwh / maxValue) * 100)}%</span>
                          </div>
                        </div>
                      </div>
                      <strong>{item.label}</strong>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
