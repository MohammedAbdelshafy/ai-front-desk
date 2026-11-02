# Privacy Policy — Mia Dental OS

> **DRAFT v0.1 — 2026-10-11 — requires qualified legal review before production use or real patient data.**
> This is a starting draft, not legal advice. It has not been reviewed by an attorney.

**Operator:** MBM (Mohammed Abdelshafy)
**Contact:** abdelshafyclapps@gmail.com
**Product:** Mia Dental OS, including the Mia Dental Prescribing Copilot
**Applies to:** dentists and clinic staff who create an account or use the demo

## 1. What we collect

**Account information (you provide it):**
- Full name, work email address, clinic name, and a password (stored only as a salted cryptographic hash — we never store your plaintext password).
- Records of your acceptance of our Terms of Service and Privacy Policy (document version + timestamp).

**Clinical workspace data (you enter it):**
- Patient labels you create (demo labels only at this stage), reported allergies, current medications, medical conditions, guided-questionnaire answers, intended prescriptions you choose to check, safety-check results, and your own recorded review conclusions.
- Audit log entries: who performed which action and when.

**Technical data:**
- Session cookies required to keep you signed in (HttpOnly, SameSite=Lax).
- Server logs: timestamps, request paths, and error diagnostics. We do not run advertising trackers or third-party analytics on clinical pages.

## 2. Why we collect it

- To provide the prescribing copilot workspace: storing your patient context is what makes the safety check possible.
- To manage accounts, trials, and subscriptions.
- To maintain the audit log, which is a core safety feature of the product.
- To detect abuse (e.g., repeated failed sign-ins) and keep the service secure.

## 3. What we do NOT do

- We do not sell your data or your patients' data. Ever.
- We do not use clinical data for marketing, advertising, or training unrelated products.
- We do not share identifiable data with third parties except as required by law or as described in section 5.

## 4. Where data lives

Data is stored in a local SQLite database on the deployment server. **This is demo-grade storage.** It is not currently HIPAA-compliant, and we do not offer a Business Associate Agreement (BAA) at this stage. **Do not enter real patient data into the demo or pilot until we confirm compliant hosting in writing.**

## 5. Disclosure

We may disclose information only:
- With your explicit instruction (e.g., you export your own records);
- To comply with a valid legal obligation;
- To protect the security of the service or prevent fraud.

## 6. Retention and deletion

See [Data Retention & Deletion](data-retention-deletion.md). In short: account data is kept while your account is active; you may request export or deletion at any time by emailing abdelshafyclapps@gmail.com; anonymized audit minimums may survive deletion as described there.

## 7. Your rights

You may at any time request: a copy of your data (export), correction of inaccurate data, or deletion of your account and associated data, by emailing abdelshafyclapps@gmail.com. We will respond within 30 days.

## 8. Cookies

We use one strictly-necessary session cookie (`mia_session`) to keep you signed in. It is HttpOnly and SameSite=Lax. We do not use advertising or cross-site tracking cookies.

## 9. Children

This service is for licensed dental professionals and their staff. It is not directed at children.

## 10. Changes

We will post material changes to this policy in the app and update the version number. Continued use after a change takes effect constitutes acceptance.

## 11. Contact

Privacy questions: abdelshafyclapps@gmail.com
