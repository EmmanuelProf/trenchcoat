import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAddress(addr: string): string {
  if (addr.length <= 10) {
    return addr;
  }
  return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}

export function formatNumber(n: number): string {
  const sign = n < 0 ? "-" : "";
  const value = Math.abs(n);

  if (value >= 1_000_000_000) {
    return `${sign}$${trim(value / 1_000_000_000)}B`;
  }
  if (value >= 1_000_000) {
    return `${sign}$${trim(value / 1_000_000)}M`;
  }
  if (value >= 1_000) {
    return `${sign}$${trim(value / 1_000)}K`;
  }
  return `${sign}$${trim(value)}`;
}

export function formatAge(days: number): string {
  if (days < 60) {
    return `${Math.round(days)} ${Math.round(days) === 1 ? "day" : "days"}`;
  }

  if (days < 365) {
    const months = Math.round(days / 30);
    return `${months} ${months === 1 ? "month" : "months"}`;
  }

  return `${Math.round(days)} days`;
}

export function getBandColor(band: string): string {
  if (band === "AVOID") {
    return "#ef4444";
  }
  if (band === "CAUTION") {
    return "#eab308";
  }
  if (band === "CLEAR") {
    return "#22c55e";
  }
  return "#737373";
}

function trim(value: number): string {
  return value.toFixed(1).replace(/\.0$/, "");
}
