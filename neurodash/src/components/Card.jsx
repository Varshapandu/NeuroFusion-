// src/components/Card.jsx
import React from "react";

export default function Card({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 p-4 rounded-md ${className}`}>
      {title && <div className="text-sm text-gray-300 font-semibold">{title}</div>}
      {subtitle && <div className="text-xs text-gray-400 mb-2">{subtitle}</div>}
      <div>{children}</div>
    </div>
  );
}
