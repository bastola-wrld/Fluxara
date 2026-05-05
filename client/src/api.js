// client/src/api.js
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = 'fluxara-dev-key-2024'; // In production, this would come from auth/env

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

export const api = {
    getFacilities: () => fetch(`${BASE}/facilities`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacility: (id) => fetch(`${BASE}/facilities/${id}`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacilityInversions: (id) => fetch(`${BASE}/facilities/${id}/inversions`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getFacilityAlerts: (id) => fetch(`${BASE}/facilities/${id}/alerts`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    getAlerts: (resolved = false) => fetch(`${BASE}/alerts?resolved=${resolved}`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getAlertCount: () => fetch(`${BASE}/alerts/count`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    resolveAlert: (id) => fetch(`${BASE}/alerts/${id}/resolve`, { method: 'PATCH', headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    getReports: () => fetch(`${BASE}/reports`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    getReport: (id) => fetch(`${BASE}/reports/${id}`, { headers }).then(r => r.ok ? r.json() : Promise.reject(r)),
    
    runInversion: (body) => fetch(`${BASE}/v1/invert`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    }).then(r => r.ok ? r.json() : Promise.reject(r)),
};
