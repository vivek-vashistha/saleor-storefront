'use client';

import { Settings } from '@/types/settings';

/**
 * Application settings singleton
 */
const settings: Settings = {
  // API settings
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4003',

  // Feature flags
  features: {
    enableTelemetry: process.env.NEXT_TELEMETRY_DISABLED !== '1',
  },

  // Application settings
  app: {
    port: parseInt(process.env.PORT || '3000', 10),
    hostname: process.env.HOSTNAME || '0.0.0.0',
  },
};

export { settings }; 