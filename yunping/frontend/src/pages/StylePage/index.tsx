import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const StylePage: React.FC = () => {
  return (
    <div className="p-6">
      <Card>
        <Title level={3}>样式配置</Title>
        <Paragraph>
          这里是样式配置页面，您可以在这里管理系统的样式设置。
        </Paragraph>
      </Card>
    </div>
  );
};

export default StylePage;
