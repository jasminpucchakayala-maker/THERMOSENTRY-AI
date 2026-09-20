from html import escape
from backend.app.models.decision_intelligence import DecisionIntelligenceAnomaly


class ReportService:
    """Builds an honest HTML report from one completed decision object."""

    @staticmethod
    def _value(value):
        return "Unavailable" if value is None or value == "" else escape(str(value))

    def render_html(self, item: DecisionIntelligenceAnomaly) -> str:
        event = item
        classification = item.classification
        persistence = item.persistence
        context = item.industrial_context
        risk = item.risk_assessment
        facilities = "".join(
            f"<li>{self._value(f.name)} ({self._value(f.type)}) - {f.distance_km} km, OSM {self._value(f.osm_id)}</li>"
            for f in context.nearby_facilities
        ) or "<li>No nearby facility found</li>"
        evidence = "".join(f"<li>{self._value(value)}</li>" for value in classification.evidence)
        explanations = "".join(f"<li>{self._value(value)}</li>" for value in [classification.reasoning, persistence.description, risk.explanation])
        return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>THERMOSENTRY AI Report {self._value(event.event_id or event.id)}</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:40px auto;color:#17394a}}h1{{color:#087f9d}}h2{{border-bottom:1px solid #b7d1d8;padding-bottom:6px}}dt{{font-weight:700;float:left;clear:left;width:220px}}dd{{margin-left:230px;margin-bottom:8px}}.risk{{font-size:1.3em;font-weight:700}}small{{color:#557586}}</style></head>
<body><h1>THERMOSENTRY AI</h1><p>Satellite Thermal Intelligence</p>
<h2>Event</h2><dl><dt>Event ID</dt><dd>{self._value(event.event_id or event.id)}</dd><dt>FIRMS ID</dt><dd>{self._value(event.firms_id)}</dd><dt>Coordinates</dt><dd>{event.latitude}, {event.longitude}</dd><dt>Acquisition</dt><dd>{event.acquisition_date} {event.acquisition_time} UTC</dd><dt>Satellite</dt><dd>{self._value(event.satellite)}</dd><dt>Instrument</dt><dd>{self._value(event.instrument)}</dd><dt>Confidence</dt><dd>{self._value(event.confidence)}</dd><dt>Brightness</dt><dd>{self._value(event.brightness_temperature)} K</dd><dt>FRP</dt><dd>{self._value(event.frp)} MW</dd><dt>Day/Night</dt><dd>{self._value(event.day_night)}</dd></dl>
<h2>Classification</h2><p><b>{self._value(classification.class_name)}</b> via {self._value(classification.method)} baseline</p><ul>{evidence}</ul>
<h2>Persistence</h2><p>{self._value(persistence.persistence_type)}: {self._value(persistence.description)}</p><p>Observations: {persistence.observation_count}; score: {persistence.persistence_score}; {persistence.first_seen} to {persistence.last_seen}</p>
<h2>Industrial Context</h2><p>Source: {self._value(context.source)}</p><ul>{facilities}</ul>
<h2>Risk</h2><p class='risk'>{risk.risk_level.value} - {risk.composite_risk_score}/100</p><p>{self._value(risk.action_recommendation)}</p><pre>{escape(str(risk.factors))}</pre>
<h2>Decision Summary</h2><ul>{explanations}</ul><p><small>Sources: NASA FIRMS, {self._value(context.source)}, Baseline Classification, THERMOSENTRY Risk Engine.</small></p>
</body></html>"""


report_service = ReportService()