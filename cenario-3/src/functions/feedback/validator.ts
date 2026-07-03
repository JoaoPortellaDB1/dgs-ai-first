import { z } from "zod";

/**
 * Validação de input do feedback (AGENTS.md: todo input externo validado com Zod).
 * `.strict()` rejeita campos não previstos.
 */
export const FeedbackSchema = z
  .object({
    queryId: z.string().min(1),
    rating: z.number().int().min(1).max(5),
    comment: z.string().max(2000).optional(),
    attendantEmail: z.string().email(),
  })
  .strict();

export type Feedback = z.infer<typeof FeedbackSchema>;
