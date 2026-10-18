import { describe, expect, it } from "vitest";
import { getPatientById, getPatients, getAppointmentById, buildAppointmentContext } from "./repositories";

describe("synthetic OB-GYN repositories", () => {
  it("returns only clearly synthetic patients", () => {
    const patients = getPatients();
    expect(patients.length).toBeGreaterThanOrEqual(4);
    expect(patients.every((patient) => patient.isSynthetic)).toBe(true);
    expect(patients.every((patient) => patient.id.startsWith("demo-"))).toBe(true);
  });

  it("keeps unknown allergies distinct from no known allergies", () => {
    const unknown = getPatientById("demo-patient-004");
    expect(unknown?.allergyStatus).toBe("unknown");
    expect(getPatientById("demo-patient-001")?.allergyStatus).toBe("confirmed-none");
  });

  it("returns null for invalid patient or appointment IDs", () => {
    expect(getPatientById("../../etc/passwd")).toBeNull();
    expect(getAppointmentById("made-up-id")).toBeNull();
  });

  it("does not carry one appointment's patient context into another", () => {
    const first = buildAppointmentContext("demo-appt-001");
    const second = buildAppointmentContext("demo-appt-002");
    expect(first).not.toBeNull();
    expect(second).not.toBeNull();
    expect(first?.patientId).not.toBe(second?.patientId);
    expect(second?.patientId).not.toEqual(first?.patientId);
  });
});
