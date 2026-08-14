import { z } from "zod";

/**
 * The one place a __ENTITY__'s shape is defined. The server action validates
 * here before anything reaches the database, so an invalid request is rejected
 * with a message a person can act on rather than a stack trace.
 */
export const __ENTITY__Schema = z.object({
  guest_name: z
    .string()
    .trim()
    .min(2, "Please give a name of at least 2 characters.")
    .max(120, "That name is too long."),
  phone: z
    .string()
    .trim()
    .min(6, "Please give a phone number we can reach you on.")
    .max(32, "That phone number is too long."),
  starts_at: z
    .string()
    .refine((value) => !Number.isNaN(Date.parse(value)), "Please choose a date and time."),
  party_size: z.coerce
    .number()
    .int("Party size must be a whole number.")
    .min(1, "A party is at least one person.")
    .max(20, "For parties over 20, please call us."),
});

export type __ENTITY_PASCAL__Input = z.infer<typeof __ENTITY__Schema>;

export function parse__ENTITY_PASCAL__(input: unknown) {
  return __ENTITY__Schema.safeParse(input);
}
