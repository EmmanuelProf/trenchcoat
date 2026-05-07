"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ChainSelector } from "@/components/ChainSelector";

const SOLANA_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const EVM_RE = /^0x[a-fA-F0-9]{40}$/;

export function PasteHero() {
  const router = useRouter();
  const [ca, setCa] = useState("");
  const [chain, setChain] = useState("solana");
  const [error, setError] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = ca.trim();
    if (!validAddress(value, chain)) {
      setError("Invalid contract address");
      return;
    }
    setError("");
    router.push(`/dossier/${encodeURIComponent(value)}?chain=${chain}`);
  }

  return (
    <form onSubmit={submit} className="w-full max-w-4xl">
      <div className="flex flex-col gap-3 md:flex-row">
        <input
          value={ca}
          onChange={(event) => {
            setCa(event.target.value);
            setError("");
          }}
          placeholder="PASTE CONTRACT ADDRESS"
          className={`h-12 flex-1 rounded border bg-[#171717] px-4 font-mono text-sm text-[#f5f5f5] outline-none placeholder:text-[#737373] ${
            error ? "border-[#ef4444]" : "border-[#262626]"
          }`}
        />
        <ChainSelector value={chain} onChange={setChain} />
        <button
          type="submit"
          className="h-12 rounded border border-[#f5f5f5] bg-[#f5f5f5] px-8 font-mono text-sm font-bold text-[#0a0a0a]"
        >
          RUN
        </button>
      </div>
      {error ? (
        <p className="mt-3 font-mono text-sm text-[#ef4444]">{error}</p>
      ) : null}
    </form>
  );
}

function validAddress(value: string, chain: string) {
  if (chain === "solana") {
    return SOLANA_RE.test(value) && !value.startsWith("0x");
  }
  return EVM_RE.test(value);
}
