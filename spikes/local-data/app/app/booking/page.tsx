import { BookingList } from "@/components/booking-list";
import { isConfigured, listOpenBooking } from "@/lib/db/booking";

export default async function BookingPage() {
  const rows = await listOpenBooking();
  const ready = isConfigured();

  return (
    <section data-scio-id="booking-page" className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <h1 data-scio-id="booking-page-heading" className="text-2xl font-semibold">
        Your bookings
      </h1>
      <a data-scio-id="booking-page-new-link" href="/booking/new" className="text-sm underline">
        Make a new booking
      </a>
      {ready ? null : (
        <p data-scio-id="booking-page-no-database" className="text-sm opacity-70">
          Connect a database to start saving bookings.
        </p>
      )}
      <BookingList rows={rows} />
    </section>
  );
}
