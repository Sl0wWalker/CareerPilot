const en = {
  appName: "CareerPilot",
  workspace: "Workspace",
  localService: "Local service",
} as const;

const es: Record<keyof typeof en, string> = {
  appName: "CareerPilot",
  workspace: "Espacio de trabajo",
  localService: "Servicio local",
};

const fr: Record<keyof typeof en, string> = {
  appName: "CareerPilot",
  workspace: "Espace de travail",
  localService: "Service local",
};

const de: Record<keyof typeof en, string> = {
  appName: "CareerPilot",
  workspace: "Arbeitsbereich",
  localService: "Lokaler Dienst",
};

type MessageKey = keyof typeof en;

const catalogs: Record<string, Record<MessageKey, string>> = { de, en, es, fr };

export function t(key: MessageKey, locale = navigator.language.split("-")[0]) {
  return catalogs[locale]?.[key] ?? en[key];
}
