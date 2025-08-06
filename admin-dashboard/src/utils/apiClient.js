import axios from 'axios';
import { API_CONFIG, REQUEST_CONFIG } from '../config/api';

// Create axios instance with default configuration
const apiClient = axios.create(REQUEST_CONFIG);

// Service health checker
export const checkServiceHealth = async (serviceName) => {
  try {
    const serviceConfig = API_CONFIG[serviceName];
    if (!serviceConfig) {
      throw new Error(`Unknown service: ${serviceName}`);
    }

    const healthUrl = `${serviceConfig.url}${serviceConfig.endpoints.health}`;
    const response = await apiClient.get(healthUrl);
    
    return {
      service: serviceName,
      status: (response.data.status === 'healthy' || response.data.status === 'ok' || response.status === 200) ? 'online' : 'offline',
      lastCheck: new Date().toISOString(),
      responseTime: response.headers['x-response-time'] || 'N/A',
      data: response.data
    };
  } catch (error) {
    return {
      service: serviceName,
      status: 'offline',
      lastCheck: new Date().toISOString(),
      error: error.message
    };
  }
};

// Check all services health
export const checkAllServicesHealth = async () => {
  const services = Object.keys(API_CONFIG);
  const results = await Promise.allSettled(
    services.map(service => checkServiceHealth(service))
  );
  
  const statuses = {};
  results.forEach((result, index) => {
    const serviceName = services[index];
    if (result.status === 'fulfilled') {
      statuses[getServiceDisplayName(serviceName)] = result.value;
    } else {
      statuses[getServiceDisplayName(serviceName)] = {
        service: serviceName,
        status: 'offline',
        lastCheck: new Date().toISOString(),
        error: result.reason?.message || 'Unknown error'
      };
    }
  });
  
  return statuses;
};

// Get service statistics
export const getServiceStats = async (serviceName) => {
  try {
    const serviceConfig = API_CONFIG[serviceName];
    if (!serviceConfig || !serviceConfig.endpoints.stats) {
      throw new Error(`Stats endpoint not available for service: ${serviceName}`);
    }

    const statsUrl = `${serviceConfig.url}${serviceConfig.endpoints.stats}`;
    const response = await apiClient.get(statsUrl);
    return response.data;
  } catch (error) {
    console.warn(`Failed to fetch ${serviceName} stats:`, error.message);
    return null;
  }
};

// Get all service statistics
export const getAllServiceStats = async () => {
  const stats = {
    subscribers: 0,
    content: 0,
    scrapeJobs: 0,
    aiJobs: 0
  };

  try {
    // Fetch subscriber stats
    const subscriberStats = await getServiceStats('subscriberManager');
    if (subscriberStats) {
      stats.subscribers = subscriberStats.total_subscribers || 0;
    }
  } catch (error) {
    console.warn('Failed to fetch subscriber stats:', error.message);
  }

  try {
    // Fetch scraper stats
    const scraperStats = await getServiceStats('webScraper');
    if (scraperStats) {
      stats.scrapeJobs = scraperStats.stats?.total_jobs || scraperStats.total_jobs || 0;
    }
  } catch (error) {
    console.warn('Failed to fetch scraper stats:', error.message);
  }

  try {
    // Fetch content stats
    const contentStats = await getServiceStats('contentManager');
    if (contentStats) {
      stats.content = contentStats.total_content || 0;
    }
  } catch (error) {
    console.warn('Failed to fetch content stats:', error.message);
  }

  try {
    // Fetch AI processor stats
    const aiStats = await getServiceStats('aiProcessor');
    if (aiStats) {
      stats.aiJobs = aiStats.total_jobs || 0;
    }
  } catch (error) {
    console.warn('Failed to fetch AI processor stats:', error.message);
  }

  return stats;
};

// Helper function to get display names for services
const getServiceDisplayName = (serviceName) => {
  const displayNames = {
    contentManager: 'Content Manager',
    aiProcessor: 'AI Processor',
    webScraper: 'Web Scraper',
    distributor: 'Distributor',
    subscriberManager: 'Subscriber Manager'
  };
  
  return displayNames[serviceName] || serviceName;
};

// Generic API call function
export const makeApiCall = async (serviceName, endpoint, method = 'GET', data = null) => {
  try {
    const serviceConfig = API_CONFIG[serviceName];
    if (!serviceConfig) {
      throw new Error(`Unknown service: ${serviceName}`);
    }

    const url = `${serviceConfig.url}${serviceConfig.endpoints[endpoint] || endpoint}`;
    const config = {
      method,
      url,
      ...REQUEST_CONFIG
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.data = data;
    }

    const response = await axios(config);
    return response.data;
  } catch (error) {
    console.error(`API call failed for ${serviceName}/${endpoint}:`, error.message);
    throw error;
  }
};

export default apiClient;