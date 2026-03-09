/**
 * 类型定义
 */

export interface Topic {
  id: number;
  name: string;
  description?: string;
  keywords: string[];
  heat_score: number;
  trend: 'rising' | 'falling' | 'stable';
  article_count: number;
  view_count?: number;
  recommendation_score?: number;
}

export interface Recommendation {
  id: number;
  topic: Topic;
  score: number;
  rank: number;
  recommendation_type: string;
  recommended_at: string;
}

export interface UserFeedback {
  id: number;
  topic_id: number;
  feedback_type: 'click' | 'like' | 'share' | 'collect' | 'skip';
  created_at: string;
}

export interface GeneratedTitle {
  title: string;
  quality_score: number;
}

export interface GeneratedOutline {
  title: string;
  style: string;
  introduction: {
    content: string;
    key_points: string[];
    word_count: number;
  };
  sections: Array<{
    number: number;
    title: string;
    key_points: string[];
    estimated_length: number;
    writing_tips?: string[];
  }>;
  conclusion: {
    content: string;
    summary_points: string[];
    call_to_action: string;
    word_count: number;
  };
  quality_score?: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  bio?: string;
  preferred_categories: string[];
  top_interests: string[];
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
}
