import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  subtext?: string;
  isHighlight?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  subtext,
  isHighlight
}) => {
  return (
    <div className="metric-card">
      <div className="metric-card-header">
        <span className="metric-label">{label}</span>
        {icon && <div className="metric-icon">{icon}</div>}
      </div>
      <div className="metric-value">{value}</div>
      {subtext && (
        <div className={`metric-subtext ${isHighlight ? "highlight" : ""}`}>
          {subtext}
        </div>
      )}
    </div>
  );
};
