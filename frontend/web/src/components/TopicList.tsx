/**
 * 话题列表组件
 */
import React from 'react';
import { Card, List, Tag, Progress, Space, Button } from 'antd';
import { FireOutlined, RiseOutlined, EyeOutlined } from '@ant-design/icons';
import type { Topic } from '../types';

interface TopicListProps {
  topics: Topic[];
  loading?: boolean;
  onTopicClick?: (topic: Topic) => void;
}

const TopicList: React.FC<TopicListProps> = ({
  topics,
  loading = false,
  onTopicClick,
}) => {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'rising':
        return <RiseOutlined style={{ color: '#52c41a' }} />;
      case 'falling':
        return <RiseOutlined style={{ color: '#ff4d4f', transform: 'rotate(180deg)' }} />;
      default:
        return null;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'rising':
        return 'success';
      case 'falling':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card title="热门话题" extra={<a href="/topics">查看全部</a>}>
      <List
        loading={loading}
        dataSource={topics}
        renderItem={(topic) => (
          <List.Item
            key={topic.id}
            actions={[
              <Button
                type="link"
                icon={<EyeOutlined />}
                onClick={() => onTopicClick?.(topic)}
              >
                查看详情
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{topic.name}</span>
                  {getTrendIcon(topic.trend)}
                  <Tag color={getTrendColor(topic.trend)}>
                    {topic.trend === 'rising' ? '上升' : topic.trend === 'falling' ? '下降' : '稳定'}
                  </Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    {topic.keywords?.slice(0, 5).map((keyword) => (
                      <Tag key={keyword}>{keyword}</Tag>
                    ))}
                  </div>
                  <Space size="large">
                    <span>
                      <FireOutlined style={{ color: '#ff4d4f' }} />
                      热度: {topic.heat_score.toFixed(2)}
                    </span>
                    <span>文章数: {topic.article_count}</span>
                  </Space>
                </Space>
              }
            />
            <Progress
              percent={topic.heat_score * 100}
              showInfo={false}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              style={{ width: 120 }}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default TopicList;
