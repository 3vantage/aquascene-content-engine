// API Configuration for AquaScene Content Engine Admin Dashboard

export const API_CONFIG = {
  contentManager: {
    url: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    endpoints: {
      health: '/health',
      content: '/api/v1/content',
      stats: '/api/v1/content/stats',
      workflows: '/api/v1/workflows'
    }
  },
  aiProcessor: {
    url: process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:8001',
    endpoints: {
      health: '/health',
      jobs: '/api/v1/jobs',
      stats: '/api/v1/jobs/stats',
      process: '/api/v1/process'
    }
  },
  webScraper: {
    url: process.env.REACT_APP_SCRAPER_URL || 'http://localhost:8002',
    endpoints: {
      health: '/health',
      scrape: '/api/v1/scrape',
      stats: '/api/v1/stats',
      jobs: '/api/v1/jobs'
    }
  },
  distributor: {
    url: process.env.REACT_APP_DISTRIBUTOR_URL || 'http://localhost:8003',
    endpoints: {
      health: '/health',
      newsletters: '/api/v1/newsletters',
      instagram: '/api/v1/instagram',
      stats: '/api/v1/stats'
    }
  },
  subscriberManager: {
    url: process.env.REACT_APP_SUBSCRIBER_URL || 'http://localhost:8004',
    endpoints: {
      health: '/health',
      subscribers: '/api/v1/subscribers',
      stats: '/api/v1/subscribers/stats',
      auth: '/api/v1/auth'
    }
  }
};

// Helper function to build full URLs
export const buildUrl = (service, endpoint) => {
  return `${API_CONFIG[service].url}${API_CONFIG[service].endpoints[endpoint]}`;
};

// Default request configuration
export const REQUEST_CONFIG = {
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
};

// Service health check configuration
export const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
export const SERVICE_TIMEOUT = 5000; // 5 seconds