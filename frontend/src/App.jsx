import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, BarChart3, ChevronRight, Eye, Flame, Gauge, Layers3, MapPin, Menu, Moon, Pause, Play, Plus, Radio, RotateCcw, Satellite, Settings2, SlidersHorizontal, Sun, X, Minus, Wifi } from 'lucide-react'
import GlobeView from './GlobeView.jsx'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000/api'
const QUERY = 'days=1&source=VIIRS_NOAA20_NRT&country=IND&use_cache=false'
const FIRMS_ENDPOINT = `${API_BASE}/thermal-anomalies?${QUERY}`
const navItems = [
  { label: 'Overview', icon: Gauge }, { label: 'Live Orbit', icon: Satellite },
  { label: 'Thermal Events', icon: Flame }, { label: 'Persistent Sources', icon: Layers3 },
  { label: 'Industrial Context', icon: BarChart3 }, { label: 'Risk Intelligence', icon: AlertTriangle }, { label: 'Reports', icon: BarChart3 },
]

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeNav, setActiveNav] = useState('Overview')
  const [rotationEnabled, setRotationEnabled] = useState(true)
  const [thermalEnabled, setThermalEnabled] = useState(true)
  const [satelliteEnabled, setSatelliteEnabled] = useState(true)
  const [orbitalEnabled, setOrbitalEnabled] = useState(true)
  const [cloudsEnabled, setCloudsEnabled] = useState(true)
  const [nightMode, setNightMode] = useState(true)
  const [investigationOpen, setInvestigationOpen] = useState(true)
  const [hoveredEvent, setHoveredEvent] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [firmsLoading, setFirmsLoading] = useState(true)
  const [firmsError, setFirmsError] = useState('')
  const [lastSync, setLastSync] = useState(null)
  const [workspaceData, setWorkspaceData] = useState(null)
  const [workspaceLoading, setWorkspaceLoading] = useState(false)
  const [workspaceError, setWorkspaceError] = useState('')
  const [zoomDelta, setZoomDelta] = useState(0)
  const [resetSignal, setResetSignal] = useState(0)
  const controls = [['THERMAL', thermalEnabled, setThermalEnabled], ['SATELLITE', satelliteEnabled, setSatelliteEnabled], ['ORBITAL', orbitalEnabled, setOrbitalEnabled], ['CLOUDS', cloudsEnabled, setCloudsEnabled]]

  useEffect(() => {
    let cancelled = false
    const loadFirmsData = async () => {
      setFirmsLoading(true)
      try {
        const response = await fetch(FIRMS_ENDPOINT)
        if (!response.ok) throw new Error(`Backend responded with HTTP ${response.status}`)
        const payload = await response.json()
        if (cancelled) return
        setAnomalies(Array.isArray(payload.data) ? payload.data : [])
        setFirmsError('')
        setLastSync(new Date())
      } catch (error) {
        if (!cancelled) setFirmsError(error.message || 'Unable to reach the FIRMS backend')
      } finally {
        if (!cancelled) setFirmsLoading(false)
      }
    }
    loadFirmsData()
    const refreshTimer = window.setInterval(loadFirmsData, 5 * 60 * 1000)
    return () => { cancelled = true; window.clearInterval(refreshTimer) }
  }, [])

  useEffect(() => {
    if (activeNav === 'Overview' || activeNav === 'Thermal Events') {
      setWorkspaceData(null)
      setWorkspaceError('')
      return undefined
    }
    let cancelled = false
    const endpoint = activeNav === 'Live Orbit'
      ? `${API_BASE}/decision-intelligence?${QUERY}&use_live_osm=false`
      : activeNav === 'Persistent Sources'
        ? `${API_BASE}/persistent-anomalies?${QUERY}`
        : activeNav === 'Industrial Context'
          ? `${API_BASE}/enriched-anomalies?${QUERY}&use_live_osm=false`
          : `${API_BASE}/decision-intelligence?${QUERY}&use_live_osm=false`
    setWorkspaceLoading(true)
    setWorkspaceError('')
    fetch(endpoint)
      .then((response) => { if (!response.ok) throw new Error(`Backend responded with HTTP ${response.status}`); return response.json() })
      .then((payload) => { if (!cancelled) setWorkspaceData(payload) })
      .catch((error) => { if (!cancelled) setWorkspaceError(error.message || 'Unable to load backend workspace data') })
      .finally(() => { if (!cancelled) setWorkspaceLoading(false) })
    return () => { cancelled = true }
  }, [activeNav])

  const handleMarkerSelect = async (event) => {
    setSelectedEvent(event)
    setInvestigationOpen(true)
    try {
      const response = await fetch(`${API_BASE}/decision/${encodeURIComponent(event.id)}?${QUERY}&use_live_osm=true`)
      if (response.ok) setSelectedEvent(await response.json())
    } catch {
      // Keep the raw FIRMS record visible if enrichment is temporarily unavailable.
    }
  }
  const formatSyncTime = lastSync ? lastSync.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'short' }) : 'Awaiting data'
  const formatValue = (value, suffix = '') => value === null || value === undefined || value === '' ? 'Unavailable' : `${value}${suffix}`
  const locationText = selectedEvent ? `${selectedEvent.latitude.toFixed(4)} N, ${selectedEvent.longitude.toFixed(4)} E` : 'Select a live detection'
  const acquisitionText = selectedEvent ? `${selectedEvent.acquisition_date} ${selectedEvent.acquisition_time} UTC` : 'Select a live detection'

  return <div className={`mission-shell ${nightMode ? '' : 'day-mode'}`}>
    <header className="mission-header">
      <div className="header-brand"><div className="brand-orbit"><Activity size={20} /></div><div><strong>THERMOSENTRY <b>AI</b></strong><small>SATELLITE THERMAL INTELLIGENCE</small></div></div>
      <div className="header-feed"><span className="live-dot" /> <strong>LIVE FIRMS</strong><small>{firmsLoading ? 'Connecting...' : firmsError ? 'Offline' : 'Connected'}</small></div>
      <div className="header-readout"><div><Radio size={16} /><span>NASA FIRMS<small>MODIS / VIIRS</small></span></div><div><span className="clock-mark">◷</span><span>LAST SYNC<small>{formatSyncTime}</small></span></div><div><Wifi size={17} /><span>SYSTEM HEALTH<small className={firmsError ? 'red' : 'green'}>{firmsError ? 'FIRMS Offline' : firmsLoading ? 'Connecting' : 'Operational'}</small></span></div></div>
      <div className="header-actions"><button aria-label="Day and night mode" onClick={() => setNightMode(!nightMode)}>{nightMode ? <Sun size={15} /> : <Moon size={15} />}<Moon size={14} /></button><button aria-label="Auto rotate" className={rotationEnabled ? 'header-toggle on' : 'header-toggle'} onClick={() => setRotationEnabled(!rotationEnabled)}><RotateCcw size={14} /> Auto Rotate <i /></button><button aria-label="Settings"><SlidersHorizontal size={16} /></button></div>
    </header>

    <aside className={`mission-sidebar ${sidebarOpen ? 'is-open' : ''}`}><button className="mobile-close" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"><X size={18} /></button><nav>{navItems.map(({ label, icon: Icon }) => <button key={label} className={activeNav === label ? 'active' : ''} onClick={() => { setActiveNav(label); setSidebarOpen(false) }}><Icon size={19} /><span>{label}</span></button>)}</nav><div className="sidebar-bottom"><button><Settings2 size={18} /> Settings</button><div className="sidebar-operator"><span>AR</span><div><strong>Alex Rao</strong><small>Mission control</small></div></div></div></aside>

    <main className="mission-stage">
      <button className="mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
      <section className="legend-panel"><div className="overlay-heading"><strong>THERMAL EVENT TYPES</strong><i /></div><LegendItem tone="fire" label="Live thermal anomaly" /><LegendItem tone="uncertain" label="FIRMS detection" /></section>
      <section className="telemetry-panel"><div className="overlay-heading"><strong>SATELLITE TELEMETRY</strong></div><div className="sat-illustration"><Satellite size={47} /><span className="solar-wing left" /><span className="solar-wing right" /></div><div className="sat-name"><strong>NOAA-20 (VIIRS)</strong><span><i /> {firmsError ? 'Offline' : 'Active'}</span><b>LEO LIVE FEED</b></div><div className="telemetry-grid"><div><span>DETECTIONS</span><strong>{anomalies.length}</strong></div><div><span>QUERY SCOPE</span><strong>INDIA</strong></div><div><span>REFRESH</span><strong>5 min</strong></div></div></section>
      <div className="globe-label noaa20"><strong>NOAA-20</strong><small>VIIRS</small></div><div className="globe-label noaa21"><strong>NOAA-21</strong><small>VIIRS</small></div><div className="globe-label suomi"><strong>Suomi-NPP</strong><small>VIIRS</small></div>
      <div className="globe-stage-wrap"><GlobeView anomalies={anomalies} rotationEnabled={rotationEnabled} thermalEnabled={thermalEnabled} satelliteEnabled={satelliteEnabled} orbitalEnabled={orbitalEnabled} cloudsEnabled={cloudsEnabled} dayMode={!nightMode} zoomDelta={zoomDelta} resetSignal={resetSignal} onMarkerHover={setHoveredEvent} onMarkerSelect={handleMarkerSelect} /></div>
      {hoveredEvent && <div className="marker-tooltip"><strong>FIRMS detection</strong><span>{hoveredEvent.latitude.toFixed(4)}, {hoveredEvent.longitude.toFixed(4)} / {hoveredEvent.source}</span></div>}
      {firmsError && <div className="firms-error">LIVE FIRMS OFFLINE · {firmsError}</div>}
      {firmsLoading && <div className="firms-loading">CONNECTING TO LIVE FIRMS...</div>}
      <div className="globe-tools"><button aria-label="Center view"><MapPin size={16} /></button><button onClick={() => setZoomDelta((value) => value + .35)} aria-label="Zoom in"><Plus size={18} /></button><button onClick={() => setZoomDelta((value) => value - .35)} aria-label="Zoom out"><Minus size={18} /></button><button aria-label="3D view">3D</button></div>
      <div className="globe-controls"><button onClick={() => setRotationEnabled(!rotationEnabled)}><span>{rotationEnabled ? <Pause size={13} /> : <Play size={13} />}</span>{rotationEnabled ? 'Pause Rotation' : 'Resume Rotation'}</button><button><Eye size={14} /> Inspect Location</button><button onClick={() => setResetSignal((value) => value + 1)}><RotateCcw size={14} /> Reset View</button></div>
      <div className="layer-dock">{controls.map(([label, value, setValue]) => <button key={label} className={value ? 'enabled' : ''} onClick={() => setValue(!value)} aria-pressed={value}><i /> {label}</button>)}</div>
      {activeNav !== 'Overview' && <NavigationPanel activeNav={activeNav} anomalies={anomalies} workspaceData={workspaceData} workspaceLoading={workspaceLoading} workspaceError={workspaceError} onSelect={handleMarkerSelect} firmsError={firmsError} />}
    </main>

    {investigationOpen && <aside className="investigation-panel"><div className="investigation-heading"><strong>EVENT INVESTIGATION</strong><button onClick={() => setInvestigationOpen(false)} aria-label="Close investigation"><X size={17} /></button></div><div className="event-card"><div className="event-image"><Flame size={29} /><small>IR - 375m</small></div><div><span className="event-code"><Flame size={12} /> FIRMS EVENT ID</span><strong>{selectedEvent?.id || 'No event selected'}</strong><span><MapPin size={12} /> {locationText}</span><small>Live NASA FIRMS detection</small></div><b className="risk-tag">{selectedEvent?.risk_assessment?.risk_level || selectedEvent?.classification?.class || 'Raw anomaly'}</b></div><div className="investigation-data"><DataRow label="Acquisition" value={acquisitionText} /><DataRow label="Satellite" value={selectedEvent?.satellite || 'Unavailable'} accent /><DataRow label="Instrument" value={selectedEvent?.instrument || 'Unavailable'} /><DataRow label="Confidence" value={formatValue(selectedEvent?.confidence, '%')} accent /><DataRow label="Brightness" value={formatValue(selectedEvent?.brightness_temperature, ' K')} orange /><DataRow label="FRP" value={formatValue(selectedEvent?.frp, ' MW')} orange /><DataRow label="Day / Night" value={selectedEvent?.day_night || 'Unavailable'} /><DataRow label="Classification" value={selectedEvent?.classification?.class || 'Not analyzed yet'} /><DataRow label="Risk Score" value={selectedEvent?.risk_assessment ? `${selectedEvent.risk_assessment.composite_risk_score}/100` : 'Not analyzed yet'} orange /><DataRow label="Source" value={selectedEvent ? 'NASA FIRMS / live' : 'Unavailable'} /></div>{selectedEvent?.id && <a className="report-link" href={`${API_BASE}/reports/${encodeURIComponent(selectedEvent.id)}?${QUERY}&use_live_osm=true`} target="_blank" rel="noreferrer">Download HTML Report <ChevronRight size={14} /></a>}</aside>}
    {!investigationOpen && <button className="reopen-investigation" onClick={() => setInvestigationOpen(true)} aria-label="Open investigation"><SlidersHorizontal size={16} /></button>}

    <section className="bottom-analytics"><AnalyticsCard icon={Flame} label="ACTIVE THERMAL EVENTS" value={anomalies.length} change={firmsError ? 'offline' : 'live query'} tone="orange" chart="M 0 25 C 28 25 34 21 56 23 S 78 11 96 23 S 117 7 132 22 S 151 8 164 9" /><AnalyticsCard icon={AlertTriangle} label="HIGH-RISK EVENTS" value="—" change="not connected" tone="red" chart="M 0 28 L 27 25 L 52 27 L 76 18 L 98 22 L 119 13 L 143 19 L 166 7" /><AnalyticsCard icon={Layers3} label="PERSISTENT SOURCES" value="—" change="not connected" tone="cyan" chart="M 0 23 C 25 25 42 29 58 20 S 81 14 96 24 S 126 4 142 22 S 156 17 166 4" /><AnalyticsCard icon={BarChart3} label="INDUSTRIAL CONTEXT" value="—" change="not connected" tone="teal" chart="M 0 29 L 30 24 L 52 27 L 73 18 L 94 21 L 116 8 L 139 18 L 166 7" /><div className="sat-update"><Satellite size={26} /><div><span>LATEST SATELLITE UPDATE</span><strong>NOAA-20 (VIIRS)</strong><small>{formatSyncTime} · Live FIRMS</small><a>Current query scope <ChevronRight size={13} /></a></div></div></section>
  </div>
}

