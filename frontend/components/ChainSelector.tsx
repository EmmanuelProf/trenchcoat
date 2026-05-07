"use client";

type ChainSelectorProps = {
  value: string;
  onChange: (chain: string) => void;
};

const CHAINS = [
  ["solana", "Solana"],
  ["base", "Base"],
  ["ethereum", "Ethereum"],
];

export function ChainSelector({ value, onChange }: ChainSelectorProps) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="h-12 rounded border border-[#262626] bg-[#171717] px-3 font-mono text-sm text-[#f5f5f5] outline-none"
      aria-label="Select chain"
    >
      {CHAINS.map(([chain, label]) => (
        <option key={chain} value={chain} className="bg-[#171717] text-[#f5f5f5]">
          {label}
        </option>
      ))}
    </select>
  );
}
