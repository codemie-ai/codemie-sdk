import { describe, expect, it } from "@jest/globals";
import { CredentialTypes } from "../../../src/models/integration";

describe("CredentialTypes", () => {
  it("does not contain ZephyrSquad, which was removed from the platform", () => {
    expect(Object.keys(CredentialTypes)).not.toContain("ZEPHYR_SQUAD");
    expect(Object.values(CredentialTypes)).not.toContain("ZephyrSquad");
  });

  it("contains MSExchange, mirroring the backend credential type", () => {
    expect(Object.keys(CredentialTypes)).toContain("MS_EXCHANGE");
    expect(CredentialTypes.MS_EXCHANGE).toBe("MSExchange");
  });
});
