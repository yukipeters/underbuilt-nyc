"use client";

import { useEffect, useRef, useState } from "react";

interface Lot {
  bbl: string;
  address: string;
  borough: string;
  zoning_district: string;
  built_far: number;
  allowed_far: number;
  unused_far: number;
  lot_area: number;
  est_add_units: number;
  year_built: number;
  residential_units: number;
  owner_type: string | null;
}

interface LotsResponse {
  total: number;
  offset: number;
  limit: number;
  lots: Lot[];
}

interface Stats {
  total_lots: number;
  total_est_add_units: number;
}

type SortKey = keyof Lot;
type SortDir = "asc" | "desc";

const LIMIT = 50;

const BOROUGHS = [
  { value: "", label: "All boroughs" },
  { value: "BK", label: "Brooklyn" },
  { value: "BX", label: "Bronx" },
  { value: "MN", label: "Manhattan" },
  { value: "QN", label: "Queens" },
  { value: "SI", label: "Staten Island" },
];

function zolaUrl(bbl: string): string {
  const padded = bbl.padStart(10, "0");
  const borough = padded[0];
  const block = parseInt(padded.slice(1, 6), 10);
  const lot = parseInt(padded.slice(6, 10), 10);
  return `https://zola.planning.nyc.gov/l/lot/${borough}/${block}/${lot}`;
}

function fmt(n: number, decimals = 2): string {
  return n.toFixed(decimals);
}

function fmtInt(n: number): string {
  return n.toLocaleString();
}

const OWNER_TYPE_LABELS: Record<string, string> = {
  C: "City",
  M: "Mixed (city/private)",
  O: "Public authority",
  P: "Private",
  X: "Tax-exempt (non-city)",
};

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "address", label: "Address" },
  { key: "borough", label: "Borough" },
  { key: "zoning_district", label: "Zone" },
  { key: "owner_type", label: "Owner type" },
  { key: "built_far", label: "Built FAR", align: "right" },
  { key: "allowed_far", label: "Allowed FAR", align: "right" },
  { key: "unused_far", label: "Unused FAR", align: "right" },
  { key: "lot_area", label: "Lot Area (sqft)", align: "right" },
  { key: "est_add_units", label: "Est. Add. Units", align: "right" },
  { key: "year_built", label: "Year Built", align: "right" },
];

