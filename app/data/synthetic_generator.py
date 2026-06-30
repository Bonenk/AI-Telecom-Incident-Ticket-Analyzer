import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()

TICKET_CATEGORIES = ["Network", "Billing", "Hardware", "Software", "Customer"]

CATEGORY_TEMPLATES = {
    "Network": {
        "subjects": [
            "Intermittent connectivity in {area}",
            "Complete service outage at {area}",
            "High packet loss on link to {area}",
            "DNS resolution failure for {domain}",
            "Latency spike detected on {device}",
            "BGP route flapping on peer {peer}",
            "VOIP call quality degradation in {area}",
            "5G signal drop in {area}",
            "Fiber cut reported near {area}",
            "VPN tunnel down between {a} and {b}",
        ],
        "descriptions": [
            "Users in {area} are experiencing intermittent connectivity. Ping tests show 30% packet loss. This started at {time}.",
            "Complete service outage in {area}. No traffic passing through {device}. Emergency maintenance required.",
            "Latency has spiked to {ms}ms on {device}. Customer complains about slow data speeds during peak hours.",
            "{area} reporting 5G signal dropping from 4 bars to 1 bar every few minutes. Handoff issues between towers.",
            "Fiber optic cable damaged near {area} due to construction. Estimated repair time unknown.",
            "VPN tunnel between {a} and {b} dropped at {time}. Reconnection attempts failing with auth errors.",
            "VOIP calls in {area} have choppy audio and frequent drops. Jitter exceeds {ms}ms.",
            "DNS resolution for {domain} is failing intermittently. Cache flush did not resolve the issue.",
            "BGP session with peer {peer} is flapping. Route advertisements inconsistent.",
        ],
    },
    "Billing": {
        "subjects": [
            "Incorrect charge on account {acc}",
            "Customer disputing overcharge of ${amt}",
            "Billing cycle not reflecting plan change",
            "Double payment applied to account {acc}",
            "Invoice missing discount for {plan} plan",
            "Autopay failed for customer {acc}",
            "Refund not processed after cancellation",
            "Tax calculation error on invoice {inv}",
            "Promotional credit not applied",
            "Late fee charged despite on-time payment",
        ],
        "descriptions": [
            "Customer reports being charged ${amt} for a service they did not add. Plan is {plan}. Account: {acc}.",
            "Account {acc} shows double payment on {date}. One payment needs to be refunded or credited.",
            "Autopay failed on {date} for account {acc}. Card on file expired. Late fee already applied.",
            "Customer upgraded to {plan} plan but billing still shows old rate. Difference of ${amt} per month.",
            "Invoice {inv} does not reflect the 10% loyalty discount promised. Customer is asking for correction.",
            "Refund of ${amt} was approved on {date} but not yet processed. Customer following up.",
            "Promotional $20 credit for signing up was not applied to first invoice. Customer upset.",
            "Tax rate on invoice {inv} appears incorrect. Customer was charged {pct}% instead of the usual rate.",
        ],
    },
    "Hardware": {
        "subjects": [
            "Router {model} overheating at customer site",
            "ONT optical signal weak in {area}",
            "Faulty ethernet ports on {device}",
            "Power supply failure on {device}",
            "CPE firmware update failed on {acc}",
            "Antenna misalignment on tower {tower}",
            "Battery backup failure at {site}",
            "Switch port errors on {device} port {port}",
            "Cable modem {model} not syncing",
            "Hardware EOL replacement needed for {acc}",
        ],
        "descriptions": [
            "Router {model} at customer site {acc} is running at 95°C. Performance degraded. Needs replacement.",
            "ONT at {acc} shows optical signal at -28dBm. Below threshold. Check fiber splice in {area}.",
            "Ports 3-6 on {device} are not registering link. Reseating cables did not help. Possible switch failure.",
            "CPE firmware upgrade to version {ver} failed at account {acc}. Device stuck in recovery mode.",
            "Power supply on {device} failed at {time}. Device on battery backup with < 30 minutes remaining.",
            "Antenna on tower {tower} has 2° azimuth misalignment. Coverage affected in {area}.",
            "Cable modem {model} on account {acc} unable to sync downstream channel. SNR below threshold.",
        ],
    },
    "Software": {
        "subjects": [
            "CRM system crash on ticket creation",
            "Provisioning API returning 503 errors",
            "Billing system report generation failure",
            "OSS inventory sync stuck since {time}",
            "NMS dashboard showing stale data",
            "API rate limiting too aggressive on {endpoint}",
            "Database query timeout on customer lookup",
            "SMS gateway not delivering messages",
            "Email notification system down",
            "Mobile app login failing with OAuth error",
        ],
        "descriptions": [
            "CRM crashes when creating tickets with attachments > 5MB. Error: {err}. Happens consistently.",
            "Provisioning API at {endpoint} returns 503 for 30% of requests. Timeout after {ms}ms.",
            "Monthly billing report generation fails at 80% complete. Error in aggregation query.",
            "OSS inventory has not synced with field updates since {time}. 500+ work orders pending.",
            "NMS dashboard shows device status from {time}. Real-time updates not reflecting.",
            "SMS gateway queue has 2000+ undelivered messages. Provider endpoint returning errors.",
            "Mobile app login fails with 'invalid_grant' OAuth error since last deployment.",
        ],
    },
    "Customer": {
        "subjects": [
            "Customer requesting service credit for outage",
            "Plan downgrade request from {plan} to {plan2}",
            "Account {acc} requesting service transfer",
            "Customer complaint about technician no-show",
            "Request for installation date change",
            "Customer wants early contract termination",
            "Multiple complaints from HOA in {area}",
            "VIP customer escalation - slow internet",
            "Wrong equipment shipped to customer",
            "Accessibility accommodation requested",
        ],
        "descriptions": [
            "Customer in {area} had 6 hours of downtime on {date}. Requesting 1 month service credit on account {acc}.",
            "Account {acc} wants to downgrade from {plan} to {plan2} due to budget constraints. Current contract has 6 months left.",
            "Customer moving from {a} to {b} on {date}. Wants to transfer service without interruption.",
            "Technician scheduled between 9-12 on {date} never arrived. Customer waited all day. Very upset.",
            "HOA board in {area} reports 15+ complaints about unreliable internet. Requesting community discount.",
            "VIP customer (account {acc}) reports 15 Mbps instead of promised 300 Mbps. Needs immediate attention.",
            "Wrong CPE model shipped. Customer received {model} instead of {model2}. Installation delayed.",
        ],
    },
}

SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low"]
SEVERITY_WEIGHTS = [0.15, 0.30, 0.35, 0.20]

STATUSES = ["Open", "In Progress", "Escalated", "Resolved", "Closed"]

RESOLUTIONS = {
    "Network": [
        "Rebooted {device} - connectivity restored. Monitoring for 24 hours.",
        "Traffic rerouted through {device2}. Fiber repair crew dispatched to {area}.",
        "DNS cache purged and records updated for {domain}. Resolution time: {min} minutes.",
        "BGP session reset with peer {peer}. Route table converged after {min} minutes.",
        "5G tower {tower} firmware updated. Signal strength normalized in {area}.",
        "VPN tunnel reconfigured with new PSK. Connection stable.",
    ],
    "Billing": [
        "Adjusted invoice {inv}. Credited ${amt} to account {acc}.",
        "Processed refund of ${amt} to account {acc}. Expected 5-7 business days.",
        "Updated billing cycle for account {acc}. Plan {plan} rate now active.",
        "Voided duplicate payment on account {acc}. Balance corrected.",
        "Applied loyalty discount of 10% to account {acc}. Next invoice will reflect.",
        "Autopay updated with new card on account {acc}. Late fee waived.",
    ],
    "Hardware": [
        "Replaced faulty cable modem {model} on account {acc}. Sync established.",
        "Router {model} replaced at account {acc}. Temperature normal. Ticket resolved.",
        "Fiber splice repaired in {area}. ONT optical signal now at -18dBm.",
        "Switch {device} port {port} disabled and patch cable replaced. Errors cleared.",
        "CPE firmware {ver} re-flashed on account {acc}. Device back online.",
        "Antenna realigned on tower {tower}. Coverage restored in {area}.",
    ],
    "Software": [
        "Restarted CRM service. Patch scheduled for next maintenance window.",
        "Provisioning API scaling group increased. 503 errors resolved.",
        "Database indexes rebuilt on customer table. Query time reduced from {ms}ms to 50ms.",
        "SMS gateway reconnected. Queue drained after {min} minutes.",
        "NMS dashboard cache cleared. Real-time updates restored.",
        "OAuth token endpoint patched. Mobile app login working.",
    ],
    "Customer": [
        "Applied 1-month credit of ${amt} to account {acc}. Customer acknowledged.",
        "Plan downgraded from {plan} to {plan2}. Effective next billing cycle.",
        "Rescheduled installation for {date}. Customer confirmed availability.",
        "Technician dispatched for same-day visit. Account {acc} priority flagged.",
        "Correct CPE model {model2} shipped. Return label sent for wrong model.",
        "HOA discount of 10% applied to accounts in {area}. Escalation resolved.",
    ],
}


def _pick_random(lst: list) -> str:
    return random.choice(lst)


