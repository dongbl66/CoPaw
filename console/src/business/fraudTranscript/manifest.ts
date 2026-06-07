import { registerBusinessModule } from "@/business/common/registry/registry";
import type { BusinessModuleManifest } from "@/business/common/registry/types";
import FraudTranscriptResultDetailPage from "./pages/ResultDetail";
import FraudTranscriptResultsPage from "./pages/Results";
import FraudTranscriptWorkbenchPage from "./workbench/FraudTranscriptWorkbenchPage";

const fraudTranscriptManifest: BusinessModuleManifest = {
  id: "fraudTranscript",
  name: "fraudTranscript",
  version: "0.1.0",
  enabledByDefault: true,
  routes: [
    {
      key: "biz-fraud-transcript-results",
      path: "/biz/fraud-transcript/results",
      label: "笔录分析报告",
      component: FraudTranscriptResultsPage,
      priority: 40,
      icon: "F",
    },
    {
      key: "biz-fraud-transcript-results-detail",
      path: "/biz/fraud-transcript/results/:resultId",
      label: "笔录分析报告详情",
      component: FraudTranscriptResultDetailPage,
      activeMenuKey: "biz-fraud-transcript-results",
      priority: 41,
      icon: "F",
    },
    {
      key: "biz-fraud-transcript-results-alias",
      path: "/biz-fraud-transcript-results",
      label: "fraud transcript results",
      component: FraudTranscriptResultsPage,
      activeMenuKey: "biz-fraud-transcript-results",
      priority: 42,
      icon: "F",
    },
  ],
  menus: [
    {
      key: "biz-fraud-transcript-results",
      path: "/biz/fraud-transcript/results",
      label: "笔录分析报告",
      groupKey: "fraud-transcript-group",
      priority: 10,
      icon: "F",
    },
  ],
  resultWorkbench: {
    bizModule: "fraud_transcript",
    Page: FraudTranscriptWorkbenchPage,
  },
};

registerBusinessModule(fraudTranscriptManifest);

export default fraudTranscriptManifest;
