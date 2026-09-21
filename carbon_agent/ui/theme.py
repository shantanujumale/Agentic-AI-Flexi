"""
Custom styling and theme definitions for the Carbon Agent Gradio interface.
"""

CUSTOM_CSS = """
/* Carbon Agent Modern Aesthetic Theme */
:root {
    --primary-green: #10b981;
    --primary-dark-green: #059669;
    --accent-teal: #06b6d4;
    --card-bg: rgba(255, 255, 255, 0.85);
    --card-border: #e2e8f0;
    --text-main: #0f172a;
    --text-muted: #64748b;
}

.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    max-width: 1350px !important;
    margin: auto !important;
}

/* Header Banner */
.app-header {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
    color: white;
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.25);
}

.app-header h1 {
    color: white !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.025em;
}

.app-header p {
    color: #a7f3d0 !important;
    font-size: 1.05rem !important;
    margin: 0 !important;
    font-weight: 400;
}

/* Metric KPI Badges */
.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.08);
}

.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #065f46;
    line-height: 1.1;
}

.kpi-label {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-top: 6px;
}

.kpi-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 2px;
}

/* Agent Action Cards */
.action-card {
    background: #f8fafc;
    border-left: 5px solid #10b981;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}

.action-card.hard {
    border-left-color: #f59e0b;
}

.badge-tag {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}

.badge-free { background: #dcfce7; color: #15803d; }
.badge-low { background: #e0f2fe; color: #0369a1; }
.badge-investment { background: #fef3c7; color: #b45309; }
.badge-easy { background: #dcfce7; color: #166534; }
.badge-medium { background: #fef9c3; color: #854d0e; }
.badge-hard { background: #fee2e2; color: #991b1b; }

/* Tool Trace Box */
.tool-trace {
    background: #1e293b;
    color: #38bdf8;
    font-family: 'Fira Code', monospace;
    font-size: 0.82rem;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 8px 0;
    overflow-x: auto;
}
"""
