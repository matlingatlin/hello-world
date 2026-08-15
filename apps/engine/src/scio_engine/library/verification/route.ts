/**
 * VERIFICATION ONLY — lets the harness ask the app what is really in its
 * database, and tell it who to act as.
 *
 * Written into the app during verification and removed with the database
 * afterwards. It goes through the APP's process on purpose: pglite is
 * single-writer, so a harness that opened the same directory itself would be
 * the corruption the spike ran into.
 *
 * Nothing but plumbing lives here; the answers come from `verify.ts`, which
 * runs with or without Next and is therefore testable.
 */
import { NextResponse } from "next/server";
import { answer } from "../../../.scio/verification/verify";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  return NextResponse.json(await answer(params));
}
