import { registerBusinessModule } from "@/business/common/registry/registry";
import type { BusinessModuleManifest } from "@/business/common/registry/types";
import GovernmentOpportunityDetailPage from "./pages/GovernmentOpportunityDetail";
import GovernmentOpportunitiesPage from "./pages/GovernmentOpportunities";
import FaeResultDetailPage from "./pages/ResultDetail";
import FaeResultsPage from "./pages/Results";
import FaeWorkbenchPage from "./workbench/FaeWorkbenchPage";

const faeManifest: BusinessModuleManifest = {
  id: "fae",
  name: "fae",
  version: "0.1.0",
  enabledByDefault: true,
  routes: [
    {
      key: "biz-fae-results",
      path: "/biz/fae/results",
      label: "FAE Saved Results",
      component: FaeResultsPage,
      priority: 28,
      icon: "F",
    },
    {
      key: "biz-fae-results-detail",
      path: "/biz/fae/results/:resultId",
      label: "FAE Result Detail",
      component: FaeResultDetailPage,
      activeMenuKey: "biz-fae-results",
      priority: 29,
      icon: "F",
    },
    {
      key: "biz-fae-government-opportunities",
      path: "/biz/fae/government-opportunities",
      label: "政企商机",
      component: GovernmentOpportunitiesPage,
      priority: 30,
      icon: "F",
    },
    {
      key: "biz-fae-government-opportunities-detail",
      path: "/biz/fae/government-opportunities/:projectId",
      label: "政企商机详情",
      component: GovernmentOpportunityDetailPage,
      activeMenuKey: "biz-fae-government-opportunities",
      priority: 31,
      icon: "F",
    },
  ],
  menus: [
    {
      key: "biz-fae-results",
      path: "/biz/fae/results",
      label: "FAE Saved Results",
      groupKey: "fae-workspace-group",
      priority: 5,
      icon: "F",
    },
    {
      key: "biz-fae-government-opportunities",
      path: "/biz/fae/government-opportunities",
      label: "政企商机",
      groupKey: "fae-workspace-group",
      priority: 10,
      icon: "F",
    },
  ],
  resultWorkbench: {
    bizModule: "fae",
    Page: FaeWorkbenchPage,
  },
};

registerBusinessModule(faeManifest);

export default faeManifest;
