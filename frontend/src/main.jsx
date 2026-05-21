import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AIAssistant } from "./components/AIAssistant";
import { DeviceAgent } from "./components/DeviceAgent";
import { Invoices } from "./components/Invoices";
import { LiveDashboard } from "./components/LiveDashboard";
import { NotFound } from "./components/NotFound";
import { SmartControl } from "./components/SmartControl";
import { UsageHistory } from "./components/UsageHistory";
import { AppShell } from "./ui/AppShell";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<LiveDashboard />} />
          <Route path="/analytics" element={<UsageHistory />} />
          <Route path="/devices" element={<SmartControl />} />
          <Route path="/billing" element={<Invoices />} />
          <Route path="/assistant" element={<Navigate to="/assistant/chat" replace />} />
          <Route path="/assistant/chat" element={<AIAssistant routeMode="chat" />} />
          <Route path="/assistant/qa" element={<AIAssistant routeMode="qa" />} />
          <Route path="/agent" element={<DeviceAgent />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
