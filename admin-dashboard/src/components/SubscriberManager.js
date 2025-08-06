import React from 'react';
import { Card, Alert } from 'antd';

const SubscriberManager = () => {
  return (
    <div>
      <Alert
        message="Subscriber Manager"
        description="Manage newsletter subscribers and email campaigns"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card title="Subscriber Manager" style={{ marginBottom: 16 }}>
        <p>Subscriber management features will be available here.</p>
        <p>This will include:</p>
        <ul>
          <li>View and manage subscribers</li>
          <li>Create email campaigns</li>
          <li>Track email performance</li>
          <li>Manage subscription preferences</li>
        </ul>
      </Card>
    </div>
  );
};

export default SubscriberManager;