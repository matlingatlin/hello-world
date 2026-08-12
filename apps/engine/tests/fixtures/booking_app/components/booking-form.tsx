"use client";

// Owned by pkg_feature_booking.
import { useState } from "react";

const SLOTS = ["18:00", "18:30", "19:00", "19:30"];

export function BookingForm() {
  const [slot, setSlot] = useState("18:30");

  return (
    <section className="card" data-scio-id="booking-form" data-scio-package="pkg_feature_booking">
      <h1 data-scio-id="booking-form-title" data-scio-package="pkg_feature_booking">
        Book a table
      </h1>

      <div className="slots" data-scio-id="booking-slots" data-scio-package="pkg_feature_booking">
        {SLOTS.map((value) => (
          <button
            key={value}
            className="slot"
            data-scio-id={`booking-slot-${value}`}
            data-scio-package="pkg_feature_booking"
            onClick={() => setSlot(value)}
          >
            {value}
          </button>
        ))}
      </div>

      <button
        className="book"
        data-scio-id="booking-submit"
        data-scio-package="pkg_feature_booking"
        onClick={() => console.log(`[booking] create_booking at ${slot}`)}
      >
        Book table
      </button>
    </section>
  );
}
