# Contributors

The Turing Club website and registration platform is built by its members. Thank you to everyone who has contributed code, architecture, design, and testing. ❤️

This list is maintained by hand alongside the GitHub [contributors graph](https://github.com/TheTuringClubJU/turing-registration/graphs/contributors). Merged a PR or contributed code and don't see your work here? Open a PR adding your line — that counts too, and each entry here is eligible for a certificate of contribution.

## Maintainer & Core Architect

- **Darsh Vithlani** ([@CODING-DARSH](https://github.com/CODING-DARSH)) — Tech Lead & Project Maintainer
  - **Core Architecture & Repository Scaffold**: Designed domain boundaries, FastAPI application entrypoint, shared security, configuration engine, and Docker/PostgreSQL environments ([#1](https://github.com/TheTuringClubJU/turing-registration/pull/1), [#2](https://github.com/TheTuringClubJU/turing-registration/pull/2)).
  - **Database Schema & SQL Constraints**: Authored the full `schema.sql` source-of-truth, including sequential race-safe `event_counters` with `next_event_code()`, atomic attendance constraints, single-active-event index, and team caps ([#3](https://github.com/TheTuringClubJU/turing-registration/pull/3), [#4](https://github.com/TheTuringClubJU/turing-registration/pull/4)).
  - **CI/CD & DevOps Automation**: Built dual-matrix GitHub Actions CI with live PostgreSQL 16 container services, automated schema migrations, Node.js 22 LTS Vitest suite, and full test coverage reporting.
  - **Frontend Check-in Dashboard & UI Engine**: Designed and developed the Apple-inspired minimalist monochrome organiser check-in dashboard, live camera scanner with auto-detecting camera fallbacks, manual check-in interface, and responsive mobile layout ([#9](https://github.com/TheTuringClubJU/turing-registration/pull/9)).
  - **Short Ticket Codes & UX Optimisation**: Designed and implemented 6-character short ticket codes (`TTC-XXXX`) to eliminate typing 36-character UUIDs on mobile devices ([#10](https://github.com/TheTuringClubJU/turing-registration/pull/10)).
  - **1.5s Admission Feedback Animations**: Created fullscreen visual feedback overlays with animated circular checkmarks for admitted participants and red cross notifications for rejected attempts.
  - **Participant & Team Visibility**: Enriched attendance records across both backend queries and frontend cards with primary attendee names, full team member rosters, and team badges.
  - **Dynamic Event Resolution**: Implemented backend active-event detection (`GET /attendance/active-event`) and client-side `localStorage` caching to remove hardcoded event UUIDs completely ([#12](https://github.com/TheTuringClubJU/turing-registration/pull/12)).
  - **Production Cloud Deployments & Proxies**: Configured Vercel frontend rewrite proxies to eliminate CORS overhead, configured Render web services, and authored system documentation (`ATTENDANCE_SYSTEM.md`).

## Contributors

- **Sukrit Kolluru** ([@userai08072008-arch](https://github.com/userai08072008-arch))
  - Implemented attendance backend models, initial QR generation via Pillow, check-in CRUD handlers, and test suites ([#8](https://github.com/TheTuringClubJU/turing-registration/pull/8)).

- **Krishnapriya** ([@krishnapriya-op](https://github.com/krishnapriya-op))
  - Created initial organiser login UI and authentication form scaffolding ([#7](https://github.com/TheTuringClubJU/turing-registration/pull/7)).

<!--
Add new contributors below this line, following the format above.
One bullet per contribution/PR, most recent contribution added to the bottom of their list.
-->
