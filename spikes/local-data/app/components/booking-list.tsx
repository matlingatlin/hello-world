"use client";

import { useTransition } from "react";
import { cancelBookingAction } from "@/app/actions/booking";
import type { BookingRow } from "@/lib/db/booking";

export function BookingList({ rows }: { rows: BookingRow[] }) {
  const [pending, startTransition] = useTransition();

  if (rows.length === 0) {
    return (
      <p data-scio-id="booking-list-empty" className="text-sm opacity-70">
        No bookings yet.
      </p>
    );
  }

  return (
    <ul data-scio-id="booking-list" className="flex flex-col gap-3">
      {rows.map((row) => (
        <li
          key={row.id}
          data-scio-id={`booking-row-${row.id}`}
          className="flex items-center justify-between rounded-[0.5rem] border p-4"
        >
          <span data-scio-id={`booking-row-${row.id}-summary`}>
            {row.guest_name} — {new Date(row.starts_at).toLocaleString()} — {row.party_size}
          </span>
          <button
            data-scio-id={`booking-row-${row.id}-cancel`}
            type="button"
            disabled={pending}
            onClick={() => startTransition(() => void cancelBookingAction(row.id))}
            className="rounded border px-3 py-1 text-sm disabled:opacity-60"
          >
            Cancel
          </button>
        </li>
      ))}
    </ul>
  );
}
