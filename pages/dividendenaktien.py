from utils.dashboard_analysis import render_dashboard


render_dashboard(
    csv_path="data/dividendenaktien.csv",
    title="💰 Dividendenaktien",
    subtitle="Analyse nach Fundamentaldaten, Scores und Empfehlung",
)