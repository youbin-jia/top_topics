/**
 * 话题列表组件：展示话题概要，详情弹窗展示参考原文链接
 */
import React, { useState } from 'react';
import { Card, List, Tag, Progress, Space, Button, Modal, Spin, Typography } from 'antd';
import { FireOutlined, RiseOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import { topicApi } from '../services/api';
import type { Topic, TopicDetail } from '../types';

const { Paragraph } = Typography;

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
  const [detailVisible, setDetailVisible] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detail, setDetail] = useState<TopicDetail | null>(null);
  const [detailError, setDetailError] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);

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

  const openDetail = async (topic: Topic) => {
    onTopicClick?.(topic);
    setSelectedTopic(topic);
    setDetailVisible(true);
    setDetail(null);
    setDetailError(false);
    setDetailLoading(true);
    try {
      const res: any = await topicApi.getDetail(topic.id);
      const payload = res?.data != null ? res.data : res;
      if (payload && typeof payload === 'object') setDetail(payload as TopicDetail);
      else setDetailError(true);
    } catch (e) {
      console.error(e);
      setDetailError(true);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <>
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
                  onClick={() => openDetail(topic)}
                >
                  查看详情
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Space wrap>
                    <span>{topic.name}</span>
                    {getTrendIcon(topic.trend)}
                    <Tag color={getTrendColor(topic.trend)}>
                      {topic.trend === 'rising' ? '上升' : topic.trend === 'falling' ? '下降' : '稳定'}
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {topic.description ? (
                      <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                        {topic.description}
                      </Paragraph>
                    ) : null}
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

      <Modal
        title={detail?.title_summary ?? detail?.name ?? selectedTopic?.name ?? '话题详情'}
        open={detailVisible}
        onCancel={() => { setDetailVisible(false); setDetail(null); setSelectedTopic(null); setDetailError(false); }}
        footer={null}
        width={560}
      >
        <Spin spinning={detailLoading}>
          {(detail || selectedTopic) && (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {detailError && (
                <div style={{ color: '#ff4d4f' }}>详情加载失败，下方为列表中的概要与参考信息。</div>
              )}
              <div>
                <div style={{ color: '#666', marginBottom: 4 }}>短视频选题概要</div>
                <Paragraph>
                  {(detail?.description || selectedTopic?.description) || (detail?.name ?? selectedTopic?.name) || '暂无概要'}
                </Paragraph>
              </div>
              <div>
                <div style={{ color: '#666', marginBottom: 8 }}>
                  <LinkOutlined /> 参考原文链接
                </div>
                {detail?.reference_links && detail.reference_links.length > 0 ? (
                  <List
                    size="small"
                    dataSource={detail.reference_links}
                    renderItem={(item) => (
                      <List.Item>
                        <Space direction="vertical" size={4}>
                          <a href={item.url} target="_blank" rel="noopener noreferrer">
                            {item.title || item.url}
                          </a>
                          <a href={item.open_url || topicApi.getOpenLink(item.url)} target="_blank" rel="noopener noreferrer" style={{ color: '#999', fontSize: 12 }}>
                            打不开？使用兜底打开
                          </a>
                        </Space>
                      </List.Item>
                    )}
                  />
                ) : (
                  <span style={{ color: '#999' }}>{detailLoading ? '加载中…' : '暂无参考链接'}</span>
                )}
              </div>
            </Space>
          )}
        </Spin>
      </Modal>
    </>
  );
};

export default TopicList;
