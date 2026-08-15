import { describe, expect, it } from "vitest";
import { devAuthEnabled, DevIdentityVerifier } from "../src/auth/dev-identity-verifier";

describe("dev auth", () => {
  it("is off unless asked for", () => {
    expect(devAuthEnabled({})).toBe(false);
    expect(devAuthEnabled({ SCIO_DEV_AUTH: "0" })).toBe(false);
    expect(devAuthEnabled({ SCIO_DEV_AUTH: "1" })).toBe(true);
    expect(devAuthEnabled({ SCIO_DEV_AUTH: "true" })).toBe(true);
  });

  it("refuses to run in production rather than accepting any token there", () => {
    expect(() => devAuthEnabled({ SCIO_DEV_AUTH: "1", NODE_ENV: "production" })).toThrow(
      /never run in production/,
    );
  });

  it("makes the token the identity, so two emails are two workspaces", async () => {
    const verifier = new DevIdentityVerifier();
    expect(await verifier.verify("dev")).toEqual({
      externalId: "dev_dev@scio.local",
      email: "dev@scio.local",
    });
    expect(await verifier.verify("dev:ada@example.com")).toEqual({
      externalId: "dev_ada@example.com",
      email: "ada@example.com",
    });
  });

  it("rejects a token that is not a dev token, rather than signing in as the default", async () => {
    // A stale Clerk session token must fail loudly, not become dev@scio.local.
    await expect(new DevIdentityVerifier().verify("eyJhbGciOi...")).rejects.toThrow();
  });
});
