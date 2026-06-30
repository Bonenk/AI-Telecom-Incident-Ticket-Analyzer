import streamlit as st


def inject_css(theme="light"):
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .agent-card {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            background: rgba(128, 128, 128, 0.05);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .agent-card::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            border-radius: 12px 0 0 12px;
        }

        .agent-card.completed::before { background: #00c853; }
        .agent-card.running::before { background: #ff9100; animation: pulse 1.5s infinite; }
        .agent-card.pending::before { background: #757575; }
        .agent-card.error::before { background: #ff1744; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .agent-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .agent-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            flex-shrink: 0;
        }

        .agent-icon.classify { background: rgba(33, 150, 243, 0.15); }
        .agent-icon.severity { background: rgba(255, 152, 0, 0.15); }
        .agent-icon.resolution { background: rgba(76, 175, 80, 0.15); }
        .agent-icon.approval { background: rgba(156, 39, 176, 0.15); }

        .agent-name {
            font-weight: 600;
            font-size: 1rem;
            flex: 1;
        }

        .agent-status {
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-weight: 500;
        }

        .agent-status.running {
            background: rgba(255, 145, 0, 0.15);
            color: #ff9100;
        }

        .agent-status.completed {
            background: rgba(0, 200, 83, 0.15);
            color: #00c853;
        }

        .agent-status.pending {
            background: rgba(117, 117, 117, 0.15);
            color: #757575;
        }

        .agent-status.error {
            background: rgba(255, 23, 68, 0.15);
            color: #ff1744;
        }

        .agent-thinking {
            margin-top: 0.75rem;
            padding: 0.75rem;
            border-radius: 8px;
            background: rgba(128, 128, 128, 0.05);
            font-size: 0.875rem;
            line-height: 1.6;
            border-left: 3px solid rgba(128, 128, 128, 0.2);
        }

        .agent-thinking .label {
            font-weight: 600;
            color: rgba(128, 128, 128, 0.7);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }

        .thinking-dots::after {
            content: '';
            animation: dots 1.5s infinite;
        }

        @keyframes dots {
            0% { content: ''; }
            33% { content: '.'; }
            66% { content: '..'; }
            100% { content: '...'; }
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.15rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        .badge.critical { background: rgba(255, 23, 68, 0.15); color: #ff1744; }
        .badge.high { background: rgba(255, 145, 0, 0.15); color: #ff9100; }
        .badge.medium { background: rgba(255, 193, 7, 0.15); color: #ffc107; }
        .badge.low { background: rgba(76, 175, 80, 0.15); color: #4caf50; }

        .badge.network { background: rgba(33, 150, 243, 0.15); color: #2196f3; }
        .badge.billing { background: rgba(255, 152, 0, 0.15); color: #ff9800; }
        .badge.hardware { background: rgba(76, 175, 80, 0.15); color: #4caf50; }
        .badge.software { background: rgba(156, 39, 176, 0.15); color: #9c27b0; }
        .badge.customer { background: rgba(0, 188, 212, 0.15); color: #00bcd4; }

        .resolution-box {
            border: 1px solid rgba(76, 175, 80, 0.3);
            border-radius: 12px;
            padding: 1.25rem;
            background: rgba(76, 175, 80, 0.05);
        }

        .stat-card {
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            background: rgba(128, 128, 128, 0.03);
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }

        .stat-card .label {
            font-size: 0.8rem;
            color: rgba(128, 128, 128, 0.7);
            margin-top: 0.25rem;
        }

        .workflow-connector {
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(128, 128, 128, 0.3);
            font-size: 1.5rem;
            margin: -0.25rem 0;
        }

        div[data-testid="stStatusWidget"] {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        button[title="Deploy this app"] { display: none !important; }
        button[title="View app status"] { display: none !important; }
        #tly-page-guide-canvas { display: none !important; }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.1);
        }

        .skeleton-container {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            padding: 0.25rem 0;
        }

        .skeleton-line {
            height: 0.75rem;
            border-radius: 4px;
            background: linear-gradient(
                90deg,
                rgba(128, 128, 128, 0.08) 25%,
                rgba(128, 128, 128, 0.2) 50%,
                rgba(128, 128, 128, 0.08) 75%
            );
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }

        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .md-content h1, .md-content h2, .md-content h3 {
            margin-top: 0.75rem;
            margin-bottom: 0.25rem;
            font-size: 1rem;
        }
        .md-content p {
            margin: 0.25rem 0;
            line-height: 1.6;
        }
        .md-content ul, .md-content ol {
            margin: 0.25rem 0;
            padding-left: 1.25rem;
        }
        .md-content li {
            margin: 0.15rem 0;
            line-height: 1.5;
        }
        .md-content strong {
            font-weight: 600;
        }
        .md-content code {
            background: rgba(128, 128, 128, 0.1);
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            font-size: 0.85em;
            font-family: 'JetBrains Mono', monospace;
        }

        .page-skeleton {
            padding: 1rem 0;
        }
        .page-skeleton .skeleton-title {
            height: 1.5rem;
            width: 40%;
            border-radius: 6px;
            background: linear-gradient(90deg, rgba(128,128,128,0.06) 25%, rgba(128,128,128,0.15) 50%, rgba(128,128,128,0.06) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            margin-bottom: 1.5rem;
        }
        .page-skeleton .skeleton-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .page-skeleton .skeleton-box {
            flex: 1;
            height: 6rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(128,128,128,0.06) 25%, rgba(128,128,128,0.12) 50%, rgba(128,128,128,0.06) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        .page-skeleton .skeleton-chart {
            height: 14rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(128,128,128,0.06) 25%, rgba(128,128,128,0.1) 50%, rgba(128,128,128,0.06) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            margin-bottom: 1rem;
        }
        .page-skeleton .skeleton-table {
            height: 8rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(128,128,128,0.06) 25%, rgba(128,128,128,0.1) 50%, rgba(128,128,128,0.06) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        [data-theme="dark"] .agent-card {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 255, 255, 0.1);
        }
        [data-theme="dark"] .stat-card {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.08);
        }
        [data-theme="dark"] .agent-thinking {
            background: rgba(255, 255, 255, 0.04);
        }
        [data-theme="dark"] .resolution-box {
            border-color: rgba(76, 175, 80, 0.2);
            background: rgba(76, 175, 80, 0.08);
        }
        [data-theme="dark"] .badge.critical { background: rgba(255, 23, 68, 0.25); }
        [data-theme="dark"] .badge.high { background: rgba(255, 145, 0, 0.25); }
        [data-theme="dark"] .badge.medium { background: rgba(255, 193, 7, 0.25); }
        [data-theme="dark"] .badge.low { background: rgba(76, 175, 80, 0.25); }
        [data-theme="dark"] .badge.network { background: rgba(33, 150, 243, 0.25); }
        [data-theme="dark"] .badge.billing { background: rgba(255, 152, 0, 0.25); }
        [data-theme="dark"] .badge.hardware { background: rgba(76, 175, 80, 0.25); }
        [data-theme="dark"] .badge.software { background: rgba(156, 39, 176, 0.25); }
        [data-theme="dark"] .badge.customer { background: rgba(0, 188, 212, 0.25); }
        [data-theme="dark"] .skeleton-line {
            background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.04) 75%);
            background-size: 200% 100%;
        }
        [data-theme="dark"] .md-content code {
            background: rgba(255, 255, 255, 0.1);
        }
    </style>
    <script>
        document.body.setAttribute('data-theme', 'THEME_PLACEHOLDER');
    </script>
    """.replace("THEME_PLACEHOLDER", theme), unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    level = severity.lower() if severity else "low"
    return f'<span class="badge {level}">{severity}</span>'


def category_badge(category: str) -> str:
    cat = category.lower() if category else "customer"
    return f'<span class="badge {cat}">{category}</span>'
