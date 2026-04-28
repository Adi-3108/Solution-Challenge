type LogLevel = "debug" | "info" | "warn" | "error";

const ORDER: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

const currentLevel = ((import.meta.env.VITE_LOG_LEVEL ?? "info") as LogLevel);

const shouldLog = (level: LogLevel): boolean => ORDER[level] >= ORDER[currentLevel];

export const logger = {
  debug: (message: string, context?: unknown): void => {
    if (shouldLog("debug")) {
      console.debug(message, context);
    }
  },
  info: (message: string, context?: unknown): void => {
    if (shouldLog("info")) {
      console.info(message, context);
    }
  },
  warn: (message: string, context?: unknown): void => {
    if (shouldLog("warn")) {
      console.warn(message, context);
    }
  },
  error: (message: string, context?: unknown): void => {
    if (shouldLog("error")) {
      console.error(message, context);
    }
  },
};

