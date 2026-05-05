// client/src/components/map.jsx
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { theme } from '../design_system'

const riskColor = {
    high: '#9B1C1C',
    medium: '#92400E',
    low: '#3D0C14',
    unknown: '#7A5C52'
}

export default function Map({ facilities, selected, onSelect }) {
    return (
        <div style={{
            background: '#FDF8F3',
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.colors.border}`,
            overflow: 'hidden',
            boxShadow: theme.shadows.md,
            height: '450px',
            fontFamily: 'serif'
        }}>
            <div style={{
                padding: '1rem 1.25rem',
                borderBottom: `1px solid ${theme.colors.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'white'
            }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.colors.primary, textTransform: 'uppercase', letterSpacing: '0.15em' }}>
                    🛰️ Permian Basin Intelligence
                </span>
                <span style={{ fontSize: '0.6rem', color: '#9ca3af', fontWeight: 500 }}>
                    Live satellite telemetry active
                </span>
            </div>
            <MapContainer
                center={[31.85, -102.1]}
                zoom={7}
                style={{ height: '385px', width: '100%' }}
                scrollWheelZoom={false}
            >
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                {facilities.map(f => (
                    <CircleMarker
                        key={f.id}
                        center={[f.lat, f.lon]}
                        radius={selected?.id === f.id ? 12 : 8}
                        fillColor={riskColor[f.risk_level || 'unknown']}
                        color={selected?.id === f.id ? '#3D0C14' : riskColor[f.risk_level || 'unknown']}
                        weight={selected?.id === f.id ? 3 : 1}
                        fillOpacity={0.8}
                        eventHandlers={{ click: () => onSelect(f) }}
                    >
                        <Popup>
                            <div style={{ minWidth: '180px', padding: '4px', fontFamily: 'serif' }}>
                                <h4 style={{ fontWeight: 'bold', color: theme.colors.primary, borderBottom: '1px solid #f3f4f6', paddingBottom: '4px', marginBottom: '8px', fontSize: '14px', margin: 0 }}>
                                    {f.name}
                                </h4>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: '4px', fontSize: '10px' }}>
                                    <span style={{ color: '#6b7280', textTransform: 'uppercase', fontWeight: 'bold' }}>EPA Reported</span>
                                    <span style={{ textAlign: 'right', fontWeight: 'bold' }}>{f.epa_reported?.toLocaleString() || 0} <span style={{ opacity: 0.5 }}>kg/hr</span></span>
                                    
                                    <span style={{ color: '#6b7280', textTransform: 'uppercase', fontWeight: 'bold' }}>Fluxara Live</span>
                                    <span style={{ textAlign: 'right', fontWeight: 'bold', color: theme.colors.primary }}>{f.fluxara_latest?.toLocaleString() || 0} <span style={{ opacity: 0.5 }}>kg/hr</span></span>
                                    
                                    <span style={{ color: '#6b7280', textTransform: 'uppercase', fontWeight: 'bold' }}>Risk Level</span>
                                    <span style={{ textAlign: 'right', fontWeight: 'bold', textTransform: 'capitalize', color: riskColor[f.risk_level] }}>{f.risk_level}</span>
                                </div>
                                <button 
                                    onClick={() => onSelect(f)}
                                    style={{
                                        width: '100%',
                                        marginTop: '12px',
                                        background: theme.colors.primary,
                                        color: 'white',
                                        padding: '4px 0',
                                        borderRadius: '4px',
                                        fontSize: '10px',
                                        fontWeight: 'bold',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em',
                                        border: 'none',
                                        cursor: 'pointer'
                                    }}
                                >
                                    View Full Analytics
                                </button>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>
        </div>
    )
}