import React from 'react';
import { Card, Alert } from 'antd';

const Distributor = () => {
  return (
    <div>
      <Alert
        message="Content Distributor"
        description="Manage content distribution across social media and email"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card title="Content Distributor" style={{ marginBottom: 16 }}>
        <p>Content distribution features will be available here.</p>
        <p>This will include:</p>
        <ul>
          <li>Social media posting schedule</li>
          <li>Email newsletter campaigns</li>
          <li>Instagram automation</li>
          <li>Distribution analytics</li>
        </ul>
      </Card>
    </div>
  );
};

export default Distributor;