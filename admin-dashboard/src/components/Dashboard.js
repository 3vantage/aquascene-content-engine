import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Badge, message } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  RobotOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { checkAllServicesHealth, getAllServiceStats } from '../utils/apiClient';
import { HEALTH_CHECK_INTERVAL } from '../config/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [serviceStatuses, setServiceStatuses] = useState({});
  const [stats, setStats] = useState({
    subscribers: 0,
    content: 0,
    scrapeJobs: 0,
    aiJobs: 0
  });

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, HEALTH_CHECK_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Check all services health using the new API client
      const [serviceStatuses, serviceStats] = await Promise.all([
        checkAllServicesHealth(),
        getAllServiceStats()
      ]);

      setServiceStatuses(serviceStatuses);
      setStats(serviceStats);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      message.error('Failed to load dashboard data. Please check your connection.');
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    message.info('Refreshing dashboard data...');
    await fetchDashboardData();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'online':
        return <Badge status="success" text="Online" />;
      case 'offline':
        return <Badge status="error" text="Offline" />;
      default:
        return <Badge status="default" text="Unknown" />;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Alert
        message="AquaScene Content Engine Dashboard"
        description="Monitor and manage your aquascaping content automation system"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Subscribers"
              value={stats.subscribers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Content Items"
              value={stats.content}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Scraping Jobs"
              value={stats.scrapeJobs}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="AI Processing Jobs"
              value={stats.aiJobs}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title="Service Status" 
            extra={
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <ReloadOutlined 
                  onClick={handleRefresh}
                  style={{ 
                    cursor: 'pointer', 
                    color: '#1890ff',
                    fontSize: '16px'
                  }}
                  spin={loading}
                  title="Refresh data"
                />
                <span style={{ fontSize: '12px', color: '#666' }}>
                  Last updated: {new Date().toLocaleTimeString()}
                </span>
              </div>
            }
          >
            <Row gutter={[16, 16]}>
              {Object.entries(serviceStatuses).map(([serviceName, serviceData]) => (
                <Col span={8} key={serviceName}>
                  <Card size="small">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{serviceName}</div>
                        {getStatusBadge(serviceData.status)}
                      </div>
                      <div>
                        {serviceData.status === 'online' ? (
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '24px' }} />
                        ) : (
                          <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: '24px' }} />
                        )}
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;