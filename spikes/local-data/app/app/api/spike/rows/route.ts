import { NextResponse } from "next/server";
import { rawQuery } from "@/lib/supabase";

/**
 * SPIKE ONLY — reads the database directly, so the harness can prove a booking
 * is really stored rather than merely rendered. A real app would never expose
 * this; it exists because "the screen says so" is exactly the evidence this
 * spike is trying to go beyond.
 */
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(await rawQuery("select * from bookings order by created_at"));
}
