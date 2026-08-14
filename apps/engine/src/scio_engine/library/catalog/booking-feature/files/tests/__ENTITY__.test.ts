import { describe, expect, it } from "vitest";
import { parse__ENTITY_PASCAL__ } from "@/lib/validation/__ENTITY__";

describe("__ENTITY__ validation", () => {
  it("accepts a complete __ENTITY__", () => {
    const result = parse__ENTITY_PASCAL__({
      guest_name: "Ada Lovelace",
      phone: "+46 70 123 45 67",
      starts_at: "2026-09-01T19:00",
      party_size: 2,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a party of zero with a message a person can act on", () => {
    const result = parse__ENTITY_PASCAL__({
      guest_name: "Ada Lovelace",
      phone: "+46 70 123 45 67",
      starts_at: "2026-09-01T19:00",
      party_size: 0,
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.message).toContain("at least one person");
    }
  });

  it("rejects a missing name", () => {
    const result = parse__ENTITY_PASCAL__({ phone: "0700000000", starts_at: "2026-09-01T19:00" });
    expect(result.success).toBe(false);
  });
});
