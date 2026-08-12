// Owned by pkg_feature_booking — the list_booking operation's screen.
const BOOKINGS = [
  { id: "b1", when: "Fri 18:30", who: "Alex, 2 guests" },
  { id: "b2", when: "Fri 19:00", who: "Sam, 4 guests" },
];

export function BookingList() {
  return (
    <section className="list" data-scio-id="booking-list" data-scio-package="pkg_feature_booking">
      <h2 data-scio-id="booking-list-title" data-scio-package="pkg_feature_booking">
        Today&apos;s bookings
      </h2>
      {BOOKINGS.map((booking) => (
        <div
          key={booking.id}
          className="row"
          data-scio-id={`booking-row-${booking.id}`}
          data-scio-package="pkg_feature_booking"
        >
          {booking.when} — {booking.who}
        </div>
      ))}
    </section>
  );
}
