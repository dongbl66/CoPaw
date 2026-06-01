import type {
  MarketingOpportunityRecord,
  MarketingResultAttachment,
  MarketingResultRecord,
} from "@/api/modules/marketingResult";
import {
  toStructuredResultEventFromRecord,
} from "@/pages/Chat/result-panel/utils";
import type {
  StructuredBusinessPayload,
  StructuredProductPayload,
  StructuredWorkbenchAttachment,
} from "@/pages/Chat/result-panel/types";

function toWorkbenchAttachment(
  attachment: MarketingResultAttachment,
): StructuredWorkbenchAttachment {
  return {
    kind: (attachment.file_type as StructuredWorkbenchAttachment["kind"]) || "file",
    fileName: attachment.file_name,
    fileUrl: attachment.file_url || undefined,
    filePath: attachment.file_path || undefined,
    previewUrl: attachment.preview_url || undefined,
    downloadUrl: attachment.download_url || undefined,
    mimeType: attachment.mime_type || undefined,
    pageIndex: attachment.page_index || undefined,
    extra: attachment.extra,
  };
}

export function toBusinessPayloadFromOpportunity(
  record: MarketingOpportunityRecord,
): StructuredBusinessPayload {
  return {
    title: record.title,
    summary: record.summary || undefined,
    basicInfo: {
      region: record.region,
      source: record.source,
      deadline: record.deadline,
      credibility: record.credibility,
      contact: record.contact,
      updatedAt: record.updated_at,
    },
    opportunities: [
      {
        title: record.title,
        level: record.level || undefined,
        region: record.region || undefined,
        source: record.source || undefined,
        budget: record.budget ?? undefined,
        purchaseAmount: record.purchase_amount ?? undefined,
        linkStatus: record.link_status || undefined,
        reason: record.reason || undefined,
        originalLink: record.original_link || undefined,
        summary: record.summary || undefined,
      },
    ],
    attachments: [],
  };
}

export function toProductPayloadFromRecord(
  record: MarketingResultRecord,
): StructuredProductPayload {
  const structuredResult = toStructuredResultEventFromRecord(record);
  if (structuredResult?.result.type === "product") {
    return structuredResult.result.payload as StructuredProductPayload;
  }

  return {
    title: record.title,
    summary: record.summary || undefined,
    scene: record.scene || undefined,
    basicInfo: record.basic_info,
    productInfo: record.product_info,
    richText: record.summary || undefined,
    attachments: record.attachments.map(toWorkbenchAttachment),
  };
}

export function getOpportunityDetailPath(opportunityId: number): string {
  return `/biz/marketing/opportunities/${opportunityId}`;
}

export function getProductSolutionDetailPath(resultId: number): string {
  return `/biz/marketing/product-solutions/${resultId}`;
}
