import React from 'react';
import { Card, Alert } from 'antd';

const WebScraper = () => {
  return (
    <div>
      <Alert
        message="Web Scraper"
        description="Monitor web scraping jobs and configure data sources"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card title="Web Scraper" style={{ marginBottom: 16 }}>
        <p>Web scraping features will be available here.</p>
        <p>This will include:</p>
        <ul>
          <li>Scraping job management</li>
          <li>Data source configuration</li>
          <li>Scraped content review</li>
          <li>Error monitoring and logs</li>
        </ul>
      </Card>
    </div>
  );
};

export default WebScraper;