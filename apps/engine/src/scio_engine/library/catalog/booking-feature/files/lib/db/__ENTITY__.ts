import { getSupabaseClient } from "@/lib/supabase";
import type { __ENTITY_PASCAL__Input } from "@/lib/validation/__ENTITY__";

export type __ENTITY_PASCAL__Row = __ENTITY_PASCAL__Input & {
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
 * Data access for __ENTITY_PLURAL__. Row-level security decides what each
 * request may see; this layer never bypasses it, so a missing policy shows up
 * as an empty result rather than as a leak.
 */
export async function listOpen__ENTITY_PASCAL__(): Promise<__ENTITY_PASCAL__Row[]> {
  if (!isConfigured()) {
    return [];
  }

  const { data, error } = await getSupabaseClient()
    .from("__ENTITY_PLURAL__")
    .select("*")
    .is("cancelled_at", null)
    .order("starts_at", { ascending: true });

  if (error) {
    throw new Error(`Could not load __ENTITY_PLURAL__: ${error.message}`);
  }
  return (data ?? []) as __ENTITY_PASCAL__Row[];
}

export async function create__ENTITY_PASCAL__(
  input: __ENTITY_PASCAL__Input,
): Promise<__ENTITY_PASCAL__Row> {
  if (!isConfigured()) {
    throw new Error("Connect a database before saving a __ENTITY__.");
  }

  const { data, error } = await getSupabaseClient()
    .from("__ENTITY_PLURAL__")
    .insert(input)
    .select()
    .single();

  if (error) {
    throw new Error(`Could not save the __ENTITY__: ${error.message}`);
  }
  return data as __ENTITY_PASCAL__Row;
}

export async function cancel__ENTITY_PASCAL__(id: string): Promise<void> {
  if (!isConfigured()) {
    throw new Error("Connect a database before cancelling a __ENTITY__.");
  }

  const { error } = await getSupabaseClient()
    .from("__ENTITY_PLURAL__")
    .update({ cancelled_at: new Date().toISOString() })
    .eq("id", id);

  if (error) {
    throw new Error(`Could not cancel the __ENTITY__: ${error.message}`);
  }
}
