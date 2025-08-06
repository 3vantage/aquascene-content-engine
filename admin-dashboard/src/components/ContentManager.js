import React from 'react';
import { Card, Alert } from 'antd';

const ContentManager = () => {
  return (
    <div>
      <Alert
        message="Content Manager"
        description="Manage your aquascaping content, articles, and media"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card title="Content Manager" style={{ marginBottom: 16 }}>
        <p>Content management features will be available here.</p>
        <p>This will include:</p>
        <ul>
          <li>Content creation and editing</li>
          <li>Media management</li>
          <li>Publication scheduling</li>
          <li>Content performance analytics</li>
        </ul>
      </Card>
    </div>
  );
};

export default ContentManager;