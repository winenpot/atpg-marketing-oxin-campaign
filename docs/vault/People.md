---
type: domain
---

# People

## The user (backend, data, operations — technical lead in practice)

Software engineer, recently joined this FMCG company; one of two people in
its AI/software department. Previously a junior Python backend dev
(Django, FastAPI, REST). Strong ML/statistics background; newer to
Docker/infra/DevOps. Spent ~10 years in the gaming lounges this project
targets — the real domain expert on the player audience, more than Mehdi.
Writes in English and Persian; messages to Arman are in Persian with
English technical terms kept as-is.

Full background and working-style notes: see the global vault's
`Preferences/About the User.md` (cross-project, not repeated here).

## Mehdi — marketing manager

Originated the campaign idea; the CEO approved it and struck the lounge
deal. Not a gamer, not the domain expert — the user is. Owns the business
side: factory/printing liaison, legal counsel, prize economy and budget,
lounge relations, launch comms, daily approval of social-challenge
submissions. RACI in `../../TEAM.md:20-31`; his TODO items are M01–M15 in
`../../TODO.md:106-124`.

How to work with him (`../../TEAM.md:62-72`): give him decisions with a
default and a deadline, not open problems; use his strengths (factory,
legal, lounges, comms) and make that visible to the CEO; write down any
verbal decision as a three-line message (decided / owner / deadline);
never surprise him in front of the CEO.

The user is openly frustrated with him at times (non-technical origin of
the idea, pitched without knowing the gamer audience). Stay professional
and steady when this comes up — don't join in, don't lecture.

## Arman — frontend developer (external)

Builds the player-facing PWA: static build (Vite + React + TS likely),
RTL layout, self-hosted fonts, consumes the API in `../../docs/API_CONTRACT.md`.
His TODO items are A01–A19 in `../../TODO.md:80-104`.

How to work with him (`../../TEAM.md:45-60`): the API contract is the
source of truth and changes go through it first; staging is the shared
reality from D2 onward; same-day answers in one chat thread; a 10-minute
call beats a long thread; "definition of done" for a screen includes
contract match, Persian error copy, loading/empty/offline states, and
testing on a real Android and iPhone.

He was asked (Persian, via the user) to research QR codes carrying a
variable and SMS OTP autofill. The `/r/:code` guidance already given to
him matches the QR-link decision made 2026-10-07 (path form, not a URL
fragment) — see [[Decisions]] — so no correction is needed there.

## CEO

Approves money, scope, and chairs the go/no-go meeting (`../../TEAM.md:20-31`,
`../../TODO.md:126-134`). Appears in the RACI table but has no items tracked
in this vault beyond that.

## Durability note

This project (and the people in it) may be a single-engagement context —
Mehdi, Arman, and the campaign specifics belong here, in the project vault,
not in Hermes's cross-project memory. Only the user's own lasting traits
and working style travel across projects (global vault).
