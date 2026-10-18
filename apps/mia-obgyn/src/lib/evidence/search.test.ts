import { describe, expect, it } from "vitest";
import { searchObgynSources } from "./search";

describe("OB-GYN reference retrieval", () => {
  it("surfaces postpartum bleeding guidance", () => {
    const results = searchObgynSources("postpartum haemorrhage bleeding after birth", { jurisdiction: "EG" });
    expect(results.some((item) => item.id === "who-pph-guideline-2025")).toBe(true);
    expect(results.every((item) => item.url.startsWith("https://"))).toBe(true);
  });

  it("does not present US-only sources as Egypt authorities", () => {
    const results = searchObgynSources("preeclampsia hypertension pregnancy", { jurisdiction: "EG" });
    expect(results.some((item) => item.jurisdiction.includes("US") && !item.jurisdiction.includes("GLOBAL_REFERENCE"))).toBe(false);
  });

  it("returns no random medicine recommendation on no match", () => {
    const results = searchObgynSources("made-up fictional obscure topic", { jurisdiction: "EG" });
    expect(results).toEqual([]);
  });
});
