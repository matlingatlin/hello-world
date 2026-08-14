"use client";

import { useState, useTransition } from "react";
import { createBookingAction } from "@/app/actions/booking";

export function BookingForm() {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  function onSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await createBookingAction(formData);
      setMessage(result.ok ? "Your booking is confirmed." : result.message);
    });
  }

  return (
    <form
      data-scio-id="booking-form"
      action={onSubmit}
      className="flex flex-col gap-4 rounded-[0.5rem] border p-5"
    >
      <label data-scio-id="booking-form-name-label" className="flex flex-col gap-1 text-sm">
        Your name
        <input
          data-scio-id="booking-form-name"
          name="guest_name"
          required
          minLength={2}
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="booking-form-phone-label" className="flex flex-col gap-1 text-sm">
        Phone
        <input
          data-scio-id="booking-form-phone"
          name="phone"
          type="tel"
          required
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="booking-form-when-label" className="flex flex-col gap-1 text-sm">
        When
        <input
          data-scio-id="booking-form-when"
          name="starts_at"
          type="datetime-local"
          required
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="booking-form-size-label" className="flex flex-col gap-1 text-sm">
        How many people
        <input
          data-scio-id="booking-form-size"
          name="party_size"
          type="number"
          min={1}
          max={20}
          defaultValue={2}
          className="rounded border px-3 py-2"
        />
      </label>

      <button
        data-scio-id="booking-form-submit"
        type="submit"
        disabled={pending}
        style={{ background: "#0f766e" }}
        className="rounded px-4 py-2 font-medium text-white disabled:opacity-60"
      >
        {pending ? "Saving…" : "Book a table"}
      </button>

      {message ? (
        <p data-scio-id="booking-form-message" role="status" className="text-sm">
          {message}
        </p>
      ) : null}
    </form>
  );
}
