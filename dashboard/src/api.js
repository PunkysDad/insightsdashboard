const BASE_URL = "http://localhost:8081";

export const fetchOverview = () => fetch(`${BASE_URL}/dashboard/overview`).then(r => r.json());
export const fetchSessions = () => fetch(`${BASE_URL}/dashboard/sessions`).then(r => r.json());
export const fetchSession = (id) => fetch(`${BASE_URL}/dashboard/sessions/${id}`).then(r => r.json());
