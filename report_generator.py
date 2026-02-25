class ReportGenerator:
    def __init__(self, bi_engine, data_cleaner):
        self.bi = bi_engine
        self.cleaner = data_cleaner

    def generate_leadership_update(self, timeframe="all", sector="all"):
        deals_kpis = self.bi.deals_kpis(timeframe=timeframe, sector=sector)
        wo_kpis = self.bi.work_orders_kpis(timeframe=timeframe, sector=sector)
        data_quality = self.cleaner.get_data_quality_report()
        
        rev = deals_kpis.get('closed_revenue', 0)
        pipe = deals_kpis.get('open_pipeline_value', 0)
        win_rate = deals_kpis.get('win_rate', 0)
        
        active = wo_kpis.get('active_projects', 0)
        delayed = wo_kpis.get('delayed_projects', 0)
        
        risk_flags = []
        if delayed > 0 and (delayed/max(active, 1) > 0.2):
            risk_flags.append(f"High risk of operational delay ({delayed} delayed projects).")
        if win_rate < 0.2 and deals_kpis.get('stage_distribution', {}).get('Closed Won', 0) > 0:
            risk_flags.append(f"Win rate is critically low at {win_rate:.1%}.")
            
        deals_hq = data_quality['deals']
        wo_hq = data_quality['work_orders']
        
        warning_texts = []
        if deals_hq['missing_close_dates'] > (deals_hq['total_records'] * 0.1):
            warning_texts.append(f"⚠ {deals_hq['missing_close_dates']} deals missing close dates.")
        if deals_hq['missing_values'] > (deals_hq['total_records'] * 0.1):
             warning_texts.append(f"⚠ {deals_hq['missing_values']} deals missing revenue numbers. Pipeline may be conservative.")
        if wo_hq['incomplete'] > (wo_hq['total_records'] * 0.1):
            warning_texts.append(f"⚠ {wo_hq['incomplete']} incomplete work order records detected.")
            
        report = {
            "title": "Leadership Update",
            "revenue_summary": f"Closed Revenue: ${rev:,.2f} | Win Rate: {win_rate:.1%}",
            "pipeline_health": f"Open Pipeline: ${pipe:,.2f}",
            "sector_breakdown": deals_kpis.get('revenue_by_sector', {}),
            "operational_status": f"Active Projects: {active} | Delayed Projects: {delayed}",
            "risk_flags": risk_flags if risk_flags else ["No critical risk flags detected."],
            "data_quality_warnings": warning_texts if warning_texts else ["Data quality is within acceptable bounds."]
        }
        return report
