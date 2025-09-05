import axios from 'axios';
import { settings } from '@/config/settings';

/**
 * Get API client instance for use outside of React components
 */
export const getApiClient = () => {
  return axios.create({
    baseURL: settings.apiUrl,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};
