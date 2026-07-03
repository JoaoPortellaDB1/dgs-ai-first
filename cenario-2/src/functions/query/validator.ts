import { z } from "zod";

/**
 * Input do query endpoint (T-01).
 * clientTier é restrito aos tiers reais da NovaTech (SLA-2024): nunca aceita "Platinum".
 */
export const QueryRequestSchema = z.object({
  question: z.string().trim().min(1, "question é obrigatória").max(1000, "question excede 1000 caracteres"),
  clientTier: z.enum(["Gold", "Silver", "Standard"]).optional(),
  conversationId: z.string().uuid().optional(),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

export type ParseResult =
  | { success: true; data: QueryRequest }
  | { success: false; error: string; details: z.ZodIssue[] };

/**
 * Valida o body cru da requisição. Não lança: JSON malformado ou schema inválido
 * viram ParseResult.success = false, para o handler responder 400 de forma controlada.
 */
export function parseQueryRequest(rawBody: unknown): ParseResult {
  const result = QueryRequestSchema.safeParse(rawBody);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return {
    success: false,
    error: "Requisição inválida",
    details: result.error.issues,
  };
}
