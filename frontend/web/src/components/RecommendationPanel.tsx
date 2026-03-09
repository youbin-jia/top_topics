/**
 * 推荐面板组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Tabs, Spin, Empty, message } from 'antd';
import { useQuery } from 'react-query';
import { recommendationApi, feedbackApi } from '../services/api';
import TopicList from './TopicList';
import type { Topic } from '../types';

const RecommendationPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('personalized');

  // 获取个性化推荐
  const {
    data: personalizedData,
    isLoading: personalizedLoading,
    refetch: refetchPersonalized,
  } = useQuery(
    'personalized-recommendations',
    () => recommendationApi.getPersonalized(20),
    { enabled: activeTab === 'personalized' }
  );

  // 获取热门推荐
  const {
    data: hotData,
    isLoading: hotLoading,
    refetch: refetchHot,
  } = useQuery(
    'hot-recommendations',
    () => recommendationApi.getHot(20),
    { enabled: activeTab === 'hot' }
  );

  // 处理话题点击
  const handleTopicClick = async (topic: Topic) => {
    try {
      // 提交点击反馈
      await feedbackApi.submit({
        topic_id: topic.id,
        type: 'click',
      });

      message.success('已记录您的兴趣');

      // 刷新推荐
      if (activeTab === 'personalized') {
        refetchPersonalized();
      } else {
        refetchHot();
      }
    } catch (error) {
      console.error('提交反馈失败:', error);
    }
  };

  // 处理点赞
  const handleLike = async (topicId: number) => {
    try {
      await feedbackApi.submit({
        topic_id: topicId,
        type: 'like',
      });

      message.success('已点赞');

      // 刷新推荐
      if (activeTab === 'personalized') {
        refetchPersonalized();
      } else {
        refetchHot();
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const tabItems = [
    {
      key: 'personalized',
      label: '个性化推荐',
      children: (
        <Spin spinning={personalizedLoading}>
          {personalizedData?.data?.length > 0 ? (
            <TopicList
              topics={personalizedData.data}
              onTopicClick={handleTopicClick}
            />
          ) : (
            <Empty description="暂无推荐" />
          )}
        </Spin>
      ),
    },
    {
      key: 'hot',
      label: '热门话题',
      children: (
        <Spin spinning={hotLoading}>
          {hotData?.data?.length > 0 ? (
            <TopicList
              topics={hotData.data}
              onTopicClick={handleTopicClick}
            />
          ) : (
            <Empty description="暂无热门话题" />
          )}
        </Spin>
      ),
    },
  ];

  return (
    <Card>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </Card>
  );
};

export default RecommendationPanel;
