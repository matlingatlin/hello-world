import { BookingForm } from "@/components/booking-form";

export default function NewBookingPage() {
  return (
    <section
      data-scio-id="booking-new-page"
      className="mx-auto flex max-w-lg flex-col gap-6 p-6"
    >
      <h1 data-scio-id="booking-new-heading" className="text-2xl font-semibold">
        Book a table
      </h1>
      <BookingForm />
    </section>
  );
}
