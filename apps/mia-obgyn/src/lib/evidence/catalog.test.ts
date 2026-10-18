import { describe, expect, it } from "vitest";
import { loadObgynCatalog, sourceMatchesJurisdiction } from "./catalog";

describe("OB-GYN evidence catalog",()=>{
 const catalog=loadObgynCatalog();
 it("has a unique, attributed, HTTPS reference directory",()=>{
  expect(catalog.length).toBeGreaterThanOrEqual(20);
  expect(new Set(catalog.map(s=>s.id)).size).toBe(catalog.length);
  expect(catalog.every(s=>s.url.startsWith("https://")&&s.title&&s.reuse_rights&&s.ingest_status)).toBe(true);
 });
 it("keeps US-only clinical authority out of Egypt mode",()=>{
  const us=catalog.find(s=>s.id==="acog-preeclampsia-practice-bulletin")!;
  expect(sourceMatchesJurisdiction(us,"EG")).toBe(false);
 });
 it("allows a clearly tagged global-reference source to appear as context",()=>{
  const source=catalog.find(s=>s.id==="ncbi-lactmed")!;
  expect(sourceMatchesJurisdiction(source,"EG")).toBe(true);
 });
});
