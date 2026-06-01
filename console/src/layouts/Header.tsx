import { Layout, Space } from "antd";
import LanguageSwitcher from "../components/LanguageSwitcher";
import ThemeToggleButton from "../components/ThemeToggleButton";
import styles from "./index.module.less";

const { Header: AntHeader } = Layout;

export default function Header() {
  return (
    <AntHeader className={styles.header}>
      <div className={styles.brandShell}>
        <span className={styles.brandMark} aria-hidden="true" />
        <span className={styles.brandText}>FAE Console</span>
      </div>

      <Space size={10} className={styles.headerControls}>
        <LanguageSwitcher />
        <ThemeToggleButton />
      </Space>
    </AntHeader>
  );
}
