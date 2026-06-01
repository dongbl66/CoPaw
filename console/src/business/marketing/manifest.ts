import { registerBusinessModule } from "@/business/common/registry/registry";
import type { BusinessModuleManifest } from "@/business/common/registry/types";
import MarketingOpportunitiesPage from "./pages/Opportunities";
import MarketingOpportunityDetailPage from "./pages/OpportunityDetail";
import MarketingProductSolutionDetailPage from "./pages/ProductSolutionDetail";
import MarketingProductSolutionsPage from "./pages/ProductSolutions";

const marketingManifest: BusinessModuleManifest = {
  id: "marketing",
  name: "marketing",
  version: "0.1.0",
  enabledByDefault: true,
  routes: [
    {
      key: "biz-marketing-product-solutions",
      path: "/biz/marketing/product-solutions",
      label: "产品方案",
      component: MarketingProductSolutionsPage,
      priority: 10,
      icon: "P",
    },
    {
      key: "biz-marketing-product-solutions-detail",
      path: "/biz/marketing/product-solutions/:resultId",
      label: "产品方案详情",
      component: MarketingProductSolutionDetailPage,
      activeMenuKey: "biz-marketing-product-solutions",
      priority: 11,
      icon: "P",
    },
    {
      key: "biz-marketing-opportunities",
      path: "/biz/marketing/opportunities",
      label: "市场商机",
      component: MarketingOpportunitiesPage,
      priority: 20,
      icon: "O",
    },
    {
      key: "biz-marketing-opportunities-detail",
      path: "/biz/marketing/opportunities/:opportunityId",
      label: "市场商机详情",
      component: MarketingOpportunityDetailPage,
      activeMenuKey: "biz-marketing-opportunities",
      priority: 21,
      icon: "O",
    },
  ],
  menus: [
    {
      key: "biz-marketing-product-solutions",
      path: "/biz/marketing/product-solutions",
      label: "产品方案",
      groupKey: "taishan-analysis-group",
      priority: 10,
      icon: "P",
    },
    {
      key: "biz-marketing-opportunities",
      path: "/biz/marketing/opportunities",
      label: "市场商机",
      groupKey: "taishan-analysis-group",
      priority: 20,
      icon: "O",
    },
  ],
};

registerBusinessModule(marketingManifest);

export default marketingManifest;
