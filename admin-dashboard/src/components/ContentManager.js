import React, { useState, useEffect } from 'react';
import { Card, Alert, Table, Button, Tag, Space, message, Spin } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { makeApiCall } from '../utils/apiClient';

const ContentManager = () => {
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState([]);

  useEffect(() => {
    fetchContent();
  }, []);

  const fetchContent = async () => {
    setLoading(true);
    try {
      const response = await makeApiCall('contentManager', 'content');
      setContent(response.data || []);
    } catch (error) {
      console.error('Failed to fetch content:', error);
      message.error('Failed to load content. Service may be unavailable.');
      // Mock data for demonstration
      setContent([
        {
          id: '1',
          title: 'Aquascaping Basics: Getting Started',
          type: 'Article',
          status: 'published',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z'
        },
        {
          id: '2',
          title: 'Plant Selection for Beginners',
          type: 'Guide',
          status: 'draft',
          created_at: '2025-01-14T15:22:00Z',
          updated_at: '2025-01-16T09:15:00Z'
        },
        {
          id: '3',
          title: 'CO2 System Setup',
          type: 'Tutorial',
          status: 'published',
          created_at: '2025-01-13T08:45:00Z',
          updated_at: '2025-01-13T08:45:00Z'
        }
      ]);
    }
    setLoading(false);
  };

  const columns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text) => <a>{text}</a>,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={
          type === 'Article' ? 'blue' : 
          type === 'Guide' ? 'green' : 
          type === 'Tutorial' ? 'orange' : 'default'
        }>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'published' ? 'green' : 'orange'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button icon={<EyeOutlined />} size="small" />
          <Button icon={<EditOutlined />} size="small" />
          <Button icon={<DeleteOutlined />} size="small" danger />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Alert
        message="Content Manager"
        description="Manage your aquascaping content, articles, and media"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card 
        title="Content Library" 
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
            Create Content
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={content}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} items`,
            }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default ContentManager;