import { AlertCircle, Loader2 } from "lucide-react";

export function LoadingState() {
  return (
    <div className="state">
      <Loader2 className="spin" size={22} />
      <span>Loading energy data</span>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div className="state error">
      <AlertCircle size={22} />
      <span>{message}</span>
    </div>
  );
}