def _fill_template(template: str) -> str:
    fillers = {
        "area": fake.city(),
        "domain": fake.domain_name(),
        "device": _pick_random(
            ["RTR-01", "SW-05", "FW-Primary", "AGG-02", "BNG-03", "OLT-07", "RNC-12"]
        ),
        "device2": _pick_random(["RTR-02", "SW-06", "AGG-01", "BNG-01", "OLT-03"]),
        "peer": f"AS{random.randint(100, 999)}",
        "a": fake.city(),
        "b": fake.city(),
        "acc": f"ACC-{random.randint(10000, 99999)}",
        "inv": f"INV-{random.randint(100000, 999999)}",
        "amt": f"{random.randint(5, 200)}.{random.randint(0, 99):02d}",
        "plan": _pick_random(
            [
                "Basic 100Mbps",
                "Standard 300Mbps",
                "Premium 1Gbps",
                "Business 500Mbps",
                "5G Ultra",
            ]
        ),
        "plan2": _pick_random(
            [
                "Basic 100Mbps",
                "Standard 300Mbps",
                "Premium 1Gbps",
                "Business 500Mbps",
                "5G Ultra",
            ]
        ),
        "date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime(
            "%Y-%m-%d"
        ),
        "time": (datetime.now() - timedelta(hours=random.randint(1, 72))).strftime(
            "%H:%M"
        ),
        "ms": str(random.randint(200, 5000)),
        "min": str(random.randint(5, 120)),
        "err": _pick_random(
            [
                "MemoryError",
                "TimeoutError",
                "ConnectionRefused",
                "SegmentationFault",
                "NullPointerException",
                "DiskFull",
            ]
        ),
        "pct": str(random.randint(8, 15)),
        "model": _pick_random(
            [
                "HG8245",
                "Huawei ONT",
                "Cisco 4331",
                "Netgear Nighthawk",
                "Nokia G-010G-Q",
                "TP-Link AX6000",
            ]
        ),
        "model2": _pick_random(
            [
                "HG8245",
                "Huawei ONT",
                "Cisco 4331",
                "Netgear Nighthawk",
                "Nokia G-010G-Q",
                "TP-Link AX6000",
            ]
        ),
        "tower": f"TOWER-{random.randint(1, 50):02d}",
        "site": _pick_random(
            ["DataCenter-1", "DataCenter-2", "POP-North", "POP-South", "CO-East"]
        ),
        "port": str(random.randint(1, 48)),
        "ver": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
        "endpoint": _pick_random(
            [
                "/api/provision",
                "/api/billing",
                "/api/customer",
                "/api/network",
                "/api/inventory",
            ]
        ),
        "customer_name": fake.name(),
        "tower_id": f"TOWER-{random.randint(1, 50):02d}",
    }
    return template.format(**fillers)


def generate_tickets(count: int = 43) -> list[dict]:
    tickets = []
    for i in range(1, count + 1):
        category = random.choices(
            TICKET_CATEGORIES, weights=[0.30, 0.20, 0.18, 0.17, 0.15], k=1
        )[0]
        templates = CATEGORY_TEMPLATES[category]
        subject = _fill_template(random.choice(templates["subjects"]))
        description = _fill_template(random.choice(templates["descriptions"]))
        severity = random.choices(SEVERITY_LEVELS, weights=SEVERITY_WEIGHTS, k=1)[0]
        created_at = datetime.now() - timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        status = _pick_random(
            STATUSES if severity != "Critical" else ["Open", "In Progress", "Escalated"]
        )
        resolution = _pick_random(RESOLUTIONS.get(category, ["Pending investigation."]))
        resolution_text = (
            _fill_template(resolution) if "{" in resolution else resolution
        )
        if status in ("Resolved", "Closed"):
            resolved_at = created_at + timedelta(hours=random.randint(1, 72))
        else:
            resolved_at = ""

        tickets.append(
            {
                "ticket_id": f"TKT-{i:04d}",
                "category": category,
                "severity": severity,
                "status": status,
                "subject": subject,
                "description": description,
                "customer_name": fake.name(),
                "customer_account": f"ACC-{random.randint(10000, 99999)}",
                "contact_email": fake.email(),
                "contact_phone": fake.phone_number(),
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S")
                if resolved_at
                else "",
                "resolution": resolution_text,
                "priority_score": 0,
            }
        )

    return tickets


def generate_outage_logs(count: int = 5) -> list[dict]:
    logs = []
    for i in range(1, count + 1):
        start = datetime.now() - timedelta(
            days=random.randint(0, 90), hours=random.randint(0, 23)
        )
        duration_hours = round(random.uniform(0.5, 12), 2)
        end = start + timedelta(hours=duration_hours)
        affected = random.randint(50, 5000)
        logs.append(
            {
                "outage_id": f"OUT-{i:04d}",
                "area": fake.city(),
                "device": _pick_random(
                    ["RTR-01", "SW-05", "FW-Primary", "AGG-02", "BNG-03", "OLT-07"]
                ),
                "start_time": start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_hours": duration_hours,
                "affected_customers": affected,
                "root_cause": _pick_random(
                    [
                        "Fiber cut",
                        "Power failure",
                        "Software bug",
                        "Hardware failure",
                        "Configuration error",
                        "DDoS attack",
                        "Weather-related damage",
                        "Third-party contractor damage",
                        "Cable theft",
                    ]
                ),
                "status": _pick_random(
                    ["Resolved", "Resolved", "Resolved", "Investigating"]
                ),
            }
        )
    return logs
