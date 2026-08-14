"use server";

import { revalidatePath } from "next/cache";
import { cancel__ENTITY_PASCAL__, create__ENTITY_PASCAL__ } from "@/lib/db/__ENTITY__";
import { parse__ENTITY_PASCAL__ } from "@/lib/validation/__ENTITY__";

export type ActionResult = { ok: true } | { ok: false; message: string };

/**
 * Server actions are the only way the UI changes data: validation happens here,
 * on the server, where a hostile client cannot skip it.
 */
export async function create__ENTITY_PASCAL__Action(formData: FormData): Promise<ActionResult> {
  const parsed = parse__ENTITY_PASCAL__({
    guest_name: formData.get("guest_name"),
    phone: formData.get("phone"),
    starts_at: formData.get("starts_at"),
    party_size: formData.get("party_size"),
  });

  if (!parsed.success) {
    return { ok: false, message: parsed.error.issues[0]?.message ?? "Please check the form." };
  }

  try {
    await create__ENTITY_PASCAL__(parsed.data);
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Something went wrong." };
  }

  revalidatePath("/__ENTITY__");
  return { ok: true };
}

export async function cancel__ENTITY_PASCAL__Action(id: string): Promise<ActionResult> {
  if (!id) {
    return { ok: false, message: "That __ENTITY__ could not be identified." };
  }
  try {
    await cancel__ENTITY_PASCAL__(id);
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : "Something went wrong." };
  }

  revalidatePath("/__ENTITY__");
  return { ok: true };
}
