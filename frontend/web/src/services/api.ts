/**
 * API客户端
 */
import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;

    // 如果是401错误且还没重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // 尝试刷新token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post('/api/v1/auth/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // 重试原请求
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // 刷新失败，清除token并跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

/**
 * 话题API
 */
export const topicApi = {
  // 获取话题列表
  getTopics: (params?: {
    limit?: number;
    category?: string;
    min_score?: number;
  }) => apiClient.get('/topics/', { params }),

  // 获取热门话题
  getHotTopics: (limit?: number) =>
    apiClient.get('/topics/hot/', { params: { limit } }),

  // 获取趋势话题
  getTrendingTopics: (limit?: number) =>
    apiClient.get('/topics/trending/', { params: { limit } }),
};

/**
 * 推荐API
 */
export const recommendationApi = {
  // 获取个性化推荐
  getPersonalized: (limit?: number) =>
    apiClient.get('/recommendations/personalized/', { params: { limit } }),

  // 获取热门推荐
  getHot: (limit?: number) =>
    apiClient.get('/recommendations/hot/', { params: { limit } }),
};

/**
 * 反馈API
 */
export const feedbackApi = {
  // 提交反馈
  submit: (data: {
    topic_id: number;
    type: 'click' | 'like' | 'share' | 'collect' | 'skip';
    dwell_time?: number;
    scroll_depth?: number;
  }) => apiClient.post('/feedback/', data),
};

/**
 * 内容生成API
 */
export const contentApi = {
  // 生成标题
  generateTitle: (data: {
    topic_id?: number;
    keywords?: string[];
    category?: string;
    n_titles?: number;
  }) => apiClient.post('/content/generate_title/', data),

  // 生成大纲
  generateOutline: (data: {
    topic_id?: number;
    topic_name?: string;
    keywords?: string[];
    style?: string;
    n_sections?: number;
  }) => apiClient.post('/content/generate_outline/', data),
};

/**
 * 用户API
 */
export const userApi = {
  // 获取用户信息
  getProfile: () => apiClient.get('/users/me/'),

  // 获取用户画像
  getUserProfile: () => apiClient.get('/users/profile/'),

  // 更新用户偏好
  updatePreferences: (data: {
    categories?: string[];
    keywords?: Record<string, number>;
  }) => apiClient.put('/users/update_preferences/', data),
};
