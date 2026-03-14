import React from 'react';
import { Layout, Typography } from 'antd';
import RecommendationPanel from './components/RecommendationPanel';

const { Header, Content } = Layout;
const { Title } = Typography;

const App: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px' }}>
        <Title level={3} style={{ color: '#fff', lineHeight: '64px', margin: 0 }}>
          AI自媒体自动选题系统
        </Title>
      </Header>
      <Content style={{ padding: 24 }}>
        <RecommendationPanel />
      </Content>
    </Layout>
  );
};

export default App;
