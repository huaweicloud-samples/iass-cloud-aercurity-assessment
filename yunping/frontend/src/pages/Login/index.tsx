import { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../../api';
import { useAppStore } from '../../store';
import './index.css';

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const { setToken, setUserInfo } = useAppStore();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const res = (await login(values)) as any;
      setToken(res.access_token);
      setUserInfo(res.user);
      message.success('登录成功');
    } catch (e: any) {
      message.error(e.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      {/* 左侧视觉区域 */}
      <div className="login-visual">
        <div className="login-visual-bg" />
        <div className="login-visual-content">
          {/* 装饰性科技圆环 */}
          <div className="tech-ring ring-outer" />
          <div className="tech-ring ring-middle" />
          <div className="tech-ring ring-inner" />
          {/* 中心核心图标 */}
          <div className="tech-core">
            <svg viewBox="0 0 100 100" className="core-icon">
              <defs>
                <linearGradient id="coreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00d4ff" />
                  <stop offset="100%" stopColor="#0070f3" />
                </linearGradient>
              </defs>
              <rect x="25" y="25" width="50" height="50" rx="8" fill="url(#coreGrad)" opacity="0.9" />
              <rect x="35" y="35" width="30" height="30" rx="4" fill="#0a1628" opacity="0.6" />
              <circle cx="50" cy="50" r="6" fill="#00d4ff" />
              <line x1="50" y1="25" x2="50" y2="10" stroke="#00d4ff" strokeWidth="2" opacity="0.6" />
              <line x1="50" y1="75" x2="50" y2="90" stroke="#00d4ff" strokeWidth="2" opacity="0.6" />
              <line x1="25" y1="50" x2="10" y2="50" stroke="#00d4ff" strokeWidth="2" opacity="0.6" />
              <line x1="75" y1="50" x2="90" y2="50" stroke="#00d4ff" strokeWidth="2" opacity="0.6" />
            </svg>
          </div>
          {/* 光束效果 */}
          <div className="light-beam beam-1" />
          <div className="light-beam beam-2" />
          <div className="light-beam beam-3" />
          {/* 粒子点 */}
          <div className="particle p1" />
          <div className="particle p2" />
          <div className="particle p3" />
          <div className="particle p4" />
          <div className="particle p5" />
          <div className="particle p6" />
          <div className="particle p7" />
          <div className="particle p8" />
        </div>
        {/* 左下角文字 */}
        <div className="login-visual-text">
          <div className="visual-text-title">智能安全评估</div>
          <div className="visual-text-sub">基于 GB/T 31168-2023 标准的自动化预审系统</div>
        </div>
      </div>

      {/* 右侧登录表单区域 */}
      <div className="login-form-area">
        <div className="login-form-wrapper">
          <div className="login-form-header">
            <h1 className="login-title">云计算服务安全评估</h1>
            <h2 className="login-subtitle">智能预审Agent</h2>
          </div>
          <Form onFinish={handleLogin} layout="vertical" className="login-form">
            <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input
                prefix={<UserOutlined className="input-icon" />}
                placeholder="用户名"
                size="large"
                className="login-input"
              />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password
                prefix={<LockOutlined className="input-icon" />}
                placeholder="密码"
                size="large"
                className="login-input"
              />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                className="login-btn"
              >
                登录
              </Button>
            </Form.Item>
          </Form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
