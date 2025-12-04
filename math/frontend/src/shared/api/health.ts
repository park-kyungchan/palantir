import { apiClient } from './client';

export interface HealthCheckResponse {
    status: string;
    version: string;
}

export const checkHealth = async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/api/v1/health');
    return response.data;
};