function LegendItem({ tone, label }) { return <div className="legend-item"><i className={tone}>{tone === 'fire' ? '♨' : '!'}</i><span>{label}</span></div> }
function NavigationPanel({ activeNav, anomalies, workspaceData, workspaceLoading, workspaceError, onSelect, firmsError }) {
  const isLiveDataView = activeNav === 'Live Orbit' || activeNav === 'Thermal Events'
  const data = workspaceData?.data || []
  return <section className="navigation-panel"><div className="navigation-panel-header"><div><span>MISSION WORKSPACE</span><h2>{activeNav}</h2></div><small>{workspaceLoading ? 'LOADING' : workspaceError ? 'OFFLINE' : isLiveDataView || workspaceData ? 'LIVE DATA' : 'MODULE NOT CONNECTED'}</small></div>{workspaceLoading ? <div className="workspace-empty"><Radio size={24} /><strong>Loading backend intelligence...</strong><span>Requesting the current THERMOSENTRY data scope.</span></div> : workspaceError ? <div className="workspace-empty"><AlertTriangle size={24} /><strong>Backend workspace unavailable</strong><span>{workspaceError}</span></div> : activeNav === 'Thermal Events' ? <div className="event-list">{anomalies.length ? anomalies.map((event) => <button key={event.id} onClick={() => onSelect(event)}><Flame size={16} /><span><strong>{event.id}</strong><small>{event.latitude.toFixed(4)}, {event.longitude.toFixed(4)} · {event.acquisition_date} {event.acquisition_time}</small></span><ChevronRight size={15} /></button>) : <p>No live FIRMS detections returned for the current query.</p>}</div> : activeNav === 'Live Orbit' ? <div className="workspace-summary"><DataRow label="Satellite" value="NOAA-20 (VIIRS)" accent /><DataRow label="Query scope" value="India bounding box" /><DataRow label="Thermal detections" value={workspaceData?.summary?.total_anomalies ?? anomalies.length} accent /><DataRow label="High-risk events" value={workspaceData?.summary?.high_risk_count ?? 'Unavailable'} /><DataRow label="Feed status" value={firmsError ? 'Offline' : 'Connected'} /></div> : activeNav === 'Persistent Sources' ? <div className="event-list">{data.filter((event) => event.persistence?.is_persistent).map((event) => <button key={event.id} onClick={() => onSelect(event)}><Layers3 size={16} /><span><strong>{event.id}</strong><small>{event.persistence.observation_count} observations · score {event.persistence.persistence_score}</small></span><ChevronRight size={15} /></button>)}</div> : activeNav === 'Industrial Context' ? <div className="event-list">{data.filter((event) => event.industrial_context?.has_nearby_industrial).map((event) => <button key={event.id} onClick={() => onSelect(event)}><BarChart3 size={16} /><span><strong>{event.industrial_context.nearest_facility_name || 'Unnamed OSM facility'}</strong><small>{event.id} · {event.industrial_context.distance_to_nearest_km ?? 'Unavailable'} km</small></span><ChevronRight size={15} /></button>)}</div> : activeNav === 'Risk Intelligence' ? <div className="event-list">{data.filter((event) => ['CRITICAL', 'HIGH'].includes(event.risk_assessment?.risk_level)).map((event) => <button key={event.id} onClick={() => onSelect(event)}><AlertTriangle size={16} /><span><strong>{event.risk_assessment.risk_level} · {event.risk_assessment.composite_risk_score}/100</strong><small>{event.id} · {event.risk_assessment.action_recommendation}</small></span><ChevronRight size={15} /></button>)}</div> : activeNav === 'Reports' ? <div className="workspace-empty"><BarChart3 size={24} /><strong>Reports are ready from analyzed events</strong><span>Select a thermal event, then use the backend report endpoint for an HTML download.</span></div> : <div className="workspace-empty"><AlertTriangle size={24} /><strong>{activeNav} is not connected yet</strong><span>This workspace will use the existing backend intelligence modules when they are implemented.</span></div>}</section>
}
function DataRow({ label, value, accent, orange }) { return <div className="data-row"><span>{label}</span><strong className={`${accent ? 'cyan-text' : ''}${orange ? ' orange-text' : ''}`}>{value}</strong></div> }
function AnalyticsCard({ icon: Icon, label, value, change, tone, chart }) { const chartId = `chart-${tone}-${label.replaceAll(' ', '-').toLowerCase()}`; return <div className="analytics-card"><Icon size={18} className={tone} /><div><span>{label}</span><strong>{value} <small className={tone}>{change}</small></strong></div><svg className="sparkline" viewBox="0 0 166 34" preserveAspectRatio="none" role="img" aria-label={`${label} trend`}><defs><linearGradient id={chartId} x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="currentColor" stopOpacity=".3" /><stop offset="1" stopColor="currentColor" stopOpacity="0" /></linearGradient></defs><path className="spark-area" d={`${chart} L 166 34 L 0 34 Z`} fill={`url(#${chartId})`} /><path className="spark-line" d={chart} /><circle className="spark-end" cx="166" cy="9" r="2.5" /></svg></div> }
export default App
