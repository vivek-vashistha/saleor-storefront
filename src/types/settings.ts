/**
 * Interface for application settings
 */
export interface Settings {
  // API settings
  apiUrl: string;

  // Feature flags
  features: {
    enableTelemetry: boolean;
  };

  // Application settings
  app: {
    port: number;
    hostname: string;
  };
}
