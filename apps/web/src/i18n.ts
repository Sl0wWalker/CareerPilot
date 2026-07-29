const en = {
  appName: "CareerPilot",
  workspace: "Workspace",
  localService: "Local service",
} as const;

type MessageKey = keyof typeof en;

const catalogs: Record<string, Record<MessageKey, string>> = { en };

export function t(key: MessageKey, locale = navigator.language.split("-")[0]) {
  return catalogs[locale]?.[key] ?? en[key];
}
