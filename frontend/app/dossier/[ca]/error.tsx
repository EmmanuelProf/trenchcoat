"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0a0a0a] px-5 text-[#f5f5f5]">
      <div className="w-full max-w-xl rounded border border-[#262626] bg-[#171717] p-6 font-mono">
        <p className="text-lg font-bold">COULDN&apos;T PULL DATA ON THIS ONE.</p>
        <button
          type="button"
          onClick={reset}
          className="mt-5 rounded border border-[#f5f5f5] bg-[#f5f5f5] px-4 py-2 text-sm font-bold text-[#0a0a0a]"
        >
          RETRY
        </button>
      </div>
    </main>
  );
}
