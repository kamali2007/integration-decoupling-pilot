import React from "react";

interface StatusBadgeProps {
  status: string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const norm = (status || "").toLowerCase();
  const displayLabel = label || status;

  return (
    <span className={`status-badge status-${norm}`}>
      <span className="status-dot" />
      {displayLabel}
    </span>
  );
};
