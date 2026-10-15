// client/src/components/emissionchart.jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { theme } from '../design_system'

export default function EmissionChart({ data }) {
    const dates = data?.dates || []
    const chartData = dates.map((d, i) => ({
        date: d,
        Reported: data.epa?.[i] ?? null,
        Observed: data.fluxara?.[i] ?? null
    }))

    // No satellite detections yet: say so. Never draw a made up line.
    if (chartData.length === 0) {
        return (
            <div style={{
                background: theme.colors.surface,
                borderRadius: theme.radius.md,
                border: `1px solid ${theme.colors.border}`,
                padding: '2rem',
                fontFamily: 'serif',
                color: theme.colors.textMuted,
                fontSize: '0.85rem'
            }}>
                No satellite plume detections in this area yet. This does not mean zero emissions:
                satellites only see large leaks, and only on clear days when they pass over.
            </div>
        )
    }

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
                padding: '1rem 1.25rem',
                borderBottom: `1px solid ${theme.colors.border}`,
                background: '#FDF8F3',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <span style={{ fontSize: '0.6rem', fontWeight: 'bold', color: theme.colors.primary, textTransform: 'uppercase', letterSpacing: '0.2em' }}>
                    Observed plume rates by month
                </span>
                <span style={{ fontSize: '0.6rem', color: '#9ca3af', fontWeight: 'medium', fontStyle: 'italic' }}>
                    kg/hr at overpass. Months without detections are not shown.
                </span>
            </div>
            <div style={{ padding: '1.5rem' }}>
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorFlux" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={theme.colors.primary} stopOpacity={0.1}/>
                                <stop offset="95%" stopColor={theme.colors.primary} stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F5F0EB" vertical={false} />
                        <XAxis 
                            dataKey="date" 
                            stroke={theme.colors.textMuted} 
                            fontSize={10} 
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis 
                            stroke={theme.colors.textMuted} 
                            fontSize={10} 
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={v => `${(v / 1000).toFixed(1)}k`} 
                        />
                        <Tooltip 
                            contentStyle={{ 
                                background: 'white', 
                                border: `1px solid ${theme.colors.border}`, 
                                borderRadius: '12px', 
                                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                                fontSize: '11px' 
                            }} 
                        />
                        <Legend 
                            verticalAlign="top" 
                            align="right"
                            wrapperStyle={{ fontSize: '10px', paddingBottom: '20px', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.1em' }} 
                        />
                        <Area 
                            type="linear" 
                            dataKey="Observed" 
                            stroke={theme.colors.primary} 
                            strokeWidth={2} 
                            fillOpacity={1} 
                            fill="url(#colorFlux)" 
                        />
                        <Line 
                            type="monotone" 
                            dataKey="Reported" 
                            stroke={theme.colors.accent} 
                            strokeWidth={2} 
                            strokeDasharray="5 5" 
                            dot={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}