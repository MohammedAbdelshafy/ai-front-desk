import { describe, expect, it } from "vitest";
import { buildReferenceAnswer } from "./answer";

describe("reference answer safety boundary", () => {
  it("never claims an approved medication pathway in phase one", () => {
    const answer = buildReferenceAnswer({question:"medicine for preeclampsia in pregnancy",filters:{jurisdiction:"EG"}});
    expect(answer.approvedMedicationPathway).toBe(false);
    expect(answer.limitations.some((item)=>item.includes("No clinical pathway"))).toBe(true);
  });
  it("abstains explicitly when no reference matches", () => {
    const answer = buildReferenceAnswer({question:"marmalade spacecraft",filters:{jurisdiction:"EG"}});
    expect(answer.status).toBe("insufficient_evidence");
    expect(answer.summary).toMatch(/could not find/i);
  });
  it("returns source metadata and explicit clinician checks", () => {
    const answer = buildReferenceAnswer({question:"postpartum haemorrhage",filters:{jurisdiction:"EG"}});
    expect(answer.sources.length).toBeGreaterThan(0);
    expect(answer.sources.every((s)=>s.url.startsWith("https://"))).toBe(true);
    expect(answer.clinicianChecks.length).toBeGreaterThan(0);
  });
});
