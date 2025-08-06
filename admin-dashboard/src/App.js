import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  UserOutlined,
  SettingOutlined,
  RobotOutlined,
  GlobalOutlined,
  MailOutlined
} from '@ant-design/icons';

import Dashboard from './components/Dashboard';
import ContentManager from './components/ContentManager';
import SubscriberManager from './components/SubscriberManager';
import AIProcessor from './components/AIProcessor';
import WebScraper from './components/WebScraper';
import Distributor from './components/Distributor';
import Settings from './components/Settings';

const { Header, Content, Sider } = Layout;

const menuItems = [
  {
    key: '1',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
    path: '/'
  },
  {
    key: '2',
    icon: <FileTextOutlined />,
    label: 'Content Manager',
    path: '/content'
  },
  {
    key: '3',
    icon: <RobotOutlined />,
    label: 'AI Processor',
    path: '/ai'
  },
  {
    key: '4',
    icon: <GlobalOutlined />,
    label: 'Web Scraper',
    path: '/scraper'
  },
  {
    key: '5',
    icon: <MailOutlined />,
    label: 'Distributor',
    path: '/distributor'
  },
  {
    key: '6',
    icon: <UserOutlined />,
    label: 'Subscribers',
    path: '/subscribers'
  },
  {
    key: '7',
    icon: <SettingOutlined />,
    label: 'Settings',
    path: '/settings'
  }
];

function App() {
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider theme="dark" width={250}>
          <div style={{ 
            padding: '16px', 
            color: 'white', 
            fontSize: '18px',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            AquaScene Admin
          </div>
          <Menu
            theme="dark"
            mode="inline"
            defaultSelectedKeys={['1']}
            items={menuItems.map(item => ({
              key: item.key,
              icon: item.icon,
              label: (
                <a href={item.path} style={{ textDecoration: 'none' }}>
                  {item.label}
                </a>
              )
            }))}
          />
        </Sider>
        <Layout>
          <Header style={{ 
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <h1 style={{ margin: 0, color: '#1890ff' }}>
              AquaScene Content Engine
            </h1>
            <div style={{ color: '#666' }}>
              {new Date().toLocaleDateString()}
            </div>
          </Header>
          <Content style={{ margin: '24px 16px 0' }}>
            <div style={{ 
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: '8px'
            }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/content" element={<ContentManager />} />
                <Route path="/ai" element={<AIProcessor />} />
                <Route path="/scraper" element={<WebScraper />} />
                <Route path="/distributor" element={<Distributor />} />
                <Route path="/subscribers" element={<SubscriberManager />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;