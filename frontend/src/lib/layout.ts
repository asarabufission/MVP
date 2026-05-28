/** App shell main padding (`p-8` top + bottom). */
const SHELL_PY = "4rem";

/**
 * Max scroll height for tables in the main column.
 * Sidebar uses `h-screen` (100vh); subtract shell padding and page chrome above/below the table.
 */
export const JOB_RUNS_TABLE_SCROLL_MAX =
  `max-h-[calc(100vh-${SHELL_PY}-14rem)]` as const;

export const DASHBOARD_ACTIVITY_TABLE_SCROLL_MAX =
  `max-h-[calc(100vh-${SHELL_PY}-26rem)]` as const;
