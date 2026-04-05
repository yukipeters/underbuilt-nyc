import LotsExplorer from "./components/LotsExplorer";

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <header className="border-b border-zinc-200 dark:border-zinc-800 px-6 py-5">
        <h1 className="text-2xl font-bold tracking-tight">Underbuilt NYC</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400 max-w-2xl">
          NYC tax lots that appear underbuilt relative to their zoning allowance.
          Estimates only — not legal advice. Results are candidates for further
          review, not confirmed development opportunities.
        </p>
      </header>
      <main className="px-6 py-6">
        <LotsExplorer />
      </main>
      <footer className="border-t border-zinc-200 dark:border-zinc-800 px-6 py-4 text-xs text-zinc-400 dark:text-zinc-500">
        Based on NYC PLUTO data. Zoning is simplified — special districts,
        overlays, bonuses, and lot-specific constraints are not modeled. Uses{" "}
        <code className="font-mono">residfar</code> from PLUTO as allowed FAR
        proxy.
      </footer>
    </div>
  );
}
