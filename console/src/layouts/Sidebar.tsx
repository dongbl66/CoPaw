import {
  Layout,
  Menu,
  Button,
  Modal,
  Input,
  Form,
  Tooltip,
  type MenuProps,
} from "antd";
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAppMessage } from "../hooks/useAppMessage";
import AgentSelector from "../components/AgentSelector";
import {
  SparkChatTabFill,
  SparkDateLine,
  SparkMagicWandLine,
  SparkLocalFileLine,
  SparkModePlazaLine,
  SparkModifyLine,
  SparkDataLine,
  SparkAgentLine,
  SparkExitFullscreenLine,
  SparkSearchUserLine,
  SparkMenuExpandLine,
  SparkMenuFoldLine,
} from "@agentscope-ai/icons";
import { clearAuthToken } from "../api/config";
import { authApi } from "../api/modules/auth";
import { composeBusinessMenus } from "../business/common/registry/composeMenus";
import {
  BUSINESS_MENU_GROUP_META,
  groupBusinessMenus,
} from "../business/common/registry/groupMenus";
import { useCodingMode } from "../stores/codingModeStore";
import styles from "./index.module.less";
import { useTheme } from "../contexts/ThemeContext";
import { KEY_TO_PATH } from "./constants";

// ── Layout ────────────────────────────────────────────────────────────────

const { Sider } = Layout;
const MOBILE_SIDEBAR_QUERY = "(max-width: 768px)";

function isMobileSidebarViewport() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia(MOBILE_SIDEBAR_QUERY).matches
  );
}
const BUSINESS_GROUP_LABEL_MAP: Record<string, { i18nKey: string; fallback: string }> =
  {
    "taishan-analysis-group": {
      i18nKey: "nav.taishanScenario",
      fallback: "泰山石膏",
    },
    "fae-workspace-group": {
      i18nKey: "nav.internalEfficiency",
      fallback: "内部提效",
    },
  };

// ── Types ─────────────────────────────────────────────────────────────────

interface SidebarProps {
  selectedKey: string;
}

const WORKBENCH_MENU_KEYS = new Set(["workspace", "skills"]);
const MANAGEMENT_MENU_KEYS = new Set([
  "cron-jobs",
  "agents",
  "models",
  "token-usage",
  "agent-config",
]);

// ── Sidebar ───────────────────────────────────────────────────────────────

