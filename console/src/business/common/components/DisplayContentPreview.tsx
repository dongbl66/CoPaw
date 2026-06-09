import { Button, Empty, Tabs, Typography } from "antd";
import { openExternalLink } from "@/utils/openExternalLink";

const { Text } = Typography;

export interface DisplayContentItem {
  type?: string;
  kind?: string;
  file_name?: string;
  fileName?: string;
  file_url?: string;
  fileUrl?: string;
  preview_url?: string;
  previewUrl?: string;
  download_url?: string;
  downloadUrl?: string;
  file_path?: string;
  filePath?: string;
  asset_id?: string;
  assetId?: string;
}

export interface DisplayContentPreviewProps {
  items?: DisplayContentItem[];
  emptyText?: string;
}

function itemType(item: DisplayContentItem): string {
  return (item.type || item.kind || "file").toLowerCase();
}

function itemName(item: DisplayContentItem, index: number): string {
  return (
    item.file_name ||
    item.fileName ||
    item.file_path ||
    item.filePath ||
    item.asset_id ||
    item.assetId ||
    `附件 ${index + 1}`
  );
}

function itemUrl(item: DisplayContentItem): string {
  return (
    item.file_url ||
    item.fileUrl ||
    item.preview_url ||
    item.previewUrl ||
    item.download_url ||
    item.downloadUrl ||
    ""
  );
}

function renderPreview(item: DisplayContentItem, index: number) {
  const type = itemType(item);
  const name = itemName(item, index);
  const url = itemUrl(item);

  if (!url) {
    return (
      <Empty
        description="该资源尚未注册可预览地址"
        style={{ padding: "48px 0" }}
      />
    );
  }

  if (type === "html") {
    return (
      <iframe
        title={`preview-html-${name}`}
        src={url}
        style={{
          width: "100%",
          minHeight: 640,
          border: "1px solid #e6edf8",
          borderRadius: 12,
          background: "#fff",
        }}
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
      />
    );
  }

  if (type === "pdf") {
    return (
      <iframe
        title={`preview-pdf-${name}`}
        src={url}
        style={{
          width: "100%",
          minHeight: 640,
          border: "1px solid #e6edf8",
          borderRadius: 12,
          background: "#fff",
        }}
      />
    );
  }

  if (type === "image") {
    return (
      <img
        alt={name}
        src={url}
        style={{
          display: "block",
          maxWidth: "100%",
          maxHeight: 640,
          margin: "0 auto",
          borderRadius: 12,
        }}
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Text>{name}</Text>
      <Button
        type="link"
        onClick={() => {
          openExternalLink(url);
        }}
      >
        打开
      </Button>
    </div>
  );
}

export function DisplayContentPreview({
  items = [],
  emptyText = "暂无可预览文件",
}: DisplayContentPreviewProps) {
  const validItems = items.filter((item) => item && typeof item === "object");
  if (validItems.length === 0) {
    return <Empty description={emptyText} />;
  }

  return (
    <Tabs
      items={validItems.map((item, index) => {
        const name = itemName(item, index);
        return {
          key: item.asset_id || item.assetId || `${itemType(item)}-${index}`,
          label: name,
          children: renderPreview(item, index),
        };
      })}
    />
  );
}

export default DisplayContentPreview;
