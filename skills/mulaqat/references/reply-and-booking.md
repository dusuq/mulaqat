# Reply handling and booking

## Classify the reply

| Type       | Signs                                            | Next move                                                        | Stage       |
| ---------- | ------------------------------------------------ | ---------------------------------------------------------------- | ----------- |
| Interested | Asks about price, details, "how would this work" | One clarifying question from the service card, then offer a call | `qualified` |
| Question   | Asks something specific                          | Answer briefly, then a soft call offer                           | `replied`   |
| Objection  | Price, timing, "we already have a vendor"        | Acknowledge, one reframe, offer a no-pressure 20-minute look     | `replied`   |
| Not now    | "Maybe later", "next quarter"                    | Ask when to check back, set `--next` to that date                | `replied`   |
| No / stop  | Declines, asks not to be contacted               | Short thanks, never contact again                                | `lost`      |

Common reframes:

- **Price:** "Fair. Most clients start with one workflow so the cost is small and the result is measurable. Want me to show what that first step would look like?"
- **Have a vendor:** "Makes sense. If there's one thing it doesn't do well, I'm happy to give a second opinion — no switch needed."
- **No time:** "Understood. The call is 20 minutes and you'd leave with a written plan whether or not we work together."

## Offer the call

With a booking link:

> Easiest is to pick a time that suits you here: <booking link>. It's a 30-minute call — I'll come with a rough plan for your case.

Without a link — 2–3 slots in **their** time zone and the user's. Confirm their time zone first; if unknown, ask.

> Would any of these work? Tue 18 Nov, 3:00 pm your time (5:00 pm PKT) · Wed 19 Nov, 11:00 am your time (1:00 pm PKT) · Thu 20 Nov, 4:00 pm your time (6:00 pm PKT)

## After a time is agreed

1. **Calendar invite** — title `Discovery call — <Name> × <User> | <Service>`; agenda: their current setup, the main pain, what a first step could look like, next steps; meeting link placeholder. Create it only with approval and a connected calendar tool.
2. **Confirmation message** — date and time in both zones, link, one line on what to bring.
3. **Reminder** — 24 hours before, one line.
4. **Call brief (one page)** — who they are; company and size; likely pain; service fit; 5 questions to ask; one relevant real result; suggested next step (proposal, pilot, quote).
5. Tracker: `update --id <id> --stage booked --next <call date>`.

## No-show

Send one friendly reschedule message with the booking link. If there's no answer, stop.
