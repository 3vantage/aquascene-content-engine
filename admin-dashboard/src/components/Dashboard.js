import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Badge } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  RobotOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

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
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Check service health
      const services = [
        { name: 'Content Manager', url: 'http://localhost:8000/health' },
        { name: 'AI Processor', url: 'http://localhost:8001/health' },
        { name: 'Web Scraper', url: 'http://localhost:8002/health' },
        { name: 'Distributor', url: 'http://localhost:8003/health' },
        { name: 'Subscriber Manager', url: 'http://localhost:8004/health' }
      ];

      const statuses = {};
      await Promise.all(
        services.map(async (service) => {
          try {
            const response = await axios.get(service.url, { timeout: 5000 });
            statuses[service.name] = {
              status: response.data.status === 'healthy' ? 'online' : 'offline',
              lastCheck: new Date().toISOString()
            };
          } catch (error) {
            statuses[service.name] = {
              status: 'offline',
              lastCheck: new Date().toISOString(),
              error: error.message
            };
          }
        })
      );

      setServiceStatuses(statuses);

      // Fetch statistics (with fallback for missing services)
      try {
        const subscriberStats = await axios.get('http://localhost:8004/api/v1/subscribers/stats');
        setStats(prev => ({ ...prev, subscribers: subscriberStats.data.total_subscribers || 0 }));
      } catch (error) {
        console.warn('Failed to fetch subscriber stats:', error.message);
      }

      try {
        const scraperStats = await axios.get('http://localhost:8002/api/v1/stats');
        setStats(prev => ({ ...prev, scrapeJobs: scraperStats.data.stats?.total_jobs || 0 }));
      } catch (error) {
        console.warn('Failed to fetch scraper stats:', error.message);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
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
          <Card title="Service Status" extra={
            <span style={{ fontSize: '12px', color: '#666' }}>
              Last updated: {new Date().toLocaleTimeString()}
            </span>
          }>
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