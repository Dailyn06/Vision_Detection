import { useEffect, useState, type ReactNode } from 'react';

type IconName =
  | 'activity'
  | 'alert'
  | 'box'
  | 'camera'
  | 'chevron'
  | 'clock'
  | 'cpu'
  | 'grid'
  | 'layers'
  | 'pause'
  | 'play'
  | 'search'
  | 'settings'
  | 'shield'
  | 'sliders'
  | 'target'
  | 'wifi';

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    activity: <path d="M3 12h4l2.2-7 4.1 14 2.2-7H21" />,
    alert: (
      <>
        <path d="M10.3 3.5 2.7 17a2 2 0 0 0 1.8 3h15a2 2 0 0 0 1.8-3L13.7 3.5a2 2 0 0 0-3.4 0Z" />
        <path d="M12 9v4M12 17h.01" />
      </>
    ),
    box: (
      <>
        <path d="m21 8-9 5-9-5 9-5 9 5Z" />
        <path d="m3 8 9 5 9-5v9l-9 5-9-5V8Z" />
        <path d="M12 13v9" />
      </>
    ),
    camera: (
      <>
        <path d="M14.5 4 16 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3l1.5-3h5Z" />
        <circle cx="12" cy="13" r="3.5" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    cpu: (
      <>
        <rect x="6" y="6" width="12" height="12" rx="2" />
        <path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3M10 10h4v4h-4z" />
      </>
    ),
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    layers: (
      <>
        <path d="m12 2 9 5-9 5-9-5 9-5Z" />
        <path d="m3 12 9 5 9-5M3 17l9 5 9-5" />
      </>
    ),
    pause: (
      <>
        <path d="M8 5v14M16 5v14" />
      </>
    ),
    play: <path d="m8 5 11 7-11 7V5Z" />,
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-5" />
      </>
    ),
    sliders: (
      <>
        <path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3" />
        <path d="M1 14h6M9 8h6M17 16h6" />
      </>
    ),
    target: (
      <>
        <circle cx="12" cy="12" r="8" />
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2V0M12 24v-2M2 12H0M24 12h-2" />
      </>
    ),
    wifi: (
      <>
        <path d="M5 12.6a11 11 0 0 1 14 0M8.5 16a6 6 0 0 1 7 0" />
        <circle cx="12" cy="20" r=".8" fill="currentColor" stroke="none" />
      </>
    ),
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

