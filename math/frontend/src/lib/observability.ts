import { onCLS, onLCP, onTTFB, type Metric } from 'web-vitals';

interface WSEvent {
    eventId: string;
    agentId: string;
    type: string;
    payload: Record<string, unknown>;
    timestamp: string;
}

function sendToAnalytics(metric: Metric) {
    const event: WSEvent = {
        eventId: crypto.randomUUID(),
        agentId: 'frontend-client',
        type: 'web_vital',
        payload: {
            name: metric.name,
            value: metric.value,
            rating: metric.rating,
            delta: metric.delta,
            id: metric.id,
        },
        timestamp: new Date().toISOString(),
    };

    // In a real app, use navigator.sendBeacon or fetch
    console.log('[Observability]', event);
}

export function reportWebVitals() {
    onCLS(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
}
