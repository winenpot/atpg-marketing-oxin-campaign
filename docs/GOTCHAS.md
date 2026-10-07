# Gotchas and watch-outs

Things that look small and sink projects like this one. Each line: the trap, then what to do.
Skim it on D1, again on D8, and before launch.

## Contents

- [Codes and printing](#codes-and-printing)
- [Legal and prizes](#legal-and-prizes)
- [Hosting and the network in Iran](#hosting-and-the-network-in-iran)
- [SMS sign-in](#sms-sign-in)
- [The lounges](#the-lounges)
- [Time and calendars](#time-and-calendars)
- [Persian text and right-to-left](#persian-text-and-right-to-left)
- [Cheating and insiders](#cheating-and-insiders)
- [Data and operations](#data-and-operations)
- [Frontend](#frontend)
- [Process](#process)
- [Sources](#sources)

## Codes and printing

| Trap | Do this |
|---|---|
| Short or "formula" codes (7–8 digits, or derivable) are farmed by scripts within days | 10 random Base32 characters + check character ([CODES.md](CODES.md#2-why-this-format)) |
| Code readable before opening (outside of the can, visible through a vending machine window) | Hidden placement is a hard requirement for the factory (Q1) |
| The printer CSV is the only plaintext copy and travels by email or chat | Encrypted archive, passphrase by phone, checksum confirmation, written deletion ([CODES.md](CODES.md#handing-codes-to-the-printer)) |
| Batches redeemable before the product is on sale | Keep them `generated`; activate at launch |
| Changing the pepper after printing | Never: every stored hash depends on it. Two people hold it in a password manager |
| Changing the alphabet, city indexes or check algorithm after printing | Frozen once the first batch is printed |
| A QR that is too dense for a small cap | Test print first; error correction M or Q; a shorter domain shrinks the QR; an all-uppercase URL can drop one QR size if routed ([CODES.md](CODES.md#1-specification-for-the-factory)) |
| Factory late | Code-card fallback, one batch per lounge ([CODES.md](CODES.md#7-plan-b-situations)) |

## Legal and prizes

| Trap | Do this |
|---|---|
| A purchase-linked draw can be treated as illegal gambling or fraud; Iranian judicial authorities have publicly warned about sales lotteries | Written legal opinion and any required permit/supervision **before** announcing a draw (L01); launching coins/challenges without the draw is a valid fallback |
| Teenagers among players: can they take part, win, travel? | Rules for minors from legal (L03); guardian consent; no travel prize to a minor without a guardian arrangement |
| Travel prizes: passports, visa refusals, and **conscription-age men usually need an exit permit (often with a bail deposit) unless they finished or are exempt from military service** | Written prize terms: eligibility, deadlines, what happens if travel is impossible (alternative prize or cash), who pays fees and taxes (L04) |
| Prize goes to a fake or farmed account | Identity check at claim time (mobile number matched to national ID through a licensed inquiry service); one prize per person |
| Promotional SMS without consent | Only OTP messages through the OTP route; marketing messages only with opt-in (L05) |
| No T&Cs or privacy notice at launch | L02 by D12; consent version stored per player |

## Hosting and the network in Iran

| Trap | Do this |
|---|---|
| Foreign hosting goes dark when international links are cut (as in June 2025, when the domestic network stayed up) | Domestic VMs ([ADR-0006](adr/0006-domestic-single-vm-docker-compose.md)) |
| Docker Hub refuses Iranian IPs; other registries can be blocked or slow | Domestic registry mirror in `daemon.json`, or `docker save`/`load`; pin images by digest ([OPERATIONS.md](OPERATIONS.md#getting-images-and-packages-onto-the-server)) |
| PyPI/npm mirrors you do not control | Install from hash-locked files (`requirements.txt` with hashes, `npm ci`); one index only, never `--extra-index-url` |
| Google Fonts, foreign CDNs, reCAPTCHA, analytics tags: blocked or slow, and the page hangs waiting for them | Self-host everything; no third-party scripts ([ADR-0007](adr/0007-static-pwa-same-origin.md)) |
| Telegram or foreign SaaS for alerts and error tracking: unreachable from a domestic server | SMS/email alerts; self-hosted Uptime Kuma and GlitchTip |
| Instagram's accessibility changes (filtered since 2022, briefly reachable in mid-2025) | Never make the server depend on reaching it; social posts are verified by a human |
| Let's Encrypt renewal needs international connectivity | Certificates renew 30 days early; monitor expiry; a domestic certificate is the fallback |
| Clock drift when international NTP is blocked | Configure domestic NTP servers; database time is the source of truth |

## SMS sign-in

| Trap | Do this |
|---|---|
| Bulk/advertising route: slow, blocked by users' ad opt-outs, needs consent | Use the provider's OTP/verify template route |
| Anything appended after `@domain #code` breaks Android autofill silently | Approve the template with that exact last line; test on a real Android and iPhone ([OPERATIONS.md](OPERATIONS.md#sms-provider)) |
| SMS pumping drains credit overnight | Cooldown and daily cap per number, nginx limit per IP, global hourly ceiling, spend alert ([SECURITY.md](SECURITY.md#threats-and-controls) T6) |
| Provider outage blocks all new sign-ins | Second provider with automatic fallback; existing sessions keep working |
| Some providers put the API key in the URL | Never log SMS request URLs |
| Retrying a timed-out send sends the code twice | Acceptable for OTP (same code); cap attempts; drop jobs older than the code's lifetime |

## The lounges

| Trap | Do this |
|---|---|
| All players in a lounge share **one public IP**: per-IP limits lock out the whole lounge | Lounge IPs in `lounge_ips.conf` with their own large budget; per-account limits do the real work |
| Lounge PCs are shared: a player who signs in on one leaves their session for the next person | Design for phones; on any shared device show "sign out" prominently; consider shorter sessions if staff report problems |
| Lounge Wi-Fi with a captive portal or flaky DNS | Test the full flow on each lounge's Wi-Fi during the field visit; mobile data as fallback |
| Staff do not understand it, so they cannot promote it | One-page staff guide, 15-minute training, a staff challenge they enjoy (M10) |
| TV leaderboard with offensive nicknames | Nickname rules and a reserved/profanity list; a "hide" action in admin |

## Time and calendars

| Trap | Do this |
|---|---|
| "Today" computed in UTC: the daily reset happens at 03:30 Tehran time | Days and weeks in `Asia/Tehran` on the server ([ARCHITECTURE.md](ARCHITECTURE.md#time)) |
| Iran stopped daylight saving time in 2023; old phones and old time-zone data still shift the clock | Never trust the phone's clock for game days; use `/config` from the server; keep `tzdata` current |
| The Iranian week starts on Saturday | Weekly boards reset Saturday 00:00 Tehran |
| Players think in Jalali dates | Store UTC; display Jalali in the app |
| Cron at a local time on a server in a DST zone fires twice or never | Server and cron in UTC |

## Persian text and right-to-left

| Trap | Do this |
|---|---|
| Phones type Persian digits `۰۱۲۳`; the server rejects them | The code parser and phone normalizer convert them (done for codes) |
| Arabic `ي`/`ك` vs Persian `ی`/`ک` make "the same" nickname twice | Fold them in the uniqueness key |
| Removing all zero-width characters breaks Persian words (ZWNJ is needed) | Allow ZWNJ inside words; reject other invisible characters and direction overrides |
| A Latin code inside an RTL sentence renders scrambled (`TO-7KQ2` reversed around dashes) | Wrap codes in `<bdi dir="ltr">` or an element with `dir="ltr"` |
| Input fields for codes inherit RTL | `dir="ltr"` on code and phone inputs |

## Cheating and insiders

| Trap | Do this |
|---|---|
| One person, many SIM cards | Caps per account, human review of the top 20 weekly, identity check at prize claim |
| Codes photographed and shared in groups | First redeemer wins (by design); hidden placement reduces it; watch heavy redeemers in the daily check |
| Staff granting coins to friends | Adjustments are ledger rows with a name and a reason; daily report by person; adjustments do not count on leaderboards |
| Fake social posts (deleted after approval, other people's posts) | Check the account handle against the player's profile; reviewers spot-check approved posts a week later |
| Bots hammering the API | nginx limits, per-account throttles, alerts on unusual rates |

## Data and operations

| Trap | Do this |
|---|---|
| Backups that have never been restored | Weekly `restore_check.sh`; record the time |
| Losing the restic password or the pepper | Password manager with two holders, tested retrieval |
| A destructive migration during the campaign makes rollback impossible | Additive migrations only; expand → migrate → contract across releases |
| Disk fills with Docker logs | Log rotation is set in the Compose file; disk alert at 80% |
| Editing balances directly in the database "just this once" | Never; compensating ledger entries only (the database refuses ledger edits anyway) |
| Running scripts as `python scripts/x.py` fails with `No module named 'app'` | Run them as modules: `python -m scripts.generate_codes` |
| Load test against production | Staging only; `loadtest_sessions` refuses production |

## Frontend

| Trap | Do this |
|---|---|
| Tokens in `localStorage` | The session is an HttpOnly cookie; JavaScript never sees it |
| Inline scripts break the Content-Security-Policy | Bundle all JavaScript; no `eval` |
| A service worker caching API responses shows stale balances | Cache only the app shell; never `/api/` |
| WebOTP does not exist on iPhone | `autocomplete="one-time-code"` covers iPhone; WebOTP is a bonus on Android |
| The QR code stays in the URL and in history | `history.replaceState` after redeeming |
| Dev server on `http://localhost` and Secure cookies | Proxy `/api` to staging; use HTTPS locally if the cookie does not stick |

## Process

| Trap | Do this |
|---|---|
| New ideas after D8 | Swap rule: something of equal size leaves the scope, in writing |
| Decisions made in a call and forgotten | Three-line written summary after every call |
| Status meetings instead of demos | Demos on staging at M1, M2, M3 |
| External dependencies discovered on D12 | Critical path items start D1 ([ROADMAP.md](../ROADMAP.md#critical-path-things-with-lead-times-we-do-not-control)) |

## Sources

- Docker Hub blocking Iranian users: [Using docker registry from Iran](https://ahmadallish.substack.com/p/using-docker-registry-from-iran-65e1a4efffcc)
- June 2025 disruption with the domestic network up: [Filterwatch, June 2025 network monitoring](https://filter.watch/english/2025/06/19/network-monitoring-june-iran-internet-status-week-1-of-israel-iran-war/)
- Iran without daylight saving time since 2023: [IANA tz mailing list](https://lists.iana.org/hyperkitty/list/tz@iana.org/message/YT372IZNNPS3LDAKFPCNTHMR3MMZTMXF/)
- WebOTP message format and browser support: [Chrome for Developers, WebOTP API](https://developer.chrome.com/docs/identity/web-apis/web-otp)
- Instagram temporarily reachable in June 2025: [IranWire](https://iranwire.com/en/news/142642-iran-lifts-blocks-on-instagram-and-whatsapp-after-two-year-ban/)
- Judicial warning about sales lotteries (headline): [Jam-e Jam Online](https://jamejamonline.ir/fa/news/1529138/)
- Military-service bail for travel abroad: [Maktabkhooneh](https://maktabkhooneh.org/mag/military-bail-for-leaving-the-country/)
- Unsolicited promotional SMS: [Entekhab](https://www.entekhab.ir/fa/news/866838/)