export default function Sidebar({ selectedKey }: SidebarProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { message } = useAppMessage();
  const { isDark } = useTheme();
  const businessMenus = composeBusinessMenus();
  const businessMenuGroups = groupBusinessMenus(
    businessMenus,
    BUSINESS_MENU_GROUP_META,
  );
  const selectedBusinessGroupKey = useMemo(
    () => businessMenus.find((menu) => menu.key === selectedKey)?.groupKey,
    [businessMenus, selectedKey],
  );
  // When coding mode is on, the sidebar "Chat" entry should land on /coding
  // (FileTree + Editor + Chat panel) rather than the bare Chat page.
  const { codingMode } = useCodingMode();
  const chatPath = codingMode ? "/coding" : "/chat";
  const [authEnabled, setAuthEnabled] = useState(false);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [accountLoading, setAccountLoading] = useState(false);
  const [accountForm] = Form.useForm();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(isMobileSidebarViewport);
  const [workbenchOpenKeys, setWorkbenchOpenKeys] = useState<string[]>([
    "workbench-group",
  ]);
  const [managementOpenKeys, setManagementOpenKeys] = useState<string[]>([
    "management-group",
  ]);
  const [sceneOpenKeys, setSceneOpenKeys] = useState<string[]>(() =>
    selectedBusinessGroupKey
      ? ["business-menu-group", selectedBusinessGroupKey]
      : [],
  );

  // ── Effects ──────────────────────────────────────────────────────────────

  useEffect(() => {
    authApi
      .getStatus()
      .then((res) => setAuthEnabled(res.enabled))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function"
    ) {
      return;
    }

    const mediaQuery = window.matchMedia(MOBILE_SIDEBAR_QUERY);
    const syncMobileSidebar = () => {
      setIsMobile(mediaQuery.matches);
      if (mediaQuery.matches) {
        setCollapsed(true);
      }
    };

    syncMobileSidebar();
    mediaQuery.addEventListener("change", syncMobileSidebar);

    return () => {
      mediaQuery.removeEventListener("change", syncMobileSidebar);
    };
  }, []);

  useEffect(() => {
    if (collapsed) {
      return;
    }

    if (WORKBENCH_MENU_KEYS.has(selectedKey)) {
      setWorkbenchOpenKeys((prev) =>
        prev.includes("workbench-group") ? prev : [...prev, "workbench-group"],
      );
    }

    if (MANAGEMENT_MENU_KEYS.has(selectedKey)) {
      setManagementOpenKeys((prev) =>
        prev.includes("management-group")
          ? prev
          : [...prev, "management-group"],
      );
    }

    if (selectedBusinessGroupKey) {
      setSceneOpenKeys((prev) => {
        const next = new Set(prev);
        next.add("business-menu-group");
        next.add(selectedBusinessGroupKey);
        return [...next];
      });
    }
  }, [collapsed, selectedBusinessGroupKey, selectedKey]);
  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleUpdateProfile = async (values: {
    currentPassword: string;
    newUsername?: string;
    newPassword?: string;
  }) => {
    const trimmedUsername = values.newUsername?.trim() || undefined;
    const trimmedPassword = values.newPassword?.trim() || undefined;

    if (values.newPassword && !trimmedPassword) {
      message.error(t("account.passwordEmpty"));
      return;
    }

    if (values.newUsername && !trimmedUsername) {
      message.error(t("account.usernameEmpty"));
      return;
    }

    if (!trimmedUsername && !trimmedPassword) {
      message.warning(t("account.nothingToUpdate"));
      return;
    }

    setAccountLoading(true);
    try {
      await authApi.updateProfile(
        values.currentPassword,
        trimmedUsername,
        trimmedPassword,
      );
      message.success(t("account.updateSuccess"));
      setAccountModalOpen(false);
      accountForm.resetFields();
      clearAuthToken();
      window.location.href = "/login";
    } catch (err: unknown) {
      const raw = err instanceof Error ? err.message : "";
      let msg = t("account.updateFailed");
      if (raw.includes("password is incorrect")) {
        msg = t("account.wrongPassword");
      } else if (raw.includes("Nothing to update")) {
        msg = t("account.nothingToUpdate");
      } else if (raw.includes("cannot be empty")) {
        msg = t("account.nothingToUpdate");
      } else if (raw) {
        msg = raw;
      }
      message.error(msg);
    } finally {
      setAccountLoading(false);
    }
  };

  // ── Collapsed nav items (all leaf pages) ──────────────────────────────

  const collapsedNavItems = [
    {
      key: "chat",
      icon: <SparkChatTabFill size={18} />,
      path: chatPath,
      label: t("nav.chat"),
    },
    {
      key: "workspace",
      icon: <SparkLocalFileLine size={18} />,
      path: "/workspace",
      label: t("nav.workspace"),
    },
    {
      key: "skills",
      icon: <SparkMagicWandLine size={18} />,
      path: "/skills",
      label: t("nav.skills"),
    },
    {
      key: "cron-jobs",
      icon: <SparkDateLine size={18} />,
      path: "/cron-jobs",
      label: t("nav.cronJobs"),
    },
    {
      key: "agents",
      icon: <SparkAgentLine size={18} />,
      path: "/agents",
      label: t("nav.digitalEmployees", "数智员工"),
    },
    {
      key: "models",
      icon: <SparkModePlazaLine size={18} />,
      path: "/models",
      label: t("nav.models"),
    },
    {
      key: "token-usage",
      icon: <SparkDataLine size={18} />,
      path: "/token-usage",
      label: t("nav.tokenUsage"),
    },
    {
      key: "agent-config",
      icon: <SparkModifyLine size={18} />,
      path: "/agent-config",
      label: t("nav.settings"),
    },
    ...businessMenus.map((menu) => ({
      key: menu.key,
      icon: <span style={{ fontSize: 18 }}>{menu.icon ?? "B"}</span>,
      path: menu.path,
      label: menu.label,
    })),
  ];

  // ── Menu items — workbench / management / business ──────────────────────

  const workbenchMenuItems: MenuProps["items"] = [
    {
      key: "workbench-group",
      label: collapsed ? null : t("nav.workbench", "工作台"),
      children: [
        {
          key: "workspace",
          label: collapsed ? null : t("nav.workspace"),
          icon: <SparkLocalFileLine size={16} />,
        },
        {
          key: "skills",
          label: collapsed ? null : t("nav.skills"),
          icon: <SparkMagicWandLine size={16} />,
        },
      ],
    },
  ];

  const managementMenuItems: MenuProps["items"] = [
    {
      key: "management-group",
      label: collapsed ? null : t("nav.management", "管理"),
      children: [
        {
          key: "cron-jobs",
          label: collapsed ? null : t("nav.cronJobs"),
          icon: <SparkDateLine size={16} />,
        },
        {
          key: "agents",
          label: collapsed ? null : t("nav.digitalEmployees", "数智员工"),
          icon: <SparkAgentLine size={16} />,
        },
        {
          key: "models",
          label: collapsed ? null : t("nav.models"),
          icon: <SparkModePlazaLine size={16} />,
        },
        {
          key: "token-usage",
          label: collapsed ? null : t("nav.tokenUsage"),
          icon: <SparkDataLine size={16} />,
        },
        {
          key: "agent-config",
          label: collapsed ? null : t("nav.settings"),
          icon: <SparkModifyLine size={16} />,
        },
      ],
    },
  ];

  const businessMenuItems: MenuProps["items"] = [
    {
      key: "business-menu-group",
      label: collapsed ? null : t("nav.sceneApplications", "场景应用"),
      children: businessMenuGroups.map((group) => {
        const groupLabelMeta = BUSINESS_GROUP_LABEL_MAP[group.key];

        return {
          key: group.key,
          label:
            collapsed
              ? null
              : t(
                  groupLabelMeta?.i18nKey ?? group.label,
                  groupLabelMeta?.fallback ?? group.label,
                ),
          children: group.menus.map((menu) => ({
            key: menu.key,
            label: collapsed ? null : menu.label,
            icon: <span style={{ fontSize: 16 }}>{menu.icon ?? "B"}</span>,
          })),
        };
      }),
    },
  ];

  // ── Render ────────────────────────────────────────────────────────────────

  const siderWidth = collapsed ? (isMobile ? 56 : 72) : 240;

  return (
    <Sider
      width={siderWidth}
      className={`${styles.sider}${
        collapsed ? ` ${styles.siderCollapsed}` : ""
      }${isDark ? ` ${styles.siderDark}` : ""}`}
    >
      {collapsed ? (
        <nav className={styles.collapsedNav}>
          {collapsedNavItems.map((item) => {
            const isActive = selectedKey === item.key;
            return (
              <Tooltip
                key={item.key}
                title={item.label}
                placement="right"
                overlayInnerStyle={{
                  background: "rgba(0,0,0,0.75)",
                  color: "#fff",
                }}
              >
                <button
                  className={`${styles.collapsedNavItem} ${
                    isActive ? styles.collapsedNavItemActive : ""
                  }`}
                  onClick={() => navigate(item.path)}
                >
                  {item.icon}
                </button>
              </Tooltip>
            );
          })}
        </nav>
      ) : (
        <>
          {/* Workbench section: selector + Chat + kept workspace items */}
          <div className={styles.agentScopedSection}>
            <div className={styles.agentSelectorContainer}>
              <AgentSelector collapsed={collapsed} />
              {/* Chat entry — sticky together with agent selector */}
              <button
                className={`${styles.stickyChatButton}${
                  selectedKey === "chat"
                    ? ` ${styles.stickyChatButtonActive}`
                    : ""
                }`}
                onClick={() => navigate(chatPath)}
              >
                <SparkChatTabFill size={16} />
                <span>{t("nav.chat")}</span>
              </button>
            </div>
            <Menu
              mode="inline"
              selectedKeys={[selectedKey]}
              openKeys={workbenchOpenKeys}
              onOpenChange={(keys) =>
                setWorkbenchOpenKeys(keys.map((key) => String(key)))
              }
              onClick={({ key }) => {
                const path = KEY_TO_PATH[String(key)];
                if (path) navigate(path);
              }}
              items={workbenchMenuItems}
              theme={isDark ? "dark" : "light"}
              className={styles.sideMenu}
            />
          </div>

          <div className={styles.managementSection}>
            <Menu
              mode="inline"
              selectedKeys={[selectedKey]}
              openKeys={managementOpenKeys}
              onOpenChange={(keys) =>
                setManagementOpenKeys(keys.map((key) => String(key)))
              }
              onClick={({ key }) => {
                const path = KEY_TO_PATH[String(key)] ?? `/${String(key)}`;
                navigate(path);
              }}
              items={managementMenuItems}
              theme={isDark ? "dark" : "light"}
              className={styles.sideMenu}
            />
          </div>

          <div className={styles.sceneSection}>
            <Menu
              mode="inline"
              selectedKeys={[selectedKey]}
              openKeys={sceneOpenKeys}
              onOpenChange={(keys) =>
                setSceneOpenKeys(keys.map((key) => String(key)))
              }
              onClick={({ key }) => {
                const path = KEY_TO_PATH[String(key)] ?? `/${String(key)}`;
                navigate(path);
              }}
              items={businessMenuItems}
              theme={isDark ? "dark" : "light"}
              className={`${styles.sideMenu} ${styles.sceneMenu}`}
            />
          </div>
        </>
      )}

      {authEnabled && !collapsed && (
        <div className={styles.authActions}>
          <Button
            type="text"
            icon={<SparkSearchUserLine size={16} />}
            onClick={() => {
              accountForm.resetFields();
              setAccountModalOpen(true);
            }}
            block
            className={`${styles.authBtn} ${
              collapsed ? styles.authBtnCollapsed : ""
            }`}
          >
            {!collapsed && t("account.title")}
          </Button>
          <Button
            type="text"
            icon={<SparkExitFullscreenLine size={16} />}
            onClick={() => {
              clearAuthToken();
              window.location.href = "/login";
            }}
            block
            className={`${styles.authBtn} ${
              collapsed ? styles.authBtnCollapsed : ""
            }`}
          >
            {!collapsed && t("login.logout")}
          </Button>
        </div>
      )}

      <div className={styles.collapseToggleContainer}>
        <Button
          type="text"
          icon={
            collapsed ? (
              <SparkMenuExpandLine size={20} />
            ) : (
              <SparkMenuFoldLine size={20} />
            )
          }
          onClick={() => setCollapsed(!collapsed)}
          className={styles.collapseToggle}
        />
      </div>

      <Modal
        open={accountModalOpen}
        onCancel={() => setAccountModalOpen(false)}
        title={t("account.title")}
        footer={null}
        destroyOnHidden
        centered
      >
        <Form
          form={accountForm}
          layout="vertical"
          onFinish={handleUpdateProfile}
        >
          <Form.Item
            name="currentPassword"
            label={t("account.currentPassword")}
            rules={[
              { required: true, message: t("account.currentPasswordRequired") },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item name="newUsername" label={t("account.newUsername")}>
            <Input placeholder={t("account.newUsernamePlaceholder")} />
          </Form.Item>
          <Form.Item name="newPassword" label={t("account.newPassword")}>
            <Input.Password placeholder={t("account.newPasswordPlaceholder")} />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            label={t("account.confirmPassword")}
            dependencies={["newPassword"]}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value && !getFieldValue("newPassword")) {
                    return Promise.resolve();
                  }
                  if (value === getFieldValue("newPassword")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(
                    new Error(t("account.passwordMismatch")),
                  );
                },
              }),
            ]}
          >
            <Input.Password
              placeholder={t("account.confirmPasswordPlaceholder")}
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={accountLoading}
              block
            >
              {t("account.save")}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Sider>
  );
}