type Status = {
  state: string; error: string | null; stale: boolean; alarm_latched: boolean;
  frames: number; object_count: number; clear_frames: number; confirm_frames: number;
  reset_eligible: boolean; fps: number; last_frame: string | null;
  dimensions: number[] | null; camera_index: number; plc_enabled: boolean; plc_connected: boolean;
};
type AlarmEvent = { id: string; time: string; evidence: Record<string, string> };

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [events, setEvents] = useState<AlarmEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [overlay, setOverlay] = useState(true);
  const [activeNav, setActiveNav] = useState('Overview');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const poll = async () => {
      try {
        const response = await fetch('/api/status', { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(4000)]) });
        if (!response.ok) throw new Error('Status unavailable');
        const next: Status = await response.json();
        if (!cancelled) { setStatus(next); setConnected(true); }
        const history = await fetch('/api/events', { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(4000)]) });
        if (!history.ok) throw new Error('History unavailable');
        const records: AlarmEvent[] = await history.json();
        if (!cancelled) setEvents(records);
      } catch {
        if (!cancelled) setConnected(false);
      } finally {
        if (!cancelled) timer = setTimeout(poll, 1000);
      }
    };
    void poll();
    return () => { cancelled = true; clearTimeout(timer); controller.abort(); };
  }, []);

  const live = connected && status?.state === 'running' && !status.stale;
  useEffect(() => {
    if (!live) { setPreview(null); return; }
    let cancelled = false;
    let objectUrl: string | null = null;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const load = async () => {
      try {
        const response = await fetch(`/api/preview?kind=${overlay ? 'annotated' : 'raw'}`, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(4000)]) });
        if (!response.ok) throw new Error('Frame unavailable');
        const blob = await response.blob();
        if (!cancelled) {
          const next = URL.createObjectURL(blob);
          const previous = objectUrl;
          objectUrl = next;
          setPreview(next); setPreviewError(false);
          if (previous) URL.revokeObjectURL(previous);
        }
      } catch { if (!cancelled) { setPreview(null); setPreviewError(true); } }
      finally { if (!cancelled) timer = setTimeout(load, 200); }
    };
    void load();
    return () => { cancelled = true; clearTimeout(timer); controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [live, overlay]);

  const command = async (action: string) => {
    setBusy(true); setMessage('');
    try {
      const response = await fetch(`/api/${action}`, { method: 'POST', headers: { 'X-Vision-Control': '1' } });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setStatus(result.status); setMessage(result.message);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Command failed'); }
    finally { setBusy(false); }
  };
  const capture = async () => {
    setBusy(true);
    try {
      const response = await fetch(`/api/preview?kind=${overlay ? 'annotated' : 'raw'}`);
      if (!response.ok) throw new Error('No live frame available');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url; link.download = `camera_${status?.camera_index}_${Date.now()}.jpg`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage('Preview frame download started (maximum width 1280 px). Full-resolution alarm evidence is available below.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Capture failed'); }
    finally { setBusy(false); }
  };
  const active = status && ['connecting', 'running', 'stopping'].includes(status.state);
  const stateLabel = !connected ? 'Disconnected' : status?.state === 'running' && status.stale ? 'Stale inspection' : status?.state;
  const metric = (label: string, value: string, icon: IconName) => (
    <article className="metric-card"><div className="metric-icon blue"><Icon name={icon} /></div>
      <div className="metric-copy"><span>{label}</span><strong>{value}</strong></div></article>
  );
  return (
    <div className="app-shell design-v2">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><span /><span /><span /></div><div><strong>PPTC</strong><small>VISION DETECTION</small></div></div>
        <nav className="main-nav" aria-label="Main navigation"><p>WORKSPACE</p>
          {(['Overview', 'Detections', 'Configuration'] as const).map((name) => (
            <button key={name} type="button" aria-label={name} aria-current={activeNav === name ? 'page' : undefined}
              className={activeNav === name ? 'active' : ''} onClick={() => setActiveNav(name)}>
              <Icon name={name === 'Overview' ? 'grid' : name === 'Detections' ? 'target' : 'sliders'} /><span>{name}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer"><div className="line-badge"><Icon name="camera" /><div><small>INSPECTION SOURCE</small><strong>MindVision camera</strong></div></div></div>
      </aside>
      <main>
        <header className="topbar"><div><p className="eyebrow">FOREIGN OBJECT INSPECTION</p><h1>Vision control</h1></div>
          <div className="topbar-actions"><strong className={live ? 'status-good' : 'status-warning'}>{stateLabel}</strong></div>
        </header>
        <div className="content">
          <section className="section-heading"><div><h2>{activeNav}</h2><p>Reference comparison inside the circular inspection area.</p></div></section>
          <div role="status" aria-live="polite" className="service-message">{status?.error || message || (!connected ? 'Cannot reach inspection service. Start vision_server.py and check the connection.' : status?.alarm_latched ? 'ALARM LATCHED ? inspect the evidence and clear the area before reset.' : 'Connected to local inspection service.')}</div>
          {activeNav === 'Overview' && <>
            <section className="metrics-grid">
              {metric('Frames processed (service session)', connected ? String(status?.frames ?? 0) : '?', 'layers')}
              {metric('Objects in latest frame', live ? String(status?.object_count ?? 0) : '?', 'target')}
              {metric('Software alarm', connected ? status?.alarm_latched ? 'LATCHED' : 'Not latched' : '?', 'alert')}
              {metric('Inspection FPS', live ? String(status?.fps ?? 0) : '?', 'activity')}
            </section>
            <section className="work-grid">
              <article className="panel vision-panel">
                <div className="panel-header"><div><span className="panel-kicker">CAMERA INSPECTION</span><h3>MindVision camera {status?.camera_index ?? '?'}</h3></div><span>{status?.dimensions?.join(' \u00D7 ') ?? 'No frame'}</span></div>
                <div className="camera-feed real-camera-feed">
                  {live && preview && !previewError ? <img src={preview} alt={overlay ? 'Live camera with foreign-object annotations' : 'Live raw camera'} /> : <div className="empty-feed"><Icon name="camera" size={36} /><p>{live ? 'Waiting for camera preview' : stateLabel}</p></div>}
                </div>
                <div className="vision-toolbar"><div className="current-inspection"><div><span>LAST INSPECTED FRAME</span><strong>{status?.last_frame ? new Date(status.last_frame).toLocaleTimeString() : 'No frame received'}</strong></div></div>
                  <div className="toolbar-actions"><button className="capture-button" disabled={!live || busy} onClick={() => void capture()}>Take photo</button>
                    <button className="secondary-button" onClick={() => setOverlay(!overlay)}>{overlay ? 'Hide overlay' : 'Show overlay'}</button>
                  </div>
                </div>
              </article>
              <aside className="right-column">
                <article className="panel control-panel"><div className="panel-header compact"><div><span className="panel-kicker">OPERATOR CONTROL</span><h3>Inspection</h3></div></div>
                  <div className="operator-controls">
                    <button className={active ? 'pause-button' : 'start-button'} disabled={!connected || busy || status?.state === 'stopping'} onClick={() => void command(active ? 'stop' : 'start')}>{active ? 'Stop inspection' : 'Start inspection'}</button>
                    <button className="secondary-button" disabled={!connected || busy || !status?.reset_eligible} onClick={() => void command('reset')}>Reset alarm</button>
                    <p>Reset requires {status?.confirm_frames ?? '?'} consecutive clear frames and a ready PLC connection when enabled. Stopping inspection also stops vision health updates.</p>
                    <p>Clear frames: {live ? status?.clear_frames : '?'}</p>
                  </div>
                </article>
                <article className="panel health-panel"><div className="panel-header compact"><h3>System health</h3></div><div className="health-list">
                  <div><span>Inspection</span><strong>{stateLabel}</strong></div>
                  <div><span>PLC communication</span><strong>{!connected ? 'Unknown' : !status?.plc_enabled ? 'Disabled' : status.plc_connected ? 'Connected' : 'Disconnected'}</strong></div>
                  <div><span>Reference</span><strong>RefPic/Ref1.png</strong></div>
                </div><p className="panel-note">PLC ladder owns physical outputs. Connection status does not confirm buzzer or light activation.</p></article>
              </aside>
            </section>
          </>}
          {activeNav === 'Configuration' && <article className="panel"><div className="panel-header"><h3>Launch configuration</h3></div><div className="operator-controls"><p>Camera index: {status?.camera_index ?? '?'}</p><p>Alarm confirmation: {status?.confirm_frames ?? '?'} frames</p><p>PLC: {status?.plc_enabled ? 'Enabled' : 'Disabled'}</p><p>Configure camera, frame rate and PLC options when launching vision_server.py. Detector ROI, difference threshold and minimum area remain in Detection.py.</p><p>The detector reports object regions, without model confidence percentages.</p></div></article>}
          {activeNav !== 'Configuration' && <section className="panel event-panel"><div className="panel-header"><div><span className="panel-kicker">SAVED EVIDENCE</span><h3>{activeNav === 'Detections' ? 'Alarm history' : 'Recent alarms'}</h3></div>{activeNav === 'Overview' && <button className="text-button" onClick={() => setActiveNav('Detections')}>View history</button>}</div>
            <div className="alarm-history">
              {!connected ? <p>History unavailable while disconnected.</p> : events.length === 0 ? <p>No saved alarm evidence found.</p> : (activeNav === 'Overview' ? events.slice(0, 5) : events).map(event => (
                <article className="alarm-record" key={event.id}><div><strong>Confirmed foreign-object alarm</strong><p>{new Date(event.time).toLocaleString()}</p><small>{event.id}</small></div><div className="evidence-links">{Object.entries(event.evidence).map(([kind, url]) => <a key={kind} href={url} target="_blank" rel="noreferrer">{kind === 'detection' ? 'Annotated' : kind === 'raw' ? 'Raw image' : 'Mask'}</a>)}</div></article>
              ))}
            </div>
          </section>}
        </div>
      </main>
    </div>
  );
}
