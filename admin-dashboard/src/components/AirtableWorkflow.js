import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Button,
  Steps,
  Alert,
  Progress,
  List,
  Tag,
  Divider,
  Space,
  Modal,
  Typography,
  Table,
  Spin,
  message
} from 'antd';
import {
  ApiOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
  EyeOutlined,
  TableOutlined,
  FileTextOutlined,
  SettingOutlined
} from '@ant-design/icons';
import axios from 'axios';
import io from 'socket.io-client';

const { Step } = Steps;
const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

const AirtableWorkflow = () => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [availableTables, setAvailableTables] = useState([]);
  const [workflowId, setWorkflowId] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize WebSocket connection for real-time updates
    socketRef.current = io(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}`, {
      path: '/api/v1/workflows/ws'
    });

    socketRef.current.on('connect', () => {
      console.log('Connected to workflow updates');
    });

    socketRef.current.on('workflow_update', (data) => {
      console.log('Workflow update:', data);
      if (data.workflow_id === workflowId) {
        setWorkflowStatus({
          ...workflowStatus,
          status: data.data.status,
          progress: data.data.progress || 0,
          logs: data.data.logs || [],
          results: data.data.results || null,
          error: data.data.error || null
        });
        setLogs(data.data.logs || []);
        setResults(data.data.results);
      }
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [workflowId, workflowStatus]);

  const testConnection = async (values) => {
    setLoading(true);
    setConnectionStatus(null);
    
    try {
      const response = await axios.post('/api/v1/workflows/airtable/test-connection', {
        airtable_api_key: values.apiKey,
        airtable_base_id: values.baseId,
        workflow_type: 'connection_test'
      });

      if (response.data.success) {
        setConnectionStatus({
          success: true,
          message: response.data.message,
          tables: response.data.tables
        });
        setAvailableTables(response.data.tables);
        setCurrentStep(1);
        message.success('Connection successful!');
      } else {
        setConnectionStatus({
          success: false,
          message: response.data.message
        });
        message.error('Connection failed');
      }
    } catch (error) {
      setConnectionStatus({
        success: false,
        message: error.response?.data?.detail || error.message
      });
      message.error('Connection test failed');
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    const values = form.getFieldsValue();
    setLoading(true);
    
    try {
      const response = await axios.post('/api/v1/workflows/airtable/schema-analysis', {
        airtable_api_key: values.apiKey,
        airtable_base_id: values.baseId,
        workflow_type: 'schema_analysis'
      });

      setWorkflowId(response.data.workflow_id);
      setWorkflowStatus({
        workflow_id: response.data.workflow_id,
        status: 'running',
        progress: 0,
        logs: ['Analysis started...'],
        results: null,
        error: null
      });
      setCurrentStep(2);
      message.success('Analysis started!');
    } catch (error) {
      message.error('Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  const runCompleteWorkflowTest = async () => {
    const values = form.getFieldsValue();
    setLoading(true);
    
    try {
      const response = await axios.post('/api/v1/workflows/test-workflow', {
        airtable_api_key: values.apiKey,
        airtable_base_id: values.baseId,
        workflow_type: 'complete_test'
      });

      setWorkflowId(response.data.workflow_id);
      setWorkflowStatus({
        workflow_id: response.data.workflow_id,
        status: 'running',
        progress: 0,
        logs: ['Complete workflow test started...'],
        results: null,
        error: null
      });
      setCurrentStep(2);
      message.success('Complete workflow test started! This will test all components end-to-end.');
    } catch (error) {
      message.error('Failed to start complete workflow test');
    } finally {
      setLoading(false);
    }
  };

  const createMetadataTable = async () => {
    if (!workflowId) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`/api/v1/workflows/airtable/create-metadata-table?workflow_id=${workflowId}`);
      
      message.success('Metadata table creation started!');
      setCurrentStep(3);
    } catch (error) {
      message.error('Failed to start metadata table creation');
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = async (fileType) => {
    if (!workflowId) return;
    
    try {
      const response = await axios.get(
        `/api/v1/workflows/download/${workflowId}/${fileType}`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${fileType}_${workflowId}.${fileType.includes('json') ? 'json' : 'txt'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success(`${fileType} file downloaded!`);
    } catch (error) {
      message.error('Failed to download file');
    }
  };

  const getStepStatus = (step) => {
    if (step < currentStep) return 'finish';
    if (step === currentStep) {
      if (workflowStatus?.status === 'failed') return 'error';
      if (workflowStatus?.status === 'running') return 'process';
      if (workflowStatus?.status === 'completed') return 'finish';
      return 'process';
    }
    return 'wait';
  };

  const renderConnectionStep = () => (
    <Card title="Step 1: Connect to Airtable">
      <Form
        form={form}
        layout="vertical"
        onFinish={testConnection}
        initialValues={{
          apiKey: '',
          baseId: ''
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="Airtable API Key"
              name="apiKey"
              rules={[{ required: true, message: 'Please input your Airtable API key!' }]}
            >
              <Input.Password
                placeholder="patXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                prefix={<ApiOutlined />}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="Airtable Base ID"
              name="baseId"
              rules={[{ required: true, message: 'Please input your Base ID!' }]}
            >
              <Input
                placeholder="appXXXXXXXXXXXXXX"
                prefix={<TableOutlined />}
              />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading}
            icon={<ApiOutlined />}
          >
            Test Connection
          </Button>
        </Form.Item>
      </Form>

      {connectionStatus && (
        <div style={{ marginTop: 16 }}>
          <Alert
            type={connectionStatus.success ? 'success' : 'error'}
            message={connectionStatus.success ? 'Connection Successful' : 'Connection Failed'}
            description={connectionStatus.message}
            showIcon
          />
          
          {connectionStatus.success && availableTables.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Title level={5}>Available Tables ({availableTables.length})</Title>
              <div>
                {availableTables.map((table, index) => (
                  <Tag key={index} color="blue" style={{ margin: 4 }}>
                    {table}
                  </Tag>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );

  const renderAnalysisStep = () => (
    <Card title="Step 2: Schema Analysis">
      <Paragraph>
        This step will analyze your Airtable base structure, including:
      </Paragraph>
      <ul>
        <li>All tables and their relationships</li>
        <li>Field types and validation rules</li>
        <li>Data patterns and quality assessment</li>
        <li>Business logic and computed fields</li>
        <li>Recommendations for improvement</li>
      </ul>

      <Alert
        message="End-to-End Workflow Test Available"
        description="Use the 'Run Complete E2E Test' button to execute the full workflow in one go: connection test → schema analysis → metadata table generation. This is perfect for testing the complete system functionality."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Space wrap>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={startAnalysis}
          loading={loading}
          disabled={currentStep < 1}
        >
          Start Analysis
        </Button>
        <Button
          type="default"
          icon={<CheckCircleOutlined />}
          onClick={runCompleteWorkflowTest}
          loading={loading}
          disabled={currentStep < 1}
          style={{ backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' }}
        >
          Run Complete E2E Test
        </Button>
        <Button onClick={() => setCurrentStep(0)}>
          Back to Connection
        </Button>
      </Space>

      {workflowStatus && workflowStatus.status === 'running' && (
        <div style={{ marginTop: 16 }}>
          <Progress 
            percent={workflowStatus.progress} 
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>
      )}

      {workflowStatus && workflowStatus.status === 'completed' && results && (
        <Alert
          type="success"
          message="Analysis Complete!"
          description="Schema analysis completed successfully. You can now create the metadata table or download the results."
          showIcon
          style={{ marginTop: 16 }}
        />
      )}

      {workflowStatus && workflowStatus.status === 'failed' && (
        <Alert
          type="error"
          message="Analysis Failed"
          description={workflowStatus.error}
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );

  const renderResultsStep = () => (
    <Card title="Step 3: Results & Metadata Table">
      {workflowStatus && workflowStatus.status === 'completed' && (
        <div>
          <Paragraph>
            Analysis completed successfully! You can now download the results or create a metadata table.
          </Paragraph>
          
          <Space wrap style={{ marginBottom: 16 }}>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => downloadFile('json')}
            >
              Download JSON Results
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => downloadFile('summary')}
            >
              Download Summary
            </Button>
            <Button
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedResult('analysis');
                setShowResultsModal(true);
              }}
            >
              View Results
            </Button>
          </Space>
          
          <Divider />
          
          <Title level={4}>Create Metadata Table</Title>
          <Paragraph>
            Generate a comprehensive metadata table in your Airtable base to document all tables and fields.
          </Paragraph>
          
          <Button
            type="primary"
            icon={<TableOutlined />}
            onClick={createMetadataTable}
            loading={loading}
          >
            Create Metadata Table
          </Button>
        </div>
      )}
    </Card>
  );

  const renderLogsStep = () => (
    <Card title="Real-time Logs" style={{ marginTop: 16 }}>
      <div style={{ maxHeight: 300, overflowY: 'auto', backgroundColor: '#f5f5f5', padding: 12, borderRadius: 4 }}>
        {logs.length > 0 ? (
          <List
            size="small"
            dataSource={logs}
            renderItem={(item, index) => (
              <List.Item style={{ padding: '4px 0', borderBottom: 'none' }}>
                <Text code style={{ fontSize: 12 }}>
                  {new Date().toLocaleTimeString()} - {item}
                </Text>
              </List.Item>
            )}
          />
        ) : (
          <Text type="secondary">No logs available</Text>
        )}
      </div>
    </Card>
  );

  return (
    <div>
      <Card>
        <Title level={2}>
          <SettingOutlined /> Airtable Schema Analysis Workflow
        </Title>
        <Paragraph>
          Analyze your Airtable base structure and create comprehensive metadata documentation.
        </Paragraph>
        
        <Steps current={currentStep} style={{ marginBottom: 24 }}>
          <Step 
            title="Connection" 
            description="Connect to Airtable"
            status={getStepStatus(0)}
            icon={<ApiOutlined />}
          />
          <Step 
            title="Analysis" 
            description="Analyze schema"
            status={getStepStatus(1)}
            icon={<PlayCircleOutlined />}
          />
          <Step 
            title="Results" 
            description="Review & export"
            status={getStepStatus(2)}
            icon={<CheckCircleOutlined />}
          />
        </Steps>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={16}>
          {currentStep === 0 && renderConnectionStep()}
          {currentStep === 1 && renderAnalysisStep()}
          {currentStep >= 2 && renderResultsStep()}
        </Col>
        <Col span={8}>
          {(workflowStatus || logs.length > 0) && renderLogsStep()}
        </Col>
      </Row>

      <Modal
        title="Analysis Results"
        visible={showResultsModal}
        onCancel={() => setShowResultsModal(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setShowResultsModal(false)}>
            Close
          </Button>
        ]}
      >
        {results && (
          <div>
            <Paragraph>
              <strong>Analysis completed for Base ID:</strong> {form.getFieldValue('baseId')}
            </Paragraph>
            <Paragraph>
              <strong>Tables analyzed:</strong> {availableTables.length}
            </Paragraph>
            <Paragraph>
              <strong>Results files:</strong>
            </Paragraph>
            <ul>
              <li>JSON Results: {results.json_file}</li>
              <li>Summary Report: {results.summary_file}</li>
            </ul>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AirtableWorkflow;