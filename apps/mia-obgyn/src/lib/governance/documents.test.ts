import { describe, expect, it } from "vitest";
import manifest from "@/data/governance-docs.json";
describe("governance readiness",()=>{
 it("blocks live use while required professional reviews remain incomplete",()=>{
  expect(manifest.documents.length).toBeGreaterThanOrEqual(15);
  expect(manifest.documents.every((x)=>x.blocksLiveUse&&x.status==="review_required")).toBe(true);
  expect(manifest.documents.some((x)=>x.status.startsWith("approved"))).toBe(false);
  expect(manifest.notice).toMatch(/DRAFT/);
 });
});
