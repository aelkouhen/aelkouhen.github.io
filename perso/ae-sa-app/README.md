# AE + SA Working Process (app)

A single self-contained HTML file that runs the process in `../ae-sa-working-process.md`.
No build step, no server, no dependencies, no network calls.

## Run it

    open index.html

Or drop it on any static host (S3, Netlify, an internal wiki attachment, a Postman
workspace file). It is one file: `index.html`.

## What it does

- **Four phases** with the lane split ("what the AE brings" / "what the SA gives back"),
  the exit question, and the exit checks. Your role is highlighted via the AE/SA toggle.
- **MEDDPICC tracker.** Eight cards: who chases it, the question that tests it, and a
  state you cycle (unknown, assumed, validated) plus an evidence note. Two or more blanks
  raises the "the next meeting is discovery, not a demo" flag.
- **The five-field brief**, with named attendees (name, title, what they decide, depth,
  stance) and a working-day notice check against what the AE is asking for.
  In SA role the same panel becomes triage: accept, or send it back with a reason.
- **Debrief log** with a next step, an owner, and a date. Flags a missing next step and
  goes quiet-alarm after 21 days.
- **POC criteria.** Starts by asking whether a POC is needed at all. If yes, the
  five-point page, a four-week timebox check, and the one hard rule: the Advance button
  is blocked until the customer has agreed the criteria.
- **Markdown export** for the brief, the POC page, and a full deal summary, plus JSON
  export/import to hand a deal to the other half of the pair.

## Accountability, in the app rather than in a policy

- Advancing a phase with open checks forces a written reason, kept on the deal under
  "Bent deliberately". Bending the process is allowed and visible.
- One rule does not bend: no POC without agreed success criteria. That check is marked
  hard and blocks the advance.
- Sending a brief with no objective, no named attendees, or no agenda warns the AE that
  the SA is entitled to send it straight back.

## Working in tandem

It is one record with two owners, and every panel now says who fills it:

| Panel | Who fills it |
| --- | --- |
| Phase and checks | Both, own lane only. Each check is tagged AE or SA. |
| MEDDPICC | AE keeps M, E, Decision Process, Paper, Competition. SA owns Decision Criteria and the technical half of Champion. Identify Pain together. |
| Call brief | AE writes it. SA accepts it or sends it back with a reason. |
| Debriefs | Whoever ran the call, same day. Both read it. |
| POC criteria | SA drafts, AE negotiates, customer agrees. |

Because storage is local, you each hold your own copy. **Data → Copy share link for this deal**
puts the whole deal in a URL you can paste into Slack; opening it imports a copy. Let whoever
is doing the work in the current phase hold the master: the AE through Qualify, the SA through
Discover and Prove, the AE again through Close.

## Branding

Postman orange `#FF6C37` is the identity colour (logo, phase meter, focus rings, highlights).
White button text sits on `#D2481C` instead, because white on `#FF6C37` is only 2.74:1.
The official logo mark and lockup are the real SVGs from `voyager.postman.com`, embedded
inline (`postman-logo-icon-orange.svg`, `postman-logo-orange.svg`, also kept as files).
Type is Inter with a system-sans fallback, no web font fetched, so the file stays offline.

Status colours stay reserved and are never brand orange: measured against `#FF6C37` they clear
the separation gates (warning ΔE 16.1 normal / 10.6 deutan, critical 13.9 / 13.8), and every
status carries an icon and a word as well as colour. Avoid the palette's `serious #ec835a`
in this app: it sits ΔE 5.2 from brand orange and would read as the accent.

## Storage

Everything lives in this browser's localStorage. Nothing leaves the machine.
Use **Data** to export a JSON backup or import someone else's deal. If the browser
blocks storage (some `file://` configurations do), the app says so and you should
export before closing the tab.

## Tests

    ./tests/run.sh

Two headless Chrome suites, 30 assertions: 12 render/logic and 18 click-interaction
(phase advance, the hard-rule block and its release, MEDDPICC cycling, brief send and
SA return, debrief add/remove, POC gate, persistence, share-link round trip, theme and
role toggles). Set `CHROME=/path/to/chrome` if Chrome is not in `/Applications`.

The three MEDDPICC state colours were run through the CVD validator: worst pair ΔE 10.7
against an 8.0 target, normal-vision 20.2 against a 15 floor. Every state carries a dot,
a glyph, and a word, so it never depends on colour alone.
