#!/usr/bin/env node

const axios = require('axios');
const { API_CONFIG } = require('./src/config/api');

async function testHealthChecks() {
  console.log('🔍 Testing Admin Dashboard Health Check System\n');
  
  const services = Object.keys(API_CONFIG);
  const results = [];
  
  for (const serviceName of services) {
    const serviceConfig = API_CONFIG[serviceName];
    const healthUrl = `${serviceConfig.url}${serviceConfig.endpoints.health}`;
    
    console.log(`📡 Testing ${serviceName} at ${healthUrl}`);
    
    try {
      const startTime = Date.now();
      const response = await axios.get(healthUrl, { timeout: 5000 });
      const responseTime = Date.now() - startTime;
      
      const status = (response.data.status === 'healthy' || response.data.status === 'ok' || response.status === 200) ? 'ONLINE' : 'OFFLINE';
      
      console.log(`   ✅ ${status} (${responseTime}ms) - ${JSON.stringify(response.data)}`);
      
      results.push({
        service: serviceName,
        status: 'ONLINE',
        responseTime: responseTime + 'ms',
        data: response.data
      });
    } catch (error) {
      console.log(`   ❌ OFFLINE - ${error.message}`);
      results.push({
        service: serviceName,
        status: 'OFFLINE',
        error: error.message
      });
    }
    console.log('');
  }
  
  console.log('📊 Health Check Summary:');
  console.log('========================');
  results.forEach(result => {
    const statusIcon = result.status === 'ONLINE' ? '🟢' : '🔴';
    console.log(`${statusIcon} ${result.service}: ${result.status} ${result.responseTime || ''}`);
  });
  
  const onlineCount = results.filter(r => r.status === 'ONLINE').length;
  const totalCount = results.length;
  
  console.log(`\n✨ Health Check Complete: ${onlineCount}/${totalCount} services online`);
  
  if (onlineCount === totalCount) {
    console.log('🎉 All services are healthy! The admin dashboard should work perfectly.');
  } else {
    console.log('⚠️  Some services are offline. The dashboard will show mock data for offline services.');
  }
}

if (require.main === module) {
  testHealthChecks().catch(console.error);
}

module.exports = { testHealthChecks };