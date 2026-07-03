import pino from "pino";

/**
 * Logger estruturado do projeto (ADR: pino, nunca console.log).
 * Nível controlado por env; default info em produção, debug em dev.
 */
export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: {
    // Nunca vazar segredos ou dado de cliente em logs estruturados.
    paths: ["req.headers.authorization", "*.apiKey", "*.token"],
    remove: true,
  },
});
