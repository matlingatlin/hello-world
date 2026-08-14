"use client";

import { useTransition } from "react";
import { cancel__ENTITY_PASCAL__Action } from "@/app/actions/__ENTITY__";
import type { __ENTITY_PASCAL__Row } from "@/lib/db/__ENTITY__";

export function __ENTITY_PASCAL__List({ rows }: { rows: __ENTITY_PASCAL__Row[] }) {
  const [pending, startTransition] = useTransition();

  if (rows.length === 0) {
    return (
      <p data-scio-id="__ENTITY__-list-empty" className="text-sm opacity-70">
        No __ENTITY_PLURAL__ yet.
      </p>
    );
  }

  return (
    <ul data-scio-id="__ENTITY__-list" className="flex flex-col gap-3">
      {rows.map((row) => (
        <li
          key={row.id}
          data-scio-id={`__ENTITY__-row-${row.id}`}
          className="flex items-center justify-between rounded-[__TOKEN_RADIUS__] border p-4"
        >
          <span data-scio-id={`__ENTITY__-row-${row.id}-summary`}>
            {row.guest_name} — {new Date(row.starts_at).toLocaleString()} — {row.party_size}
          </span>
          <button
            data-scio-id={`__ENTITY__-row-${row.id}-cancel`}
            type="button"
            disabled={pending}
            onClick={() => startTransition(() => void cancel__ENTITY_PASCAL__Action(row.id))}
            className="rounded border px-3 py-1 text-sm disabled:opacity-60"
          >
            Cancel
          </button>
        </li>
      ))}
    </ul>
  );
}
