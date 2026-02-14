import React from 'react';
import { Card } from 'antd';

const Visualization: React.FC = () => {
  return (
    <div>
      <h2>可视化</h2>
      <Card title="3D 分子结构查看器" style={{ height: '600px' }}>
        <div style={{ width: '100%', height: '100%', background: '#000', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          3D Molecular Viewer Placeholder (e.g. NGL Viewer / Mol* could be integrated here)
        </div>
      </Card>
    </div>
  );
};

export default Visualization;
