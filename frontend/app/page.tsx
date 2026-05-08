"use client";

import { useRouter } from "next/navigation";

import IntroLoader from "@/components/IntroLoader";

export default function Home() {
  const router = useRouter();

  return (
    <main style={{ minHeight: "100vh", background: "#0a0a0a" }}>
      <IntroLoader onComplete={() => router.push("/showcase")} />
    </main>
  );
}
