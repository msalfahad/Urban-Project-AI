# Team dashboard data

`build_dashboard_data.py <docs/agents dir> <out dir> [<board commit>]` turns BOARD.md, PLAN.md, SCOREBOARD.md and
OWNER_QUESTIONS.md into the dashboard's data files (tasks, milestones, targets, owner_questions). The hourly "Dashboard
refresher" runs it, adds agents.json (from the scheduled tasks) and refresh.json, and uploads all six files to the owner's
dashboard. Stdlib only. A value the board does not state is written as null, never estimated.

Project names in the data: "Alsenan Chalet", "Apartment (development project 2)", "Engine (all projects)". No client
names or personal data belong here.
