// client/src/components/metriccards.jsx
import { theme } from '../design_system'

export default function MetricCards({ metrics }) {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', fontFamily: 'serif' }}>
            {metrics.map((m, i) => (
                <div key={i} style={{
                    padding: '1.5rem',
                    borderRadius: theme.radius.md,
                    transition: 'all 0.3s ease',
                    background: m.gold ? theme.colors.primary : theme.colors.surface,
                    color: m.gold ? theme.colors.secondary : theme.colors.text,
                    border: m.gold ? 'none' : `1px solid ${theme.colors.border}`,
                    boxShadow: theme.shadows.sm,
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    <p style={{
                        fontSize: '0.6rem',
                        textTransform: 'uppercase',
                        fontWeight: 'bold',
                        letterSpacing: '0.2em',
                        marginBottom: '0.5rem',
                        color: m.gold ? theme.colors.accent : theme.colors.textMuted
                    }}>
                        {m.label}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                        <p style={{ fontSize: '2.25rem', fontWeight: 'bold', letterSpacing: '-0.05em', margin: 0 }}>
                            {m.value}
                        </p>
                        <span style={{ fontSize: '0.6rem', fontWeight: 'medium', opacity: 0.6 }}>
                            {m.unit || ''}
                        </span>
                    </div>
                    <p style={{ fontSize: '0.7rem', marginTop: '0.5rem', fontStyle: 'italic', opacity: 0.7, margin: 0 }}>
                        {m.sub}
                    </p>
                    {m.gold && (
                        <div style={{
                            marginTop: '1rem',
                            height: '4px',
                            width: '3rem',
                            background: theme.colors.accent,
                            borderRadius: '2px'
                        }} />
                    )}
                </div>
            ))}
        </div>
    )
}