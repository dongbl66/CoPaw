export type StructuredResultType =
  | "business"
  | "product"
  | "web"
  | "pdf"
  | "html"
  | "table"
  | "text"
  | "view_model"
  | "actions"
  | (string & {});

export interface StructuredResultAction {
  key: string;
  label: string;
  actionType: "open_url" | "download" | "copy" | "emit_event";
  payload?: Record<string, unknown>;
}

export interface StructuredResultTableColumn {
  key: string;
  title: string;
  dataIndex?: string;
}

export interface StructuredResultEvent {
  eventType: "structured_result";
  version: string;
  title?: string;
  subtitle?: string;
  result: {
    type: StructuredResultType;
    payload: unknown;
  };
  layout?: {
    autoOpen?: boolean;
    replace?: boolean;
    panelWidth?: number;
  };
  meta?: {
    bizModule?: string;
    source?: string;
    timestamp?: number;
  };
}

export interface StructuredResultPushEvent {
  object: "structured_result_event";
  status: string;
  session_id?: string;
  message_id?: string;
  structured_result: StructuredResultEvent;
}

export interface StructuredTextPayload {
  text: string;
  markdown?: boolean;
}

export interface StructuredWebPayload {
  url: string;
}

export interface StructuredPdfPayload {
  fileUrl?: string;
  filePath?: string;
  fileName?: string;
}

export interface StructuredHtmlPayload {
  html?: string;
  url?: string;
}

export interface StructuredTablePayload {
  columns: StructuredResultTableColumn[];
  rows: Record<string, unknown>[];
}

export interface StructuredActionsPayload {
  actions: StructuredResultAction[];
}

export interface StructuredViewModelField {
  key?: string;
  label: string;
  value?: string | number | null;
  variant?: "text" | "tag";
  color?: string;
}

export interface StructuredViewModelSection {
  key: string;
  title: string;
  fields?: StructuredViewModelField[];
  text?: string;
  attachments?: StructuredWorkbenchAttachment[];
}

export interface StructuredViewModelPayload {
  summary?: string;
  sections: StructuredViewModelSection[];
}

export interface StructuredWorkbenchAttachment {
  kind: "pdf" | "html" | "web" | "image" | "file";
  fileName?: string;
  fileUrl?: string;
  filePath?: string;
  previewUrl?: string;
  downloadUrl?: string;
  mimeType?: string;
  pageIndex?: number;
  extra?: Record<string, unknown>;
}

export interface StructuredBusinessOpportunity {
  title: string;
  level?: string;
  type?: string;
  region?: string;
  source?: string;
  publishTime?: string;
  deadline?: string;
  credibility?: string | number;
  contact?: string;
  budget?: string | number;
  purchaseAmount?: string | number;
  linkStatus?: string;
  reason?: string;
  originalLink?: string;
  summary?: string;
}

export interface StructuredBusinessPayload {
  title?: string;
  summary?: string;
  scene?: string;
  basicInfo?: Record<string, unknown>;
  productInfo?: Record<string, unknown>;
  opportunities?: StructuredBusinessOpportunity[];
  attachments?: StructuredWorkbenchAttachment[];
}

export interface StructuredProductPayload {
  title?: string;
  summary?: string;
  scene?: string;
  basicInfo?: Record<string, unknown>;
  productInfo?: Record<string, unknown>;
  richText?: string;
  attachments?: StructuredWorkbenchAttachment[];
}
