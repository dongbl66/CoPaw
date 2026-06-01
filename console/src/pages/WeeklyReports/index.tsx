import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Empty,
  Input,
  Select,
  Tag,
  Modal,
  Form,
  DatePicker,
  message,
  Popconfirm,
  Spin,
  Descriptions,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PageHeader } from "@/components/PageHeader";
import { consoleApi, type WeeklyReport } from "@/api/modules/console";
import dayjs from "dayjs";
import styles from "./index.module.less";

const { TextArea } = Input;
const { RangePicker } = DatePicker;

const STATUS_OPTIONS = [
  { label: "全部", value: "" },
  { label: "草稿", value: "draft" },
  { label: "已提交", value: "submitted" },
  { label: "已归档", value: "archived" },
];

const STATUS_TAG_COLORS: Record<string, string> = {
  draft: "default",
  submitted: "processing",
  archived: "success",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  submitted: "已提交",
  archived: "已归档",
};

export default function WeeklyReportsPage() {
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null);
  const [form] = Form.useForm();

  // Load reports
  const loadReports = async () => {
    setLoading(true);
    try {
      const res = await consoleApi.listWeeklyReports({
        status: statusFilter || undefined,
      });
      setReports(res.reports);
    } catch (err) {
      console.error("Failed to load reports:", err);
      message.error("加载周报失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [statusFilter]);

  // Handle view report
  const handleView = (report: WeeklyReport) => {
    setSelectedReport(report);
    setViewModalVisible(true);
  };

  // Handle edit report
  const handleEdit = (report: WeeklyReport) => {
    setSelectedReport(report);
    form.setFieldsValue({
      title: report.title,
      period: [dayjs(report.period_start), dayjs(report.period_end)],
      author: report.author,
      project_name: report.project_name,
      tags: report.tags?.join(", "),
      content: report.content,
      status: report.status,
    });
    setEditModalVisible(true);
  };

  // Handle create new report
  const handleCreate = () => {
    setSelectedReport(null);
    form.resetFields();
    // Set default date range (this week)
    const today = dayjs();
    const startOfWeek = today.startOf("week");
    const endOfWeek = today.endOf("week");
    form.setFieldsValue({
      period: [startOfWeek, endOfWeek],
      status: "draft",
    });
    setEditModalVisible(true);
  };

  // Handle save report
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const periodStart = values.period[0].format("YYYY-MM-DD");
      const periodEnd = values.period[1].format("YYYY-MM-DD");
      const tags = values.tags
        ? values.tags.split(",").map((t: string) => t.trim()).filter(Boolean)
        : [];

      if (selectedReport) {
        // Update existing report
        await consoleApi.updateWeeklyReport(selectedReport.id, {
          title: values.title,
          content: values.content,
          status: values.status,
          project_name: values.project_name,
          tags: tags.length > 0 ? tags : undefined,
        });
        message.success("周报更新成功");
      } else {
        // Create new report
        await consoleApi.createWeeklyReport({
          title: values.title,
          period_start: periodStart,
          period_end: periodEnd,
          author: values.author,
          content: values.content,
          project_name: values.project_name,
          tags: tags.length > 0 ? tags : undefined,
        });
        message.success("周报创建成功");
      }

      setEditModalVisible(false);
      loadReports();
    } catch (err) {
      console.error("Failed to save report:", err);
      message.error("保存周报失败");
    }
  };

  // Handle delete report
  const handleDelete = async (reportId: string) => {
    try {
      await consoleApi.deleteWeeklyReport(reportId);
      message.success("删除成功");
      loadReports();
    } catch (err) {
      console.error("Failed to delete report:", err);
      message.error("删除失败");
    }
  };

  return (
    <div className={styles.page}>
      <PageHeader
        items={[{ title: "项目周报" }]}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建周报
          </Button>
        }
      />

      <div className={styles.content}>
        <div className={styles.toolbar}>
          <Select
            style={{ width: 200 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
            placeholder="筛选状态"
          />
        </div>

        <Spin spinning={loading}>
          {reports.length > 0 ? (
            <div className={styles.reportList}>
              {reports.map((report) => (
                <Card
                  key={report.id}
                  className={styles.reportCard}
                  hoverable
                  actions={[
                    <EyeOutlined key="view" onClick={() => handleView(report)} />,
                    <EditOutlined key="edit" onClick={() => handleEdit(report)} />,
                    <Popconfirm
                      key="delete"
                      title="确定要删除这个周报吗？"
                      onConfirm={() => handleDelete(report.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <DeleteOutlined />
                    </Popconfirm>,
                  ]}
                >
                  <div className={styles.reportHeader}>
                    <div className={styles.reportTitle}>{report.title}</div>
                    <Tag color={STATUS_TAG_COLORS[report.status]}>
                      {STATUS_LABELS[report.status]}
                    </Tag>
                  </div>
                  <div className={styles.reportMeta}>
                    <span>
                      周期: {report.period_start} ~ {report.period_end}
                    </span>
                    <span>作者: {report.author}</span>
                    {report.project_name && <span>项目: {report.project_name}</span>}
                  </div>
                  {report.tags?.length > 0 && (
                    <div className={styles.reportTags}>
                      {report.tags.map((tag) => (
                        <Tag key={tag}>{tag}</Tag>
                      ))}
                    </div>
                  )}
                  <div className={styles.reportTime}>
                    更新于: {dayjs(report.updated_at * 1000).format("YYYY-MM-DD HH:mm")}
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Empty description="暂无周报" />
          )}
        </Spin>
      </div>

      {/* View Modal */}
      <Modal
        title={selectedReport?.title}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            onClick={() => {
              setViewModalVisible(false);
              if (selectedReport) {
                handleEdit(selectedReport);
              }
            }}
          >
            编辑
          </Button>,
        ]}
        width={800}
      >
        {selectedReport && (
          <div className={styles.viewModal}>
            <Descriptions column={2} bordered size="small" className={styles.meta}>
              <Descriptions.Item label="周期">
                {selectedReport.period_start} ~ {selectedReport.period_end}
              </Descriptions.Item>
              <Descriptions.Item label="作者">
                {selectedReport.author}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_TAG_COLORS[selectedReport.status]}>
                  {STATUS_LABELS[selectedReport.status]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="项目">
                {selectedReport.project_name || "-"}
              </Descriptions.Item>
            </Descriptions>
            {selectedReport.tags?.length > 0 && (
              <div className={styles.tags}>
                {selectedReport.tags.map((tag) => (
                  <Tag key={tag}>{tag}</Tag>
                ))}
              </div>
            )}
            <div className={styles.content}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {selectedReport.content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </Modal>

      {/* Edit/Create Modal */}
      <Modal
        title={selectedReport ? "编辑周报" : "新建周报"}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={handleSave}
        okText="保存"
        cancelText="取消"
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: "请输入标题" }]}
          >
            <Input placeholder="请输入周报标题" />
          </Form.Item>

          <Form.Item
            label="周期"
            name="period"
            rules={[{ required: true, message: "请选择周期" }]}
          >
            <RangePicker style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            label="作者"
            name="author"
            rules={[{ required: true, message: "请输入作者" }]}
          >
            <Input placeholder="请输入作者姓名" />
          </Form.Item>

          <Form.Item label="项目名称" name="project_name">
            <Input placeholder="请输入项目名称（可选）" />
          </Form.Item>

          <Form.Item label="标签" name="tags">
            <Input placeholder="请输入标签，用逗号分隔" />
          </Form.Item>

          {selectedReport && (
            <Form.Item label="状态" name="status">
              <Select options={STATUS_OPTIONS.slice(1)} />
            </Form.Item>
          )}

          <Form.Item
            label="内容"
            name="content"
            rules={[{ required: true, message: "请输入内容" }]}
          >
            <TextArea
              rows={15}
              placeholder="支持 Markdown 格式"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
