"use client";

import { useState, useTransition } from "react";
import { create__ENTITY_PASCAL__Action } from "@/app/actions/__ENTITY__";

export function __ENTITY_PASCAL__Form() {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  function onSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await create__ENTITY_PASCAL__Action(formData);
      setMessage(result.ok ? "Your __ENTITY__ is confirmed." : result.message);
    });
  }

  return (
    <form
      data-scio-id="__ENTITY__-form"
      action={onSubmit}
      className="flex flex-col gap-4 rounded-[__TOKEN_RADIUS__] border p-5"
    >
      <label data-scio-id="__ENTITY__-form-name-label" className="flex flex-col gap-1 text-sm">
        Your name
        <input
          data-scio-id="__ENTITY__-form-name"
          name="guest_name"
          required
          minLength={2}
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="__ENTITY__-form-phone-label" className="flex flex-col gap-1 text-sm">
        Phone
        <input
          data-scio-id="__ENTITY__-form-phone"
          name="phone"
          type="tel"
          required
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="__ENTITY__-form-when-label" className="flex flex-col gap-1 text-sm">
        When
        <input
          data-scio-id="__ENTITY__-form-when"
          name="starts_at"
          type="datetime-local"
          required
          className="rounded border px-3 py-2"
        />
      </label>

      <label data-scio-id="__ENTITY__-form-size-label" className="flex flex-col gap-1 text-sm">
        How many people
        <input
          data-scio-id="__ENTITY__-form-size"
          name="party_size"
          type="number"
          min={1}
          max={20}
          defaultValue={2}
          className="rounded border px-3 py-2"
        />
      </label>

      <button
        data-scio-id="__ENTITY__-form-submit"
        type="submit"
        disabled={pending}
        style={{ background: "__TOKEN_ACCENT__" }}
        className="rounded px-4 py-2 font-medium text-white disabled:opacity-60"
      >
        {pending ? "Saving…" : "Book a table"}
      </button>

      {message ? (
        <p data-scio-id="__ENTITY__-form-message" role="status" className="text-sm">
          {message}
        </p>
      ) : null}
    </form>
  );
}
