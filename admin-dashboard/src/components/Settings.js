import React from 'react';
import { Card, Alert } from 'antd';

const Settings = () => {
  return (
    <div>
      <Alert
        message="System Settings"
        description="Configure system-wide settings and preferences"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card title="System Settings" style={{ marginBottom: 16 }}>
        <p>System configuration features will be available here.</p>
        <p>This will include:</p>
        <ul>
          <li>API key management</li>
          <li>Service configuration</li>
          <li>Notification settings</li>
          <li>Backup and maintenance</li>
        </ul>
      </Card>
    </div>
  );
};

export default Settings;