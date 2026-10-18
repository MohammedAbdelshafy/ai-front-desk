import { appointments, patients, questionnaireResponses, questionnaireTemplates } from "./fixtures";
import type { Appointment, Patient, QuestionnaireResponse, QuestionnaireTemplate } from "../domain/types";

export function getPatients(): Patient[] { return patients.map((patient) => ({ ...patient })); }
export function getPatientById(id: string): Patient | null {
  if (!/^demo-patient-\d{3}$/.test(id)) return null;
  const value = patients.find((patient) => patient.id === id);
  return value ? { ...value } : null;
}
export function getAppointments(): Appointment[] { return appointments.map((item) => ({ ...item })); }
export function getAppointmentById(id: string): Appointment | null {
  if (!/^demo-appt-\d{3}$/.test(id)) return null;
  const item = appointments.find((appointment) => appointment.id === id);
  return item ? { ...item } : null;
}
export function buildAppointmentContext(appointmentId: string): { appointmentId:string; patientId:string; patient:Patient; appointment:Appointment; questionnaire:QuestionnaireResponse | null } | null {
  const appointment = getAppointmentById(appointmentId);
  if (!appointment || !appointment.isSynthetic) return null;
  const patient = getPatientById(appointment.patientId);
  if (!patient || !patient.isSynthetic || patient.id !== appointment.patientId) return null;
  const questionnaire = questionnaireResponses.find((response) => response.id === appointment.questionnaireId && response.patientId === patient.id && response.appointmentId === appointment.id) ?? null;
  return { appointmentId: appointment.id, patientId: patient.id, patient, appointment, questionnaire };
}
export function getQuestionnaireTemplates(): QuestionnaireTemplate[] { return questionnaireTemplates.map((x) => ({ ...x })); }
export function getQuestionnaireTemplate(id: string): QuestionnaireTemplate | null { return questionnaireTemplates.find((item) => item.id === id) ?? null; }
export function getQuestionnaireResponses(): QuestionnaireResponse[] { return questionnaireResponses.map((x) => ({ ...x })); }
export function getQuestionnaireResponse(id: string): QuestionnaireResponse | null { return questionnaireResponses.find((x) => x.id === id) ?? null; }
