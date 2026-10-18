import type { QuestionnaireQuestion, QuestionnaireResponse, QuestionnaireTemplate } from "../domain/types";

export type ValidationResult = { valid:boolean; missing:string[]; hiddenUnanswered:string[] };
export function shouldShowQuestion(question: QuestionnaireQuestion, answers: Record<string,string>): boolean {
  if (!question.showIf) return true;
  return answers[question.showIf.questionId] === question.showIf.equals;
}
export function validateQuestionnaire(template: QuestionnaireTemplate, answers: Record<string,string>): ValidationResult {
  const missing:string[]=[];
  const hiddenUnanswered:string[]=[];
  for (const question of template.questions) {
    const answer=(answers[question.id] ?? "").trim();
    if (!shouldShowQuestion(question,answers)) {
      if (answer) hiddenUnanswered.push(question.id);
      continue;
    }
    if (question.required && !answer) missing.push(question.id);
  }
  return {valid:missing.length===0,missing,hiddenUnanswered};
}
export function createDemoSubmission(template:QuestionnaireTemplate,answers:Record<string,string>,patientId:string,appointmentId:string):QuestionnaireResponse {
  const result=validateQuestionnaire(template,answers);
  if (!result.valid) throw new Error(`Missing required answers: ${result.missing.join(", ")}`);
  const visibleAnswers=Object.fromEntries(Object.entries(answers).filter(([key])=>template.questions.some((question)=>question.id===key && shouldShowQuestion(question,answers))));
  return {id:`demo-response-${Date.now()}`,templateId:template.id,templateVersion:template.version,patientId,appointmentId,answers:visibleAnswers,status:"submitted",submittedAt:new Date().toISOString(),isSynthetic:true};
}
