"use server";

import { revalidatePath } from "next/cache";
import { cancelBooking, createBooking } from "@/lib/db/booking";
import { parseBooking } from "@/lib/validation/booking";

export type ActionResult = { ok: true } | { ok: false; message: string };

/**
 * Server actions are the only way the UI changes data: validation happens here,
 * on the server, where a hostile client cannot skip it.
 */
export async function createBookingAction(formData: FormData): Promise<ActionResult> {
  const parsed = parseBooking({
    guest_name: formData.get("guest_name"),
    phone: formData.get("phone"),
    starts_at: formData.get("starts_at"),
    party_size: formData.get("party_size"),
  });

  if (!parsed.success) {
    return { ok: false, message: parsed.error.issues[0]?.message ?? "Please check the form." };
  }

  try {
    await createBooking(parsed.data);
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Something went wrong." };
  }

  revalidatePath("/booking");
  return { ok: true };
}

export async function cancelBookingAction(id: string): Promise<ActionResult> {
  if (!id) {
    return { ok: false, message: "That booking could not be identified." };
  }
  try {
    await cancelBooking(id);
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Something went wrong." };
  }

  revalidatePath("/booking");
  return { ok: true };
}
