from utils.dashboard_analysis import render_dashboard


render_dashboard(
    csv_path="data/aktien_universum.csv",
    category_column="Dividenden",
    title="💰 Dividendenaktien",
    subtitle="Analyse nach Fundamentaldaten, Scores und Empfehlung",
)