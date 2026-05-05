// client/src/components/facilitytable.jsx
import { theme } from '../design_system'

export default function FacilityTable({ facilities, selected, onSelect }) {
    return (
        <div style={{
            background: theme.colors.surface,
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.colors.border}`,
            overflow: 'hidden',
            boxShadow: theme.shadows.sm,
            fontFamily: 'serif'
        }}>
            <div style={{
                padding: '0.75rem 1rem',
                borderBottom: `1px solid ${theme.colors.border}`,
                background: '#FDF8F3',
                fontSize: '0.6rem',
                fontWeight: 'bold',
                color: theme.colors.primary,
                textTransform: 'uppercase',
                letterSpacing: '0.2em'
            }}>
                🏭 Real-Time Facility Intelligence
            </div>
            <div style={{ overflowY: 'auto', maxHeight: '350px' }}>
                {facilities.map(f => (
                    <div
                        key={f.id}
                        onClick={() => onSelect(f)}
                        style={{
                            padding: '1rem',
                            borderBottom: `1px solid #EDE4D8`,
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            background: selected?.id === f.id ? '#EDE4D8' : 'transparent',
                            transition: 'background 0.2s'
                        }}
                    >
                        <div>
                            <p style={{ fontSize: '0.85rem', fontWeight: 'bold', color: theme.colors.text, margin: 0 }}>{f.name}</p>
                            <p style={{ fontSize: '0.6rem', color: theme.colors.textMuted, marginTop: '0.1rem', margin: 0 }}>
                                {f.state} · EPA: {f.epa_reported?.toLocaleString() || 0} kg/hr
                            </p>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <p style={{ fontSize: '0.85rem', fontWeight: 'bold', color: theme.colors.primary, margin: 0 }}>
                                {f.fluxara_latest?.toLocaleString() || 0} <span style={{ fontSize: '0.6rem', fontWeight: 'normal', opacity: 0.6 }}>kg/hr</span>
                            </p>
                            <span style={{
                                fontSize: '0.5rem',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontWeight: 'bold',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                background: f.risk_level === 'high' ? '#fee2e2' : f.risk_level === 'medium' ? '#ffedd5' : '#dcfce7',
                                color: f.risk_level === 'high' ? '#991b1b' : f.risk_level === 'medium' ? '#9a3412' : '#166534'
                            }}>
                                {f.risk_level}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}