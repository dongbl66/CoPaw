import { describe, expect, it } from "vitest";
import type { MarketingResultRecord } from "@/api/modules/marketingResult";
import {
  extractStructuredResultFromPayload,
  toStructuredResultEventFromRecord,
} from "./utils";

function createMarketingResultRecord(
  overrides: Partial<MarketingResultRecord> = {},
): MarketingResultRecord {
  return {
    id: 1,
    title: "Structured marketing result",
    result_type: "product",
    save_status: "saved",
    scene: "marketing",
    summary: "Fallback summary",
    detail_content: [],
    info: {},
    basic_info: {},
    product_info: {},
    attachments: [],
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    ...overrides,
  };
}

describe("result-panel utils", () => {
  it("returns a stored structured result when the record payload is valid", () => {
    const record = createMarketingResultRecord({
      info: {
        structuredResult: {
          eventType: "structured_result",
          version: "1.0",
          title: "Stored result",
          result: {
            type: "text",
            payload: {
              text: "Stored body",
            },
          },
        },
      },
    });

    expect(toStructuredResultEventFromRecord(record)).toEqual(
      expect.objectContaining({
        title: "Stored result",
        result: expect.objectContaining({
          type: "text",
        }),
      }),
    );
  });

  it("falls back to the record summary when no valid structured result is stored", () => {
    const record = createMarketingResultRecord({
      title: "Fallback title",
      scene: "retail",
      summary: "Summary text",
      info: {
        structuredResult: {
          eventType: "not_structured",
        },
      },
    });

    expect(toStructuredResultEventFromRecord(record)).toEqual(
      expect.objectContaining({
        eventType: "structured_result",
        title: "Fallback title",
        subtitle: "retail",
        result: {
          type: "text",
          payload: {
            text: "Summary text",
          },
        },
      }),
    );
  });

  it("extracts a structured result from direct push-event payloads", () => {
    const payload = {
      object: "structured_result_event",
      status: "completed",
      structured_result: {
        eventType: "structured_result",
        version: "1.0",
        title: "Direct payload",
        result: {
          type: "text",
          payload: {
            text: "Direct body",
          },
        },
      },
    };

    expect(extractStructuredResultFromPayload(payload)).toEqual(
      payload.structured_result,
    );
  });

  it("extracts a structured result from chat output metadata payloads", () => {
    const payload = {
      output: [
        {
          metadata: {
            structured_result: {
              eventType: "structured_result",
              version: "1.0",
              title: "Metadata payload",
              result: {
                type: "text",
                payload: {
                  text: "Metadata body",
                },
              },
            },
          },
        },
      ],
    };

    expect(extractStructuredResultFromPayload(payload)).toEqual(
      payload.output[0].metadata.structured_result,
    );
  });
});
