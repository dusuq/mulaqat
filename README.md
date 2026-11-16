# Mulaqat — ملاقات

**A Claude skill that turns LinkedIn into booked discovery calls — without getting your account banned.**

_Mulaqat_ is Urdu for "meeting". It helps freelancers, agencies and consultants find the right prospects on LinkedIn, write personal outreach, handle replies, book calls, and keep a steady flow of LinkedIn posts and articles.

[![test](https://github.com/dusuq/mulaqat/actions/workflows/test.yml/badge.svg)](https://github.com/dusuq/mulaqat/actions/workflows/test.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)

---

## Why it drafts instead of auto-sending

LinkedIn's User Agreement (section 8.2) and its [Prohibited software and extensions](https://www.linkedin.com/help/linkedin/answer/a1341387) page ban tools that scrape LinkedIn or automatically connect, message, comment or post for you. Accounts that use them get restricted or shut down — and your LinkedIn account is the asset you're trying to grow.

So Mulaqat does everything around the click: research, writing, queuing, tracking, booking. You approve and send. Ten to fifteen minutes a day.

Posting to your **own profile** through LinkedIn's official API is allowed, so content can be published that way once you approve it.

## What it does

| Area            | What you get                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Profile**     | Headline, About, Featured and banner copy that brings inbound leads                                                   |
| **Prospects**   | Ideal-customer profile per service, LinkedIn search filters, buying-intent signals, short notes on profiles you paste |
| **Daily queue** | Numbered list of connection notes, follow-ups, replies and comments — approve with "1, 3, 5"                          |
| **Outreach**    | Personal connection notes (≤200 chars), first message, two follow-ups, then stop                                      |
| **Replies**     | Classifies each reply (interested / question / objection / not now / no) and drafts the answer                        |
| **Booking**     | Booking link or slots in both time zones, invite draft, confirmation, reminder, one-page call brief                   |
| **Content**     | Weekly post calendar, posts, carousel outlines, 700–1,200-word articles                                               |
| **Tracking**    | CSV pipeline tracker with due list, safe weekly limits, stale invites and a funnel report                             |

It ships with a catalog for a software/automation agency — WhatsApp AI agents, CRM, POS, ERP, PWAs, WordPress, e-commerce, AI automation, ads — and you swap in your own services in a config file.

## Install

### Claude Code (plugin)

```text
/plugin marketplace add dusuq/mulaqat
/plugin install mulaqat@mulaqat
```

### Claude Code (plain skill)

```bash
git clone https://github.com/dusuq/mulaqat.git
mkdir -p ~/.claude/skills
cp -r mulaqat/skills/mulaqat ~/.claude/skills/
```

### Claude.ai / Claude desktop app

1. Download this repo as a ZIP and unzip it.
2. Zip just the `skills/mulaqat` folder (so `mulaqat/SKILL.md` is at the top of the zip).
3. In Claude, open **Settings → Capabilities → Skills**, upload the zip, and turn it on.

(Skill settings can move between app versions; if you can't find them, check Anthropic's help pages for "skills".)

## Use it

Just ask in your own words, in any language:

- "Set up Mulaqat for me" — creates your `mulaqat.config.md`
- "Find prospects for WhatsApp automation in the UAE"
- "What's my queue today?"
- "Here's a reply I got: …"
- "Book a call with Sara"
- "Plan this week's LinkedIn posts"
- "Write an article on why small shops need a POS"
- "Weekly report"

## Configure

Copy the template from [`skills/mulaqat/references/config-template.md`](skills/mulaqat/references/config-template.md) into `mulaqat.config.md` in your working folder (or let Mulaqat create it). Fill in your services with **real** results, target markets, booking link and time zone. Mulaqat never invents results — it leaves `[ADD REAL RESULT]` where proof is missing.

`mulaqat.config.md` and `mulaqat-pipeline.csv` are in `.gitignore`: they hold your prospects' data, so keep them out of public repos.

## The tracker

`skills/mulaqat/scripts/tracker.py` is a standalone, standard-library Python script (3.9+). Claude runs it for you, but you can use it directly:

```bash
T=skills/mulaqat/scripts/tracker.py
python3 $T add --name "Sara Khan" --company "Acme Retail" --service "WhatsApp AI agents" --country UAE
python3 $T update --id 1 --stage requested --next 2026-11-19
python3 $T queue          # what's due today
python3 $T limits         # requests in the last 7 days vs the safe cap (80, or 30 with --small-account)
python3 $T stale          # requests pending > 21 days — withdraw them
python3 $T report         # acceptance rate, reply rate, booked, won
```

Stages: `found → requested → connected → messaged → replied → qualified → booked → won / lost`.

## Safety limits built in

|                     | Commonly observed       | Mulaqat keeps you at                           |
| ------------------- | ----------------------- | ---------------------------------------------- |
| Connection requests | ~100 per rolling 7 days | ≤80/week, ≤20/day (30/week for small accounts) |
| Connection note     | 300 characters          | ≤200                                           |
| Pending invitations | ~1,500                  | withdraw after 21 days                         |
| Follow-ups          | —                       | 2 max, and never after a "no"                  |

LinkedIn doesn't publish these numbers; see [`references/linkedin-limits.md`](skills/mulaqat/references/linkedin-limits.md) for sources.

## Repository layout

```text
.claude-plugin/          plugin + marketplace manifests
skills/mulaqat/
  SKILL.md               the skill Claude loads
  references/            playbooks: services, outreach, replies & booking, content, limits, config
  scripts/tracker.py     CSV pipeline tracker
tests/                   unit tests (python -m unittest discover -s tests)
```

## Contributing

Issues and pull requests are welcome — especially new service catalogs, playbooks for other industries, and translations. Run `python -m unittest discover -s tests` before opening a PR.

## Disclaimer

Mulaqat is not affiliated with or endorsed by LinkedIn. You are responsible for how you use LinkedIn and for following its terms and local privacy laws (e.g. GDPR).

## License

[MIT](LICENSE) © 2026 Ehsan Elahi Zaheer ([DUSUQ](https://github.com/dusuq))
