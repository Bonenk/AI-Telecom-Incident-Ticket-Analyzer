#!/usr/bin/env bash
set -euo pipefail

# Seed synthetic data if the database is empty
python -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from app.services.database import TicketDatabase
from app.data.synthetic_generator import generate_tickets, generate_outage_logs

db = TicketDatabase()
existing = db.list_synthetic_tickets()
if not existing:
    print('Seeding synthetic tickets and outage logs...')
    tickets = generate_tickets(200)
    logs = generate_outage_logs(50)
    db.seed_synthetic_data(tickets, logs)
    print(f'  -> {len(tickets)} tickets, {len(logs)} logs')
else:
    print(f'Synthetic data already present ({len(existing)} tickets).')

# Clean up duplicates: for each ticket_id with multiple open analyses, keep only the latest
all_analyses = db.list_analyses(limit=500)
seen = {}
for a in all_analyses:
    tid = a['ticket_id']
    is_open = a['human_decision'] is None or a['human_decision'] == ''
    if is_open:
        if tid in seen:
            db.delete_analysis(a['id'])
            print(f'  Removed duplicate open analysis for {tid}')
        else:
            seen[tid] = a['id']
"

exec "$@"
