import { describe, expect, it } from "vitest";
import { questionnaireTemplates } from "../demo/fixtures";
import { createDemoSubmission, shouldShowQuestion, validateQuestionnaire } from "./engine";

describe("pre-visit questionnaire engine", () => {
  const template = questionnaireTemplates[0];
  it("shows conditional details only when the parent answer activates them", () => {
    const followUp = template.questions.find((x) => x.id === "allergy-details")!;
    expect(shouldShowQuestion(followUp, { allergies: "Yes" })).toBe(true);
    expect(shouldShowQuestion(followUp, { allergies: "Not sure" })).toBe(false);
  });
  it("requires critical intake fields without treating unknown as no", () => {
    expect(validateQuestionnaire(template, { reason:"Question", "symptom-onset":"Not sure", pain:"no", bleeding:"no", pregnancy:"Not sure", breastfeeding:"Not sure", allergies:"Not sure", medicines:"not sure", "consent-understanding":"Understood" }).valid).toBe(true);
    expect(validateQuestionnaire(template, { reason:"", allergies:"" }).valid).toBe(false);
  });
  it("pins submissions to the exact questionnaire version and removes hidden answers", () => {
    const answers = {reason:"Test", "symptom-onset":"Today",pain:"no",bleeding:"no",pregnancy:"Not sure",breastfeeding:"No",allergies:"No known allergies","allergy-details":"should be hidden",medicines:"Not sure","consent-understanding":"Understood"};
    const response = createDemoSubmission(template, answers, "demo-patient-001", "demo-appt-001");
    expect(response.templateVersion).toBe(1);
    expect(response.answers["allergy-details"]).toBeUndefined();
  });
});
