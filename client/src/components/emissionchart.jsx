// client/src/components/emissionchart.jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { theme } from '../design_system'

export default function EmissionChart({ data }) {
    // Standardize data format
    const chartData = data.dates.map((d, i) => ({
        date: d,
        EPA: data.epa[i],
        Fluxara: data.fluxara[i]
    }))

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
                    📈 Emission Attribution Trends
                </span>
                <span style={{ fontSize: '0.6rem', color: '#9ca3af', fontWeight: 'medium', fontStyle: 'italic' }}>
                    Values in kg/hr
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
                            type="monotone" 
                            dataKey="Fluxara" 
                            stroke={theme.colors.primary} 
                            strokeWidth={2} 
                            fillOpacity={1} 
                            fill="url(#colorFlux)" 
                        />
                        <Line 
                            type="monotone" 
                            dataKey="EPA" 
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