import pino from "pino";

/**
 * Logger estruturado do projeto (AGENTS.md: pino, nunca console.log).
 * `redact` remove segredos e cabeçalhos sensíveis. Dados pessoais do atendente
 * (ex: attendantEmail) NÃO devem ser passados ao logger em nenhum nível.
 */
export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: {
    paths: ["req.headers.authorization", "*.apiKey", "*.token", "*.attendantEmail"],
    remove: true,
  },
});
