import { searchObgynSources, type MatchedSource, type SearchFilters } from "./search";

export type EvidenceAnswer = {
  status: "references_found" | "insufficient_evidence";
  summary: string;
  sources: MatchedSource[];
  matchReasons: string[];
  limitations: string[];
  clinicianChecks: string[];
  approvedMedicationPathway: false;
};

export function buildReferenceAnswer(input: { question: string; filters: SearchFilters; selectedContext?: string[] }): EvidenceAnswer {
  const question = input.question.trim().slice(0, 240);
  const sources = searchObgynSources(question, input.filters);
  const found = sources.length > 0;
  return {
    status: found ? "references_found" : "insufficient_evidence",
    summary: found
      ? "I found reference pages that may help you review this topic. These are source-directory matches, not a validated clinical interpretation or a medication recommendation."
      : "I could not find a relevant source in this directory for that wording. Do not infer that a medicine is safe or that guidance does not exist. Try alternative terms or consult the current local protocol/senior clinician.",
    sources,
    matchReasons: sources.map((s) => `${s.title}: matched ${s.matchReason || "source metadata"}`),
    limitations: [
      "No clinical pathway in this prototype has been approved for prescribing.",
      "A source match is not evidence grading, diagnosis, interaction checking, or individualized treatment advice.",
      "This prototype has no external model call and should not receive real patient data.",
      ...(input.selectedContext?.length ? ["Only selected fictional demo context is attached; all case-specific decisions require clinician verification."] : []),
    ],
    clinicianChecks: [
      "Confirm the clinical question and relevant clinical findings.",
      "Check allergies and reactions, current medicines, history, gestational stage and breastfeeding status when relevant.",
      "Verify the exact locally marketed product, current national guidance, contraindications, interactions and monitoring using approved clinical resources.",
      "Follow the hospital's escalation pathway for urgent or deteriorating cases.",
    ],
    approvedMedicationPathway: false,
  };
}
