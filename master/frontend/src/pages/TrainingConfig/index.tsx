import React from 'react';
import { Form, Select, InputNumber, Switch, Button, Card } from 'antd';

const TrainingConfig: React.FC = () => {
  const onFinish = (values: any) => {
    console.log('Success:', values);
  };

  return (
    <div>
      <h2>训练配置</h2>
      <Card title="模型参数配置">
        <Form
          name="basic"
          labelCol={{ span: 4 }}
          wrapperCol={{ span: 16 }}
          initialValues={{ remember: true }}
          onFinish={onFinish}
        >
          <Form.Item label="模型架构" name="model" rules={[{ required: true, message: '请选择模型架构!' }]}>
            <Select>
              <Select.Option value="resnet50">ResNet-50</Select.Option>
              <Select.Option value="transformer">Transformer</Select.Option>
              <Select.Option value="gnn">GNN</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="批次大小 (Batch Size)" name="batchSize" initialValue={32}>
            <InputNumber min={1} max={1024} />
          </Form.Item>

          <Form.Item label="学习率 (Learning Rate)" name="lr" initialValue={0.001}>
            <InputNumber step={0.0001} />
          </Form.Item>

          <Form.Item label="Epochs" name="epochs" initialValue={100}>
            <InputNumber min={1} />
          </Form.Item>

          <Form.Item label="使用 GPU" name="useGpu" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
          
          <Form.Item label="混合精度训练 (AMP)" name="amp" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>

          <Form.Item wrapperCol={{ offset: 4, span: 16 }}>
            <Button type="primary" htmlType="submit">
              开始训练
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default TrainingConfig;
