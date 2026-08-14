import { getSupabaseClient } from "@/lib/supabase";
import type { BookingInput } from "@/lib/validation/booking";

export type BookingRow = BookingInput & {
  id: string;
  created_at: string;
  cancelled_at: string | null;
};

/**
 * Whether this deployment has a database yet. A preview runs before anyone has
 * connected Supabase, and a screen that 500s because of that tells the user
 * their app is broken when it is merely empty.
 */
export function isConfigured(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  );
}

/**
 * Data access for bookings. Row-level security decides what each
 * request may see; this layer never bypasses it, so a missing policy shows up
 * as an empty result rather than as a leak.
 */
export async function listOpenBooking(): Promise<BookingRow[]> {
  if (!isConfigured()) {
    return [];
  }

  const { data, error } = await getSupabaseClient()
    .from("bookings")
    .select("*")
    .is("cancelled_at", null)
    .order("starts_at", { ascending: true });

  if (error) {
    throw new Error(`Could not load bookings: ${error.message}`);
  }
  return (data ?? []) as BookingRow[];
}

export async function createBooking(
  input: BookingInput,
): Promise<BookingRow> {
  if (!isConfigured()) {
    throw new Error("Connect a database before saving a booking.");
  }

  const { data, error } = await getSupabaseClient()
    .from("bookings")
    .insert(input)
    .select()
    .single();

  if (error) {
    throw new Error(`Could not save the booking: ${error.message}`);
  }
  return data as BookingRow;
}

export async function cancelBooking(id: string): Promise<void> {
  if (!isConfigured()) {
    throw new Error("Connect a database before cancelling a booking.");
  }

  const { error } = await getSupabaseClient()
    .from("bookings")
    .update({ cancelled_at: new Date().toISOString() })
    .eq("id", id);

  if (error) {
    throw new Error(`Could not cancel the booking: ${error.message}`);
  }
}
