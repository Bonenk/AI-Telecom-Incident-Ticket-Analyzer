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
"

exec "$@"
