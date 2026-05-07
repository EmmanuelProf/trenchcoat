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

export function formatNumber(
  n: number | null | undefined,
  options: { currency?: boolean; price?: boolean } = {}
): string {
  if (n == null) {
    return "UNKNOWN";
  }

  const sign = n < 0 ? "-" : "";
  const value = Math.abs(n);
  const prefix = options.currency || options.price ? "$" : "";

  if (options.price && value < 0.01) {
    return `${sign}${prefix}${value.toPrecision(8).replace(/\.?0+$/, "")}`;
  }

  if (value >= 1_000_000_000) {
    return `${sign}${prefix}${trim(value / 1_000_000_000)}B`;
  }
  if (value >= 1_000_000) {
    return `${sign}${prefix}${trim(value / 1_000_000)}M`;
  }
  if (value >= 1_000) {
    return `${sign}${prefix}${trim(value / 1_000)}K`;
  }
  return `${sign}${prefix}${trim(value)}`;
}

export function formatAge(days: number | null | undefined): string {
  if (days == null) {
    return "UNKNOWN";
  }
  if (days < 1) {
    return "< 1 day";
  }
  if (days < 30) {
    return `${Math.floor(days)} days`;
  }
  if (days < 365) {
    return `${Math.floor(days / 30)} months`;
  }
  return `${(days / 365).toFixed(1)} years`;
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
