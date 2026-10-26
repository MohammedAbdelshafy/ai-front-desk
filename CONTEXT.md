---
type: repository
status: active
owner_repo: MohammedAbdelshafy/ai-front-desk
product_name: Mia Dental OS
source_of_truth: https://github.com/MohammedAbdelshafy/ai-front-desk
---

# Mia Dental OS CONTEXT

One job: help a clinic or service team organize first inquiries and hand off the next action, without pretending a demo is live.

## Inputs
- Commands and limits: [README](README.md)
- Implementation: [ai_front_desk](ai_front_desk/)
- Tests: [tests](tests/)
- Customer wording: [Jarvis ICM language guide](https://github.com/MohammedAbdelshafy/jarvis-mbm/blob/feature/icm-portfolio-map/ICM/_shared/customer-language.md)

## Process
1. Collect only the information needed for the stated administrative task.
2. Validate the request and flag missing or conflicting answers.
3. Route issues needing staff judgment to a human.
4. Keep the default behavior dry-run until the actual provider and delivery path are verified.
5. For the dental demo, use fictional patient records only. Clinical forms require qualified dentist review.
6. Do not claim live bookings, a live AI model, production authentication, compliance certification or medication guidance unless independently verified.

## Output
An intake summary, an explicit handoff and a clear record of what still needs staff attention.

## Check
Run the documented test suite. Verify the actual configuration before enabling messages. Never use real patient data in the demo or automate diagnosis/prescribing.
