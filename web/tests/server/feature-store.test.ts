import { describe, expect, it } from "vitest";

import { buildFixtureFeatures } from "@/server/predict/feature-store";

describe("feature store", () => {
  it("builds feature vector for known teams", () => {
    const fixture = buildFixtureFeatures("Arsenal", "Leeds");
    expect(fixture.context.home.canonical).toBe("arsenal");
    expect(fixture.context.away.canonical).toBe("leeds");
    expect(fixture.vector.attGap).toBeDefined();
  });

  it("rejects identical teams", () => {
    expect(() => buildFixtureFeatures("Arsenal", "Arsenal")).toThrow();
  });

  it("rejects unknown team", () => {
    expect(() => buildFixtureFeatures("Arsenal", "Unknown FC")).toThrow();
  });
});
