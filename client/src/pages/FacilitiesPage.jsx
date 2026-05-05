// client/src/pages/FacilitiesPage.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { theme } from '../design_system';

export default function FacilitiesPage() {
    const [facilities, setFacilities] = useState([]);
    const [search, setSearch] = useState('');
    const [filterState, setFilterState] = useState('All');
    const [filterRisk, setFilterRisk] = useState('All');
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        api.getFacilities()
            .then(setFacilities)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const filtered = facilities.filter(f => {
        const matchesSearch = f.name.toLowerCase().includes(search.toLowerCase());
        const matchesState = filterState === 'All' || f.state === filterState;
        const matchesRisk = filterRisk === 'All' || f.risk_level?.toLowerCase() === filterRisk.toLowerCase();
        return matchesSearch && matchesState && matchesRisk;
    });

    if (loading) return (
        <div style={{ padding: '4rem', textAlign: 'center', color: theme.colors.primary, fontFamily: 'serif' }}>
            Loading intelligence directory...
        </div>
    );

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', fontFamily: 'serif' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: theme.colors.primary, marginBottom: '2rem' }}>Industrial Facilities Directory</h1>
            
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '1rem',
                marginBottom: '2rem',
                background: 'white',
                padding: '1.5rem',
                borderRadius: '12px',
                boxShadow: theme.shadows.sm,
                border: `1px solid ${theme.colors.border}`
            }}>
                <input 
                    type="text" 
                    placeholder="Search by facility name..." 
                    style={{ flex: 1, minWidth: '200px', padding: '0.75rem', border: `1px solid ${theme.colors.border}`, borderRadius: '8px', background: '#F5F0EB' }}
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
                <select 
                    style={{ padding: '0.75rem', border: `1px solid ${theme.colors.border}`, borderRadius: '8px', background: '#F5F0EB' }}
                    value={filterState}
                    onChange={e => setFilterState(e.target.value)}
                >
                    <option value="All">All States</option>
                    <option value="TX">Texas</option>
                    <option value="NM">New Mexico</option>
                </select>
                <select 
                    style={{ padding: '0.75rem', border: `1px solid ${theme.colors.border}`, borderRadius: '8px', background: '#F5F0EB' }}
                    value={filterRisk}
                    onChange={e => setFilterRisk(e.target.value)}
                >
                    <option value="All">All Risk Levels</option>
                    <option value="High">High Risk</option>
                    <option value="Medium">Medium Risk</option>
                    <option value="Low">Low Risk</option>
                </select>
            </div>

            <div style={{
                background: 'white',
                borderRadius: '12px',
                boxShadow: theme.shadows.sm,
                border: `1px solid ${theme.colors.border}`,
                overflow: 'hidden'
            }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: '#F5F0EB', color: theme.colors.primary, borderBottom: `1px solid ${theme.colors.border}` }}>
                        <tr>
                            <th style={{ padding: '1rem' }}>Facility Name</th>
                            <th style={{ padding: '1rem' }}>Location</th>
                            <th style={{ padding: '1rem' }}>EPA Reported (kg/hr)</th>
                            <th style={{ padding: '1rem' }}>Fluxara Latest (kg/hr)</th>
                            <th style={{ padding: '1rem' }}>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody style={{ divideY: `1px solid ${theme.colors.border}` }}>
                        {filtered.map(f => (
                            <tr 
                                key={f.id} 
                                style={{ borderBottom: `1px solid ${theme.colors.border}`, cursor: 'pointer', transition: 'background 0.2s' }}
                                onClick={() => navigate(`/facility/${f.id}`)}
                                onMouseEnter={e => e.currentTarget.style.background = '#F5F0EB'}
                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                            >
                                <td style={{ padding: '1rem', fontWeight: 'bold' }}>{f.name}</td>
                                <td style={{ padding: '1rem' }}>{f.state}, {f.country}</td>
                                <td style={{ padding: '1rem' }}>{f.epa_reported || 'N/A'}</td>
                                <td style={{ padding: '1rem' }}>{f.fluxara_latest || 'N/A'}</td>
                                <td style={{ padding: '1rem' }}>
                                    <span style={{
                                        padding: '4px 12px',
                                        borderRadius: '20px',
                                        fontSize: '0.7rem',
                                        fontWeight: 'bold',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em',
                                        background: f.risk_level === 'high' ? '#fee2e2' : f.risk_level === 'medium' ? '#ffedd5' : '#dcfce7',
                                        color: f.risk_level === 'high' ? '#991b1b' : f.risk_level === 'medium' ? '#9a3412' : '#166534'
                                    }}>
                                        {f.risk_level}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
