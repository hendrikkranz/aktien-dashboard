from utils.dashboard_analysis import render_dashboard


render_dashboard(
    csv_path="data/aktien_universum.csv",
    category_column="Dauergewinner",
    title="📈 Dauergewinner",
    subtitle="Analyse nach Fundamentaldaten, Scores und Empfehlung",
)