export default function LotsExplorer() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [borough, setBorough] = useState("");
  const [minUnusedFar, setMinUnusedFar] = useState("");
  const [minEstUnits, setMinEstUnits] = useState("");
  const [offset, setOffset] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>("est_add_units");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const [data, setData] = useState<LotsResponse | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce the search query
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setDebouncedQuery(query);
      setOffset(0);
    }, 300);
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [query]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [borough, minUnusedFar, minEstUnits]);

  // Fetch stats once
  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  // Fetch lots
  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (debouncedQuery) params.set("q", debouncedQuery);
    if (borough) params.set("borough", borough);
    if (minUnusedFar) params.set("min_unused_far", minUnusedFar);
    if (minEstUnits) params.set("min_est_units", minEstUnits);
    params.set("limit", String(LIMIT));
    params.set("offset", String(offset));

    fetch(`/api/lots?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: LotsResponse) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [debouncedQuery, borough, minUnusedFar, minEstUnits, offset]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const lots = data?.lots ?? [];
  const sortedLots = [...lots].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    const cmp =
      typeof av === "number" && typeof bv === "number"
        ? av - bv
        : String(av).localeCompare(String(bv));
    return sortDir === "asc" ? cmp : -cmp;
  });

  const total = data?.total ?? 0;
  const page = Math.floor(offset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);

  const inputClass =
    "rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400";

  return (
    <div className="space-y-4">
      {/* Stats */}
      {stats && (
        <div className="flex gap-6 text-sm text-zinc-500 dark:text-zinc-400">
          <span>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
              {fmtInt(stats.total_lots)}
            </span>{" "}
            lots
          </span>
          <span>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100">
              {fmtInt(stats.total_est_add_units)}
            </span>{" "}
            est. additional units
          </span>
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-end">
        <input
          type="search"
          placeholder="Search address…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={`${inputClass} w-56`}
        />
        <select
          value={borough}
          onChange={(e) => setBorough(e.target.value)}
          className={inputClass}
        >
          {BOROUGHS.map((b) => (
            <option key={b.value} value={b.value}>
              {b.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm">
          <span className="text-zinc-500 dark:text-zinc-400 whitespace-nowrap">
            Min unused FAR
          </span>
          <input
            type="number"
            min="0"
            step="0.5"
            value={minUnusedFar}
            onChange={(e) => setMinUnusedFar(e.target.value)}
            className={`${inputClass} w-20`}
            placeholder="0"
          />
        </label>
        <label className="flex items-center gap-1.5 text-sm">
          <span className="text-zinc-500 dark:text-zinc-400 whitespace-nowrap">
            Min est. units
          </span>
          <input
            type="number"
            min="1"
            step="1"
            value={minEstUnits}
            onChange={(e) => setMinEstUnits(e.target.value)}
            className={`${inputClass} w-20`}
            placeholder="1"
          />
        </label>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          Failed to load lots: {error}. Is the backend running?
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded border border-zinc-200 dark:border-zinc-800">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-zinc-50 dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`px-3 py-2 font-medium text-zinc-600 dark:text-zinc-400 whitespace-nowrap cursor-pointer select-none hover:text-zinc-900 dark:hover:text-zinc-100 ${
                    col.align === "right" ? "text-right" : "text-left"
                  }`}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="ml-1 text-zinc-400">
                      {sortDir === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </th>
              ))}
              <th className="px-3 py-2 text-left font-medium text-zinc-600 dark:text-zinc-400">
                ZoLa
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={COLUMNS.length + 1}
                  className="px-3 py-8 text-center text-zinc-400"
                >
                  Loading…
                </td>
              </tr>
            )}
            {!loading && sortedLots.length === 0 && (
              <tr>
                <td
                  colSpan={COLUMNS.length + 1}
                  className="px-3 py-8 text-center text-zinc-400"
                >
                  No lots found.
                </td>
              </tr>
            )}
            {!loading &&
              sortedLots.map((lot) => (
                <tr
                  key={lot.bbl}
                  className="border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900"
                >
                  <td className="px-3 py-2 font-mono text-xs max-w-[220px] truncate">
                    {lot.address}
                  </td>
                  <td className="px-3 py-2">{lot.borough}</td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {lot.zoning_district}
                  </td>
                  <td className="px-3 py-2 text-sm">
                    {lot.owner_type
                      ? (OWNER_TYPE_LABELS[lot.owner_type] ?? lot.owner_type)
                      : "Private"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmt(lot.built_far)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmt(lot.allowed_far)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums font-medium">
                    {fmt(lot.unused_far)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {fmtInt(lot.lot_area)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums font-semibold">
                    {fmtInt(lot.est_add_units)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-zinc-500">
                    {lot.year_built > 0 ? lot.year_built : "—"}
                  </td>
                  <td className="px-3 py-2">
                    <a
                      href={zolaUrl(lot.bbl)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                    >
                      ZoLa ↗
                    </a>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
          <span>
            {fmtInt(offset + 1)}–{fmtInt(Math.min(offset + LIMIT, total))} of{" "}
            {fmtInt(total)} lots
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              disabled={offset === 0}
              className="px-3 py-1 rounded border border-zinc-300 dark:border-zinc-700 disabled:opacity-40 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              ← Prev
            </button>
            <span className="px-2 py-1">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setOffset(offset + LIMIT)}
              disabled={offset + LIMIT >= total}
              className="px-3 py-1 rounded border border-zinc-300 dark:border-zinc-700 disabled:opacity-40 hover:bg-zinc-100 dark:hover:bg-zinc-800"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
